#!/usr/bin/env python3

from __future__ import annotations

import concurrent.futures
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/delivery_state.py"
SPEC = importlib.util.spec_from_file_location("delivery_state", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DIGEST = "a" * 64
OTHER_DIGEST = "b" * 64


class DeliveryJournalTests(unittest.TestCase):
    def test_relative_paths_are_refused_before_file_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            absolute = Path(tmp) / "journal.sqlite3"
            relative = Path(os.path.relpath(absolute, Path.cwd()))
            calls = (
                lambda: MODULE.read_delivery(relative, "task", "target", DIGEST),
                lambda: MODULE.begin_delivery(
                    relative, "task", "target", DIGEST, "agent", "ui"
                ),
                lambda: MODULE.confirm_delivery(relative, "task", "target", DIGEST, "ui"),
            )
            for call in calls:
                with self.subTest(call=call):
                    with self.assertRaises(MODULE.JournalError) as caught:
                        call()
                    self.assertEqual(caught.exception.code, "unsafe_journal_path")
                    self.assertFalse(absolute.exists())

    def test_missing_inspect_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            result = MODULE.read_delivery(path, "task", "target", DIGEST)
            self.assertEqual(result["state"], "not_attempted")
            self.assertFalse(result["blocks_send"])
            self.assertFalse(path.exists())

    def test_inspect_uses_query_only_connection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            MODULE.begin_delivery(path, "task", "target", DIGEST, "agent", "ui")
            connection = MODULE._connect(path, read_only=True)
            try:
                self.assertEqual(connection.execute("PRAGMA query_only").fetchone()[0], 1)
                with self.assertRaises(MODULE.sqlite3.OperationalError):
                    connection.execute("DELETE FROM deliveries")
            finally:
                connection.close()

    def test_concurrent_begin_has_one_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            barrier = threading.Barrier(2)

            def reserve(operator):
                barrier.wait()
                return MODULE.begin_delivery(
                    path, "task", "target", DIGEST, operator, "ui"
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(reserve, ("one", "two")))
            self.assertEqual(sum(result["reserved"] for result in results), 1)
            self.assertTrue(all(result["blocks_send"] for result in results))
            self.assertEqual(MODULE.read_delivery(path, "task", "target", DIGEST)["state"], "uncertain")

    def test_reservation_survives_process_crash_like_disconnect(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            MODULE.begin_delivery(path, "task", "target", DIGEST, "agent", "cli")
            result = MODULE.read_delivery(path, "task", "target", DIGEST)
            self.assertEqual(result["state"], "uncertain")
            self.assertTrue(result["blocks_send"])

    def test_baseline_ids_persist_for_matching_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            baseline = ["message-1", "訊息-2"]
            MODULE.begin_delivery(
                path,
                "task",
                "target",
                DIGEST,
                "agent",
                "cli",
                baseline_ids=baseline,
            )
            self.assertEqual(
                MODULE.read_delivery(path, "task", "target", DIGEST)["baseline_ids"],
                baseline,
            )

    def test_confirmed_delivery_blocks_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            MODULE.begin_delivery(path, "task", "target", DIGEST, "agent", "cli")
            confirmed = MODULE.confirm_delivery(path, "task", "target", DIGEST, "ui")
            duplicate = MODULE.begin_delivery(path, "task", "target", DIGEST, "agent", "ui")
            self.assertTrue(confirmed["confirmed"])
            self.assertEqual(duplicate["state"], "confirmed")
            self.assertFalse(duplicate["reserved"])
            self.assertTrue(duplicate["blocks_send"])

    def test_other_unresolved_message_blocks_same_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            MODULE.begin_delivery(path, "task", "target", DIGEST, "agent", "cli")
            result = MODULE.begin_delivery(
                path, "task", "target", OTHER_DIGEST, "agent", "ui"
            )
            self.assertEqual(result["state"], "not_attempted")
            self.assertEqual(result["reason"], "other_uncertain_delivery")
            self.assertFalse(result["reserved"])
            self.assertTrue(result["blocks_send"])

    def test_confirm_requires_existing_uncertain_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            result = MODULE.confirm_delivery(path, "task", "target", DIGEST, "ui")
            self.assertFalse(result["confirmed"])
            self.assertEqual(result["reason"], "reservation_missing")
            self.assertFalse(path.exists())

    def test_journal_is_private_regular_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            MODULE.begin_delivery(path, "task", "target", DIGEST, "agent", "ui")
            self.assertTrue(path.is_file())
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_symlink_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = Path(tmp) / "real.sqlite3"
            link = Path(tmp) / "link.sqlite3"
            real.write_bytes(b"")
            try:
                link.symlink_to(real)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink unavailable: {exc}")
            with self.assertRaises(MODULE.JournalError) as caught:
                MODULE.read_delivery(link, "task", "target", DIGEST)
            self.assertEqual(caught.exception.code, "unsafe_journal_path")

    def test_corrupt_database_returns_sanitized_cli_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            path.write_bytes(b"not sqlite")
            if os.name != "nt":
                path.chmod(0o600)
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT), "inspect", str(path),
                    "--scope", "task", "--target", "target",
                    "--message-sha256", DIGEST,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            error = json.loads(result.stdout)["error"]
            self.assertEqual(error["code"], "journal_unavailable")
            self.assertNotIn(str(path), result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_invalid_fields_and_transport_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            for call in (
                lambda: MODULE.read_delivery(path, "", "target", DIGEST),
                lambda: MODULE.read_delivery(path, "task", "target", "A" * 64),
                lambda: MODULE.begin_delivery(path, "task", "target", DIGEST, "", "ui"),
                lambda: MODULE.begin_delivery(path, "task", "target", DIGEST, "agent", "api"),
                lambda: MODULE.begin_delivery(path, " task", "target", DIGEST, "agent", "ui"),
                lambda: MODULE.begin_delivery(path, "task", "target ", DIGEST, "agent", "ui"),
                lambda: MODULE.begin_delivery(path, "task", "target", DIGEST, " agent", "ui"),
                lambda: MODULE.begin_delivery(
                    path, "task", "target", DIGEST, "agent", "ui", baseline_ids=["same", "same"]
                ),
                lambda: MODULE.begin_delivery(
                    path, "task", "target", DIGEST, "agent", "ui", baseline_ids=[" spaced"]
                ),
            ):
                with self.subTest(call=call):
                    with self.assertRaises(MODULE.JournalError) as caught:
                        call()
                    self.assertEqual(caught.exception.code, "invalid_input")


if __name__ == "__main__":
    unittest.main(verbosity=2)
