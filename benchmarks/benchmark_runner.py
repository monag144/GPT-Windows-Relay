#!/usr/bin/env python3
"""PCE011 A-Z benchmark scorer. Evaluates evidence; never drives or modifies the Relay."""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from overnight_observer import summarize as summarize_observer

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "CASES_2026-10-08T0805Z_A_TO_Z.json"
ZERO_METRICS = ("manual_rescues", "duplicate_effects", "unsafe_executions")
SAFETY = set("CKLMOVY")

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_name(path.name + ".partial")
    staging.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    staging.replace(path)

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def catalog():
    obj = read(CATALOG)
    if [c["id"] for c in obj["cases"]] != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        raise ValueError("benchmark catalog must contain exactly A-Z")
    return obj

def applicable(case, meta):
    kind = case["scope"]
    return kind == "both" or kind == meta["product"] or (kind == "firefox" and meta["browser"] == "firefox")

def create(args):
    p = args.output.resolve()
    if p.exists():
        raise FileExistsError("refusing to overwrite a previous run")
    if not re.fullmatch("[A-Fa-f0-9]{40}", args.sha):
        raise ValueError("exact 40-character commit SHA required")
    if args.runtime_sha and not re.fullmatch("[A-Fa-f0-9]{64}", args.runtime_sha):
        raise ValueError("runtime hash must be 64-character SHA-256")
    p.mkdir(parents=True)
    save(p / "run.json", {
        "schema": "pce011-run-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "product": args.product, "browser": args.browser, "label": args.label,
        "source_sha": args.sha.lower(), "loaded_runtime_sha256": args.runtime_sha,
        "catalog_sha256": digest(CATALOG)
    })
    save(p / "cases.json", {})
    print(json.dumps({"created": str(p), "label": args.label}))
    return 0

def record(args):
    root = args.run.resolve()
    meta = read(root / "run.json")
    if meta["catalog_sha256"] != digest(CATALOG):
        raise ValueError("benchmark specification changed")
    case = next(c for c in catalog()["cases"] if c["id"] == args.case)
    if not applicable(case, meta):
        raise ValueError("case does not apply to selected product/browser")
    evidence = {}
    if args.result == "PASS":
        if not args.reviewer or not args.evidence:
            raise ValueError("PASS requires reviewer and on-disk structured evidence")
    if args.evidence:
        p = args.evidence.resolve()
        if not p.is_file():
            raise FileNotFoundError(str(p))
        data = read(p)
        if not isinstance(data, dict):
            raise ValueError("evidence must be a JSON object")
        evidence = {"local_path": str(p), "sha256": digest(p)}
    cases = read(root / "cases.json")
    cases[args.case] = {
        "result": args.result,
        "reviewer": args.reviewer or "",
        "evidence": evidence,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "note": (args.note or "")[:240]
    }
    save(root / "cases.json", cases)
    print(json.dumps({"recorded": args.case, "result": args.result}))
    return 0

def proof(case_id, item):
    if not item:
        return "NOT_RUN", "no test executed"
    if item["result"] != "PASS":
        return item["result"], "reported non-pass"
    if not item.get("reviewer") or not item.get("evidence"):
        return "BLOCKED", "missing reviewer or evidence"
    data = item["evidence"]
    p = Path(data["local_path"])
    if not p.is_file() or digest(p) != data["sha256"]:
        return "BLOCKED", "evidence changed or disappeared"
    try:
        e = read(p)
        if e.get("passed") is not True:
            return "BLOCKED", "evidence does not assert an observed pass"
        if case_id in SAFETY or case_id in "UZ":
            if any(e.get(key) != 0 for key in ZERO_METRICS):
                return "FAIL", "safety/rescue count nonzero or omitted"
        if case_id in "UZ":
            threshold = 43200 if case_id == "U" else 86400
            source = e.get("observer_log", {})
            observer_path = Path(source["path"])
            if not observer_path.is_file() or digest(observer_path) != source["sha256"]:
                return "BLOCKED", "independent raw observer evidence missing/changed"
            observer = summarize_observer(observer_path, threshold)
            if not observer.get("qualified_for_tcp_gate"):
                return "FAIL", "independent raw observer coverage failed"
            receipts = e.get("hourly_receipts", [])
            hours = threshold // 3600
            if sorted({r.get("hour") for r in receipts if r.get("executions") == 1
                       and r.get("visible_result") is True
                       and r.get("duplicate_effects") == 0}) != list(range(hours)):
                return "FAIL", "hourly exact-once visible receipt missing"
            if e.get("unrecovered_stalls") != 0:
                return "FAIL", "unrecovered stalled operation"
    except (KeyError, ValueError, TypeError, OSError):
        return "BLOCKED", "invalid evidence structure"
    return "PASS", "local reviewer-attested evidence (not reproduced by scorer)"

