"""Offline adapter contracts: no real CLI, account, or external message."""
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("grok_cli", SCRIPTS / "grok_cli.py")
assert spec and spec.loader
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class FakeBackend:
    def __init__(self):
        self.calls = []
        self.records = [{"id": "test-bot", "name": "Synthetic bot", "kind": "bot"}]
        self.messages = []
        self.fail_send = False
        self.fail_read_after_send = False
        self.append_sent = True
        self.wrong_target = False

    def call(self, argv, message=None):
        self.calls.append((argv, message))
        if argv == ["bots", "list"]:
            return self.records
        if argv[0] == "send":
            if self.append_sent:
                self.messages.append({"id": "new-message", "role": "user", "text": message})
            if self.fail_send:
                raise adapter.AdapterError("cli_timeout")
            return {"id": "test-bot", "name": "Synthetic bot", "kind": "bot", "result": {"accepted": True}}
        if self.fail_read_after_send and any(c[0][0] == "send" for c in self.calls):
            raise adapter.AdapterError("cli_timeout")
        return {"target": {"id": "wrong" if self.wrong_target else "test-bot", "name": "Synthetic bot", "kind": "bot"}, "messages": self.messages.copy()}


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.journal = Path(self.temp.name) / "delivery.sqlite3"
        self.message = "Synthetic request\n請核對結果，不要重送"
        self.digest = hashlib.sha256(self.message.encode()).hexdigest()
        self.backend = FakeBackend()

    def send(self):
        return adapter.send_once(self.backend, journal=self.journal, scope="test-task", operator="test-agent", target_id="test-bot", target_name="Synthetic bot", message=self.message, digest=self.digest)

    def reconcile(self):
        return adapter.reconcile(self.backend, journal=self.journal, scope="test-task", target_id="test-bot", target_name="Synthetic bot", message=self.message, digest=self.digest)

    def test_confirmed_readback_blocks_second_dispatch(self):
        result = self.send()
        self.assertEqual(result["delivery"], "confirmed")
        self.assertEqual(self.send()["reason"], "delivery_already_recorded")
        self.assertEqual(sum(a[0] == "send" for a, _ in self.backend.calls), 1)
        sent = next(c for c in self.backend.calls if c[0][0] == "send")
        self.assertEqual(sent, (["send", "test-bot", "--stdin"], self.message))

    def test_timeout_after_actual_send_never_retries_and_can_reconcile(self):
        self.backend.fail_send = True
        result = self.send()
        self.assertEqual(result["delivery"], "uncertain")
        self.assertFalse(result["retry_allowed"])
        self.assertFalse(result["ui_fallback_allowed"])
        self.send()
        self.assertEqual(sum(a[0] == "send" for a, _ in self.backend.calls), 1)
        self.assertEqual(self.reconcile()["delivery"], "confirmed")

    def test_ack_without_outgoing_readback_is_not_delivery(self):
        self.backend.append_sent = False
        self.assertEqual(self.send()["delivery"], "uncertain")
        self.assertEqual(self.reconcile()["delivery"], "uncertain")

    def test_assistant_echo_does_not_confirm_user_send(self):
        self.backend.append_sent = False
        self.backend.messages = [{"id": "old-assistant", "role": "assistant", "text": self.message}]
        self.assertEqual(self.send()["delivery"], "uncertain")

    def test_old_identical_text_does_not_suppress_new_scoped_intent(self):
        self.backend.messages = [{"id": "old-user", "role": "user", "text": self.message}]
        self.assertEqual(self.send()["delivery"], "confirmed")
        self.assertEqual(sum(a[0] == "send" for a, _ in self.backend.calls), 1)

    def test_stale_identical_text_cannot_confirm_unseen_new_send(self):
        self.backend.append_sent = False
        self.backend.messages = [{"id": "old-user", "role": "user", "text": self.message}]
        self.assertEqual(self.send()["delivery"], "uncertain")
        self.assertEqual(self.reconcile()["delivery"], "uncertain")

    def test_wrong_target_refuses_before_reservation_or_send(self):
        self.backend.wrong_target = True
        with self.assertRaises(adapter.AdapterError):
            self.send()
        self.assertFalse(self.journal.exists())
        self.assertFalse(any(a[0] == "send" for a, _ in self.backend.calls))

    def test_name_collision_with_target_id_refuses(self):
        self.backend.records.append({"id": "other-bot", "name": "test-bot", "kind": "bot"})
        with self.assertRaises(adapter.AdapterError):
            self.send()
        self.assertFalse(self.journal.exists())

    def test_digest_mismatch_refuses_before_backend(self):
        self.digest = "a" * 64
        with self.assertRaises(adapter.AdapterError):
            self.send()
        self.assertEqual(self.backend.calls, [])

    def test_readback_failure_keeps_reservation(self):
        self.backend.fail_read_after_send = True
        self.assertEqual(self.send()["delivery"], "uncertain")
        self.assertEqual(self.send()["reason"], "delivery_already_recorded")

    def test_unknown_message_role_refuses_before_send(self):
        self.backend.messages = [{"id": "old", "role": "invalid-role", "text": "text"}]
        with self.assertRaises(adapter.AdapterError):
            self.send()

    def test_environment_drops_gateway_credentials_and_node_injection(self):
        env = adapter.child_environment({"HOME": "/synthetic/home", "NODE_OPTIONS": "--require evil.js", "GROK_BOT_GATEWAY_TOKEN": "synthetic-token", "CURSOR_ACCESS_TOKEN": "synthetic-token", "HTTPS_PROXY": "untrusted"}, Path("/synthetic/node"))
        self.assertEqual(env["HOME"], "/synthetic/home")
        self.assertNotIn("NODE_OPTIONS", env)
        self.assertNotIn("GROK_BOT_GATEWAY_TOKEN", env)
        self.assertNotIn("HTTPS_PROXY", env)

    def test_source_hash_pin_rejects_modified_runtime(self):
        root = Path(self.temp.name) / "cli"
        (root / "src").mkdir(parents=True)
        for relative in adapter.PINNED_RUNTIME_FILES:
            (root / relative).write_bytes(b"original")
        pin = {"files": {relative: hashlib.sha256(b"original").hexdigest() for relative in adapter.PINNED_RUNTIME_FILES}}
        adapter.verify_source(root, pin)
        (root / "src/gateway.js").write_bytes(b"changed")
        with self.assertRaises(adapter.AdapterError):
            adapter.verify_source(root, pin)

    def test_empty_or_incomplete_source_pin_is_refused(self):
        for files in ({}, {"src/cli.js": "0" * 64}):
            with self.assertRaisesRegex(adapter.AdapterError, "invalid_source_pin"):
                adapter.verify_source(Path(self.temp.name), {"files": files})

    def test_cli_errors_never_include_raw_output(self):
        for code, out in [(1, b"private token or transcript"), (0, b"invalid private json"), (0, b"\xff")]:
            with self.assertRaises(adapter.AdapterError) as caught:
                adapter.decode_result(code, out)
            self.assertNotIn("private", str(caught.exception))

    def test_schema_rejects_malformed_normalized_messages(self):
        with self.assertRaises(adapter.AdapterError):
            adapter.validate_thread({"target": {"id": "test-bot", "name": "Synthetic bot", "kind": "bot"}, "messages": {}}, "test-bot", "Synthetic bot")

    def test_json_roundtrip_message_digest_preserved(self):
        payload = json.loads(json.dumps({"text": self.message}, ensure_ascii=False))
        adapter.validate_message(payload["text"], self.digest)

    def test_offline_check_never_executes_supplied_runtime(self):
        root = Path(self.temp.name)
        scripts = root / "scripts"
        (root / "assets").mkdir()
        (root / "src").mkdir()
        for relative in adapter.PINNED_RUNTIME_FILES:
            (root / relative).write_bytes(b"synthetic fixture")
        pin = {"source_commit": "synthetic", "files": {relative: hashlib.sha256(b"synthetic fixture").hexdigest() for relative in adapter.PINNED_RUNTIME_FILES}}
        (root / "assets/cli-compatibility.json").write_text(json.dumps(pin))
        marker = root / "marker"
        runtime = root / "untrusted-node"
        runtime.write_text("#!/bin/sh\ntouch " + str(marker) + "\n")
        runtime.chmod(0o700)
        with patch.object(adapter, "SCRIPTS", scripts), patch.object(sys, "argv", ["adapter", "check", "--cli-dir", str(root), "--node", str(runtime)]), patch.object(adapter.subprocess, "run", side_effect=AssertionError("must not execute")), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(adapter.main(), 0)
        self.assertFalse(marker.exists())
        result = json.loads(output.getvalue())
        self.assertEqual(result["node_version"], "not_executed_offline")
        self.assertFalse(result["network_used"])

    def test_invalid_arguments_do_not_echo_private_values(self):
        sentinel = "SENTINEL_DO_NOT_LEAK"
        with patch.object(sys, "argv", ["adapter", "check", "--cli-dir", "synthetic", "--node", "synthetic", "--unexpected", sentinel]), redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                adapter.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertNotIn(sentinel, stdout.getvalue() + stderr.getvalue())
        self.assertEqual(json.loads(stdout.getvalue())["error"]["code"], "invalid_input")


