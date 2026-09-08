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
SCRIPT = ROOT / "scripts/assess_capabilities.py"
SPEC = importlib.util.spec_from_file_location("assess_capabilities", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DIGEST = "a" * 64
NOW = MODULE.parse_time("2026-09-08T02:00:00Z", "now")


def snapshot(**changes):
    value = {
        "schema_version": 1,
        "observed_at": "2026-09-08T01:58:00Z",
        "run_id": "run-current",
        "intent": {
            "operator": "current-agent",
            "conversation": "review-safe-alias",
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


class DecisionTests(unittest.TestCase):
    def decide(self, payload=None, **scope):
        values = {
            "now": NOW,
            "run_id": "run-current",
            "operator": "current-agent",
            "conversation": "review-safe-alias",
            "message_sha256": DIGEST,
        }
        values.update(scope)
        checked = MODULE.require_snapshot(payload if payload is not None else snapshot())
        return MODULE.decide(checked, **values)

    def test_complete_current_contract_reaches_send_gate(self):
        self.assertEqual(self.decide()["action"], "ready_for_send_gate")

    def test_stale_and_future_observations_are_rejected(self):
        stale = self.decide(snapshot(observed_at="2026-09-08T01:54:59Z"))
        future = self.decide(snapshot(observed_at="2026-09-08T02:00:01Z"))
        self.assertEqual(stale["reason"], "observation_stale")
        self.assertEqual(future["reason"], "observation_from_future")

    def test_five_minute_boundary_is_accepted(self):
        result = self.decide(snapshot(observed_at="2026-09-08T01:55:00Z"))
        self.assertEqual(result["action"], "ready_for_send_gate")

    def test_different_run_is_rejected(self):
        self.assertEqual(self.decide(run_id="run-next")["reason"], "different_run")

    def test_target_and_digest_are_scoped(self):
        target = self.decide(conversation="different-conversation")
        digest = self.decide(message_sha256="b" * 64)
        self.assertEqual(target["fields"], ["conversation"])
        self.assertEqual(digest["fields"], ["message_sha256"])

    def test_revoked_authorization_stops_at_review(self):
        result = self.decide(snapshot(send_authorized=False))
        self.assertEqual(result["action"], "review_only")
        self.assertEqual(result["reason"], "send_not_authorized")

    def test_available_claim_without_evidence_is_not_accepted(self):
        payload = snapshot()
        payload["capabilities"]["activate_send"]["evidence"] = "unknown"
        result = self.decide(payload)
        self.assertEqual(result["action"], "inspect")
        self.assertIn("activate_send", result["capabilities"])

    def test_documentation_is_not_fresh_readback(self):
        payload = snapshot()
        payload["capabilities"]["read_sent_state"]["evidence"] = "current_tool_docs"
        self.assertEqual(self.decide(payload)["reason"], "fresh_readback_missing")

    def test_readable_host_without_send_tool_is_review_only(self):
        payload = snapshot()
        payload["capabilities"]["activate_send"] = {"available": False, "evidence": "unknown"}
        self.assertEqual(self.decide(payload)["action"], "review_only")

    def test_malformed_intent_object_is_structured_invalid_input(self):
        payload = snapshot(intent={"operator": "current-agent"})
        with self.assertRaises(MODULE.InputError):
            MODULE.require_snapshot(payload)

    def test_non_string_evidence_is_rejected_without_type_error(self):
        payload = snapshot()
        payload["capabilities"]["activate_send"]["evidence"] = []
        with self.assertRaises(MODULE.InputError):
            MODULE.require_snapshot(payload)


class CliTests(unittest.TestCase):
    def command(self, path):
        return [
            sys.executable,
            str(SCRIPT),
            str(path),
            "--run-id", "run-current",
            "--operator", "current-agent",
            "--conversation", "review-safe-alias",
            "--message-sha256", DIGEST,
            "--now", "2026-09-08T02:00:00Z",
        ]

    def test_cli_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capabilities.json"
            path.write_text(json.dumps(snapshot()))
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = subprocess.run(self.command(path), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["action"], "ready_for_send_gate")
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_malformed_snapshot_exits_two_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capabilities.json"
            path.write_text(json.dumps(snapshot(intent=[])))
            result = subprocess.run(self.command(path), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["error"]["code"], "invalid_input")
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
