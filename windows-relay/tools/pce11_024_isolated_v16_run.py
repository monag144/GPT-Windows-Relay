#!/usr/bin/env python3
"""PCE11.024: first bounded historical v16 loopback-health check under a private Win32 Job.

No production Relay or Firefox mutations; never uses the legacy Popen-before-Job
canary. Guarded by verified PCE11.022 complete source acceptance, PCE11.023
native Windows Job proof, source SHA, independent config/state and fresh tests.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="44a0a76ae0e81bc5e832af09fbaf1deb20dc6f8e"
ACCEPTANCE_SHA="b154c0776b15862b34d3fa7689013c20b690dc7a"
PRIOR_ACCEPTANCE="SOURCE_ACCEPTANCE_2026-10-08T102230Z"
NATIVE_PROOF="PRIVATE_JOB_SMOKE_2026-10-08T102641Z.json"
V16_BLOB="414b74121b1a5a5f2a049ebc84097223e7b5e69f"
EXPECTED_ZIP="f8ab9b9925b0a6e4688d85a1d6ee2c79563fed9c6e50dd5b75cbf9c0e140c0b7"

def command(args,timeout=60,cwd=None):
    p=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:raise RuntimeError("Git/check command failed: "+str(args[:3])+" exit "+str(p.returncode)+": "+p.stderr[-180:])
    return p.stdout.strip()

def git(repo,*items,timeout=50):
    exe=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    return command([exe,"-C",str(repo),*items],timeout)

def previous_acceptance(live):
    report=live/"bin"/PRIOR_ACCEPTANCE/"acceptance.json"
    if not report.is_file():raise RuntimeError("PCE11.022 acceptance report missing")
    data=json.loads(report.read_text(encoding="utf-8"))
    suites={r["suite"]:r for r in data.get("unit_suites",[])}
    if data.get("repo_sha")!=ACCEPTANCE_SHA or data.get("full_acceptance") is not True:
        raise RuntimeError("not qualified PCE11.022 source acceptance")
    for key,minimum in (("windows_full",476),("consumer_full",119),
                        ("consumer_governance",8),("consumer_migration",2)):
        s=suites.get(key,{})
        if not s.get("passed") or int(s.get("tests_ran") or 0)<minimum:
            raise RuntimeError("PCE11.022 previously accepted suite now unverified: "+key)
    if len(data.get("javascript_checks",[]))!=4 or not all(x.get("passed") for x in data["javascript_checks"]):
        raise RuntimeError("PCE11.022 JS syntax acceptance not verified")
    if not data.get("archive") or not data.get("historic_v16") or data.get("no_new_process") is not True:
        raise RuntimeError("archive/v16/prod guard absent in .022 evidence")
    return True

def previous_native(live):
    path=live/"bin"/NATIVE_PROOF
    if not path.is_file():raise RuntimeError("native Job smoke evidence missing")
    d=json.loads(path.read_text(encoding="utf-8"))
    checks={
        "original_source":d.get("git_head")==PREVIOUS,
        "contained_started":d.get("bounded_child_started") is True,
        "native_termination_proven":d.get("termination_verified") is True,
        "production_pid_preserved":d.get("production_identity_preserved") is True,
        "isolation_port_freed":d.get("isolated_port_free") is True,
        "never_v16_sidecar":d.get("sidecar_launched") is False,
        "own_job_terminated":"private_job_terminated" in d.get("job_events",[]),
        "own_child_handles_closed":"child_handles_closed" in d.get("job_events",[]),
        "own_job_closed":"job_handle_closed" in d.get("job_events",[]),
        "no_recorded_failure":not d.get("failure"),
    }
    if not all(checks.values()):raise RuntimeError("native Job smoke evidence rejected "+str(checks))
    return checks

def test_current_source(repo):
    cases=[]
    for area,pattern in (("windows-relay","test_pce11_win32_containment.py"),
                         ("windows-relay","test_pce11_v16_health_canary.py"),
                         ("windows-relay","test_*.py"),("consumer","test_*.py")):
        p=subprocess.run([sys.executable,"-B","-m","unittest","discover",
                          "-s","tests","-p",pattern,"-v"],
                         cwd=str(repo/area),stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         text=True,encoding="utf-8",errors="replace",timeout=125,
                         env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"))
        import re
        count=re.search(r"(?m)^Ran (\d+) tests? in",p.stderr)
        success=(p.returncode==0 and re.search(r"(?m)^OK(?:\s|$)",p.stderr) is not None)
        record={"suite":area+"/"+pattern,"passed":success,
                "count":int(count.group(1)) if count else None}
        cases.append(record)
        if not success:raise RuntimeError("fresh source suite failed "+area+"/"+pattern+": "+p.stderr[-250:])
    return cases

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--live",type=Path,required=True)
    parser.add_argument("--expected-head",required=True)
    args=parser.parse_args()
    repo=args.repo.resolve();live=args.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("wrong source/live roots")
    if git(repo,"rev-parse","HEAD")!=PREVIOUS:
        raise RuntimeError("canonical source HEAD differs from .023; no unsafe pull")
    if git(repo,"branch","--show-current")!=BRANCH or "monag144/gpt-windows-relay" not in git(repo,"remote","get-url","origin").lower():
        raise RuntimeError("wrong source branch or origin")
    if git(repo,"status","--porcelain"):raise RuntimeError("dirty canonical source")
    refs=git(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if not refs or refs[0]!=args.expected_head:raise RuntimeError("GitHub HEAD not pinned")
    git(repo,"fetch","--no-tags","origin","refs/heads/"+BRANCH,timeout=65)
    if git(repo,"rev-parse","FETCH_HEAD")!=args.expected_head:raise RuntimeError("fetched wrong Git object")
    git(repo,"merge-base","--is-ancestor","HEAD","FETCH_HEAD")
    git(repo,"merge","--ff-only","FETCH_HEAD",timeout=60)
    if git(repo,"rev-parse","HEAD")!=args.expected_head or git(repo,"status","--porcelain"):
        raise RuntimeError("canonical FF did not preserve clean source checkout")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    proof=engineering_preflight(repo,24,series=11)
    if not proof.get("ok"):raise RuntimeError("PCE11.024 five-control preflight blocked")
    previous_acceptance(live)
    native=previous_native(live)
    suites=test_current_source(repo)
    sys.path.insert(0,str(repo/"windows-relay"/"tools"))
    import pce11_016_v16_health_canary as health
    if health.SIDECAR_PORT!=8768 or health.PROD_PORT!=8766:
        raise RuntimeError("independent loopback port contract drifted")
    import pce11_013_isolated_supervisor as legacy
    import pce11_win32_containment as contained
    if "raise RuntimeError(\"canary disabled until suspended-start containment is tested\")" not in (repo/"windows-relay"/"tools"/"pce11_013_isolated_supervisor.py").read_text(encoding="utf-8"):
        raise RuntimeError("unsafe legacy canary was enabled")
    backup=health.check_archive(live)
    if backup.get("original_zip_sha256")!=EXPECTED_ZIP:
        raise RuntimeError("original recovery ZIP fingerprint changed")
    stage=legacy.candidate(repo,live)
    if stage.get("normalized_worktree_blob")!=V16_BLOB:
        raise RuntimeError("historical v16 working source not pinned")
    if not contained.containment_contract_self_test():
        raise RuntimeError("private Job ordering simulation failed")
    if not legacy.win_job_available() or sys.platform!="win32":
        raise RuntimeError("Win32 Job API absent")
    # First explicit live-identity check; no request may change main ARMED or STOP.
    health.verify_no_sidecar()
    main=health.main_baseline()
    if not isinstance(main.get("pending_missions"),int):
        raise RuntimeError("main queue count unavailable")
    if main.get("outbound_owner")!="browser":
        raise RuntimeError("production outbound owner is unexpected")
    result=None
    try:
        # One one-shot v16 8768 server. Its own Job alone owns its lifecycle.
        result=health.run_health_canary(live,stage,legacy,contained)
    except BaseException as exc:
        # The called routine always attempts private child teardown and writes
        # sandbox forensic report. Never issue generic PID or taskkill recovery.
        print("PCE11_024_CANARY_FAILURE="+type(exc).__name__+": "+str(exc)[:270],file=sys.stderr)
        raise
    if result.get("main_after",{}).get("pid")!=main["pid"] or not result.get("cleanup_verified"):
        raise RuntimeError("sidecar succeeded but production PID / cleanup evidence invalid")
    if result.get("baseline_main",{}).get("pid")!=main["pid"]:
        raise RuntimeError("production PID changed between preflight and launch")
    if not result.get("status_ok") or result.get("private_missions_count")!=0:
        raise RuntimeError("isolated status health did not prove private zero-mission state")
    if not result.get("job_contained") or not result.get("production_main_identity_preserved"):
        raise RuntimeError("main or private Job isolation contract failed")
    report=live/"bin"/("V16_HEALTH_GATE_"+datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")+".json")
    if report.exists():raise RuntimeError("cannot overwrite isolated health evidence")
    receipt={
        "schema":"pce011-first-isolated-v16-health-v1",
        "github_sha":args.expected_head,
        "five_mandatory_read_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
        "native_job_proof":native,"fresh_suites":suites,"archive":backup,
        "v16_git_sha":stage["git_head"],"v16_blob":V16_BLOB,
        "canary_pid":result["child_pid"],"sandbox_report":str(Path(result["sandbox"])/"health-report.json"),
        "sidecar_status_ok":result["status_ok"],
        "private_missions_zero":result["private_missions_count"]==0,
        "job_contained":result["job_contained"],"job_cleanup_verified":result["cleanup_verified"],
        "main_pid_before":main["pid"],"main_pid_after":result["main_after"]["pid"],
        "production_identity_preserved":result["production_main_identity_preserved"],
        "port8768_free_after":result["sidecar_released"],
        "browser_touched":False,"prod_relay_modified":False,
        "operational_stop_tested":False,"production_cutover_authorized":False,
        "twelve_hour_endurance_accepted":False,
    }
    report.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("PCE11_024_V16_HEALTH="+json.dumps({
        "report":str(report),"sandbox_report":receipt["sandbox_report"],
        "source_sha":args.expected_head,"tests":suites,"v16_blob":V16_BLOB,
        "pid":receipt["canary_pid"],"status_ok":receipt["sidecar_status_ok"],
        "private_missions_zero":True,"job_cleanup":receipt["job_cleanup_verified"],
        "main_pid_preserved":receipt["production_identity_preserved"],
        "port8768_free_after":receipt["port8768_free_after"],
        "production_replaced":False,"browser_touched":False,
        "live_overnight_accepted":False},separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        print("PCE11_024_BLOCKED="+type(exc).__name__+": "+str(exc)[:300],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