@unittest.skipUnless(os.name == "posix", "Live subprocess adapter supports macOS; POSIX fault harness")
class SubprocessBoundaryTests(unittest.TestCase):
    def call_fixture(self, code, *, message=None, timeout=2, output_limit=1024):
        original_popen = subprocess.Popen

        def local_fixture(_argv, **kwargs):
            # Run only this synthetic Python child, never the CLI or authentication.
            return original_popen([sys.executable, "-c", code], **kwargs)

        backend = adapter.CliBackend(Path.cwd(), Path(sys.executable), {})
        with patch.object(adapter, "verify_source"), patch.object(adapter.subprocess, "Popen", side_effect=local_fixture), patch.object(adapter, "CALL_TIMEOUT", timeout), patch.object(adapter, "MAX_OUTPUT_BYTES", output_limit):
            return backend.call(["synthetic-fixture"], message)

    def test_real_child_receives_exact_stdin_without_message_in_argv(self):
        message = "--json 請測試\nsecond line"
        result = self.call_fixture("import json,sys; print(json.dumps({'text':sys.stdin.read(), 'args':sys.argv}))", message=message)
        self.assertEqual(result["text"], message)
        self.assertEqual(result["args"], ["-c"])

    def test_silent_child_is_killed_at_deadline(self):
        with self.assertRaisesRegex(adapter.AdapterError, "cli_timeout"):
            self.call_fixture("import time; time.sleep(5)", timeout=0.1)

    def test_large_output_is_stopped_before_full_capture(self):
        with self.assertRaisesRegex(adapter.AdapterError, "cli_output_limit"):
            self.call_fixture("import sys; sys.stdout.write('x'*65536); sys.stdout.flush()", output_limit=128)

    def test_nonzero_child_does_not_expose_stderr(self):
        with self.assertRaisesRegex(adapter.AdapterError, "^cli_error$"):
            self.call_fixture("import sys; print('synthetic private text', file=sys.stderr); sys.exit(1)")


if __name__ == "__main__":
    unittest.main()
