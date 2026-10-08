#!/usr/bin/env python3
"""PCE11.030: native contained Python venv redirector lineage experiment.

Starts ONE harmless private Python interpreter with no TCP listeners. Actual
Python code writes PID, PPID, interpreter paths and sleeps in its private Job.
Verifies actual host Process IsProcessInJob(private-owned handle), checks parent
relationship, cleans the private Job, and rechecks main 8766 and unused 8768.
No Relay server, browser, STOP, ARM, mission or deployed-file mutation.
"""
from __future__ import annotations
import argparse,ctypes,hashlib,json,os,shutil,subprocess,sys,time
from ctypes import wintypes
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="36f01f1c75d6df3ec1c35f743b91b68f9a15e175"
AUDIT="docs/audits/AUDIT_2026-10-08T1049Z_PCE11_OPERATIONS_025_029.md"
REPORT_029="PCE11_029_PID_IDENTITY_DIAG_2026-10-08T104655Z.json"
EXPECTED_MAIN=18632
PROCESS_QUERY_LIMITED_INFORMATION=0x1000
WAIT_OBJECT_0=0
SYNCHRONIZE=0x00100000

def run(argv,timeout=60):
    p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
      text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:raise RuntimeError("Git verification failed rc="+str(p.returncode))
    return p.stdout.strip()
def git(repo,*args,timeout=45):
    exe=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    return run([exe,"-C",str(repo),*args],timeout)

def job_member(pid,job):
    """Query exact owned Job object via Win32; do not scan or mutate processes."""
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.OpenProcess.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.IsProcessInJob.argtypes=(wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL))
    kernel.IsProcessInJob.restype=wintypes.BOOL
    kernel.CloseHandle.argtypes=(wintypes.HANDLE,)
    kernel.CloseHandle.restype=wintypes.BOOL
    handle=kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,False,pid)
    if not handle:raise OSError("unable to open observed child for read-only Job query")
    try:
        member=wintypes.BOOL()
        ok=kernel.IsProcessInJob(handle,job,ctypes.byref(member))
        if not ok:raise OSError("IsProcessInJob failed")
        return bool(member.value)
    finally:
        if not kernel.CloseHandle(handle):
            raise OSError("query-only process handle close failed")

def open_sync_handle(pid):
    """Hold a read-only lifetime handle across Job termination for exit proof."""
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.OpenProcess.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
    kernel.OpenProcess.restype=wintypes.HANDLE
    handle=kernel.OpenProcess(SYNCHRONIZE,False,pid)
    if not handle:raise OSError("cannot open private child wait handle")
    return handle

def await_exit_and_close(handle):
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.WaitForSingleObject.argtypes=(wintypes.HANDLE,wintypes.DWORD)
    kernel.WaitForSingleObject.restype=wintypes.DWORD
    kernel.CloseHandle.argtypes=(wintypes.HANDLE,)
    kernel.CloseHandle.restype=wintypes.BOOL
    try:
        return kernel.WaitForSingleObject(handle,4000)==WAIT_OBJECT_0
    finally:
        if not kernel.CloseHandle(handle):
            raise OSError("private child wait handle close failed")

