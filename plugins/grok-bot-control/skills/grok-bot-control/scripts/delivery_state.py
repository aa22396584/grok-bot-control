#!/usr/bin/env python3
"""Maintain a local SQLite delivery journal without sending any messages."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn


SHA256 = re.compile(r"^[0-9a-f]{64}$")
TRANSPORTS = {"cli", "ui"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS deliveries (
    scope TEXT NOT NULL,
    target TEXT NOT NULL,
    digest TEXT NOT NULL,
    operator TEXT NOT NULL,
    reserved_transport TEXT NOT NULL CHECK (reserved_transport IN ('cli', 'ui')),
    state TEXT NOT NULL CHECK (state IN ('uncertain', 'confirmed')),
    reserved_at TEXT NOT NULL,
    baseline_ids TEXT,
    confirmed_transport TEXT CHECK (confirmed_transport IN ('cli', 'ui')),
    confirmed_at TEXT,
    PRIMARY KEY (scope, target, digest)
)
"""


class JournalError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise JournalError("invalid_input", f"{field} must be a non-blank string")
    return value


def _digest(value: Any) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise JournalError("invalid_input", "digest must be a lowercase SHA-256 string")
    return value


def _transport(value: Any) -> str:
    if not isinstance(value, str) or value not in TRANSPORTS:
        raise JournalError("invalid_input", "transport must be cli or ui")
    return value


def _validate_scope(scope: str, target: str, digest: str) -> tuple[str, str, str]:
    return _text(scope, "scope"), _text(target, "target"), _digest(digest)


