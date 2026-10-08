#!/usr/bin/env python3
"""PCE11.029 read-only postmortem for isolated v16 launch PID vs HTTP PID.

No server launch, port binding, STOP/arm/queue mutations, browser control, PID
termination, secret reading, or source checkout modification other than a clean
GitHub-fast-forward of canonical source. No claim of ancestry without evidence.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="2e6ff2a811a743af99f020ea7dabd653ab3b3b0a"
INCIDENT="docs/incidents/INCIDENT_2026-10-08T1043Z_PCE11_028_V16_PID_IDENTITY_MISMATCH.md"
SANDBOX="PCE11_ISOLATED_V16_CANARY_20261008T104351Z_79f9e6b1e22d"
SOURCE_BLOB="414b74121b1a5a5f2a049ebc84097223e7b5e69f"
def cmd(argv,timeout=55):
    p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
      text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:raise RuntimeError("read-only Git verification failed rc="+str(p.returncode))
    return p.stdout.strip()
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as r:
        for chunk in iter(lambda:r.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def inspect_python(path):
    if not path:return {"present":False}
    p=Path(path)
    try:
        p=p.resolve()
        out={"present":p.is_file(),"absolute_path":str(p)}
        if p.is_file():
            out.update({"size":p.stat().st_size,"sha256":sha(p),
                "suffix":p.suffix,"basename":p.name})
        return out
    except (OSError,ValueError) as err:
        return {"present":False,"error_type":type(err).__name__}
def current_pid_image(pid):
    # Tasklist is inspection only; historical PIDs may have been recycled.
    tool=shutil.which("tasklist")
    if not tool or type(pid)!=int or pid<1:return {"available":False}
    try:
        p=subprocess.run([tool,"/FI","PID eq "+str(pid),"/FO","CSV","/NH"],
            text=True,capture_output=True,encoding="utf-8",errors="replace",timeout=8)
        if p.returncode:return {"available":False}
        import csv,io
        rows=list(csv.reader(io.StringIO(p.stdout)))
        for row in rows:
            if len(row)>1 and row[1].strip()==str(pid):
                return {"available":True,"listed_now":True,
                     "image":row[0][:100],"historical_identity_verified":False}
        return {"available":True,"listed_now":False,
                  "historical_identity_verified":False}
    except (OSError,subprocess.TimeoutExpired):
        return {"available":False}
def read_json(path):
    if not path.is_file() or path.stat().st_size>131072:
        raise RuntimeError("exact private health evidence absent/oversized")
    x=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(x,dict):raise RuntimeError("health report is not an object")
    return x
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--expected-head",required=True)
    a=ap.parse_args()
    repo=a.repo.resolve();live=a.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("canonical source and deployed roots must be distinct")
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    def g(*parts,timeout=55):
        return cmd([git,"-C",str(repo),*parts],timeout)
    if g("rev-parse","HEAD")!=PREVIOUS:
        raise RuntimeError("local source baseline not PCE11.028")
    if g("branch","--show-current")!=BRANCH or "monag144/gpt-windows-relay" not in g("remote","get-url","origin").lower():
        raise RuntimeError("unexpected GitHub source identity")
    if g("status","--porcelain"):raise RuntimeError("dirty checkout; no mutation")
    remote=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=a.expected_head:raise RuntimeError("GitHub HEAD not pinned")
    g("fetch","--no-tags","origin","refs/heads/"+BRANCH,timeout=65)
    if g("rev-parse","FETCH_HEAD")!=a.expected_head:raise RuntimeError("unexpected source fetched")
    g("merge-base","--is-ancestor","HEAD","FETCH_HEAD")
    g("merge","--ff-only","FETCH_HEAD",timeout=60)
    if g("rev-parse","HEAD")!=a.expected_head or g("status","--porcelain"):
        raise RuntimeError("GitHub source FF identity could not be verified")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    proof=engineering_preflight(repo,29,series=11)
    if not proof["ok"] or not (repo/INCIDENT).is_file():
        raise RuntimeError("governance/incident record missing")
    sandbox=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))/"GPTWindowsRelay"/"pce11-isolated"/SANDBOX
    report_path=sandbox/"health-report.json"
    report=read_json(report_path)
    if (report.get("schema")!="pce011-contained-v16-health-v1" or
        report.get("sandbox")!=str(sandbox) or report.get("port")!=8768 or
        report.get("child_pid")!=1640 or report.get("observed_status_pid")!=11180 or
        report.get("observed_pending_missions")!=0):
        raise RuntimeError("original second-canary evidence contradicted")
    if not all(report.get(k) is True for k in
       ("job_contained","cleanup_verified","sidecar_released","production_main_identity_preserved",
        "status_missions_zero")) or report.get("status_pid_matches_child") is not False:
        raise RuntimeError("recorded job cleanup or mismatch facts missing")
    # Never read or disclose the private token/config; only check erased state.
    private_credential_still_exists=(sandbox/"private"/"bridge.json").exists()
    sys.path.insert(0,str(repo/"windows-relay"/"tools"))
    import pce11_016_v16_health_canary as health
    import pce11_013_isolated_supervisor as stage
    current_listeners={"8766":health.port_pids(8766),"8768":health.port_pids(8768)}
    live_main=health.main_baseline()   # authenticated READ-ONLY GET /status
    if (current_listeners["8766"]!=[18632] or live_main["pid"]!=18632 or
        live_main["outbound_owner"]!="browser" or
        live_main["armed"] is not True or current_listeners["8768"]):
        raise RuntimeError("current live identity differs or port 8768 occupied")
    historic=stage.candidate(repo,live)
    if historic["normalized_worktree_blob"]!=SOURCE_BLOB:
        raise RuntimeError("v16 stage source pin changed")
    # File metadata may suggest an interpreter redirector; it does not
    # establish parentage of exited Windows PIDs 1640 and 11180.
    interpreter=inspect_python(sys.executable)
    base=inspect_python(getattr(sys,"_base_executable",None))
    same_exec=(interpreter.get("sha256") and
               interpreter.get("sha256")==base.get("sha256"))
    pid_data={"created_child_pid":1640,"observed_http_pid":11180,
      "identity_equal":False,
      "launch_executable":interpreter,
      "base_executable":base,
      "exe_contents_equal_if_both_available":same_exec,
      "venv_interpreter":sys.prefix!=sys.base_prefix,
      "historical_process_ancestry_proven":False,
      "historic_child_current_tasklist":current_pid_image(1640),
      "historic_http_pid_current_tasklist":current_pid_image(11180),
      "tasklist_may_contain_reused_PIDs":True}
    conclusion=("Executable/redirector identity may explain a distinct HTTP host PID, "
      "but ancestor relationship and job membership of exited host PID 11180 "
      "were not captured during PCE11.028. Must prove them in a separately "
      "gated bounded experiment; do NOT relax host PID check.")
    evidence={"schema":"pce011-029-readonly-pid-lineage-v1",
        "canonical_commit":a.expected_head,
        "five_read_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
        "original_report":str(report_path),"original_report_sha256":sha(report_path),
        "original_status":{"observed_pid":11180,"contained_launcher_pid":1640,
          "private_missions":0,"pid_mismatch":True,"job_cleanup":True},
        "private_credential_erased":not private_credential_still_exists,
        "listeners_now":current_listeners,"main_now":live_main,
        "process_identity":pid_data,"historic_blob":SOURCE_BLOB,
        "conclusion":conclusion,"no_new_v16_process":True,
        "no_production_mutation":True,"relaunch_authorized":False}
    when=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    output=live/"bin"/("PCE11_029_PID_IDENTITY_DIAG_"+when+".json")
    if output.exists():raise RuntimeError("no overwrite of prior evidence")
    output.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    result={"report":str(output),"commit":a.expected_head,
      "read_sha256":evidence["five_read_sha256"],
      "launch_pid":1640,"http_pid":11180,"mission_count":0,
      "native_job_cleanup_verified":True,
      "current_main_pid":live_main["pid"],
      "main_armed":live_main["armed"],
      "main_pending_missions":live_main["pending_missions"],
      "port8768_free":True,
      "executable":interpreter,
      "base_executable":base,
      "venv_interpreter":pid_data["venv_interpreter"],
      "historical_process_ancestry_proven":False,
      "private_token_erased":not private_credential_still_exists,
      "no_sidecar_launched":True,
      "live_cutover_authorized":False}
    print("PCE11_029_PID_FORENSICS="+json.dumps(result,separators=(",",":")))
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as e:
        print("PCE11_029_BLOCKED="+type(e).__name__+": "+str(e)[:350],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
