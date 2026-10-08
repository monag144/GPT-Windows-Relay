#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTROL_HARNESS_VERSION = 3

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
    docs = Path(repo_root) / "docs" / "incidents"; docs.mkdir(parents=True, exist_ok=True); path = docs / incident_filename(hint, observed_at=observed_at)
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

def validate_windows_runtime_contract(run_ps1: str, consumer_run_ps1: str, relay_control_ps1: str, cutover_py: str) -> dict:
    checks={
        "main_runner_not_consumer":"GPTWindowsRelayConsumer" not in run_ps1,
        "main_runner_mutex":"Local\\GPTWindowsRelaySupervisor" in run_ps1,
        "main_runner_default_server":"& $py $server server" in run_ps1 and "--config $config --state-dir $stateDir server" not in run_ps1,
        "consumer_runner_isolated":"GPTWindowsRelayConsumer" in consumer_run_ps1 and "Local\\GPTWindowsRelayConsumerSupervisor" in consumer_run_ps1 and "--config $config --state-dir $stateDir server" in consumer_run_ps1,
        "relay_control_targets_main_runner":"$run=Join-Path $root 'run-control.ps1'" in relay_control_ps1,
        "rollback_restarts_watchdog":"rollback_watchdog_started" in cutover_py and "start_watchdog(ns.live)" in cutover_py,
        "hud_gui_is_verified":"wait_hud_process" in cutover_py and "rollback_hud_ready" in cutover_py,
    }
    blockers=[name for name,ok in checks.items() if not ok]
    return {"ok":not blockers,"checks":checks,"blockers":blockers}

def evaluate_runtime_transition(observed: dict) -> dict:
    if not isinstance(observed,dict): raise ControlHarnessError("runtime observation must be a dict")
    checks={
        "main_8766":bool(observed.get("main_8766")),
        "consumer_8767":bool(observed.get("consumer_8767")),
        "distinct_listener_pids":bool(observed.get("main_pid")) and bool(observed.get("consumer_pid")) and observed.get("main_pid")!=observed.get("consumer_pid"),
        "one_hud":int(observed.get("hud_processes",0))==1,
        "firefox_runtime":bool(observed.get("firefox_runtime")),
        "helper_finalized":bool(observed.get("helper_finalized")),
    }
    if observed.get("rolled_back") is True:
        checks["rollback_exact"]=observed.get("rollback_exact") is True
    blockers=[name for name,ok in checks.items() if not ok]
    return {"ok":not blockers,"checks":checks,"blockers":blockers}

def assess_engineering_operation_budget(current_operation:int,max_operation:int=100,current_series:int=8,next_chat_title:str|None=None)->dict:
    if current_operation<0 or current_operation>max_operation: raise ControlHarnessError("invalid operation")
    if current_series<1: raise ControlHarnessError("invalid engineering series")
    r=max_operation-current_operation
    successor_title=next_chat_title or f"💻PC Engineering {current_series+1}🔧"
    return {"current_series":current_series,"current_operation":current_operation,"remaining_after_current":r,"next_chat_title":successor_title,"rotation_priority":"P0" if r<=25 else "P1","rotation_build_due":r<=25,"rotation_live_proof_due":r<=10,"block_non_rotation_mutations":r<=4}

def build_control_harness_contract(mission_id: str) -> dict:
    return {
        "version": CONTROL_HARNESS_VERSION,
        "mission_id": mission_id,
        "turn_discipline": {
            "read_every_turn": [
                "consumer/control_harness.py",
                "windows-relay/TASKS.md",
                "docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md",
                "docs/windows-relay-mission-and-roadmap.md"
            ],
            "canonical_windows_repository": "monag144/GPT-Windows-Relay",
            "sandwich_required": True,
            "audit_every_engineering_turns": 5,
            "audit_rule": "Every fifth engineering turn/operation, audit the preceding five for harness compliance, incidents, repeated/disproven approaches, repository destination, test evidence, rollback discipline, and roadmap drift.",
            "harness_hole_rule": "If a stale, contradictory, unenforced, or missing control is discovered, repair the harness/test contract before continuing risky mutation."
        },
        "test_runtime": {
            "default_runner": "unittest",
            "selection_rule": "Prefer Python stdlib unittest while the repository suite has no external-runner dependency.",
            "external_runner_rule": "If an external runner such as pytest is used, capability-probe that exact interpreter and runner import before starting the suite. Executable existence is not proof of runner capability.",
            "bytecode_rule": "Run acceptance with bytecode generation disabled where practical."
        },
        "migration_evidence": {
            "manifest_path": "docs/migration/MIGRATION_2026-10-08T0110Z_TERMUX_WINDOWS_EVIDENCE_MANIFEST.json",
            "source_repository": "monag144/GPT-Termux-Relay",
            "source_commit": "249e3bb46c6ea57968d9ecf5157d73867a7f918d",
            "verification_rule": "Migration provenance is the committed Git object. Verify each entry against the blob id at an explicit treeish such as HEAD:<destination_path>; do not infer provenance from checked-out working-tree bytes.",
            "diff_check_rule": "Run git diff --check over the branch; every reported path must either be absent from the error set or have a committed HEAD blob id that exactly matches the manifest entry. Any non-manifest or changed-blob whitespace error blocks promotion."
        },
        "source_tree_hygiene": {
            "dirty_preflight_rule": "Classify every dirty path before cleanup. Only deterministic generated caches may be removed automatically; any unknown or source-like path fails closed.",
            "test_rule": "Run source acceptance with Python bytecode generation disabled when practical so tests do not create the next preflight failure.",
            "ignore_contract": [".gitignore::__pycache__/", ".gitignore::*.py[cod]", ".gitignore::.pytest_cache/"]
        },
        "incident_logging": {
            "method": "write_incident",
            "path_rule": "docs/incidents/INCIDENT_<UTC timestamp>_<short hint>.md",
            "rule": "Log abnormal rendering, autonomy, user-rescue, tooling, transport, data-loss, duplicate-send, or execution incidents as small timestamped records. Do not create a giant current/active/authoritative incident document."
        },
        "reflection": {
            "method": "append_reflection",
            "rule": "After an incident, record evidence-backed learning and the smallest next change. Exact duplicate reflections are denied by SHA-256 and counted rather than appended again."
        },
        "runtime_gates": {
            "source_contract_method":"validate_windows_runtime_contract",
            "transition_method":"evaluate_runtime_transition",
            "rule":"A live transition is blocked unless 8766 main, isolated 8767 consumer, exactly one HUD, browser runtime evidence, and helper finalization are observed.",
            "browser_discovery_settle": {
                "settle_ms": 500,
                "stale_pending_lease_ms": 5000,
                "rule": "A discovered packet may not remain indefinitely in an unchanged pending-settle record. If the settle lease expires, the pending record must be cleared, observed, and re-armed."
            },
            "firefox_identity_bootstrap": {
                "known_conversation_rule": "When an exact ChatGPT conversation URL is known, call resolve-conversation-tab first, require exactly one canonical URL match, and use its returned Firefox PID/tab identity for subsequent list/reload/refresh actions.",
                "list_tabs_rule": "Do not use unscoped list-tabs as the bootstrap primitive when multiple visible Firefox windows may exist; unscoped list-tabs is only valid when single-window Firefox state is itself the named acceptance condition."
            }
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
