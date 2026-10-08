#!/usr/bin/env python3
"""PCE11.034: one bounded actual v16 canary after 033 source + 030 real Job proof.

No production change. Independently attests actual HTTP listening PID, direct
parent, exact private Windows Job membership and observed host termination.
Never bypass failed health, never replay earlier action IDs.
"""
from __future__ import annotations
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="e4e89c4075ddc49e6bb6bae8db8bed2e48cad280"
SOURCE_REPORT="SOURCE_HOST_IDENTITY_ACCEPTANCE_033_2026-10-08T110349Z"
SOURCE_BLOB="414b74121b1a5a5f2a049ebc84097223e7b5e69f"
NATIVE_REPORT="PCE11_030_LINEAGE_20261008T105116Z/lineage-report.json"
NATIVE_HEAD="8db22edb17697805beb528f8491f9b4f60572533"
MAIN_PID=18632
def run(args,timeout=60):
    p=subprocess.run(args,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:raise RuntimeError("git verification returned "+str(p.returncode))
    return p.stdout.strip()
def g(repo,*args,timeout=55):
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    return run([git,"-C",str(repo),*args],timeout=timeout)
def read(path):
    if not path.is_file() or path.stat().st_size>1048576:raise RuntimeError("required acceptance record missing/oversized")
    val=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(val,dict):raise RuntimeError("acceptance record malformed")
    return val
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--live",type=Path,required=True)
    p.add_argument("--expected-head",required=True)
    a=p.parse_args()
    repo=a.repo.resolve();live=a.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:raise RuntimeError("invalid source/live roots")
    if g(repo,"rev-parse","HEAD")!=PREVIOUS or g(repo,"branch","--show-current")!=BRANCH:
        raise RuntimeError("unexpected PCE11.033 clean source base")
    if "monag144/gpt-windows-relay" not in g(repo,"remote","get-url","origin").lower():
        raise RuntimeError("noncanonical GitHub origin")
    if g(repo,"status","--porcelain"):raise RuntimeError("dirty source checkout")
    remote=g(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if len(remote)<2 or remote[0]!=a.expected_head:raise RuntimeError("GitHub branch moved")
    g(repo,"fetch","--no-tags","origin","refs/heads/"+BRANCH,timeout=70)
    if g(repo,"rev-parse","FETCH_HEAD")!=a.expected_head:raise RuntimeError("fetched different Git source")
    g(repo,"merge-base","--is-ancestor","HEAD","FETCH_HEAD")
    g(repo,"merge","--ff-only","FETCH_HEAD",timeout=70)
    if g(repo,"rev-parse","HEAD")!=a.expected_head or g(repo,"status","--porcelain"):
        raise RuntimeError("not an exact clean GitHub fast-forward")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    proof=engineering_preflight(repo,34,series=11)
    if not proof["ok"]:raise RuntimeError("five mandatory controls rejected")
    accepted=read(live/"bin"/SOURCE_REPORT/"acceptance.json")
    if (accepted.get("schema")!="pce011-033-native-host-identity-v1" or
        accepted.get("sha")!=PREVIOUS or accepted.get("source_acceptance_passed") is not True or
        accepted.get("historic_v16_blob")!=SOURCE_BLOB or
        accepted.get("isolated_v16_launched") is not False):
        raise RuntimeError("PCE11.033 exact source acceptance absent")
    suites={v["name"]:v for v in accepted.get("unit_suites",[])}
    for key,minimum in (("target_v16",12),("target_host_identity",9),("target_containment",12),
                        ("windows_full",493),("consumer_full",119)):
        x=suites.get(key,{})
        if x.get("passed") is not True or int(x.get("tests") or 0)<minimum:
            raise RuntimeError("PCE11.033 source suite not accepted "+key)
    if len(accepted.get("javascript_checks",[]))!=4 or not all(v.get("passed") for v in accepted["javascript_checks"]):
        raise RuntimeError("PCE11.033 JS acceptance absent")
    native=read(Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))/"GPTWindowsRelay"/"ops"/NATIVE_REPORT)
    if (native.get("schema")!="pce011-030-native-python-lineage-v1" or
        native.get("source_sha")!=NATIVE_HEAD or native.get("success") is not True or
        native.get("host_direct_child_of_launcher") is not True or
        native.get("host_is_in_exact_private_job") is not True or
        native.get("launcher_in_exact_private_job") is not True or
        native.get("observed_host_exit_after_job_close") is not True or
        native.get("main_preserved") is not True):
        raise RuntimeError("independent native Windows launcher/host Job proof missing")
    sys.path.insert(0,str(repo/"windows-relay"/"tools"))
    import pce11_016_v16_health_canary as h
    import pce11_013_isolated_supervisor as legacy
    import pce11_win32_containment as containment
    if not containment.containment_contract_self_test():
        raise RuntimeError("suspended-start Job mock contract failed")
    if "obsolete .018 canary entrypoint disabled" not in (repo/"windows-relay"/"tools"/"pce11_016_v16_health_canary.py").read_text():
        raise RuntimeError("obsolete canary entrypoint not disabled")
    archive=h.check_archive(live)
    stage=legacy.candidate(repo,live)
    if stage.get("normalized_worktree_blob")!=SOURCE_BLOB:
        raise RuntimeError("staged historical v16 source changed")
    h.verify_no_sidecar()
    before=h.main_baseline()
    if (before["pid"]!=MAIN_PID or before["armed"] is not True or
        before["outbound_owner"]!="browser" or type(before["pending_missions"]) is not int):
        raise RuntimeError("production main identity/queue check blocked")
    try:
        result=h.run_health_canary(live,stage,legacy,containment)
    except BaseException as exc:
        report_text=str(exc).split("forensic evidence ",1)
        summary={"reason":type(exc).__name__,"report":report_text[-1] if len(report_text)==2 else None,
                 "health_passed":False,"prod_cutover_authorized":False}
        if len(report_text)==2:
            try:
                rp=Path(report_text[-1])
                safe_root=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))/"GPTWindowsRelay"/"pce11-isolated"
                if rp.name=="health-report.json" and safe_root.resolve() in rp.resolve().parents:
                    saved=read(rp)
                    keys=("child_pid","observed_status_pid","observed_pending_missions","listener_pid_matches_status",
                          "host_parent_pid","host_job_member","host_identity_verified","host_exited_after_job_close",
                          "host_handle_closed","cleanup_verified","sidecar_released",
                          "production_main_identity_preserved","failure")
                    summary["observed"]={k:saved.get(k) for k in keys}
            except Exception:
                summary["forensic_read_error"]=True
        print("PCE11_034_HEALTH_REJECTED="+json.dumps(summary,separators=(",",":")))
        raise
    after=h.main_baseline()
    if (after["pid"]!=before["pid"] or after["armed"] is not True or
        result.get("host_identity_verified") is not True or
        result.get("host_job_member") is not True or
        result.get("listener_pid_matches_status") is not True or
        result.get("host_exited_after_job_close") is not True or
        result.get("host_handle_closed") is not True or
        result.get("cleanup_verified") is not True or
        result.get("sidecar_released") is not True or
        result.get("private_missions_count")!=0):
        raise RuntimeError("isolated v16 health returned but identity/cleanup postgate rejected")
    dest=live/"bin"/"PCE11_034_FIRST_ACCEPTED_HOST_HEALTH.json"
    if dest.exists():raise RuntimeError("refuse to overwrite historical accepted canary evidence")
    evidence={"schema":"pce011-034-owned-host-health-v1","github_sha":a.expected_head,
              "five_control_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
              "source_acceptance":SOURCE_REPORT,"native_job_proof":NATIVE_REPORT,
              "sandbox_report":str(Path(result["sandbox"])/"health-report.json"),
              "launcher_pid":result["child_pid"],"http_host_pid":result["observed_status_pid"],
              "http_host_parent_pid":result["host_parent_pid"],
              "exact_job":result["host_job_member"],"listener_pid_match":result["listener_pid_matches_status"],
              "host_exit":result["host_exited_after_job_close"],"private_missions_zero":True,
              "job_cleanup":result["cleanup_verified"],"prod_before":before,"prod_after":after,
              "production_cutover_authorized":False,"browser_touched":False,
              "overnight_endurance_accepted":False}
    dest.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    print("PCE11_034_V16_OWNED_HOST_HEALTH="+json.dumps({
        "report":str(dest),"sandbox_report":evidence["sandbox_report"],
        "launcher_pid":evidence["launcher_pid"],"http_pid":evidence["http_host_pid"],
        "parent_pid":evidence["http_host_parent_pid"],"host_in_exact_job":evidence["exact_job"],
        "listener_owned":evidence["listener_pid_match"],"host_exit":evidence["host_exit"],
        "private_missions_zero":True,"job_cleanup":True,"main_pid_preserved":after["pid"]==before["pid"],
        "port8768_released":True,"runtime_health_accepted":True,
        "production_cutover_authorized":False},separators=(",",":")))
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        print("PCE11_034_BLOCKED="+type(exc).__name__+": "+str(exc)[:300],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
