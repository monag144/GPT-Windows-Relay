#!/usr/bin/env python3
"""Read-only strict PCE14 evidence grader. Never executes relay/browser actions.

Measured performance and coverage have distinct denominators:
- measured: successes / actual attempts, provided attempts > 0.
- coverage: completed verified trials / required trials; success rate UNKNOWN.
- not_run: no observed denominator; NEVER manufacture 0% performance.
Anything measured below 90% is FAIL. Any unproven critical gate BLOCKS release.
Unit tests being green do not stand in for real GUI delivery.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

THRESHOLD = 90.0
VALID_MODES = {"observed", "coverage", "not_run"}


def grade(percent: float) -> str:
    if not isinstance(percent, (int, float)) or not 0 <= percent <= 100:
        raise ValueError("percentage outside 0-100")
    if percent < 90:
        return "F"
    if percent < 95:
        return "C"
    if percent < 98:
        return "B"
    return "A"


def assess_case(case: dict) -> dict:
    required = {"id", "name", "purpose", "mode", "passed", "attempted",
                "critical", "evidence", "improvement"}
    if not isinstance(case, dict) or not required.issubset(case):
        raise ValueError("missing required case field")
    mode = case["mode"]
    if mode not in VALID_MODES:
        raise ValueError("invalid case mode")
    if not isinstance(case["critical"], bool):
        raise ValueError("critical must be boolean")
    result = {"id": case["id"], "name": case["name"],
              "purpose": case["purpose"], "mode": mode,
              "critical": case["critical"], "evidence": case["evidence"],
              "improvement": case["improvement"], "observed_pass_percent": None,
              "coverage_percent": None, "grade": "U", "status": "UNPROVEN"}
    if mode == "observed":
        passed, attempted = case["passed"], case["attempted"]
        if (type(passed) is not int or type(attempted) is not int
                or attempted < 1 or passed < 0 or passed > attempted):
            raise ValueError("invalid observed numerator/denominator")
        pct = 100.0 * passed / attempted
        result.update({"observed_pass_percent": round(pct, 2),
                       "attempts": attempted, "successes": passed,
                       "grade": grade(pct),
                       "status": "PASS" if pct >= THRESHOLD else "FAIL"})
    elif mode == "coverage":
        attempts, planned = case["attempted"], case.get("planned")
        passed = case["passed"]
        if (type(attempts) is not int or type(planned) is not int
                or type(passed) is not int or planned < 1
                or attempts < 0 or attempts > planned
                or passed < 0 or passed > attempts):
            raise ValueError("invalid coverage data")
        pct = 100.0 * attempts / planned
        result.update({"coverage_percent": round(pct, 2),
                       "attempts": attempts, "planned": planned,
                       "successes": passed, "grade": grade(pct),
                       "status": "PASS_COVERAGE" if pct >= THRESHOLD else "FAIL_COVERAGE"})
        if attempts > 0:
            result["observed_pass_percent"] = round(100.0 * passed / attempts, 2)
            # Passing coverage with failing observed effects is not acceptable.
            if result["observed_pass_percent"] < THRESHOLD:
                result["status"] = "FAIL"
                result["grade"] = grade(result["observed_pass_percent"])
    elif case["passed"] is not None or case["attempted"] is not None:
        raise ValueError("not_run cannot imply observed counts")
    return result


def assess(evidence: dict) -> dict:
    if (not isinstance(evidence, dict) or evidence.get("schema_version") != 1
            or evidence.get("minimum_pass_percent") != THRESHOLD
            or not isinstance(evidence.get("cases"), list)
            or not evidence["cases"]):
        raise ValueError("invalid strict-grade evidence")
    items = [assess_case(case) for case in evidence["cases"]]
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate criterion ids")
    passed = sum(item["status"] in ("PASS", "PASS_COVERAGE") for item in items)
    failed = sum(item["status"] in ("FAIL", "FAIL_COVERAGE") for item in items)
    unproven = len(items) - passed - failed
    critical_blocked = [item["id"] for item in items
                        if item["critical"] and item["status"] not in ("PASS", "PASS_COVERAGE")]
    overall = round(100 * passed / len(items), 2)
    return {
        "minimum_pass_percent": THRESHOLD,
        "as_of": evidence.get("as_of"),
        "pending_action": evidence.get("pending_action"),
        "observed_gate_count": sum(item["mode"] == "observed" for item in items),
        "gate_count": len(items),
        "passed_gates": passed,
        "failed_gates": failed,
        "unproven_gates": unproven,
        "proven_gate_coverage_percent": overall,
        "overall_evidence_grade": grade(overall),
        "overall_release_status": "BLOCKED" if critical_blocked else "ELIGIBLE_FOR_NEXT_REVIEW",
        "critical_blocked_ids": critical_blocked,
        "performance_claim": "Gate coverage is NOT a production delivery success probability",
        "cases": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_file", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = assess(json.loads(args.evidence_file.read_text(encoding="utf-8")))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
