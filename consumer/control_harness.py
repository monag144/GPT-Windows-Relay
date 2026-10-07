#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTROL_HARNESS_VERSION = 1

class ControlHarnessError(ValueError):
    pass

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _stamp(value: datetime | None = None) -> str:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")

def _slug(value: str) -> str:
    out = re.sub(r"[^A-Za-z0-9]+", "_", str(value).strip()).strip("_").upper()
    return (out or "INCIDENT")[:72]

def canonical_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def exact_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def default_state_dir() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GPTWindowsRelayConsumer"
    root.mkdir(parents=True, exist_ok=True)
    return root

def record_once(kind: str, value: Any, *, state_root: Path | None = None, locator: str | None = None) -> dict:
    if not isinstance(kind, str) or not kind.strip():
        raise ControlHarnessError("record kind is required")
    raw = canonical_bytes(value); digest = hashlib.sha256(raw).hexdigest(); root = state_root or default_state_dir(); root.mkdir(parents=True, exist_ok=True)
    db = root / "control-harness-records.sqlite3"; con = sqlite3.connect(db)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS exact_records(kind TEXT NOT NULL, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, duplicate_count INTEGER NOT NULL DEFAULT 0, locator TEXT, PRIMARY KEY(kind,sha256))")
        row = con.execute("SELECT first_seen,duplicate_count,locator FROM exact_records WHERE kind=? AND sha256=?", (kind,digest)).fetchone()
        now = _now()
        if row:
            con.execute("UPDATE exact_records SET last_seen=?, duplicate_count=duplicate_count+1 WHERE kind=? AND sha256=?", (now,kind,digest)); con.commit()
            return {"accepted":False,"duplicate":True,"kind":kind,"sha256":digest,"bytes":len(raw),"first_seen":row[0],"duplicate_count":int(row[1])+1,"locator":row[2]}
        con.execute("INSERT INTO exact_records(kind,sha256,bytes,first_seen,last_seen,duplicate_count,locator) VALUES(?,?,?,?,?,?,?)", (kind,digest,len(raw),now,now,0,locator)); con.commit()
        return {"accepted":True,"duplicate":False,"kind":kind,"sha256":digest,"bytes":len(raw),"first_seen":now,"duplicate_count":0,"locator":locator}
    finally:
        con.close()

def incident_filename(hint: str, *, observed_at: datetime | None = None) -> str:
    return f"INCIDENT_{_stamp(observed_at)}_{_slug(hint)}.md"

def write_incident(repo_root: Path, hint: str, sections: dict[str,str], *, observed_at: datetime | None = None) -> dict:
    if not isinstance(sections, dict) or not sections:
        raise ControlHarnessError("incident sections are required")
    docs = Path(repo_root) / "docs"; docs.mkdir(parents=True, exist_ok=True); path = docs / incident_filename(hint, observed_at=observed_at)
    body = [f"# INCIDENT {_stamp(observed_at)} — {hint.strip()}", ""]
    for heading, text in sections.items():
        body.extend([f"## {str(heading).strip()}", str(text).strip(), ""])
    rendered = "\n".join(body).rstrip()+"\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == rendered:
            return {"created":False,"duplicate":True,"path":str(path),"sha256":exact_sha256(rendered)}
        raise ControlHarnessError(f"incident path collision: {path.name}")
    path.write_text(rendered, encoding="utf-8")
    return {"created":True,"duplicate":False,"path":str(path),"sha256":exact_sha256(rendered)}

def append_reflection(mission_id: str, incident_ref: str, learning: str, next_change: str, evidence: list[str] | None = None, *, state_root: Path | None = None) -> dict:
    base={"mission_id":str(mission_id),"incident_ref":str(incident_ref),"learning":str(learning).strip(),"next_change":str(next_change).strip(),"evidence":[str(x) for x in (evidence or [])]}
    root=state_root or default_state_dir(); verdict=record_once("reflection",base,state_root=root,locator="control-reflections.jsonl")
    if not verdict["accepted"]: return verdict
    rec={"time":_now(),**base,"sha256":verdict["sha256"]}; out=root/"control-reflections.jsonl"
    with out.open("a",encoding="utf-8") as f: f.write(json.dumps(rec,ensure_ascii=False,separators=(",", ":"))+"\n")
    return {**verdict,"path":str(out)}


