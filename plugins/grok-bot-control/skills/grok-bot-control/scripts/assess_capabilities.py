#!/usr/bin/env python3
"""Assess a scoped host capability snapshot without probing any tools."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


CAPABILITIES = {
    "read_conversation",
    "read_composer",
    "write_composer",
    "activate_send",
    "read_sent_state",
}
READ_CAPABILITIES = {"read_conversation", "read_composer", "read_sent_state"}
EVIDENCE = {"unknown", "current_tool_docs", "fresh_state_readback"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_AGE = timedelta(minutes=5)


class InputError(ValueError):
    pass


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise InputError(f"{field} must be a timezone-aware ISO-8601 string")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise InputError(f"{field} is not valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InputError(f"{field} must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{field} must be a non-blank string")
    return value


def require_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise InputError(f"{field} must be a lowercase SHA-256 string")
    return value


def require_snapshot(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("snapshot must be a JSON object")
    required = {
        "schema_version", "observed_at", "run_id", "intent",
        "target_identity", "send_authorized", "capabilities",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise InputError(f"missing required fields: {', '.join(missing)}")
    extra = sorted(data.keys() - required)
    if extra:
        raise InputError(f"unknown fields: {', '.join(extra)}")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise InputError("schema_version must be 1")
    parse_time(data["observed_at"], "observed_at")
    require_text(data["run_id"], "run_id")
    if not isinstance(data["send_authorized"], bool):
        raise InputError("send_authorized must be boolean")

    intent = data["intent"]
    if not isinstance(intent, dict) or set(intent) != {"operator", "conversation", "message_sha256"}:
        raise InputError("intent requires only operator, conversation, and message_sha256")
    require_text(intent["operator"], "intent.operator")
    require_text(intent["conversation"], "intent.conversation")
    require_digest(intent["message_sha256"], "intent.message_sha256")

    target = data["target_identity"]
    if not isinstance(target, dict):
        raise InputError("target_identity must be an object")
    if set(target) != {"confirmed", "evidence"}:
        raise InputError("target_identity requires only confirmed and evidence")
    if not isinstance(target["confirmed"], bool):
        raise InputError("target_identity.confirmed must be boolean")
    if (
        not isinstance(target["evidence"], str)
        or target["evidence"] not in {"unknown", "fresh_target_readback"}
    ):
        raise InputError("target_identity.evidence is invalid")
    if not target["confirmed"] and target["evidence"] != "unknown":
        raise InputError("unconfirmed target must have unknown evidence")

    capabilities = data["capabilities"]
    if not isinstance(capabilities, dict):
        raise InputError("capabilities must be an object")
    if set(capabilities) != CAPABILITIES:
        missing_caps = sorted(CAPABILITIES - set(capabilities))
        extra_caps = sorted(set(capabilities) - CAPABILITIES)
        detail = []
        if missing_caps:
            detail.append("missing: " + ",".join(missing_caps))
        if extra_caps:
            detail.append("unknown: " + ",".join(extra_caps))
        raise InputError("capability fields invalid (" + "; ".join(detail) + ")")
    for name, record in capabilities.items():
        if not isinstance(record, dict) or set(record) != {"available", "evidence"}:
            raise InputError(f"capabilities.{name} requires only available and evidence")
        if not isinstance(record["available"], bool):
            raise InputError(f"capabilities.{name}.available must be boolean")
        if not isinstance(record["evidence"], str) or record["evidence"] not in EVIDENCE:
            raise InputError(f"capabilities.{name}.evidence is invalid")
        if not record["available"] and record["evidence"] != "unknown":
            raise InputError(f"unavailable capability {name} must have unknown evidence")
    return data


def decide(
    snapshot: dict[str, Any],
    *,
    now: datetime,
    run_id: str,
    operator: str,
    conversation: str,
    message_sha256: str,
) -> dict[str, Any]:
    require_text(run_id, "run_id")
    require_text(operator, "operator")
    require_text(conversation, "conversation")
    require_digest(message_sha256, "message_sha256")
    if now.tzinfo is None or now.utcoffset() is None:
        raise InputError("now must include a timezone offset")
    now = now.astimezone(timezone.utc)

    observed_at = parse_time(snapshot["observed_at"], "observed_at")
    if observed_at > now:
        return {"action": "inspect", "reason": "observation_from_future"}
    if now - observed_at > MAX_AGE:
        return {"action": "inspect", "reason": "observation_stale"}
    if snapshot["run_id"] != run_id:
        return {"action": "inspect", "reason": "different_run"}

    intent = snapshot["intent"]
    mismatches = sorted(
        name for name, current in {
            "operator": operator,
            "conversation": conversation,
            "message_sha256": message_sha256,
        }.items()
        if intent[name] != current
    )
    if mismatches:
        return {"action": "inspect", "reason": "intent_mismatch", "fields": mismatches}

    target = snapshot["target_identity"]
    if not target["confirmed"] or target["evidence"] != "fresh_target_readback":
        return {"action": "inspect", "reason": "target_not_freshly_confirmed"}

    capabilities = snapshot["capabilities"]
    unavailable = sorted(name for name, value in capabilities.items() if not value["available"])
    if unavailable:
        missing_reads = sorted(name for name in READ_CAPABILITIES if not capabilities[name]["available"])
        if missing_reads:
            return {
                "action": "handoff_only",
                "reason": "missing_capabilities",
                "missing": unavailable,
            }
        unknown_reads = sorted(
            name for name in READ_CAPABILITIES
            if capabilities[name]["evidence"] == "unknown"
        )
        if unknown_reads:
            return {
                "action": "inspect",
                "reason": "capability_evidence_missing",
                "capabilities": unknown_reads,
            }
        stale_reads = sorted(
            name for name in READ_CAPABILITIES
            if capabilities[name]["evidence"] != "fresh_state_readback"
        )
        if stale_reads:
            return {
                "action": "inspect",
                "reason": "fresh_readback_missing",
                "capabilities": stale_reads,
            }
        return {
            "action": "review_only",
            "reason": "missing_capabilities",
            "missing": unavailable,
        }
    unknown = sorted(name for name, value in capabilities.items() if value["evidence"] == "unknown")
    if unknown:
        return {"action": "inspect", "reason": "capability_evidence_missing", "capabilities": unknown}
    stale_reads = sorted(
        name for name in READ_CAPABILITIES
        if capabilities[name]["evidence"] != "fresh_state_readback"
    )
    if stale_reads:
        return {"action": "inspect", "reason": "fresh_readback_missing", "capabilities": stale_reads}
    if not snapshot["send_authorized"]:
        return {"action": "review_only", "reason": "send_not_authorized"}
    return {"action": "ready_for_send_gate", "reason": "capability_contract_satisfied"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--conversation", required=True)
    parser.add_argument("--message-sha256", required=True)
    parser.add_argument("--now", help="timezone-aware ISO-8601 time; defaults to current UTC")
    args = parser.parse_args()
    try:
        now = parse_time(args.now, "now") if args.now else datetime.now(timezone.utc)
        result = decide(
            require_snapshot(json.loads(args.snapshot.read_text(encoding="utf-8"))),
            now=now,
            run_id=args.run_id,
            operator=args.operator,
            conversation=args.conversation,
            message_sha256=args.message_sha256,
        )
    except (InputError, json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        print(json.dumps({"error": {"code": "invalid_input", "message": str(exc)}}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
