#!/usr/bin/env python3
"""PCE11.025: inspect failed contained v16 sidecar with zero process mutation.

Reads immutable .024 sandbox health JSON; identifies current listeners on
8766/8768, read-only authenticated production /status, and recorded sidecar
child identity. Does NOT kill/restart/STOP/replay/relaunch/arm or touch browser.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
AUDIT="docs/audits/AUDIT_2026-10-08T1031Z_PCE11_OPERATIONS_020_024.md"
SANDBOX="PCE11_ISOLATED_V16_CANARY_20261008T102936Z_2a7894efa7d3"
FIELDS=("schema","time_utc","sandbox","port","baseline_main",
  "private_config_and_state","isolated_process_started","job_contained",
  "child_pid","status_ok","private_missions_count","sidecar_status",
  "cleanup_verified","production_main_identity_preserved",
  "main_after","production_main_identity_error","sidecar_released",
  "failure","private_config_cleanup_failed","prod_process_modified",
  "operator_stop_triggered","browser_control_used","token_exposed")

def run(args,timeout=35):
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if result.returncode:raise RuntimeError("Git verification command returned "+str(result.returncode))
    return result.stdout.strip()

def process_image(pid):
    """Best-effort read-only tasklist metadata, never act on PID."""
    if not isinstance(pid,int) or pid<=0:return {"known":False}
    exe=shutil.which("tasklist")
    if not exe:return {"known":False,"reason":"tasklist unavailable"}
    try:
        p=subprocess.run([exe,"/FI","PID eq "+str(pid),"/FO","CSV","/NH"],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
            encoding="utf-8",errors="replace",timeout=8)
        if p.returncode:return {"known":False,"reason":"tasklist error"}
        import csv,io
        rows=list(csv.reader(io.StringIO(p.stdout)))
        for row in rows:
            if len(row)>=2 and row[1].strip()==str(pid):
                return {"known":True,"listed":True,"image_name":row[0][:120]}
        return {"known":True,"listed":False}
    except (OSError,subprocess.TimeoutExpired):
        return {"known":False,"reason":"tasklist inspection unavailable"}

def safe_port_pids(health,port):
    try:return {"known":True,"pids":health.port_pids(port)}
    except Exception as ex:return {"known":False,"error_type":type(ex).__name__}

def source(repo):
    sys.path.insert(0,str(repo/"windows-relay"/"tools"))
    import pce11_016_v16_health_canary as health
    if health.PROD_PORT!=8766 or health.SIDECAR_PORT!=8768:
        raise RuntimeError("unexpected read-only port contract")
    return health

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--live",type=Path,required=True)
    parser.add_argument("--expected-head",required=True)
    args=parser.parse_args()
    repo=args.repo.resolve();live=args.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("separate canonical/live roots required")
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    g=lambda *items:run([git,"-C",str(repo),*items])
    if g("rev-parse","HEAD")!=args.expected_head:
        raise RuntimeError("PCE11.025 governance sync not installed")
    if g("branch","--show-current")!=BRANCH:
        raise RuntimeError("unexpected canonical checkout branch")
    if "monag144/gpt-windows-relay" not in g("remote","get-url","origin").lower():
        raise RuntimeError("unexpected GitHub source origin")
    if g("status","--porcelain"):
        raise RuntimeError("dirty canonical source, do not continue")
    remote=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=args.expected_head:
        raise RuntimeError("remote source moved since audit sync")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    gov=engineering_preflight(repo,25,series=11)
    checkpoint=gov["checkpoints"].get("audit",{})
    if not gov["ok"] or checkpoint.get("path")!=AUDIT or checkpoint.get("window")!=[20,24]:
        raise RuntimeError("PCE11.025 five-slot audit was not locally accepted")

    # Do not discover a replacement artifact by recency: only inspect the
    # exact sandbox produced by the .024 attempted action.
    sandbox=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))/"GPTWindowsRelay"/"pce11-isolated"/SANDBOX
    report=sandbox/"health-report.json"
    if not report.is_file() or report.stat().st_size>1024*1024:
        raise RuntimeError("exact .024 health report missing or unexpectedly large")
    original=json.loads(report.read_text(encoding="utf-8-sig"))
    if not isinstance(original,dict) or original.get("schema")!="pce011-contained-v16-health-v1":
        raise RuntimeError("wrong or malformed isolated sidecar report")
    if original.get("sandbox")!=str(sandbox):
        raise RuntimeError("canary report sandbox identity mismatch")
    if original.get("port")!=8768:
        raise RuntimeError("report belongs to wrong listener port")
    values={key:original.get(key) for key in FIELDS if key in original}
    # No private token or raw log is opened or copied. If future reports
    # contain extra keys, they will not be forwarded by allowlist.
    health=source(repo)
    listeners={"8766":safe_port_pids(health,8766),
               "8768":safe_port_pids(health,8768)}
    backend={}
    try:
        b=health.main_baseline()
        backend={"checked":True,"pid":b["pid"],"armed":b["armed"],
          "outbound_owner":b["outbound_owner"],"pending_missions":b["pending_missions"]}
    except Exception as ex:
        backend={"checked":False,"exception":type(ex).__name__}
    pid=original.get("child_pid")
    child=process_image(pid)
    child["recorded_pid"]=pid if isinstance(pid,int) else None
    unknown=(not listeners["8768"]["known"] or not listeners["8766"]["known"]
             or not backend.get("checked") or not child.get("known"))
    still_listening=bool(listeners["8768"].get("pids"))
    child_still_listed=bool(child.get("listed"))
    clean=(original.get("cleanup_verified") is True
       and original.get("sidecar_released") is True
       and not still_listening and not child_still_listed
       and not unknown)
    main_proven=(backend.get("checked")
       and original.get("baseline_main",{}).get("pid")==backend["pid"]
       and original.get("production_main_identity_preserved") is True
       and original.get("main_after",{}).get("pid")==backend["pid"])
    classification=("CLEANUP_AND_MAIN_VERIFIED" if clean and main_proven
       else "UNSAFE_OR_UNPROVEN_POST_CANARY_STATE")
    info={"schema":"pce011-025-readonly-failure-forensics-v1",
       "audit_sha256":checkpoint["sha256"],
       "head":args.expected_head,
       "read_sha256":{k:v["sha256"] for k,v in gov["reads"].items()},
       "original_report":str(report),"report_values":values,
       "current_listeners":listeners,"current_production_get_status":backend,
       "child_tasklist_inspection":child,
       "cleanup_reconciled":clean,"main_identity_reconciled":bool(main_proven),
       "classification":classification,
       "canary_relaunch_allowed":False,
       "production_replacement_allowed":False,
       "side_effects_performed":False}
    now=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    dest=live/"bin"/("PCE11_025_V16_FAILURE_FORENSICS_"+now+".json")
    if dest.exists():raise RuntimeError("forensic evidence collision")
    dest.write_text(json.dumps(info,indent=2)+"\n",encoding="utf-8")
    outgoing={"report":str(dest),"git_sha":args.expected_head,
      "five_reads_sha256":info["read_sha256"],
      "audit_window":checkpoint["window"],
      "saved_canary":{k:values.get(k) for k in
          ("child_pid","isolated_process_started","job_contained","status_ok",
           "private_missions_count","cleanup_verified","sidecar_released",
           "production_main_identity_preserved","failure")},
      "current_listeners":listeners,
      "current_main":backend,
      "child_identity":child,
      "classification":classification,
      "new_processes_launched":False,"new_sidecar_authorized":False}
    print("PCE11_025_V16_FORENSICS="+json.dumps(outgoing,separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as ex:
        print("PCE11_025_BLOCKED="+type(ex).__name__+": "+str(ex)[:300],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