def evaluate_improvement(baseline: dict, candidate: dict) -> dict:
    """Fail closed on safety regressions; promote only with evidence of useful improvement."""
    for name, value in (("baseline", baseline), ("candidate", candidate)):
        if not isinstance(value, dict):
            raise ControlHarnessError(f"{name} metrics must be a dict")
    blockers=[]
    if int(candidate.get("test_failures", 0)) != 0: blockers.append("test_failures")
    if not bool(candidate.get("canary_success", False)): blockers.append("canary_failed")
    if int(candidate.get("side_effect_replays", 0)) > int(baseline.get("side_effect_replays", 0)): blockers.append("side_effect_replay_regression")
    if int(candidate.get("user_rescues", 0)) > int(baseline.get("user_rescues", 0)): blockers.append("user_rescue_regression")
    if int(candidate.get("data_loss_events", 0)) > int(baseline.get("data_loss_events", 0)): blockers.append("data_loss_regression")
    improvements=[]
    if float(candidate.get("delivery_success_rate", 0.0)) > float(baseline.get("delivery_success_rate", 0.0)): improvements.append("delivery_success_rate")
    if int(candidate.get("duplicate_bytes_avoided", 0)) > int(baseline.get("duplicate_bytes_avoided", 0)): improvements.append("duplicate_bytes_avoided")
    if float(candidate.get("median_latency_ms", 1e30)) < float(baseline.get("median_latency_ms", 1e30)): improvements.append("median_latency_ms")
    if bool(candidate.get("target_incident_closed", False)): improvements.append("target_incident_closed")
    return {"promote":not blockers and bool(improvements),"blockers":blockers,"improvements":improvements}

def build_control_harness_contract(mission_id: str) -> dict:
    return {
        "version": CONTROL_HARNESS_VERSION,
        "mission_id": mission_id,
        "incident_logging": {
            "method": "write_incident",
            "path_rule": "docs/INCIDENT_<UTC timestamp>_<short hint>.md",
            "rule": "Log abnormal rendering, autonomy, user-rescue, tooling, transport, data-loss, duplicate-send, or execution incidents as small timestamped records. Do not create a giant current/active/authoritative incident document."
        },
        "reflection": {
            "method": "append_reflection",
            "rule": "After an incident, record evidence-backed learning and the smallest next change. Exact duplicate reflections are denied by SHA-256 and counted rather than appended again."
        },
        "continuous_improvement": {
            "method": "evaluate_improvement",
            "cycle": ["observe", "incident-log", "reflect", "minimal-change", "targeted-test", "full-suite", "live-canary", "revision-promotion", "measure"],
            "rules": ["evidence before claims", "never replay uncertain side effects", "change one failure mode at a time when practical", "shipped behavior changes require a new revision", "keep rollback evidence"]
        },
        "data_policy": {
            "exact_duplicate_rule": "SHA-256 the exact canonical bytes before persistence or resend. If kind+hash already exists, reference the first record and increment duplicate_count instead of storing the same bytes again.",
            "method": "record_once",
            "goal": "Accumulated data should become indexed evidence, not repeated payload waste."
        },
        "capture_policy": {
            "visual": "Use managed screenshot capture and ChatGPT attachment transport for visual state.",
            "text_preference": ["semantic UIA/readback", "window Ctrl+A then Ctrl+C clipboard capture fallback"],
            "send_rule": "Hash captured bytes before storing/sending; deny exact duplicate captures; attach large captured text instead of repeatedly pasting giant payloads."
        }
    }