def _journal_path(value: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise JournalError("unsafe_journal_path", "journal path must be absolute")
    return path


def _baseline_ids(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) > 100:
        raise JournalError("invalid_input", "baseline_ids must be a list of at most 100 strings or null")
    checked = [_text(item, "baseline_ids item") for item in value]
    if len(set(checked)) != len(checked):
        raise JournalError("invalid_input", "baseline_ids must contain unique strings")
    return checked


def _stored_baseline(value: Any) -> list[str] | None:
    if value is None:
        return None
    try:
        return _baseline_ids(json.loads(value))
    except (JournalError, json.JSONDecodeError, TypeError) as exc:
        raise JournalError("journal_unavailable", "journal contains invalid delivery evidence") from exc


def _validate_existing_path(path: Path) -> None:
    if path.is_symlink():
        raise JournalError("unsafe_journal_path", "journal path must not be a symlink")
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise JournalError("journal_unavailable", "journal is unavailable") from exc
    if not stat.S_ISREG(mode):
        raise JournalError("unsafe_journal_path", "journal path must be a regular file")
    if os.name != "nt" and stat.S_IMODE(mode) & 0o077:
        raise JournalError("insecure_journal", "journal must not be group or world accessible")
    parent = path.parent
    try:
        parent_mode = parent.stat().st_mode
    except OSError as exc:
        raise JournalError("journal_unavailable", "journal parent is unavailable") from exc
    if parent.is_symlink() or not stat.S_ISDIR(parent_mode):
        raise JournalError("unsafe_journal_path", "journal parent must be a directory")
    if os.name != "nt" and stat.S_IMODE(parent_mode) & 0o077:
        raise JournalError("insecure_parent", "journal parent must not be group or world accessible")


def _prepare_parent(path: Path) -> None:
    parent = path.parent
    try:
        if not parent.exists():
            parent.mkdir(mode=0o700, parents=True)
        if parent.is_symlink() or not parent.is_dir():
            raise JournalError("unsafe_journal_path", "journal parent must be a directory")
        if os.name != "nt" and stat.S_IMODE(parent.stat().st_mode) & 0o077:
            raise JournalError("insecure_parent", "journal parent must not be group or world accessible")
    except JournalError:
        raise
    except OSError as exc:
        raise JournalError("journal_unavailable", "journal parent is unavailable") from exc


def _prepare_journal(path: Path) -> None:
    _prepare_parent(path)
    if not path.exists():
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(path, flags, 0o600)
        except FileExistsError:
            pass
        except OSError as exc:
            raise JournalError("journal_unavailable", "journal could not be created") from exc
        else:
            os.close(descriptor)
    _validate_existing_path(path)
    try:
        path.chmod(0o600)
    except OSError as exc:
        raise JournalError("journal_unavailable", "journal permissions could not be secured") from exc


def _connect(path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    try:
        if read_only:
            database = path.absolute().as_uri() + "?mode=ro"
            connection = sqlite3.connect(
                database, timeout=5, isolation_level=None, uri=True
            )
            connection.execute("PRAGMA query_only = ON")
        else:
            connection = sqlite3.connect(path, timeout=5, isolation_level=None)
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection
    except sqlite3.Error as exc:
        raise JournalError("journal_unavailable", "journal database is unavailable") from exc


def _rollback(connection: sqlite3.Connection) -> None:
    try:
        connection.rollback()
    except sqlite3.Error:
        pass


def _record_result(
    state: str, reason: str, baseline_ids: list[str] | None = None
) -> dict[str, Any]:
    return {
        "state": state,
        "blocks_send": state in {"uncertain", "confirmed"},
        "reason": reason,
        "baseline_ids": baseline_ids,
    }


def read_delivery(path: Path, scope: str, target: str, digest: str) -> dict[str, Any]:
    """Read one delivery and any same-target uncertainty without creating a journal."""
    scope, target, digest = _validate_scope(scope, target, digest)
    path = _journal_path(path)
    if path.is_symlink():
        raise JournalError("unsafe_journal_path", "journal path must not be a symlink")
    if not path.exists():
        return _record_result("not_attempted", "no_record")
    _validate_existing_path(path)
    connection = _connect(path, read_only=True)
    try:
        row = connection.execute(
            "SELECT state, baseline_ids FROM deliveries WHERE scope = ? AND target = ? AND digest = ?",
            (scope, target, digest),
        ).fetchone()
        if row:
            return _record_result(row[0], "matching_delivery", _stored_baseline(row[1]))
        unresolved = connection.execute(
            "SELECT 1 FROM deliveries WHERE scope = ? AND target = ? AND state = 'uncertain' LIMIT 1",
            (scope, target),
        ).fetchone()
        if unresolved:
            return {
                "state": "not_attempted",
                "blocks_send": True,
                "reason": "other_uncertain_delivery",
                "baseline_ids": None,
            }
        return _record_result("not_attempted", "no_record")
    except sqlite3.Error as exc:
        raise JournalError("journal_unavailable", "journal database could not be read") from exc
    finally:
        connection.close()


def begin_delivery(
    path: Path,
    scope: str,
    target: str,
    digest: str,
    operator: str,
    transport: str,
    baseline_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Atomically reserve an uncertain delivery before an external send attempt."""
    scope, target, digest = _validate_scope(scope, target, digest)
    operator = _text(operator, "operator")
    transport = _transport(transport)
    baseline_ids = _baseline_ids(baseline_ids)
    path = _journal_path(path)
    _prepare_journal(path)
    connection = _connect(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(SCHEMA)
        row = connection.execute(
            "SELECT state FROM deliveries WHERE scope = ? AND target = ? AND digest = ?",
            (scope, target, digest),
        ).fetchone()
        if row:
            connection.commit()
            return {
                **_record_result(row[0], "duplicate_delivery"),
                "reserved": False,
            }
        unresolved = connection.execute(
            "SELECT 1 FROM deliveries WHERE scope = ? AND target = ? AND state = 'uncertain' LIMIT 1",
            (scope, target),
        ).fetchone()
        if unresolved:
            connection.commit()
            return {
                "state": "not_attempted",
                "blocks_send": True,
                "reason": "other_uncertain_delivery",
                "reserved": False,
            }
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        connection.execute(
            """INSERT INTO deliveries
               (scope, target, digest, operator, reserved_transport, state, reserved_at, baseline_ids)
               VALUES (?, ?, ?, ?, ?, 'uncertain', ?, ?)""",
            (
                scope,
                target,
                digest,
                operator,
                transport,
                now,
                json.dumps(baseline_ids, ensure_ascii=False) if baseline_ids is not None else None,
            ),
        )
        connection.commit()
        return {
            "state": "uncertain",
            "blocks_send": True,
            "reason": "delivery_reserved",
            "reserved": True,
        }
    except sqlite3.Error as exc:
        _rollback(connection)
        raise JournalError("journal_unavailable", "delivery could not be reserved") from exc
    finally:
        connection.close()


def confirm_delivery(
    path: Path,
    scope: str,
    target: str,
    digest: str,
    transport: str,
) -> dict[str, Any]:
    """Confirm an existing matching reservation with caller-recorded evidence."""
    scope, target, digest = _validate_scope(scope, target, digest)
    transport = _transport(transport)
    path = _journal_path(path)
    if path.is_symlink():
        raise JournalError("unsafe_journal_path", "journal path must not be a symlink")
    if not path.exists():
        return {
            "state": "not_attempted",
            "blocks_send": False,
            "reason": "reservation_missing",
            "confirmed": False,
        }
    _validate_existing_path(path)
    connection = _connect(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT state FROM deliveries WHERE scope = ? AND target = ? AND digest = ?",
            (scope, target, digest),
        ).fetchone()
        if not row:
            connection.commit()
            return {
                "state": "not_attempted",
                "blocks_send": False,
                "reason": "reservation_missing",
                "confirmed": False,
            }
        if row[0] == "confirmed":
            connection.commit()
            return {
                "state": "confirmed",
                "blocks_send": True,
                "reason": "already_confirmed",
                "confirmed": True,
            }
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        connection.execute(
            """UPDATE deliveries
               SET state = 'confirmed', confirmed_transport = ?, confirmed_at = ?
               WHERE scope = ? AND target = ? AND digest = ? AND state = 'uncertain'""",
            (transport, now, scope, target, digest),
        )
        connection.commit()
        return {
            "state": "confirmed",
            "blocks_send": True,
            "reason": "delivery_confirmed",
            "confirmed": True,
        }
    except sqlite3.Error as exc:
        _rollback(connection)
        raise JournalError("journal_unavailable", "delivery could not be confirmed") from exc
    finally:
        connection.close()


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        print(json.dumps({"error": {"code": "invalid_input", "message": "invalid command arguments"}}))
        self.exit(2)


def _common(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("journal", type=Path)
    subparser.add_argument("--scope", required=True)
    subparser.add_argument("--target", required=True)
    subparser.add_argument("--message-sha256", required=True)


def main() -> int:
    parser = SafeArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=SafeArgumentParser)
    inspect_parser = commands.add_parser("inspect")
    _common(inspect_parser)
    begin_parser = commands.add_parser("begin")
    _common(begin_parser)
    begin_parser.add_argument("--operator", required=True)
    begin_parser.add_argument("--transport", required=True, choices=sorted(TRANSPORTS))
    begin_parser.add_argument("--baseline-id", action="append")
    confirm_parser = commands.add_parser("confirm")
    _common(confirm_parser)
    confirm_parser.add_argument("--transport", required=True, choices=sorted(TRANSPORTS))
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            result = read_delivery(args.journal, args.scope, args.target, args.message_sha256)
        elif args.command == "begin":
            result = begin_delivery(
                args.journal,
                args.scope,
                args.target,
                args.message_sha256,
                args.operator,
                args.transport,
                args.baseline_id,
            )
        else:
            result = confirm_delivery(
                args.journal,
                args.scope,
                args.target,
                args.message_sha256,
                args.transport,
            )
    except JournalError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": str(exc)}}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
