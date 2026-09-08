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
SCRIPT = ROOT / "scripts/assess_send.py"
SPEC = importlib.util.spec_from_file_location("assess_send", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DIGEST = "a" * 64


def state(**changes):
    value = {
        "schema_version": 1,
        "phase": "drafting",
        "operator": "codex",
        "conversation": "target-conversation",
        "last_sent": {
            "message_sha256": None,
            "ui_readback_confirmed": False,
            "uncertain_send": False,
            "bot_acknowledged": False,
        },
    }
    value.update(changes)
    return value


class DecisionTests(unittest.TestCase):
    def decide(self, payload=None, operator="codex", observation="absent"):
        checked = MODULE.require_state(payload if payload is not None else state())
        return MODULE.decide(checked, operator, DIGEST, observation)

    def test_single_writer_refuses_other_operator(self):
        self.assertEqual(self.decide(operator="other")["reason"], "different_operator")

    def test_whitespace_conversation_never_authorizes_send(self):
        result = self.decide(state(conversation="   "), observation="matching-draft-only")
        self.assertEqual(result["action"], "inspect")
        self.assertEqual(result["reason"], "conversation_unset")

    def test_absent_draft_can_be_pasted_once(self):
        self.assertEqual(self.decide()["action"], "paste_once")

    def test_matching_draft_can_be_sent_once(self):
        self.assertEqual(self.decide(observation="matching-draft-only")["action"], "send_once")

    def test_matching_sent_is_marked_not_resent(self):
        self.assertEqual(self.decide(observation="matching-sent")["action"], "mark_sent")

    def test_confirmed_digest_stops_duplicate(self):
        sent = {
            "message_sha256": DIGEST,
            "ui_readback_confirmed": True,
            "uncertain_send": False,
            "bot_acknowledged": False,
        }
        self.assertEqual(
            self.decide(state(last_sent=sent))["reason"],
            "message_already_confirmed_sent",
        )

    def test_acknowledged_digest_stops_duplicate_without_ui_bit(self):
        sent = {
            "message_sha256": DIGEST,
            "ui_readback_confirmed": False,
            "uncertain_send": False,
            "bot_acknowledged": True,
        }
        result = self.decide(
            state(last_sent=sent),
            observation="matching-draft-only",
        )
        self.assertEqual(result["action"], "stop")
        self.assertEqual(result["reason"], "message_already_confirmed_sent")

    def test_uncertain_send_requires_resolution(self):
        sent = {
            "message_sha256": DIGEST,
            "ui_readback_confirmed": False,
            "uncertain_send": True,
            "bot_acknowledged": False,
        }
        payload = state(phase="waiting_bot", last_sent=sent)
        self.assertEqual(self.decide(payload, observation="absent")["action"], "inspect")
        self.assertEqual(
            self.decide(payload, observation="matching-draft-only")["action"],
            "send_once",
        )

    def test_terminal_phase_stops(self):
        self.assertEqual(self.decide(state(phase="complete"))["action"], "stop")

    def test_blocked_phase_never_authorizes_send(self):
        for observation in ("absent", "matching-draft-only", "matching-sent"):
            with self.subTest(observation=observation):
                result = self.decide(state(phase="blocked"), observation=observation)
                self.assertEqual(result["action"], "inspect")
                self.assertEqual(result["reason"], "phase_blocked")

    def test_unknown_phase_is_rejected(self):
        with self.assertRaises(MODULE.InputError):
            MODULE.require_state(state(phase="unknown"))

    def test_different_uncertain_digest_cannot_be_bypassed(self):
        sent = {
            "message_sha256": "b" * 64,
            "ui_readback_confirmed": False,
            "uncertain_send": True,
            "bot_acknowledged": False,
        }
        payload = state(phase="waiting_bot", last_sent=sent)
        for observation in ("matching-draft-only", "matching-sent", "absent"):
            with self.subTest(observation=observation):
                result = self.decide(payload, observation=observation)
                self.assertEqual(result["action"], "inspect")
                self.assertEqual(result["reason"], "different_uncertain_send_unresolved")

    def test_invalid_conflicting_state_is_rejected(self):
        sent = {
            "message_sha256": DIGEST,
            "ui_readback_confirmed": True,
            "uncertain_send": True,
            "bot_acknowledged": False,
        }
        with self.assertRaises(MODULE.InputError):
            MODULE.require_state(state(last_sent=sent))


class CliTests(unittest.TestCase):
    def test_cli_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps(state()))
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(path),
                    "--operator",
                    "codex",
                    "--message-sha256",
                    DIGEST,
                    "--observation",
                    "absent",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["action"], "paste_once")
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