def read_json(path):
    if not path.is_file() or path.stat().st_size>131072:
        raise RuntimeError("required evidence JSON missing or too large")
    obj=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj,dict):raise RuntimeError("invalid evidence structure")
    return obj

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--expected-head",required=True)
    ap.add_argument("--repo",required=True,type=Path)
    ap.add_argument("--live",required=True,type=Path)
    a=ap.parse_args()
    repo=a.repo.resolve();live=a.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("invalid source/live roots")
    if git(repo,"rev-parse","HEAD")!=a.expected_head:
        raise RuntimeError("PCE11.030 governance audit sync not yet installed")
    if git(repo,"branch","--show-current")!=BRANCH or git(repo,"status","--porcelain"):
        raise RuntimeError("canonical branch mismatch or dirty source")
    if "monag144/gpt-windows-relay" not in git(repo,"remote","get-url","origin").lower():
        raise RuntimeError("wrong GitHub origin")
    remote=git(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if len(remote)<2 or remote[0]!=a.expected_head:
        raise RuntimeError("GitHub canonical remote HEAD unpinned")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    gate=engineering_preflight(repo,30,series=11)
    checkpoint=gate["checkpoints"].get("audit",{})
    if not gate.get("ok") or checkpoint.get("window")!=[25,29] or checkpoint.get("path")!=AUDIT:
        raise RuntimeError("PCE11.030 five-slot checkpoint not verified")
    evidence=read_json(live/"bin"/REPORT_029)
    if (evidence.get("canonical_commit")!=PREVIOUS or
        evidence.get("schema")!="pce011-029-readonly-pid-lineage-v1" or
        evidence.get("original_status",{}).get("observed_pid")!=11180 or
        evidence.get("original_status",{}).get("contained_launcher_pid")!=1640 or
        evidence.get("original_status",{}).get("job_cleanup") is not True):
        raise RuntimeError("original PID discrepancy / cleanup history not pinned")
    sys.path.insert(0,str(repo/"windows-relay"/"tools"))
    import pce11_016_v16_health_canary as health
    import pce11_win32_containment as containment
    if sys.platform!="win32" or not containment.containment_contract_self_test():
        raise RuntimeError("Windows native containment prerequisite missing")
    baseline=health.main_baseline()
    if (baseline.get("pid")!=EXPECTED_MAIN or baseline.get("armed") is not True or
        baseline.get("outbound_owner")!="browser" or
        health.port_pids(8768)):
        raise RuntimeError("live server / private port guard failed")
    if not Path(sys.executable).is_file() or not Path(sys.executable).is_absolute():
        raise RuntimeError("current Python launcher path invalid")

    local=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sandbox=local/"GPTWindowsRelay"/"ops"/("PCE11_030_LINEAGE_"+stamp)
    sandbox.mkdir(parents=True,exist_ok=False)
    reply=sandbox/"inert-python-process.json"
    record=sandbox/"lineage-report.json"
    # One-file handshake containing *only* safe process metadata.
    # The host sleeps solely until its dedicated Job is terminated below.
    program=("import json,os,sys,time,pathlib;"
       "f=pathlib.Path(sys.argv[1]);"
       "f.open('x',encoding='utf-8').write(json.dumps({"
       "'pid':os.getpid(),'ppid':os.getppid(),"
       "'executable':sys.executable,'base_executable':getattr(sys,'_base_executable',None)}));"
       "time.sleep(30)")
    result={
      "schema":"pce011-030-native-python-lineage-v1",
      "source_sha":a.expected_head,
      "mandatory_read_sha256":{k:v["sha256"] for k,v in gate["reads"].items()},
      "audit":{"path":checkpoint["path"],"window":checkpoint["window"]},
      "historical_launch_pid":1640,"historical_http_pid":11180,
      "main_before":baseline,"private_port8768_free_before":True,
      "contained_launcher_pid":None,"observed_python_host_pid":None,
      "observed_python_host_ppid":None,"host_same_as_launcher":None,
      "host_direct_child_of_launcher":None,
      "host_is_in_exact_private_job":None,"launcher_in_exact_private_job":None,
      "job_kill_verified":False,"observed_host_exit_after_job_close":False,
      "main_preserved":False,
      "port8768_free_after":False,"no_relay_service_started":True,
      "browser_touched":False,"operator_STOP_used":False,
      "production_mutated":False,"v16_relaunch_authorized":False,
      "success":False,"job_events":[]}
    owned=None;host_wait_handle=None;failure=None
    try:
        owned=containment.ContainedProcess()
        owned.start([sys.executable,"-B","-c",program,str(reply)],cwd=str(sandbox))
        result["contained_launcher_pid"]=owned.pid
        result["launcher_in_exact_private_job"]=job_member(owned.pid,owned.job)
        deadline=time.monotonic()+6.0
        while not reply.is_file() and time.monotonic()<deadline:
            if owned.poll() is not None:
                raise RuntimeError("venv launcher exited before private process handshake")
            time.sleep(0.08)
        if not reply.is_file():raise RuntimeError("private Python host handshake did not arrive")
        payload=read_json(reply)
        host=payload.get("pid");parent=payload.get("ppid")
        if type(host) is not int or host<=0 or type(parent) is not int or parent<=0:
            raise RuntimeError("private Python process identities malformed")
        result["observed_python_host_pid"]=host
        result["observed_python_host_ppid"]=parent
        result["host_same_as_launcher"]=host==owned.pid
        result["host_direct_child_of_launcher"]=parent==owned.pid
        result["host_executable"]=Path(payload["executable"]).name
        result["host_base_executable"]=Path(payload["base_executable"]).name
        result["host_is_in_exact_private_job"]=job_member(host,owned.job)
        host_wait_handle=open_sync_handle(host)
        if not result["launcher_in_exact_private_job"] or not result["host_is_in_exact_private_job"]:
            raise RuntimeError("inert interpreter host not safely contained in exact owned job")
        if not result["host_same_as_launcher"] and not result["host_direct_child_of_launcher"]:
            raise RuntimeError("inert process ancestry does not demonstrate a direct redirector child")
    except BaseException as ex:
        failure=type(ex).__name__+": "+str(ex)[:190]
    finally:
        if owned is not None:
            try:owned.close()
            except BaseException as ex:
                failure=failure or "native cleanup failure: "+type(ex).__name__+": "+str(ex)[:180]
            result["job_events"]=list(owned.events)
            result["job_kill_verified"]=bool(
                owned.disposed and "private_job_terminated" in owned.events and
                "child_handles_closed" in owned.events and
                "job_handle_closed" in owned.events and not any(x.startswith("native cleanup") for x in [failure or ""]))
        if host_wait_handle is not None:
            try:
                result["observed_host_exit_after_job_close"]=await_exit_and_close(host_wait_handle)
                if not result["observed_host_exit_after_job_close"]:
                    failure=failure or "private interpreter child did not exit after Job close"
            except BaseException as ex:
                failure=failure or "private interpreter exit verification failed: "+type(ex).__name__
        try:
            after=health.main_baseline()
            result["main_after"]=after
            result["main_preserved"]=after==baseline
            result["port8768_free_after"]=not health.port_pids(8768)
        except BaseException as ex:
            failure=failure or "post-main verification failed: "+type(ex).__name__
        if failure:result["failure"]=failure
        result["success"]=bool(not failure and result["job_kill_verified"]
           and result["main_preserved"] and result["port8768_free_after"]
           and result["observed_host_exit_after_job_close"]
           and result["host_is_in_exact_private_job"] and
           result["launcher_in_exact_private_job"])
        record.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("PCE11_030_NATIVE_LINEAGE="+json.dumps({
      "report":str(record),"git_sha":a.expected_head,
      "launcher_pid":result["contained_launcher_pid"],
      "host_pid":result["observed_python_host_pid"],
      "host_parent_pid":result["observed_python_host_ppid"],
      "host_same_as_launcher":result["host_same_as_launcher"],
      "host_direct_child":result["host_direct_child_of_launcher"],
      "launcher_inside_job":result["launcher_in_exact_private_job"],
      "host_inside_job":result["host_is_in_exact_private_job"],
      "job_cleanup":result["job_kill_verified"],
      "host_exit_observed":result["observed_host_exit_after_job_close"],
      "main_pid_preserved":result["main_preserved"],
      "port8768_free_after":result["port8768_free_after"],
      "success":result["success"],"failure":failure,
      "v16_server_launched":False,"production_cutover_authorized":False},separators=(",",":")))
    return 0 if result["success"] else 2

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        print("PCE11_030_BLOCKED="+type(exc).__name__+": "+str(exc)[:350],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
