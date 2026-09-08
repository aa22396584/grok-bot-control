#!/usr/bin/env python3
"""Optional, explicit CLI adapter. Only check is offline; live commands require opt-in."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import plistlib
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

MAX_MESSAGE_BYTES = 65536
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
CALL_TIMEOUT = 35.0
PINNED_RUNTIME_FILES = {"package.json", "src/cli.js", "src/commands.js", "src/headers.js",
                        "src/transcript.js", "src/store.js", "src/app-session.js", "src/gateway.js"}
SCRIPTS = Path(__file__).resolve().parent


class AdapterError(ValueError):
    """Public, fixed reason code only; never include process output or paths."""


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        print(json.dumps({"ok": False, "error": {"code": "invalid_input"},
                          "retry_allowed": False, "ui_fallback_allowed": False}))
        self.exit(2)


def require(value: object, code: str) -> None:
    if not value:
        raise AdapterError(code)


def journal_module():
    spec = importlib.util.spec_from_file_location("delivery_state", SCRIPTS / "delivery_state.py")
    require(spec and spec.loader, "journal_unavailable")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def verify_source(root: Path, pin: dict[str, Any]) -> None:
    files = pin.get("files")
    if not isinstance(files, dict) or set(files) != PINNED_RUNTIME_FILES:
        raise AdapterError("invalid_source_pin")
    require(all(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
                for digest in files.values()), "invalid_source_pin")
    require(root.is_absolute() and root.is_dir() and not root.is_symlink(), "cli_source_missing")
    for relative, digest in files.items():
        path = root / relative
        require(path.resolve().is_relative_to(root.resolve()), "cli_source_mismatch")
        require(path.is_file() and not path.is_symlink(), "cli_source_mismatch")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "cli_source_mismatch")


def child_environment(source: dict[str, str], node: Path) -> dict[str, str]:
    # App-session authentication only. Never inherit endpoint/token overrides,
    # proxies, NODE_OPTIONS, module paths, or dynamic-loader injection settings.
    env = {key: source[key] for key in ("HOME", "TMPDIR", "SystemRoot") if key in source}
    env["PATH"] = os.pathsep.join((str(node.parent), "/usr/bin", "/bin"))
    env["LANG"] = "en_US.UTF-8"
    return env


def decode_result(returncode: int, stdout: bytes) -> Any:
    require(returncode == 0, "cli_error")
    require(len(stdout) <= MAX_OUTPUT_BYTES, "cli_output_limit")
    try:
        return json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AdapterError("cli_invalid_json") from None


class CliBackend:
    def __init__(self, root: Path, node: Path, pin: dict[str, Any]):
        self.root, self.node, self.pin = root, node, pin

    def call(self, argv: list[str], message: str | None = None) -> Any:
        verify_source(self.root, self.pin)
        command = [str(self.node), str(self.root / "src/cli.js"), "--gateway", "--json", *argv]
        # A private anonymous stdin file avoids both argv exposure and a blocked
        # pipe write before the deadline loop starts. Live support is macOS only.
        with tempfile.TemporaryFile() as stdin:
            if message is not None:
                stdin.write(message.encode("utf-8"))
            stdin.seek(0)
            try:
                proc = subprocess.Popen(
                    command, stdin=stdin, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, cwd=self.root,
                    env=child_environment(dict(os.environ), self.node), start_new_session=True,
                )
            except OSError:
                raise AdapterError("cli_start_failed") from None
            output = bytearray()
            deadline = time.monotonic() + CALL_TIMEOUT
            try:
                stdout_pipe = proc.stdout
                if stdout_pipe is None:
                    raise AdapterError("cli_start_failed")
                with selectors.DefaultSelector() as selector:
                    selector.register(stdout_pipe, selectors.EVENT_READ)
                    while True:
                        remaining = deadline - time.monotonic()
                        require(remaining > 0, "cli_timeout")
                        if not selector.select(remaining):
                            raise AdapterError("cli_timeout")
                        chunk = os.read(stdout_pipe.fileno(), 65536)
                        if not chunk:
                            break
                        require(len(output) + len(chunk) <= MAX_OUTPUT_BYTES, "cli_output_limit")
                        output.extend(chunk)
                proc.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                raise AdapterError("cli_timeout") from None
            finally:
                # Kill any remaining descendants as well as an unfinished CLI.
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
                if proc.stdout:
                    proc.stdout.close()
            return decode_result(proc.returncode, bytes(output))


def validate_message(message: str, digest: str) -> None:
    require(isinstance(message, str) and message and message == message.strip(), "invalid_message")
    require("\0" not in message and len(message.encode("utf-8")) <= MAX_MESSAGE_BYTES, "invalid_message")
    require(re.fullmatch(r"[0-9a-f]{64}", digest), "invalid_message_digest")
    require(hashlib.sha256(message.encode("utf-8")).hexdigest() == digest, "message_digest_mismatch")


def validate_roster(payload: Any) -> list[dict[str, str]]:
    require(isinstance(payload, list), "invalid_roster")
    result = []
    for record in payload:
        require(isinstance(record, dict), "invalid_roster")
        require(all(isinstance(record.get(k), str) and record[k].strip() for k in ("id", "name")), "invalid_roster")
        require(record.get("kind") in {"bot", "group"}, "invalid_roster")
        result.append({k: record[k] for k in ("id", "name", "kind")})
    require(len({r["id"] for r in result}) == len(result), "ambiguous_roster")
    return result


def verify_target(backend: Any, target_id: str, target_name: str) -> None:
    require(target_id and target_name and not target_id.startswith("-"), "invalid_target")
    records = validate_roster(backend.call(["bots", "list"]))
    matches = [r for r in records if r["id"] == target_id or r["name"] == target_id]
    require(len(matches) == 1, "target_missing_or_ambiguous")
    require(matches[0] == {"id": target_id, "name": target_name, "kind": "bot"}, "target_mismatch")


def validate_thread(payload: Any, target_id: str, target_name: str) -> dict[str, Any]:
    require(isinstance(payload, dict), "invalid_thread")
    require(payload.get("target") == {"id": target_id, "name": target_name, "kind": "bot"}, "target_mismatch")
    messages = payload.get("messages")
    require(isinstance(messages, list), "invalid_thread")
    for entry in messages:
        require(isinstance(entry, dict), "invalid_thread")
        require(entry.get("role") in {"user", "assistant", "unknown"}, "invalid_thread")
        require(isinstance(entry.get("text"), str), "invalid_thread")
        message_id = entry.get("id")
        require(message_id is None or isinstance(message_id, str) and message_id.strip() == message_id and message_id, "invalid_thread")
    return payload


def read_thread(backend: Any, target_id: str, target_name: str, limit: int = 50) -> dict[str, Any]:
    require(1 <= limit <= 100, "invalid_limit")
    verify_target(backend, target_id, target_name)
    result = validate_thread(backend.call(["thread", target_id, "--normalized", "--limit", str(limit)]), target_id, target_name)
    return {**result, "received_at": datetime.now(timezone.utc).isoformat()}


def contains_new_outgoing(payload: dict[str, Any], message: str, baseline_ids: list[str]) -> bool:
    return any(entry["role"] == "user" and entry["text"] == message
               and entry.get("id") and entry["id"] not in baseline_ids
               for entry in payload["messages"])


def outcome(state: str, reason: str) -> dict[str, Any]:
    return {"ok": state == "confirmed", "delivery": state, "reason": reason,
            "retry_allowed": False, "ui_fallback_allowed": False}


def send_once(backend: Any, *, journal: Path, scope: str, operator: str,
              target_id: str, target_name: str, message: str, digest: str) -> dict[str, Any]:
    validate_message(message, digest)
    delivery = journal_module()
    state = delivery.read_delivery(journal, scope, target_id, digest)
    if state["blocks_send"]:
        return outcome(state["state"], "delivery_already_recorded")
    before = read_thread(backend, target_id, target_name)
    baseline_ids = list(dict.fromkeys(entry["id"] for entry in before["messages"] if entry.get("id")))
    reservation = delivery.begin_delivery(journal, scope, target_id, digest, operator, "cli", baseline_ids=baseline_ids)
    require(reservation.get("reserved") is True, "delivery_reservation_refused")
    try:
        acknowledgement = backend.call(["send", target_id, "--stdin"], message)
        require(isinstance(acknowledgement, dict) and acknowledgement.get("id") == target_id
                and acknowledgement.get("name") == target_name and acknowledgement.get("kind") == "bot"
                and isinstance(acknowledgement.get("result"), dict), "invalid_send_acknowledgement")
    except (AdapterError, OSError, ValueError):
        return outcome("uncertain", "send_requires_reconciliation")
    # An acknowledgement is neither transcript readback nor completion of the task.
    return reconcile(backend, journal=journal, scope=scope, target_id=target_id,
                     target_name=target_name, message=message, digest=digest)


def reconcile(backend: Any, *, journal: Path, scope: str, target_id: str,
              target_name: str, message: str, digest: str) -> dict[str, Any]:
    validate_message(message, digest)
    delivery = journal_module()
    state = delivery.read_delivery(journal, scope, target_id, digest)
    if state["state"] == "confirmed":
        return outcome("confirmed", "delivery_already_recorded")
    require(state["state"] == "uncertain", "no_recorded_attempt")
    baseline = state.get("baseline_ids")
    if not isinstance(baseline, list):
        return outcome("uncertain", "baseline_unavailable_use_original_surface")
    try:
        after = read_thread(backend, target_id, target_name)
    except (AdapterError, OSError, ValueError):
        return outcome("uncertain", "readback_unavailable")
    if contains_new_outgoing(after, message, baseline):
        delivery.confirm_delivery(journal, scope, target_id, digest, "cli")
        return outcome("confirmed", "matching_outgoing_readback")
    # A missing match in a bounded transcript tail never proves non-delivery.
    return outcome("uncertain", "no_conclusive_readback")


def main() -> int:
    parser = SafeArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["check", "bots", "thread", "send", "reconcile"])
    parser.add_argument("--cli-dir", type=Path, required=True)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--app-bundle", type=Path)
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--allow-send", action="store_true")
    parser.add_argument("--target-id")
    parser.add_argument("--target-name")
    parser.add_argument("--message-file", type=Path)
    parser.add_argument("--message-sha256")
    parser.add_argument("--journal", type=Path)
    parser.add_argument("--scope")
    parser.add_argument("--operator")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    try:
        pin = json.loads((SCRIPTS.parent / "assets/cli-compatibility.json").read_text(encoding="utf-8"))
        verify_source(args.cli_dir, pin)
        require(args.node.is_absolute() and args.node.is_file(), "node_missing")
        if args.operation == "check":
            result = {"ok": True, "source_commit": pin["source_commit"], "source_hashes_verified": True,
                      "node_version": "not_executed_offline", "credential_accessed": False,
                      "network_used": False, "live_compatibility": "requires_current_app_and_target_check"}
        else:
            require(args.allow_live, "live_opt_in_required")
            require(sys.platform == "darwin", "live_host_not_validated")
            require(args.app_bundle == Path("/Applications/Grok Bot.app"), "canonical_app_bundle_required")
            plist_path = args.app_bundle / "Contents/Info.plist"
            require(args.app_bundle.resolve() == args.app_bundle and plist_path.resolve() == plist_path
                    and plist_path.is_file(), "invalid_app_bundle")
            with plist_path.open("rb") as handle:
                app_info = plistlib.load(handle)
            require(app_info.get("CFBundleIdentifier") == pin["app_bundle_id"], "app_identity_mismatch")
            require(app_info.get("CFBundleShortVersionString") in pin["app_versions"], "app_version_not_validated")
            version = subprocess.run([str(args.node), "--version"], capture_output=True, timeout=5,
                                     env=child_environment(dict(os.environ), args.node), check=False)
            node_match = re.fullmatch(rb"v([0-9]+)\.\d+\.\d+\s*", version.stdout)
            require(version.returncode == 0 and node_match is not None, "unsupported_node")
            require(node_match and int(node_match[1]) in pin["node_major_versions"], "unsupported_node")
            backend = CliBackend(args.cli_dir, args.node, pin)
            if args.operation == "bots":
                result = {"ok": True, "bots": validate_roster(backend.call(["bots", "list"]))}
            else:
                require(args.target_id and args.target_name, "target_required")
                if args.operation == "thread":
                    result = {"ok": True, **read_thread(backend, args.target_id, args.target_name, args.limit)}
                else:
                    require(args.message_file and args.journal and args.scope and args.message_sha256, "delivery_arguments_required")
                    require(args.message_file.is_absolute() and args.message_file.is_file() and not args.message_file.is_symlink()
                            and args.message_file.stat().st_size <= MAX_MESSAGE_BYTES, "invalid_message_file")
                    message = args.message_file.read_text(encoding="utf-8")
                    common = dict(journal=args.journal, scope=args.scope, target_id=args.target_id,
                                  target_name=args.target_name, message=message, digest=args.message_sha256)
                    if args.operation == "send":
                        require(args.allow_send and args.operator, "send_opt_in_required")
                        result = send_once(backend, operator=args.operator, **common)
                    else:
                        result = reconcile(backend, **common)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result.get("ok") else 3
    except AdapterError as exc:
        code = str(exc)
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        code = "invalid_input_or_environment"
    print(json.dumps({"ok": False, "error": {"code": code}, "retry_allowed": False, "ui_fallback_allowed": False}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
