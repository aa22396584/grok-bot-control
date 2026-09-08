#!/usr/bin/env python3
"""Read a coordination snapshot and advise a follow-up action without side effects."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PHASES = {"drafting", "waiting_bot", "reviewing", "complete", "blocked", "cancelled"}
TIME_FIELDS = ("waiting_since", "last_progress_at", "last_nudge_at", "announced_eta")


class InputError(ValueError):
    pass


def parse_time(value: Any, field: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InputError(f"{field} must be a timezone-aware ISO-8601 string or null")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise InputError(f"{field} is not valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InputError(f"{field} must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def require_schema(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("state must be a JSON object")
    required = {
        "schema_version", "phase", *TIME_FIELDS, "nudges_since_progress",
        "stall_notice_sent", "nudge_policy", "operator", "conversation", "last_sent",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise InputError(f"missing required fields: {', '.join(missing)}")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise InputError("schema_version must be 1")
    if not isinstance(data["phase"], str) or data["phase"] not in PHASES:
        raise InputError("phase is invalid")
    if not isinstance(data["operator"], str):
        raise InputError("operator must be a string")
    if data["conversation"] is not None and not isinstance(data["conversation"], str):
        raise InputError("conversation must be a string or null")
    last_sent = data["last_sent"]
    if not isinstance(last_sent, dict):
        raise InputError("last_sent must be an object")
    if "uncertain_send" not in last_sent or not isinstance(last_sent["uncertain_send"], bool):
        raise InputError("last_sent.uncertain_send must be boolean")
    count = data["nudges_since_progress"]
    if type(count) is not int or count < 0:
        raise InputError("nudges_since_progress must be a non-negative integer")
    if not isinstance(data["stall_notice_sent"], bool):
        raise InputError("stall_notice_sent must be boolean")
    policy = data["nudge_policy"]
    if not isinstance(policy, dict):
        raise InputError("nudge_policy must be an object")
    for field in ("enabled", "first_after_minutes", "repeat_after_minutes", "max_per_stall"):
        if field not in policy:
            raise InputError(f"missing nudge_policy field: {field}")
    if not isinstance(policy["enabled"], bool):
        raise InputError("nudge_policy.enabled must be boolean")
    for field in ("first_after_minutes", "repeat_after_minutes", "max_per_stall"):
        if type(policy[field]) is not int or policy[field] < 0:
            raise InputError(f"nudge_policy.{field} must be a non-negative integer")
    if count > policy["max_per_stall"]:
        raise InputError("nudges_since_progress exceeds nudge cap")
    return data


def decide(data: dict[str, Any], now: datetime) -> dict[str, Any]:
    times = {field: parse_time(data[field], field) for field in TIME_FIELDS}
    if data["phase"] != "waiting_bot":
        return {"action": "none", "reason": f"phase_{data['phase']}"}
    policy = data["nudge_policy"]
    if not policy["enabled"]:
        return {"action": "none", "reason": "nudge_policy_disabled"}
    if data["last_sent"]["uncertain_send"]:
        return {"action": "inspect", "reason": "uncertain_send_unresolved"}
    if (
        not data["operator"].strip()
        or not data["conversation"]
        or not data["conversation"].strip()
    ):
        return {"action": "inspect", "reason": "missing_operator_or_conversation"}

    unexpected_future = sorted(
        field for field, value in times.items()
        if field != "announced_eta" and value is not None and value > now
    )
    if unexpected_future:
        return {"action": "inspect", "reason": "future_timestamp:" + ",".join(unexpected_future)}

    waiting = times["waiting_since"]
    progress = times["last_progress_at"]
    last_nudge = times["last_nudge_at"]
    eta = times["announced_eta"]
    count = data["nudges_since_progress"]
    cap = policy["max_per_stall"]
    if waiting is None or progress is None:
        return {"action": "inspect", "reason": "missing_wait_or_progress_time"}
    if (count == 0) != (last_nudge is None):
        return {"action": "inspect", "reason": "inconsistent_nudge_fields"}
    if last_nudge is not None and (last_nudge < waiting or last_nudge < progress):
        return {"action": "inspect", "reason": "nudge_precedes_wait_or_progress"}
    if data["stall_notice_sent"] and count < cap:
        return {"action": "inspect", "reason": "stall_notice_before_nudge_cap"}

    due = max(waiting, progress) + timedelta(minutes=policy["first_after_minutes"])
    if last_nudge is not None:
        due = max(due, last_nudge + timedelta(minutes=policy["repeat_after_minutes"]))
    if eta is not None and eta > now:
        due = max(due, eta)
    if now < due:
        return {"action": "wait", "reason": "waiting_interval_or_eta", "next_check_at": format_time(due)}
    if count >= cap:
        if data["stall_notice_sent"]:
            return {"action": "none", "reason": "stall_already_reported"}
        return {"action": "notify_user", "reason": "nudge_cap_reached_without_progress"}
    return {"action": "nudge_due", "reason": "bot_stalled_past_due"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--now", help="timezone-aware ISO-8601 time; defaults to current UTC")
    args = parser.parse_args()
    try:
        now = parse_time(args.now, "now") if args.now else datetime.now(timezone.utc)
        assert now is not None
        result = decide(
            require_schema(json.loads(args.state.read_text(encoding="utf-8"))), now
        )
    except (InputError, json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        print(json.dumps({"error": {"code": "invalid_input", "message": str(exc)}}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
