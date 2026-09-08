#!/usr/bin/env python3
"""Run the public submission fixtures against the plugin's offline helpers."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"
SKILL = ROOT / "plugins/grok-bot-control/skills/grok-bot-control"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_catalog(catalog: dict[str, Any], fixtures: dict[str, Any]) -> None:
    cases = catalog.get("cases")
    if not isinstance(cases, list):
        raise ValueError("test_cases.json cases must be an array")
    positive = sum(case.get("type") == "positive" for case in cases)
    negative = sum(case.get("type") == "negative" for case in cases)
    if positive < 5 or negative < 3:
        raise ValueError("catalog must include at least five positive and three negative cases")
    seen: set[str] = set()
    required = {
        "id", "type", "user_prompt", "expected_workflow",
        "expected_result_shape", "fixture_ref", "invocation", "expected_exact_result",
    }
    for case in cases:
        missing = sorted(required - case.keys())
        if missing:
            raise ValueError(f"{case.get('id', '<unknown>')} missing: {', '.join(missing)}")
        if case["id"] in seen:
            raise ValueError(f"duplicate case id: {case['id']}")
        seen.add(case["id"])
        if case["type"] not in {"positive", "negative"}:
            raise ValueError(f"{case['id']} has invalid type")
        if case["type"] == "negative" and not str(case.get("negative_why", "")).strip():
            raise ValueError(f"{case['id']} must explain negative_why")
        if case["fixture_ref"] not in fixtures:
            raise ValueError(f"{case['id']} references missing fixture {case['fixture_ref']}")


def invoke(case: dict[str, Any], state: dict[str, Any], send: ModuleType, wait: ModuleType) -> dict[str, Any]:
    invocation = case["invocation"]
    helper = invocation.get("helper")
    if helper == "assess_send":
        checked = send.require_state(state)
        return send.decide(
            checked,
            invocation["operator"],
            invocation["message_sha256"],
            invocation["observation"],
        )
    if helper == "assess_wait":
        now = wait.parse_time(invocation["now"], "now")
        if now is None:
            raise ValueError(f"{case['id']} now must not be null")
        return wait.decide(wait.require_schema(state), now)
    raise ValueError(f"{case['id']} uses unknown helper {helper!r}")


def main() -> int:
    catalog = load_json(SUBMISSION / "test_cases.json")
    fixture_document = load_json(SUBMISSION / "fixture_states.json")
    fixtures = fixture_document.get("fixtures")
    if not isinstance(fixtures, dict):
        raise ValueError("fixture_states.json fixtures must be an object")
    validate_catalog(catalog, fixtures)

    send = load_module("review_assess_send", SKILL / "scripts/assess_send.py")
    wait = load_module("review_assess_wait", SKILL / "scripts/assess_wait.py")
    results = []
    for case in catalog["cases"]:
        fixture = copy.deepcopy(fixtures[case["fixture_ref"]])
        before = copy.deepcopy(fixture)
        actual = invoke(case, fixture, send, wait)
        passed = actual == case["expected_exact_result"] and fixture == before
        results.append({
            "id": case["id"],
            "type": case["type"],
            "passed": passed,
            "actual": actual,
            "fixture_unchanged": fixture == before,
        })

    summary = {
        "schema_version": 1,
        "mode": "synthetic_offline",
        "network_or_ui_used": False,
        "total": len(results),
        "passed": sum(result["passed"] for result in results),
        "failed": sum(not result["passed"] for result in results),
        "results": results,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
