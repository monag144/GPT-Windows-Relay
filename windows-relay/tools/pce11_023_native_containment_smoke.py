#!/usr/bin/env python3
"""PCE11.023 native Windows Job containment smoke using a harmless sleeper, not Relay.

Fail-closed: clean pinned GitHub source, five-control preflight, previous full
acceptance, updated regression suites, fresh live 8766 read-only identity,
unoccupied 8768, then create ONLY a private suspended Python child.
No TCP server, browser, STOP, arm, mission, or HUD mutation.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="b154c0776b15862b34d3fa7689013c20b690dc7a"
PRIOR_ACCEPTANCE="SOURCE_ACCEPTANCE_2026-10-08T102230Z"
PROGRAM="pce11-native-private-job-smoke-v1"
def command(args,cwd=None,timeout=60):
    result=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
          text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if result.returncode:
        raise RuntimeError("command failed "+str(args[:3])+" rc="+str(result.returncode)+" "+result.stderr[-220:])
    return result.stdout.strip()
def g(repo,*args,timeout=40):
    exe=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    return command([exe,"-C",str(repo),*args],timeout=timeout)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--expected-head",required=True)
    a=ap.parse_args()
    repo=a.repo.resolve();live=a.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("invalid independent source/live directories")
    if g(repo,"rev-parse","HEAD")!=PREVIOUS:
        raise RuntimeError("unexpected PCE11.022 source base; do not overwrite")
    if g(repo,"branch","--show-current")!=BRANCH:
        raise RuntimeError("canonical branch mismatch")
    if "monag144/gpt-windows-relay" not in g(repo,"remote","get-url","origin").lower():
        raise RuntimeError("wrong GitHub origin")
    if g(repo,"status","--porcelain"):raise RuntimeError("dirty checkout")
    remote=g(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=a.expected_head:raise RuntimeError("remote GitHub commit moved")
    g(repo,"fetch","--no-tags","origin","refs/heads/"+BRANCH,timeout=65)
    if g(repo,"rev-parse","FETCH_HEAD")!=a.expected_head:
        raise RuntimeError("fetched Git object incorrect")
    g(repo,"merge-base","--is-ancestor","HEAD","FETCH_HEAD")
    g(repo,"merge","--ff-only","FETCH_HEAD",timeout=60)
    if g(repo,"rev-parse","HEAD")!=a.expected_head or g(repo,"status","--porcelain"):
        raise RuntimeError("source fast-forward was not clean and exact")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    pre=engineering_preflight(repo,23,series=11)
    if not pre["ok"]:raise RuntimeError("preflight failed")
    data=json.loads((live/"bin"/PRIOR_ACCEPTANCE/"acceptance.json").read_text(encoding="utf-8"))
    previous={x["suite"]:x for x in data.get("unit_suites",[])}
    if (data.get("repo_sha")!=PREVIOUS or data.get("full_acceptance") is not True
        or data.get("no_new_process") is not True
        or any(not previous.get(key,{}).get("passed") for key in
              ("windows_full","consumer_full","consumer_governance","consumer_migration"))
        or len(data.get("javascript_checks",[]))!=4
        or not data.get("archive") or not data.get("historic_v16")):
        raise RuntimeError("the successful PCE11.022 source acceptance is absent")
    suites=[]
    def run_suite(name,cwd,args,timeout=115):
        p=subprocess.run(args,cwd=str(cwd),stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         text=True,encoding="utf-8",errors="replace",timeout=timeout,
                         env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"))
        import re
        match=re.search(r"(?m)^Ran (\d+) tests? in ",p.stderr)
        success=p.returncode==0 and bool(re.search(r"(?m)^OK(?:\s|$)",p.stderr))
        d={"name":name,"passed":success,"count":int(match.group(1)) if match else 0}
        suites.append(d)
        if not success:raise RuntimeError("pre-launch suite failed "+name+
          " rc="+str(p.returncode)+" tail="+p.stderr[-330:])
    py=sys.executable
    for label,root,pattern in (
        ("containment",repo/"windows-relay","test_pce11_win32_containment.py"),
        ("windows_full",repo/"windows-relay","test_*.py"),
        ("consumer_full",repo/"consumer","test_*.py")):
        run_suite(label,root,[py,"-B","-m","unittest","discover","-s","tests",
                              "-p",pattern,"-v"],timeout=120)
    sys.path.insert(0,str(repo/"windows-relay"/"tools"))
    import pce11_win32_containment as safe
    import pce11_016_v16_health_canary as health
    if sys.platform!="win32" or not safe.containment_contract_self_test():
        raise RuntimeError("Win32 private Job API or mocked containment contract failed")
    health.check_archive(live)
    baseline=health.main_baseline()
    if baseline["pid"]<=0 or baseline["armed"] is not True:
        raise RuntimeError("main server not positively identified and armed")
    health.verify_no_sidecar()
    output=live/"bin"/("PRIVATE_JOB_SMOKE_"+datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")+".json")
    if output.exists():raise RuntimeError("evidence overwrite forbidden")
    verdict={"schema":PROGRAM,"git_head":a.expected_head,
      "mandatory_reads":{k:v["sha256"] for k,v in pre["reads"].items()},
      "tests":suites,"main_before":baseline,
      "main_after":None,"job_events":[],"child_pid":None,
      "bounded_child_started":False,"termination_verified":False,
      "production_identity_preserved":False,"isolated_port_free":False,
      "sidecar_launched":False,"production_mutated":False,"canary_authorized":False}
    child=None;failure=None
    try:
        child=safe.ContainedProcess()
        # The child has NO network/listener operations. 120s sleep is killed
        # immediately by closing its OWN private Job; it is not a background task.
        child.start([py,"-B","-c","import time; time.sleep(120)"],cwd=str(repo))
        verdict["child_pid"]=child.pid
        verdict["bounded_child_started"]=child.contained and child.resumed
        if not verdict["bounded_child_started"]:raise RuntimeError("suspended-job start incomplete")
        if child.poll() is not None:
            raise RuntimeError("test sleeper unexpectedly exited without Job cleanup")
    except BaseException as ex:
        failure=type(ex).__name__+": "+str(ex)[:230]
    finally:
        if child is not None:
            try:child.close()
            except BaseException as ex:
                failure=failure or "private child cleanup: "+type(ex).__name__+": "+str(ex)[:180]
            verdict["job_events"]=child.events
            verdict["termination_verified"]=bool(
                child.disposed and "child_contained" in child.events and
                "private_job_terminated" in child.events and
                "child_handles_closed" in child.events and
                "job_handle_closed" in child.events and not failure)
        try:
            post=health.main_baseline()
            verdict["main_after"]=post
            verdict["production_identity_preserved"]=(
                post["pid"]==baseline["pid"] and post["armed"] and
                post["outbound_owner"]==baseline["outbound_owner"])
        except BaseException as ex:
            failure=failure or "postmain verification: "+type(ex).__name__+": "+str(ex)[:180]
        try:verdict["isolated_port_free"]=not health.port_pids(8768)
        except BaseException as ex:failure=failure or "sidecar port post-check: "+type(ex).__name__
        if failure:verdict["failure"]=failure
        output.write_text(json.dumps(verdict,indent=2)+"\n",encoding="utf-8")
    passed=bool(not failure and verdict["termination_verified"] and
                verdict["production_identity_preserved"] and verdict["isolated_port_free"])
    print("PCE11_023_JOB_SMOKE="+json.dumps({
       "report":str(output),"commit":a.expected_head,"tests":suites,
       "child_pid":verdict["child_pid"],"native_job_kill_verified":verdict["termination_verified"],
       "main_pid_preserved":verdict["production_identity_preserved"],
       "port8768_free":verdict["isolated_port_free"],
       "success":passed,"failure":failure,"v16_server_launched":False,
       "live_cutover_authorized":False},separators=(",",":")))
    return 0 if passed else 2

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as err:
        print("PCE11_023_BLOCKED="+type(err).__name__+": "+str(err)[:300],file=sys.stderr)
        raise SystemExit(2)
    finally:
        print("Reply to this with the sandwich technique")
