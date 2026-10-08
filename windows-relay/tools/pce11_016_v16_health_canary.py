#!/usr/bin/env python3
"""PCE11.016 source-only gate; PCE11.017 independently contained v16 GET /status canary.

Never touches 8766 process, Firefox, HUD, consumer state, or queues. This tool is
separate from old disabled v16 supervisor canary and uses only a private job.
"""
from __future__ import annotations
import argparse,hashlib,json,os,secrets,shutil,subprocess,sys,time,urllib.error,urllib.request
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
BASE_SHA="2b02b506d8850882d806f8461c25b0a7f03140fd"
PROD_PORT=8766
SIDECAR_PORT=8768
MAIN_APP="GPTWindowsRelay"
REQUIRED_ARCHIVE_SHA="f8ab9b9925b0a6e4688d85a1d6ee2c79563fed9c6e50dd5b75cbf9c0e140c0b7"
CANARY_NAME="PCE11_ISOLATED_V16_CANARY"
HEALTH_TIMEOUT_SECONDS=9

def command(argv,cwd=None,timeout=40):
    p=subprocess.run(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode!=0:raise RuntimeError("command failed "+str(argv[:3])+" rc="+str(p.returncode)+" "+p.stderr[-350:])
    return p.stdout.strip()

def git(root,*items,timeout=35):
    exe=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    return command([exe,"-C",str(root),*items],timeout=timeout)

def hash_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def port_pids(port):
    exe=shutil.which("netstat")
    if not exe:raise RuntimeError("netstat required for port-identity proof")
    matches=[]
    for line in command([exe,"-ano","-p","tcp"],timeout=20).splitlines():
        cells=line.split()
        if len(cells)<5 or cells[0].upper()!="TCP" or cells[3].upper()!="LISTENING":continue
        if cells[1].rsplit(":",1)[-1]==str(port) and cells[4].isdigit():
            matches.append(int(cells[4]))
    return sorted(set(matches))

def get_status(port,token,timeout=1.0):
    req=urllib.request.Request("http://127.0.0.1:"+str(port)+"/status",method="GET",
           headers={"X-GPT-Windows-Relay-Token":str(token)})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        data=json.loads(resp.read(8192))
    if not isinstance(data,dict) or data.get("ok") is not True:raise RuntimeError("GET status was invalid")
    return {field:data.get(field) for field in
      ("ok","pid","armed","outbound_owner","pending_missions","stop_generation","browser_quiesced_generation")}

def main_config():
    config=Path(os.environ.get("APPDATA",Path.home()))/MAIN_APP/"bridge.json"
    if not config.is_file():raise RuntimeError("main authentication config not available")
    values=json.loads(config.read_text(encoding="utf-8-sig"))
    if not isinstance(values,dict) or values.get("port")!=PROD_PORT or not values.get("token"):
        raise RuntimeError("main backend config invalid")
    return str(values["token"])

def main_baseline():
    owners=port_pids(PROD_PORT)
    if len(owners)!=1:raise RuntimeError("main port listener count unexpected")
    status=get_status(PROD_PORT,main_config(),timeout=1.5)
    if status["pid"]!=owners[0] or status["armed"] is not True:
        raise RuntimeError("main backend identity or ARMED guard failed")
    return {"pid":owners[0],"armed":status["armed"],
       "outbound_owner":status["outbound_owner"],
       "pending_missions":status["pending_missions"]}

def check_archive(live):
    manifests=sorted((live/"bin").glob("BROKEN_*.manifest.json"),reverse=True)
    if not manifests:raise RuntimeError("original backup manifest missing")
    m=json.loads(manifests[0].read_text(encoding="utf-8"))
    z=Path(m["archive_path"])
    if not z.is_file() or hash_file(z)!=REQUIRED_ARCHIVE_SHA or m.get("zip_sha256")!=REQUIRED_ARCHIVE_SHA:
        raise RuntimeError("archive restore provenance failed")
    return {"original_zip_sha256":REQUIRED_ARCHIVE_SHA,"file_count":m.get("file_count"),
            "zip_verified":True,"restore_exercised":False}

def source_checks(repo,live):
    sys.path.insert(0,str(repo/"windows-relay"/"tools"))
    import pce11_013_isolated_supervisor as legacy
    import pce11_win32_containment as containment
    stage=legacy.candidate(repo,live)
    if stage.get("normalized_worktree_blob")!=legacy.V16_BLOB:
        raise RuntimeError("historical v16 source pin did not validate")
    if not containment.containment_contract_self_test():
        raise RuntimeError("suspended-start containment simulation failed")
    if not legacy.win_job_available() or sys.platform!="win32":
        raise RuntimeError("Win32 Job Object API unsupported")
    return stage,legacy,containment

def verify_no_sidecar():
    occupied=port_pids(SIDECAR_PORT)
    if occupied:raise RuntimeError("isolated port is occupied; never attach to existing service")
    return True

def static_gate(repo,live):
    tests=[]
    for pattern in ("test_pce11_isolated_supervisor.py",
                    "test_pce11_win32_containment.py",
                    "test_pce11_v16_health_canary.py"):
        out=command([sys.executable,"-B","-m","unittest","discover","-s","tests","-p",pattern,"-v"],
                    cwd=str(repo/"windows-relay"),timeout=65)
        tests.append({"pattern":pattern,"pass":True})
    # Explicitly preserve the disabled unsafe historical canary.
    original=(repo/"windows-relay"/"tools"/"pce11_013_isolated_supervisor.py").read_text(encoding="utf-8")
    if 'raise RuntimeError("canary disabled until suspended-start containment is tested")' not in original:
        raise RuntimeError("old uncontrolled canary unexpectedly enabled")
    # Fresh full source acceptance is required before even an isolated canary.
    for suite in ("windows-relay","consumer"):
        res=subprocess.run([sys.executable,"-B","-m","unittest","discover",
                 "-s","tests","-p","test_*.py"],cwd=str(repo/suite),
                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                 encoding="utf-8",errors="replace",timeout=100)
        if res.returncode or "OK" not in res.stderr:
            raise RuntimeError("full "+suite+" source suite failed: "+res.stderr[-700:])
        tests.append({"pattern":suite+"/tests/test_*.py","pass":True,
                      "suite_full":True})
    node=shutil.which("node")
    if not node:raise RuntimeError("node runtime not available for JS syntax gates")
    js_paths=("windows-relay/extension/content.js",
              "windows-relay/extension/service_worker.js",
              "windows-relay/extension-persistent/content.js",
              "windows-relay/extension-persistent/service_worker.js")
    for relative in js_paths:
        file=repo/relative
        if not file.is_file():raise RuntimeError("missing JS syntax gate file "+relative)
        command([node,"--check",str(file)],timeout=20)
        tests.append({"pattern":relative,"pass":True,"js_syntax":True})
    left=repo/"windows-relay"/"extension"/"content.js"
    right=repo/"windows-relay"/"extension-persistent"/"content.js"
    if hash_file(left)!=hash_file(right):
        raise RuntimeError("content-script mirror bytes mismatch")
    git(repo,"diff","--check")
    return tests

def create_private(live):
    base=Path(os.environ.get("LOCALAPPDATA",Path.home()))/MAIN_APP/"pce11-isolated"
    base.mkdir(parents=True,exist_ok=True)
    sandbox=base/(CANARY_NAME+"_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+secrets.token_hex(6))
    sandbox.mkdir(exist_ok=False)
    private=sandbox/"private"
    private.mkdir(exist_ok=False)
    state=sandbox/"state"
    state.mkdir(exist_ok=False)
    cfg=private/"bridge.json"
    token=secrets.token_urlsafe(48)
    cfg.write_text(json.dumps({"version":1,"host":"127.0.0.1",
                        "port":SIDECAR_PORT,"token":token})+"\n",encoding="utf-8")
    return sandbox,state,cfg,token

def run_health_canary(live,stage,legacy,containment):
    verify_no_sidecar()
    baseline=main_baseline()
    sandbox,state,cfg,token=create_private(live)
    args=[sys.executable,"-B",stage["source"],
          "--config",str(cfg),"--state-dir",str(state),"server"]
    legacy.validate_launch(args,state,cfg)
    p=None
    result={"schema":"pce011-contained-v16-health-v1",
      "time_utc":datetime.now(timezone.utc).isoformat(),
      "sandbox":str(sandbox),"port":SIDECAR_PORT,"baseline_main":baseline,
      "private_config_and_state":True,"token_exposed":False,
      "isolated_process_started":False,"job_contained":False,"status_ok":False,
      "private_missions_count":None,"cleanup_verified":False,
      "production_main_identity_preserved":False,
      "prod_process_modified":False,"operator_stop_triggered":False,
      "browser_control_used":False,"sidecar_released":False}
    failure=None
    try:
        p=containment.ContainedProcess()
        # CRITICAL: start() creates child SUSPENDED, attaches it to private Job,
        # and only THEN resumes; failure path cannot leave a running orphan.
        p.start(args,cwd=str(Path(stage["source"]).parent))
        result["isolated_process_started"]=p.resumed
        result["job_contained"]=p.contained
        result["child_pid"]=p.pid
        deadline=time.monotonic()+HEALTH_TIMEOUT_SECONDS
        while time.monotonic()<deadline:
            if p.poll() is not None:raise RuntimeError("sidecar exited before status responded")
            try:
                status=get_status(SIDECAR_PORT,token,timeout=0.6)
            except (urllib.error.URLError,ConnectionError,TimeoutError,OSError):
                time.sleep(0.15)
                continue
            if status["pid"]!=p.pid or status["pending_missions"]!=0:
                raise RuntimeError("foreign sidecar PID or inherited production missions")
            result["status_ok"]=True
            result["private_missions_count"]=0
            result["sidecar_status"]={k:status[k] for k in ("ok","pid","pending_missions","armed")}
            break
        if not result["status_ok"]:raise RuntimeError("contained sidecar did not answer within bound")
    except BaseException as exc:
        failure=type(exc).__name__+": "+str(exc)[:190]
    finally:
        if p is not None:
            try:p.close()
            except BaseException as e:
                failure=failure or "cleanup failed "+type(e).__name__
        for _ in range(20):
            if not port_pids(SIDECAR_PORT):break
            time.sleep(0.12)
        result["sidecar_released"]=not port_pids(SIDECAR_PORT)
        result["cleanup_verified"]=bool(p is not None and p.disposed and result["sidecar_released"]
           and "private_job_terminated" in p.events and "child_handles_closed" in p.events)
        try:
            post=main_baseline()
            result["production_main_identity_preserved"]=post["pid"]==baseline["pid"] and post["armed"] is True
            result["main_after"]={"pid":post["pid"],"armed":post["armed"],
                     "outbound_owner":post["outbound_owner"],
                     "pending_count_observed":post["pending_missions"]}
        except Exception as e:
            result["production_main_identity_error"]=type(e).__name__
        # Private token is never included in report and is unlinked after server stop.
        try:cfg.unlink(missing_ok=True)
        except OSError:result["private_config_cleanup_failed"]=True
        if failure:result["failure"]=failure
        report=sandbox/"health-report.json"
        report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    if failure or not result["status_ok"] or not result["cleanup_verified"] or not result["production_main_identity_preserved"]:
        raise RuntimeError("isolated v16 canary failed; forensic evidence "+str(sandbox/"health-report.json"))
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--live",type=Path,required=True)
    parser.add_argument("--expected-head",required=True)
    parser.add_argument("--mode",choices=("preflight","canary"),required=True)
    a=parser.parse_args()
    repo=a.repo.resolve();live=a.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:raise RuntimeError("source/live mismatch")
    if git(repo,"branch","--show-current")!=BRANCH:
        raise RuntimeError("canonical branch mismatch")
    if "monag144/gpt-windows-relay" not in git(repo,"remote","get-url","origin").lower():
        raise RuntimeError("wrong canonical GitHub origin")
    if git(repo,"status","--porcelain"):raise RuntimeError("dirty canonical checkout")
    remote=git(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=a.expected_head:raise RuntimeError("remote SHA changed")
    if a.mode=="preflight":
        if git(repo,"rev-parse","HEAD")!=BASE_SHA:raise RuntimeError("unexpected source base before .016")
        git(repo,"pull","--ff-only","origin",BRANCH,timeout=75)
    if git(repo,"rev-parse","HEAD")!=a.expected_head:raise RuntimeError("unverified pulled source")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    ordinal=16 if a.mode=="preflight" else 17
    proof=engineering_preflight(repo,ordinal,series=11)
    if not proof["ok"]:raise RuntimeError("PCE11 governance failure")
    archive=check_archive(live)
    stage,legacy,containment=source_checks(repo,live)
    verify_no_sidecar()
    if a.mode=="preflight":
        test=static_gate(repo,live)
        report={"schema":"pce011-v16-canary-preflight-v1","source":a.expected_head,
                "governance":proof,"historic_source":stage,"archive":archive,
                "tests":test,"port8768_free":True,"process_launched":False,
                "canary_not_run":True,"next_requires_independent_017_gate":True}
        dest=live/"bin"/("V16_CANARY_PREFLIGHT_"+datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")+".json")
        if dest.exists():raise FileExistsError("preflight report collision")
        dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print("PCE11_016_CANARY_PREFLIGHT="+json.dumps({
          "id":proof["id"],"source_sha":a.expected_head,
          "reads_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
          "report":str(dest),"archive_verified":True,
          "staged_v16_blob":stage["normalized_worktree_blob"],
          "static_tests":test,"sidecar_running":False,
          "sidecar_launch_authorized_by_this_action":False
          },separators=(",",":")))
        return 0
    reports=sorted((live/"bin").glob("V16_CANARY_PREFLIGHT_*.json"),reverse=True)
    if not reports:raise RuntimeError(".016 preflight evidence absent")
    prior=json.loads(reports[0].read_text(encoding="utf-8"))
    if prior.get("schema")!="pce011-v16-canary-preflight-v1" or prior.get("source")!=a.expected_head:
        raise RuntimeError("previous .016 source acceptance missing")
    result=run_health_canary(live,stage,legacy,containment)
    print("PCE11_017_V16_HEALTH="+json.dumps({
      "id":proof["id"],"source":a.expected_head,"pid":result["child_pid"],
      "status_ok":result["status_ok"],"private_missions_zero":result["private_missions_count"]==0,
      "contained":result["job_contained"],"cleanup_verified":result["cleanup_verified"],
      "main_unchanged_pid":result["production_main_identity_preserved"],
      "sanitized_report":str(Path(result["sandbox"])/"health-report.json"),
      "port8768_free_after":result["sidecar_released"],
      "production_replaced":False,"browser_touched":False},separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as e:
        print("PCE11_V16_CANARY_BLOCKED="+type(e).__name__+": "+str(e)[:290],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
