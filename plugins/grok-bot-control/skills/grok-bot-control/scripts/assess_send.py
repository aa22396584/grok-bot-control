#!/usr/bin/env python3
"""Advise one UI send step from recorded state and a fresh observation.

This helper is read-only. It never opens an app, edits state, or sends content.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
OBSERVATIONS = {"absent", "matching-draft-only", "matching-sent", "ambiguous"}
TERMINAL_PHASES = {"complete", "cancelled"}
NON_SENDING_PHASES = {"blocked"}
PHASES = {"drafting", "waiting_bot", "reviewing", "complete", "blocked", "cancelled"}


class InputError(ValueError):
    pass


def optional_sha(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise InputError(f"{field} must be a lowercase SHA-256 string or null")
    return value


def require_state(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("state must be a JSON object")
    for field in ("schema_version", "phase", "operator", "conversation", "last_sent"):
        if field not in data:
            raise InputError(f"missing required field: {field}")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise InputError("schema_version must be 1")
    if not isinstance(data["phase"], str) or data["phase"] not in PHASES:
        raise InputError("phase is invalid")
    if not isinstance(data["operator"], str):
        raise InputError("operator must be a string")
    if data["conversation"] is not None and not isinstance(data["conversation"], str):
        raise InputError("conversation must be a string or null")
    sent = data["last_sent"]
    if not isinstance(sent, dict):
        raise InputError("last_sent must be an object")
    for field in ("message_sha256", "ui_readback_confirmed", "uncertain_send", "bot_acknowledged"):
        if field not in sent:
            raise InputError(f"missing last_sent field: {field}")
    optional_sha(sent["message_sha256"], "last_sent.message_sha256")
    for field in ("ui_readback_confirmed", "uncertain_send", "bot_acknowledged"):
        if not isinstance(sent[field], bool):
            raise InputError(f"last_sent.{field} must be boolean")
    if sent["uncertain_send"] and sent["ui_readback_confirmed"]:
        raise InputError("uncertain_send conflicts with ui_readback_confirmed")
    if sent["uncertain_send"] and sent["bot_acknowledged"]:
        raise InputError("uncertain_send conflicts with bot_acknowledged")
    if sent["bot_acknowledged"] and sent["message_sha256"] is None:
        raise InputError("bot acknowledgement requires a message digest")
    return data


def decide(
    state: dict[str, Any], operator: str, message_sha256: str, observation: str
) -> dict[str, str]:
    if not operator.strip():
        raise InputError("operator must not be blank")
    optional_sha(message_sha256, "message_sha256")
    if observation not in OBSERVATIONS:
        raise InputError("observation is invalid")

    owner = state["operator"].strip()
    if not owner:
        return {"action": "inspect", "reason": "operator_unclaimed"}
    if owner != operator:
        return {"action": "stop", "reason": "different_operator"}
    if state["phase"] in TERMINAL_PHASES:
        return {"action": "stop", "reason": f"phase_{state['phase']}"}
    if state["phase"] in NON_SENDING_PHASES:
        return {"action": "inspect", "reason": f"phase_{state['phase']}"}
    if not state["conversation"] or not state["conversation"].strip():
        return {"action": "inspect", "reason": "conversation_unset"}

    sent = state["last_sent"]
    same_recorded = sent["message_sha256"] == message_sha256
    if same_recorded and (sent["ui_readback_confirmed"] or sent["bot_acknowledged"]):
        return {"action": "stop", "reason": "message_already_confirmed_sent"}
    if sent["uncertain_send"]:
        if not same_recorded:
            return {"action": "inspect", "reason": "different_uncertain_send_unresolved"}
        if observation == "matching-sent":
            return {"action": "mark_sent", "reason": "uncertain_resolved_to_sent"}
        if observation == "matching-draft-only":
            return {"action": "send_once", "reason": "uncertain_resolved_to_draft_only"}
        return {"action": "inspect", "reason": "uncertain_send_not_resolved"}
    if observation == "matching-sent":
        return {"action": "mark_sent", "reason": "matching_message_visible"}
    if observation == "matching-draft-only":
        return {"action": "send_once", "reason": "matching_draft_only"}
    if observation == "absent" and state["phase"] == "drafting":
        return {"action": "paste_once", "reason": "message_absent_in_drafting"}
    return {"action": "inspect", "reason": "observation_requires_reconciliation"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--message-sha256", required=True)
    parser.add_argument("--observation", choices=sorted(OBSERVATIONS), required=True)
    args = parser.parse_args()
    try:
        state = require_state(json.loads(args.state.read_text()))
        result = decide(state, args.operator, args.message_sha256, args.observation)
    except (InputError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": {"code": "invalid_input", "message": str(exc)}}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
