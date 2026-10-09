#!/usr/bin/env python3
"""Read-only, evidence-driven Windows Relay behavioral benchmark.

No UI actions, HTTP requests, listener restarts, credential reads, or retries.
Real runs require separately collected relay AND independent observer traces.
Fixture results are always labeled FIXTURE_PASS, never live acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "CASES_2026-10-09T2200Z_RELAY_BEHAVIORAL.json"
SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
SHA64 = re.compile(r"^[0-9a-fA-F]{64}$")
CLEAN_FIELDS = {
    "case_id", "trial_id", "source", "event", "at_ms", "operation_id",
    "tab_id", "conversation_id", "payload_sha256", "observer_id",
    "role", "runtime_sha256", "payload_bytes", "readback_bytes",
    "readback_sha256", "unicode_seen", "multiline_seen"
}


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    result = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError("expected JSON object: " + str(path))
    return result


def load_catalog(path: Path = CATALOG) -> dict:
    doc = load_json(path)
    cases = doc.get("cases")
    if doc.get("schema") != "pce14-relay-behavior-v1" or not isinstance(cases, list):
        raise ValueError("invalid behavioral catalog")
    ids = [c.get("id") for c in cases]
    if len(ids) != 20 or ids != ["R%02d" % n for n in range(1, 21)]:
        raise ValueError("expected unique R01..R20")
    for case in cases:
        if not case.get("required") or case.get("limit_ms", 0) <= 0:
            raise ValueError("invalid case definition: " + case["id"])
        if any(not re.fullmatch(r"(relay|observer):[a-z0-9_]+", v)
               for v in case["required"] + case["forbidden"]):
            raise ValueError("invalid event key in " + case["id"])
    return doc


def validate_manifest(meta: dict, catalog_path: Path = CATALOG) -> None:
    if meta.get("schema") != "pce14-relay-run-v1":
        raise ValueError("unsupported run manifest")
    if meta.get("mode") not in ("fixture", "live"):
        raise ValueError("mode must be fixture or live")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{4,80}", str(meta.get("run_id", ""))):
        raise ValueError("invalid run_id")
    if not SHA40.fullmatch(str(meta.get("source_sha", ""))):
        raise ValueError("source commit must be exact 40-hex")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", str(meta.get("observer_id", ""))):
        raise ValueError("observer_id required")
    if meta.get("catalog_sha256") != digest(catalog_path):
        raise ValueError("catalog SHA mismatch")
    if meta["mode"] == "live":
        if not SHA64.fullmatch(str(meta.get("loaded_runtime_sha256", ""))):
            raise ValueError("live run requires loaded-runtime SHA-256 evidence")
        if meta.get("observer_independent") is not True:
            raise ValueError("live run requires a separate independent observer")
        if meta.get("isolated_profile") is not True:
            raise ValueError("live run requires isolated test profile")
    elif meta.get("observer_independent") is True:
        raise ValueError("fixture mode must not impersonate independent observation")


def load_events(path: Path) -> list[dict]:
    result = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid JSONL line " + str(line_no)) from exc
        if not isinstance(event, dict) or set(event) - CLEAN_FIELDS:
            raise ValueError("unknown or raw-content field in line " + str(line_no))
        required = ("case_id", "trial_id", "event", "source", "at_ms",
                    "operation_id", "tab_id", "payload_sha256")
        if any(x not in event for x in required):
            raise ValueError("incomplete trace line " + str(line_no))
        if event["source"] not in ("relay", "observer"):
            raise ValueError("invalid trace source")
        if not isinstance(event["at_ms"], int) or isinstance(event["at_ms"], bool) or event["at_ms"] < 0:
            raise ValueError("invalid monotonic timestamp")
        if not SHA64.fullmatch(str(event["payload_sha256"])):
            raise ValueError("payload SHA invalid")
        for name in ("trial_id", "operation_id", "tab_id", "event"):
            if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", str(event[name])):
                raise ValueError("invalid " + name)
        result.append(event)
    return result


def key(event: dict) -> str:
    return event["source"] + ":" + event["event"]


def percentile_95(values: list[int]) -> int | None:
    if not values:
        return None
    values = sorted(values)
    return values[(95 * len(values) + 99) // 100 - 1]


def check_trial(case: dict, events: list[dict], meta: dict, globally_forbidden: list[str]) -> dict:
    if not events:
        return {"status": "BLOCKED", "reason": "missing trial evidence"}
    ref = events[0]
    fixed = ("case_id", "trial_id", "operation_id", "tab_id", "payload_sha256")
    if any(e[field] != ref[field] for e in events for field in fixed):
        return {"status": "FAIL", "reason": "cross-trial or cross-tab identity contamination"}
    if any(e["source"] == "observer" and e.get("observer_id") != meta["observer_id"]
           for e in events):
        return {"status": "FAIL", "reason": "observer provenance mismatch"}
    stamps = [e["at_ms"] for e in events]
    if stamps != sorted(stamps):
        return {"status": "FAIL", "reason": "nonmonotonic event order"}
    signals = [key(e) for e in events]
    violations = sorted(set(signals) & set(globally_forbidden + case["forbidden"]))
    if violations:
        return {"status": "FAIL", "reason": "forbidden: " + ",".join(violations)}
    if signals.count("relay:send_invoked") != case["sends"]:
        return {"status": "FAIL", "reason": "send count mismatch"}
    if signals.count("relay:effect_committed") != case["effects"]:
        return {"status": "FAIL", "reason": "backend effect count mismatch"}
    if any(signals.count(k) > 1 for k in ("relay:send_invoked", "relay:effect_committed",
                                          "relay:ack_confirmed", "relay:new_chat_clicked")):
        return {"status": "FAIL", "reason": "duplicate irreversible transition"}
    if "observer:trial_complete" not in signals or signals[-1] != "observer:trial_complete":
        return {"status": "BLOCKED", "reason": "independent terminal observation absent"}
    need = iter(case["required"])
    expected = next(need, None)
    for signal in signals:
        if signal == expected:
            expected = next(need, None)
            if expected is None:
                break
    if expected is not None:
        return {"status": "FAIL", "reason": "required event missing/out of order: " + expected}
    elapsed = stamps[-1] - stamps[0]
    if elapsed > case["limit_ms"]:
        return {"status": "FAIL", "reason": "latency limit exceeded", "duration_ms": elapsed}
    for event in events:
        if key(event) in ("observer:composer_exact", "observer:payload_sha_verified"):
            if event.get("readback_sha256") != ref["payload_sha256"]:
                return {"status": "FAIL", "reason": "readback digest absent or different"}
        if key(event) == "observer:composer_exact":
            if (not isinstance(event.get("payload_bytes"), int)
                or isinstance(event.get("payload_bytes"), bool)
                or event.get("payload_bytes", 0) <= 0
                or event.get("readback_bytes") != event.get("payload_bytes")):
                return {"status": "FAIL", "reason": "composer byte count absent/mismatched"}
            if case.get("payload_constraint") == "unicode_and_multiline":
                if event.get("unicode_seen") is not True or event.get("multiline_seen") is not True:
                    return {"status": "FAIL", "reason": "unicode/multiline evidence absent"}
            if case.get("payload_constraint") == "min_12000_bytes":
                if event["readback_bytes"] < 12000:
                    return {"status": "FAIL", "reason": "long-payload size not demonstrated"}
        if key(event) == "observer:user_turn_verified":
            if (event.get("role") != "user"
                or event.get("operation_id") != ref["operation_id"]
                or event.get("payload_sha256") != ref["payload_sha256"]
                or not event.get("conversation_id")):
                return {"status": "FAIL", "reason": "exact user-role proof invalid"}
        if key(event) == "observer:loaded_runtime_attested" and meta["mode"] == "live":
            if event.get("runtime_sha256") != meta["loaded_runtime_sha256"]:
                return {"status": "FAIL", "reason": "loaded-runtime attestation disagrees"}
    return {"status": "TRACE_PASS" if meta["mode"] == "live" else "FIXTURE_PASS",
            "reason": "trace checks satisfied; underlying observer not independently audited",
            "duration_ms": elapsed}


def score(meta: dict, catalog: dict, events: list[dict]) -> dict:
    cases = {c["id"]: c for c in catalog["cases"]}
    if any(e["case_id"] not in cases for e in events):
        raise ValueError("trace names unknown benchmark case")
    if meta["mode"] == "live" and not any(key(e) == "observer:loaded_runtime_attested" for e in events):
        raise ValueError("no positive live loaded-runtime evidence in trace")
    by_case = defaultdict(lambda: defaultdict(list))
    ownership = {}
    for event in events:
        ident = event["trial_id"]
        owner = ownership.setdefault(ident, event["case_id"])
        if owner != event["case_id"]:
            raise ValueError("trial ID reused across scenarios")
        by_case[event["case_id"]][ident].append(event)
    verdicts = {}
    expected_trials = int(catalog["minimum_trials"])
    for case_id, case in cases.items():
        trials = by_case.get(case_id, {})
        if not trials:
            verdicts[case_id] = {"status": "NOT_RUN", "trials": 0, "median_ms": None,
                                 "p95_ms": None, "reasons": ["no trial"]}
            continue
        outputs = [check_trial(case, seq, meta, catalog["forbidden_global"]) for seq in trials.values()]
        times = [r["duration_ms"] for r in outputs if r.get("duration_ms") is not None]
        bad = [r for r in outputs if r["status"] == "FAIL"]
        if bad:
            state = "FAIL"
        elif len(outputs) < expected_trials or any(r["status"] == "BLOCKED" for r in outputs):
            state = "BLOCKED"
        else:
            state = "TRACE_PASS" if meta["mode"] == "live" else "FIXTURE_PASS"
        verdicts[case_id] = {
            "status": state, "trials": len(outputs),
            "median_ms": statistics.median(times) if times else None,
            "p95_ms": percentile_95(times),
            "reasons": sorted({r["reason"] for r in outputs if r["status"] in ("FAIL", "BLOCKED")})
        }
    success = "TRACE_PASS" if meta["mode"] == "live" else "FIXTURE_PASS"
    passed = sum(1 for r in verdicts.values() if r["status"] == success)
    return {
        "schema": "pce14-relay-behavior-score-v1",
        "run_id": meta["run_id"], "mode": meta["mode"],
        "source_sha": meta["source_sha"],
        "loaded_runtime_sha256": meta.get("loaded_runtime_sha256"),
        "catalog_sha256": meta["catalog_sha256"],
        "counts": {"passing": passed, "total": len(cases),
                   "failed": sum(r["status"] == "FAIL" for r in verdicts.values()),
                   "blocked": sum(r["status"] == "BLOCKED" for r in verdicts.values()),
                   "not_run": sum(r["status"] == "NOT_RUN" for r in verdicts.values())},
        "capabilities": verdicts,
        "trace_coverage_complete": bool(passed == len(cases)),
        "full_behavioral_gate": False,
        "release_qualified": False,
        "warning": ("Trace assertions do not independently authenticate their producer. "
                    "Live acceptance additionally needs vetted out-of-band observer, A-Z safety, "
                    "actual loaded Firefox provenance and genuine 12h/24h endurance. "
                    "This runner never sends, clicks or restarts anything.")
    }


def write_once(path: Path, data: dict) -> None:
    path = path.resolve()
    if path.exists() or path.with_suffix(path.suffix + ".partial").exists():
        raise FileExistsError("output exists: refusing overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_suffix(path.suffix + ".partial")
    with scratch.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
    scratch.replace(path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only behavioral capability benchmark")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    args = parser.parse_args(argv)
    try:
        meta = load_json(args.manifest)
        catalog = load_catalog(args.catalog)
        validate_manifest(meta, args.catalog)
        trace = load_events(args.trace)
        report = score(meta, catalog, trace)
        report["trace_sha256"] = digest(args.trace)
        report["generated_utc"] = datetime.now(timezone.utc).isoformat()
        write_once(args.output, report)
        print("RELAY_BENCHMARK " + json.dumps({
            "run_id": report["run_id"], "mode": report["mode"], **report["counts"],
            "full_behavioral_gate": report["full_behavioral_gate"],
            "report": str(args.output)
        }, sort_keys=True))
        return 0 if report["counts"]["passing"] == report["counts"]["total"] else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("RELAY_BENCHMARK_BLOCKED " + str(exc)[:240], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