def assessment(folder):
    folder = Path(folder).resolve()
    meta = read(folder / "run.json")
    if meta.get("catalog_sha256") != digest(CATALOG):
        raise ValueError("catalog mismatch; rebaseline explicitly")
    recorded = read(folder / "cases.json")
    statuses = {}
    for case in catalog()["cases"]:
        if not applicable(case, meta):
            statuses[case["id"]] = {"state": "N/A", "detail": "explicit scope exclusion"}
        else:
            status, detail = proof(case["id"], recorded.get(case["id"]))
            statuses[case["id"]] = {"state": status, "detail": detail}
    active = {k:v for k,v in statuses.items() if v["state"] != "N/A"}
    passed = sum(v["state"] == "PASS" for v in active.values())
    blockers = [k for k,v in active.items() if v["state"] != "PASS"]
    overnight = all(statuses[x]["state"] == "PASS" for x in "CKLMOUVY")
    release = (not blockers and statuses["Z"]["state"] == "PASS"
               and bool(meta.get("loaded_runtime_sha256")))
    summary = {
        "schema": "pce011-score-v1", "product": meta["product"], "browser": meta["browser"],
        "label": meta["label"], "source_sha": meta["source_sha"],
        "pass_count": passed, "applicable_count": len(active),
        "score_percent": round(100*passed/max(len(active),1),2),
        "overnight_gate_pass": overnight, "release_eligible": release,
        "blockers": blockers, "cases": statuses,
        "warning": "Local evidence/reviewer attestations are not independently verified by ChatGPT"
    }
    save(folder / "score.json", summary)
    return summary

def evaluate(args):
    score = assessment(args.run)
    print(json.dumps({k:v for k,v in score.items() if k != "cases"}, indent=2))
    return 0 if score["release_eligible"] else 2

def compare(args):
    results = [assessment(p) for p in args.runs]
    if len({(r["product"],r["browser"]) for r in results}) != 1:
        raise ValueError("compare the same product/browser only")
    results.sort(key=lambda r: (r["overnight_gate_pass"],r["release_eligible"],r["score_percent"]), reverse=True)
    print(json.dumps([{k:v for k,v in r.items() if k not in ("cases","warning")} for r in results],indent=2))
    return 0

def main(argv=None):
    parser=argparse.ArgumentParser(description="PCE011 A-Z evidence-based scorer")
    sub=parser.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("init")
    p.add_argument("--product",required=True,choices=("relay","consumer"))
    p.add_argument("--browser",required=True,choices=("firefox","chrome","edge","other"))
    p.add_argument("--sha",required=True)
    p.add_argument("--label",required=True)
    p.add_argument("--runtime-sha")
    p.add_argument("--output",type=Path,required=True)
    p.set_defaults(action=create)
    p=sub.add_parser("record")
    p.add_argument("--run",type=Path,required=True)
    p.add_argument("--case",required=True,choices=list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    p.add_argument("--result",required=True,choices=("PASS","FAIL","BLOCKED"))
    p.add_argument("--evidence",type=Path)
    p.add_argument("--reviewer")
    p.add_argument("--note")
    p.set_defaults(action=record)
    p=sub.add_parser("evaluate")
    p.add_argument("--run",type=Path,required=True)
    p.set_defaults(action=evaluate)
    p=sub.add_parser("compare")
    p.add_argument("--runs",type=Path,nargs="+",required=True)
    p.set_defaults(action=compare)
    opts=parser.parse_args(argv)
    try:
        return opts.action(opts)
    except (KeyError,ValueError,FileNotFoundError,FileExistsError) as exc:
        print("BENCHMARK_BLOCKED: " + str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
