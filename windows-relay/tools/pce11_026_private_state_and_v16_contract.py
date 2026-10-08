#!/usr/bin/env python3
"""PCE11.026: read-only private sandbox postmortem for failed v16 /status.

Do not launch any process, read credentials, mutate production state or infer
unrecorded HTTP response. Forensics limited to exact .024 sandbox/state/state.json,
prior .025 evidence and immutable historical v16 source status contract.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
BASE="368c80824f6354aef470f80de60a6cccfd704382"
SANDBOX_NAME="PCE11_ISOLATED_V16_CANARY_20261008T102936Z_2a7894efa7d3"
PRIOR_NAME="PCE11_025_V16_FAILURE_FORENSICS_2026-10-08T103325Z.json"
ORIGINAL_BLOB="414b74121b1a5a5f2a049ebc84097223e7b5e69f"

def run(cmd,timeout=60):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:raise RuntimeError("verified Git command failed "+str(cmd[:3])+" exit="+str(p.returncode))
    return p.stdout.strip()

def git(root,*terms,timeout=45):
    exe=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    return run([exe,"-C",str(root),*terms],timeout)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def read_json(path,max_bytes=1000000):
    if not path.is_file() or path.stat().st_size>max_bytes:
        raise RuntimeError("required forensic JSON file absent or too large: "+path.name)
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict):raise RuntimeError("forensic JSON is not object: "+path.name)
    return value

def examine_state(state_dir):
    state=state_dir/"state.json"
    if not state.is_file():
        return {"file_present":False,"queue_count":None,"snapshot_only":True}
    d=read_json(state)
    missions=d.get("missions")
    processed=d.get("processed")
    return {"file_present":True,"sha256":sha(state),
      "byte_count":state.stat().st_size,
      "updated_utc":datetime.fromtimestamp(state.stat().st_mtime,timezone.utc).isoformat(),
      "version":d.get("version"),"armed":d.get("armed"),
      "queue_count":len(missions) if isinstance(missions,list) else None,
      "processed_count":len(processed) if isinstance(processed,dict) else None,
      "active_action_present":bool(d.get("active_action")),
      "snapshot_only":True,
      "private_state_not_evidence_of_original_http_payload":True}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--expected-head",required=True)
    a=ap.parse_args()
    repo=a.repo.resolve(); live=a.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("source/live roots are invalid")
    if git(repo,"rev-parse","HEAD")!=BASE or git(repo,"branch","--show-current")!=BRANCH:
        raise RuntimeError("local checkout not at verified .025 baseline")
    if git(repo,"status","--porcelain"):
        raise RuntimeError("canonical checkout dirty")
    if "monag144/gpt-windows-relay" not in git(repo,"remote","get-url","origin").lower():
        raise RuntimeError("GitHub remote identity mismatch")
    remote=git(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=a.expected_head:
        raise RuntimeError("source branch advanced; no unverified pull")
    git(repo,"fetch","--no-tags","origin","refs/heads/"+BRANCH,timeout=60)
    if git(repo,"rev-parse","FETCH_HEAD")!=a.expected_head:
        raise RuntimeError("fetched object does not match pinned revision")
    git(repo,"merge-base","--is-ancestor","HEAD","FETCH_HEAD")
    git(repo,"merge","--ff-only","FETCH_HEAD",timeout=65)
    if git(repo,"rev-parse","HEAD")!=a.expected_head or git(repo,"status","--porcelain"):
        raise RuntimeError("source fast-forward not clean/exact")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    gov=engineering_preflight(repo,26,series=11)
    if not gov["ok"]:raise RuntimeError("missing mandatory five document controls")
    prior=read_json(live/"bin"/PRIOR_NAME)
    if (prior.get("schema")!="pce011-025-readonly-failure-forensics-v1"
       or prior.get("head")!=BASE
       or prior.get("classification")!="CLEANUP_AND_MAIN_VERIFIED"
       or prior.get("cleanup_reconciled") is not True
       or prior.get("main_identity_reconciled") is not True):
        raise RuntimeError(".025 forensic report did not positively reconcile cleanup and main")
    sandbox=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))/"GPTWindowsRelay"/"pce11-isolated"/SANDBOX_NAME
    original=read_json(sandbox/"health-report.json")
    if original.get("schema")!="pce011-contained-v16-health-v1" or original.get("sandbox")!=str(sandbox):
        raise RuntimeError("wrong original .024 health report")
    if original.get("failure")!="RuntimeError: foreign sidecar PID or inherited production missions":
        raise RuntimeError("recorded canary error changed")
    state=examine_state(sandbox/"state")
    # Check only existence, not contents of private auth config/token.
    token_file_exists=(sandbox/"private"/"bridge.json").exists()
    sys.path.insert(0,str(repo/"windows-relay"/"tools"))
    import pce11_013_isolated_supervisor as staged
    record=staged.candidate(repo,live)
    if record["tracked_git_blob"]!=ORIGINAL_BLOB or record["normalized_worktree_blob"]!=ORIGINAL_BLOB:
        raise RuntimeError("historical v16 provenance drift")
    source_text=Path(record["source"]).read_text(encoding="utf-8-sig")
    markers={
      "pid_uses_os_getpid": "'pid':os.getpid()" in source_text,
      "count_from_private_state": "'pending_missions':self.server.state.pending_mission_count()" in source_text,
      "state_ctor_respects_cli_state_dir": "State(a.state_dir/'state.json')" in source_text,
      "fresh_state_missions_empty": "'missions':[]" in source_text,
      "private_status_endpoint": "if request_path=='/status'" in source_text}
    if not all(markers.values()):
        raise RuntimeError("historical v16 /status or private state source contract changed")
    # No authenticated request to an inactive sidecar, no new subprocesses
    # except read-only git. Original HTTP response was not stored.
    result={"schema":"pce011-026-private-state-v16-contract-v1",
      "repo_sha":a.expected_head,
      "mandatory_sha256":{k:v["sha256"] for k,v in gov["reads"].items()},
      "sandbox":str(sandbox),"original_child_pid":original.get("child_pid"),
      "original_failure":original["failure"],
      "original_status_payload_persisted":"sidecar_status" in original,
      "private_auth_config_exists_after_cleanup":token_file_exists,
      "private_state_after_child_exit":state,"historical_v16_source":markers,
      "staged_git_sha":record["git_head"],
      "original_job_cleanup_verified":prior["cleanup_reconciled"],
      "production_identity_preserved":prior["main_identity_reconciled"],
      "exact_failed_condition_proven":False,
      "diagnostic_conclusion":"Actual rejected HTTP PID and mission count were not recorded. Private state is a later snapshot only.",
      "sidecar_started":False,"production_mutated":False,"retry_authorized":False}
    output=live/"bin"/("PCE11_026_PRIVATE_STATE_DIAG_"+datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")+".json")
    if output.exists():raise RuntimeError("report collision")
    output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("PCE11_026_PRIVATE_STATE="+json.dumps({
      "report":str(output),"source_sha":a.expected_head,
      "child_pid":result["original_child_pid"],"failure":result["original_failure"],
      "private_state":state,
      "auth_file_still_present":token_file_exists,
      "historical_contract":markers,
      "rejected_http_fields_recorded":result["original_status_payload_persisted"],
      "actual_failed_condition_proven":False,
      "job_cleanup_and_main_confirmed":True,
      "no_process_launched":True,"new_canary_authorized":False},
      separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as ex:
        print("PCE11_026_BLOCKED="+type(ex).__name__+": "+str(ex)[:300],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
