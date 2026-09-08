#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/assess_wait.py"
SPEC = importlib.util.spec_from_file_location("assess_wait", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
NOW = MODULE.parse_time("2026-09-08T02:00:00+08:00", "now")


def state(**changes):
    value = {
        "schema_version": 1,
        "phase": "waiting_bot",
        "operator": "codex",
        "conversation": "target-conversation",
        "waiting_since": "2026-09-08T01:30:00+08:00",
        "last_progress_at": "2026-09-08T01:30:00+08:00",
        "last_nudge_at": None,
        "announced_eta": None,
        "nudges_since_progress": 0,
        "stall_notice_sent": False,
        "last_sent": {
            "uncertain_send": False,
        },
        "nudge_policy": {
            "enabled": True,
            "first_after_minutes": 20,
            "repeat_after_minutes": 30,
            "max_per_stall": 2,
        },
    }
    value.update(changes)
    return value


class DecisionTests(unittest.TestCase):
    def decide(self, **changes):
        return MODULE.decide(MODULE.require_schema(state(**changes)), NOW)

    def test_before_boundary_waits_and_boundary_nudges(self):
        self.assertEqual(self.decide(
            waiting_since="2026-09-08T01:41:00+08:00",
            last_progress_at="2026-09-08T01:41:00+08:00",
        )["action"], "wait")
        self.assertEqual(self.decide(
            waiting_since="2026-09-08T01:40:00+08:00",
            last_progress_at="2026-09-08T01:40:00+08:00",
        )["action"], "nudge_due")

    def test_progress_and_eta_delay_nudge(self):
        self.assertEqual(self.decide(last_progress_at="2026-09-08T01:55:00+08:00")["action"], "wait")
        self.assertEqual(self.decide(announced_eta="2026-09-08T02:45:00+08:00")["action"], "wait")

    def test_repeat_and_cap(self):
        common = {
            "waiting_since": "2026-09-08T00:30:00+08:00",
            "last_progress_at": "2026-09-08T00:30:00+08:00",
        }
        self.assertEqual(self.decide(**common, nudges_since_progress=1,
            last_nudge_at="2026-09-08T01:30:00+08:00")["action"], "nudge_due")
        self.assertEqual(self.decide(**common, nudges_since_progress=2,
            last_nudge_at="2026-09-08T01:30:00+08:00")["action"], "notify_user")
        self.assertEqual(self.decide(**common, nudges_since_progress=2,
            last_nudge_at="2026-09-08T01:30:00+08:00", stall_notice_sent=True)["action"], "none")

    def test_inconsistent_or_future_state_requires_inspection(self):
        self.assertEqual(self.decide(nudges_since_progress=1)["action"], "inspect")
        self.assertEqual(self.decide(last_progress_at="2026-09-08T02:01:00+08:00")["action"], "inspect")

    def test_uncertain_send_and_missing_owner_require_inspection(self):
        self.assertEqual(
            self.decide(last_sent={"uncertain_send": True})["reason"],
            "uncertain_send_unresolved",
        )
        self.assertEqual(self.decide(operator="")["reason"], "missing_operator_or_conversation")
        self.assertEqual(self.decide(conversation=None)["reason"], "missing_operator_or_conversation")

    def test_whitespace_conversation_never_authorizes_nudge(self):
        result = self.decide(conversation="   ")
        self.assertEqual(result["action"], "inspect")
        self.assertEqual(result["reason"], "missing_operator_or_conversation")

    def test_nonwaiting_and_disabled_do_nothing(self):
        self.assertEqual(self.decide(phase="complete")["action"], "none")
        disabled = state()
        disabled["nudge_policy"]["enabled"] = False
        self.assertEqual(MODULE.decide(MODULE.require_schema(disabled), NOW)["action"], "none")


class CliTests(unittest.TestCase):
    def test_cli_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps(state()))
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--now", "2026-09-08T02:00:00+08:00"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["action"], "nudge_due")
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_invalid_schema_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps(state(schema_version=2)))
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["error"]["code"], "invalid_input")


if __name__ == "__main__":
    unittest.main(verbosity=2)
