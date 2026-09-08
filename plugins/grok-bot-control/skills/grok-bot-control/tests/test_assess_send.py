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


def capability_snapshot(**changes):
    value = {
        "schema_version": 1,
        "observed_at": "2026-09-08T01:58:00Z",
        "run_id": "run-current",
        "intent": {
            "operator": "codex",
            "conversation": "target-conversation",
            "message_sha256": DIGEST,
        },
        "target_identity": {"confirmed": True, "evidence": "fresh_target_readback"},
        "send_authorized": True,
        "capabilities": {
            "read_conversation": {"available": True, "evidence": "fresh_state_readback"},
            "read_composer": {"available": True, "evidence": "fresh_state_readback"},
            "write_composer": {"available": True, "evidence": "current_tool_docs"},
            "activate_send": {"available": True, "evidence": "current_tool_docs"},
            "read_sent_state": {"available": True, "evidence": "fresh_state_readback"},
        },
    }
    value.update(changes)
    return value


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
    def bound_command(self, state_path, capability_path, operator="codex"):
        return [
            sys.executable,
            str(SCRIPT),
            str(state_path),
            "--operator", operator,
            "--message-sha256", DIGEST,
            "--observation", "absent",
            "--capabilities", str(capability_path),
            "--run-id", "run-current",
            "--now", "2026-09-08T02:00:00Z",
        ]

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

    def test_bound_capability_contract_allows_existing_send_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            capability_path = Path(tmp) / "capabilities.json"
            state_path.write_text(json.dumps(state()))
            capability_path.write_text(json.dumps(capability_snapshot()))
            result = subprocess.run(
                self.bound_command(state_path, capability_path),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["action"], "paste_once")

    def test_bound_contract_reads_utf8_non_ascii_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            capability_path = Path(tmp) / "capabilities.json"
            operator = "協作員"
            conversation = "工作對話"
            payload = capability_snapshot(intent={
                "operator": operator,
                "conversation": conversation,
                "message_sha256": DIGEST,
            })
            state_path.write_bytes(
                json.dumps(
                    state(operator=operator, conversation=conversation),
                    ensure_ascii=False,
                ).encode("utf-8")
            )
            capability_path.write_bytes(
                json.dumps(payload, ensure_ascii=False).encode("utf-8")
            )
            result = subprocess.run(
                self.bound_command(state_path, capability_path, operator=operator),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["action"], "paste_once")

    def test_bound_contract_rejects_other_intent_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            capability_path = Path(tmp) / "capabilities.json"
            payload = capability_snapshot()
            payload["intent"]["message_sha256"] = "b" * 64
            state_path.write_text(json.dumps(state()))
            capability_path.write_text(json.dumps(payload))
            result = subprocess.run(
                self.bound_command(state_path, capability_path),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["action"], "inspect")
            self.assertEqual(
                json.loads(result.stdout)["reason"],
                "capability_preflight:intent_mismatch",
            )

    def test_bound_contract_honors_revoked_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            capability_path = Path(tmp) / "capabilities.json"
            state_path.write_text(json.dumps(state()))
            capability_path.write_text(json.dumps(capability_snapshot(send_authorized=False)))
            result = subprocess.run(
                self.bound_command(state_path, capability_path),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["action"], "stop")
            self.assertEqual(
                json.loads(result.stdout)["reason"],
                "capability_preflight:send_not_authorized",
            )

    def test_malformed_bound_snapshot_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            capability_path = Path(tmp) / "capabilities.json"
            state_path.write_text(json.dumps(state()))
            capability_path.write_text("[]")
            result = subprocess.run(
                self.bound_command(state_path, capability_path),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["error"]["code"], "invalid_input")
            self.assertNotIn("Traceback", result.stderr)

    def test_invalid_utf8_state_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            capability_path = Path(tmp) / "capabilities.json"
            state_path.write_bytes(b"\xff")
            capability_path.write_text(json.dumps(capability_snapshot()), encoding="utf-8")
            result = subprocess.run(
                self.bound_command(state_path, capability_path),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["error"]["code"], "invalid_input")
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
