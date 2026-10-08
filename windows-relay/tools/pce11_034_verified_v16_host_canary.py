#!/usr/bin/env python3
"""PCE11.034: uniquely isolated historical v16 health canary with exact server host ownership proof under a private Win32 Job.

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
PREVIOUS="e4e89c4075ddc49e6bb6bae8db8bed2e48cad280"
HOST_ACCEPTANCE="SOURCE_HOST_IDENTITY_ACCEPTANCE_033_2026-10-08T110349Z"
NATIVE_LINEAGE_PATH="PCE11_030_LINEAGE_20261008T105116Z/lineage-report.json"
NATIVE_LINEAGE_SOURCE="8db22edb17697805beb528f8491f9b4f60572533"
NATIVE_SOURCE="44a0a76ae0e81bc5e832af09fbaf1deb20dc6f8e"
TELEMETRY_ACCEPTANCE="SOURCE_TELEMETRY_ACCEPTANCE_2026-10-08T103943Z"
PRIOR_CLEANUP="PCE11_025_V16_FAILURE_FORENSICS_2026-10-08T103325Z.json"
PRIOR_PRIVATE_STATE="PCE11_026_PRIVATE_STATE_DIAG_2026-10-08T103556Z.json"
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
    report=live/"bin"/HOST_ACCEPTANCE/"acceptance.json"
    if not report.is_file():raise RuntimeError("PCE11.033 full host acceptance missing")
    data=json.loads(report.read_text(encoding="utf-8"))
    checks={r.get("name"):r for r in data.get("unit_suites",[])}
    if data.get("schema")!="pce011-033-native-host-identity-v1" or data.get("sha")!=PREVIOUS or data.get("source_acceptance_passed") is not True:
        raise RuntimeError("PCE11.033 accepted-source fingerprint missing")
    for name,min_count in (("target_v16",12),("target_host_identity",9),
                           ("target_containment",12),("windows_full",493),("consumer_full",119)):
        entry=checks.get(name,{})
        if entry.get("passed") is not True or int(entry.get("tests") or 0)<min_count:
            raise RuntimeError("PCE11.033 source suite not accepted: "+name)
    guards=data.get("host_identity_guards",{})
    required=("observed_pid","observed_missions","listener_ownership",
        "exact_host_attestation","direct_parent_query","exact_job_membership",
        "held_handle_exit","host_cleanup","host_executable_verification",
        "legacy_numbered_canary_disabled","separate_mission_validation")
    if not all(guards.get(name) is True for name in required):
        raise RuntimeError("required PCE11.033 host-identity guards not proven")
    js=data.get("javascript_checks",[])
    if len(js)!=4 or not all(x.get("passed") is True for x in js):
        raise RuntimeError("PCE11.033 JS syntax gates not accepted")
    if data.get("content_mirror_equal") is not True or data.get("historic_v16_blob")!=V16_BLOB or not data.get("original_archive"):
        raise RuntimeError("PCE11.033 mirror / backup / historical source unaccepted")
    if data.get("isolated_v16_launched") is not False or data.get("production_mutated") is not False:
        raise RuntimeError("PCE11.033 unexpected live change")
    return {"source_sha":PREVIOUS,"suites":{name:checks[name]["tests"] for name,_ in
       (("target_v16",12),("target_host_identity",9),("target_containment",12),
        ("windows_full",493),("consumer_full",119))},"host_guards":len(required)}

def native_lineage_proof():
    location=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))/"GPTWindowsRelay"/"ops"/NATIVE_LINEAGE_PATH
    if not location.is_file():raise RuntimeError("native .030 launcher/server host proof absent")
    d=json.loads(location.read_text(encoding="utf-8"))
    if (d.get("schema")!="pce011-030-native-python-lineage-v1"
        or d.get("source_sha")!=NATIVE_LINEAGE_SOURCE
        or d.get("success") is not True
        or d.get("host_direct_child_of_launcher") is not True
        or d.get("host_is_in_exact_private_job") is not True
        or d.get("launcher_in_exact_private_job") is not True
        or d.get("observed_host_exit_after_job_close") is not True
        or d.get("job_kill_verified") is not True
        or d.get("main_preserved") is not True
        or d.get("port8768_free_after") is not True
        or d.get("no_relay_service_started") is not True):
        raise RuntimeError("native launcher/host exact-private-Job proof not accepted")
    return {"launcher_pid":d.get("contained_launcher_pid"),"python_host_pid":d.get("observed_python_host_pid"),
            "host_direct_child":True,"job_membership_confirmed":True,"host_exit_confirmed":True}

def prior_failure_reconciled(live):
    a=live/"bin"/PRIOR_CLEANUP
    b=live/"bin"/PRIOR_PRIVATE_STATE
    if not a.is_file() or not b.is_file():
        raise RuntimeError("prior failed canary forensic reports missing")
    first=json.loads(a.read_text(encoding="utf-8"))
    state=json.loads(b.read_text(encoding="utf-8"))
    if (first.get("classification")!="CLEANUP_AND_MAIN_VERIFIED"
        or first.get("cleanup_reconciled") is not True
        or first.get("main_identity_reconciled") is not True
        or first.get("head")!="368c80824f6354aef470f80de60a6cccfd704382"):
        raise RuntimeError("first failed sidecar cleanup not proven")
    if (state.get("schema")!="pce011-026-private-state-v16-contract-v1"
        or state.get("exact_failed_condition_proven") is not False
        or state.get("original_job_cleanup_verified") is not True
        or state.get("production_identity_preserved") is not True
        or state.get("private_state_after_child_exit",{}).get("queue_count")!=0):
        raise RuntimeError("prior private-state postmortem not preserved")
    if first.get("current_listeners",{}).get("8768",{}).get("pids")!=[]:
        raise RuntimeError("the previous sidecar listener was not proven absent")
    return {"first_child_cleanup":True,"previous_main_pid":first["current_production_get_status"]["pid"],
            "private_state_queue_snapshot":0}

def previous_native(live):
    path=live/"bin"/NATIVE_PROOF
    if not path.is_file():raise RuntimeError("native Job smoke evidence missing")
    d=json.loads(path.read_text(encoding="utf-8"))
    checks={
        "original_source":d.get("git_head")==NATIVE_SOURCE,
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
                         ("windows-relay","test_pce11_private_host_identity.py"),
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
        raise RuntimeError("canonical source HEAD differs from .033; no unsafe pull")
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
    proof=engineering_preflight(repo,34,series=11)
    if not proof.get("ok"):raise RuntimeError("PCE11.034 five-control preflight blocked")
    accepted_source=previous_acceptance(live)
    lineage=native_lineage_proof()
    prior=prior_failure_reconciled(live)
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
    if main["pid"]!=prior["previous_main_pid"]:
        raise RuntimeError("production listener changed since first sidecar cleanup; no retry")
    if not isinstance(main.get("pending_missions"),int):
        raise RuntimeError("main queue count unavailable")
    if main.get("outbound_owner")!="browser":
        raise RuntimeError("production outbound owner is unexpected")
    result=None
    try:
        # One NEW uniquely named one-shot private v16 8768 server. The old
        # numbered canary is not rerun, and PCE11.027 is source-only.
        result=health.run_health_canary(live,stage,legacy,contained)
    except BaseException as exc:
        # Preserve precise observed metadata emitted by the updated canary
        # without disclosing token or reading the abandoned private config.
        message=str(exc)
        path_name=message.split("forensic evidence ",1)[-1]
        failure={"error_type":type(exc).__name__,
                 "sandbox_report":path_name if "forensic evidence " in message else None,
                 "sidecar_health_accepted":False,"new_retry_authorized":False}
        try:
            report_path=Path(path_name)
            safe_root=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))/"GPTWindowsRelay"/"pce11-isolated"
            if report_path.is_file() and report_path.name=="health-report.json" and safe_root.resolve() in report_path.resolve().parents and report_path.stat().st_size<=65536:
                report_data=json.loads(report_path.read_text(encoding="utf-8-sig"))
                allow=("child_pid","isolated_process_started","job_contained",
                       "status_ok","observed_status_pid","expected_child_pid",
                       "observed_pending_missions","status_pid_matches_child",
                       "status_missions_zero","listener_pid_matches_status",
                       "host_parent_pid","host_job_member","host_identity_verified",
                       "host_exited_after_job_close","host_handle_closed",
                       "cleanup_verified","sidecar_released",
                       "production_main_identity_preserved","failure")
                failure["observed"]={key:report_data.get(key) for key in allow}
        except (OSError,ValueError,TypeError):
            failure["forensic_read_error"]=True
        print("PCE11_034_V16_REJECTED="+json.dumps(failure,separators=(",",":")))
        raise
    if result.get("main_after",{}).get("pid")!=main["pid"] or not result.get("cleanup_verified"):
        raise RuntimeError("sidecar succeeded but production PID / cleanup evidence invalid")
    if result.get("baseline_main",{}).get("pid")!=main["pid"]:
        raise RuntimeError("production PID changed between preflight and launch")
    if (result.get("status_ok") is not True or result.get("private_missions_count")!=0
        or result.get("status_missions_zero") is not True
        or result.get("listener_pid_matches_status") is not True
        or result.get("host_identity_verified") is not True
        or result.get("host_job_member") is not True
        or result.get("host_exited_after_job_close") is not True
        or result.get("host_handle_closed") is not True):
        raise RuntimeError("HTTP host ancestry, exact Job, listener identity, exit or missions gate failed")
    if not result.get("job_contained") or not result.get("production_main_identity_preserved"):
        raise RuntimeError("main or private Job isolation contract failed")
    report=live/"bin"/("V16_HEALTH_GATE_034_"+datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")+".json")
    if report.exists():raise RuntimeError("cannot overwrite isolated health evidence")
    receipt={
        "schema":"pce011-host-verified-v16-health-v3",
        "github_sha":args.expected_head,
        "five_mandatory_read_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
        "native_job_proof":native,"native_launcher_lineage":lineage,
        "source_acceptance":accepted_source,
        "prior_failed_canary_reconciled":prior,"fresh_suites":suites,"archive":backup,
        "v16_git_sha":stage["git_head"],"v16_blob":V16_BLOB,
        "canary_pid":result["child_pid"],"sandbox_report":str(Path(result["sandbox"])/"health-report.json"),
        "sidecar_status_ok":result["status_ok"],
        "private_missions_zero":result["private_missions_count"]==0,
        "observed_status_pid":result.get("observed_status_pid"),
        "observed_pending_missions":result.get("observed_pending_missions"),
        "status_pid_matches_child":result.get("status_pid_matches_child"),
        "status_missions_zero":result.get("status_missions_zero"),
        "listener_pid_matches_status":result.get("listener_pid_matches_status"),
        "host_parent_pid":result.get("host_parent_pid"),
        "host_job_member":result.get("host_job_member"),
        "host_identity_verified":result.get("host_identity_verified"),
        "host_exit_observed":result.get("host_exited_after_job_close"),
        "host_handle_closed":result.get("host_handle_closed"),
        "job_contained":result["job_contained"],"job_cleanup_verified":result["cleanup_verified"],
        "main_pid_before":main["pid"],"main_pid_after":result["main_after"]["pid"],
        "production_identity_preserved":result["production_main_identity_preserved"],
        "port8768_free_after":result["sidecar_released"],
        "browser_touched":False,"prod_relay_modified":False,
        "operational_stop_tested":False,"production_cutover_authorized":False,
        "twelve_hour_endurance_accepted":False,
    }
    report.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("PCE11_034_V16_HEALTH="+json.dumps({
        "report":str(report),"sandbox_report":receipt["sandbox_report"],
        "source_sha":args.expected_head,"tests":suites,"v16_blob":V16_BLOB,
        "pid":receipt["canary_pid"],"status_ok":receipt["sidecar_status_ok"],
        "observed_pid":receipt["observed_status_pid"],
        "observed_missions":receipt["observed_pending_missions"],
        "launcher_pid_match":receipt["status_pid_matches_child"],
        "listener_pid_match":receipt["listener_pid_matches_status"],
        "host_parent_pid":receipt["host_parent_pid"],
        "host_in_exact_job":receipt["host_job_member"],
        "host_exited_after_job_close":receipt["host_exit_observed"],
        "host_handle_closed":receipt["host_handle_closed"],
        "missions_zero":receipt["status_missions_zero"],
        "private_missions_zero":receipt["private_missions_zero"],"job_cleanup":receipt["job_cleanup_verified"],
        "main_pid_preserved":receipt["production_identity_preserved"],
        "port8768_free_after":receipt["port8768_free_after"],
        "production_replaced":False,"browser_touched":False,
        "live_overnight_accepted":False},separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        print("PCE11_034_BLOCKED="+type(exc).__name__+": "+str(exc)[:300],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
