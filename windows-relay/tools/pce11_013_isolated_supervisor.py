#!/usr/bin/env python3
"""PCE11.013/014 isolated v16 service canary, never replaces main Relay.

013 = static contract preflight only. 014 = a SINGLE fresh sandboxed canary:
random private token, dedicated 127.0.0.1:8768, unique state, one Windows
Job Object with KILL_ON_JOB_CLOSE; authenticated GET /status; cleanup verified.
No POST /action, no browser, no process scanning/termination outside our job.
"""
from __future__ import annotations
import argparse,ast,ctypes,hashlib,json,os,secrets,shutil,socket,subprocess,sys,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
BASE_SHA="4140181bb354462c1ff8026491cfff7ae92ca686"
V16_SHA="694d47ab89596d5c3801f749caa352b951a2be52"
V16_BLOB="414b74121b1a5a5f2a049ebc84097223e7b5e69f"
PORT=8768

def invoke(args,timeout=30):
    p=subprocess.run(args,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:raise RuntimeError("verification command failure: "+Path(str(args[0])).name+" rc="+str(p.returncode))
    return p.stdout.strip()
def git(repo,*args,timeout=35):
    exe=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    return invoke([exe,"-C",str(repo),*args],timeout=timeout)
def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\x00"+raw).hexdigest()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()
def pid_for_port():
    exe=shutil.which("netstat")
    if not exe:raise RuntimeError("netstat unavailable")
    pids=[]
    for line in invoke([exe,"-ano","-p","tcp"],timeout=15).splitlines():
        items=line.split()
        if len(items)<5 or items[0].upper()!="TCP" or items[3].upper()!="LISTENING":continue
        if items[1].rsplit(":",1)[-1]==str(PORT) and items[-1].isdigit():
            pids.append(int(items[-1]))
    return sorted(set(pids))

def safe_status(port,token,timeout=1):
    request=urllib.request.Request("http://127.0.0.1:"+str(port)+"/status",
             headers={"X-GPT-Windows-Relay-Token":token},method="GET")
    with urllib.request.urlopen(request,timeout=timeout) as resp:
        value=json.loads(resp.read(8192))
    if not isinstance(value,dict) or value.get("ok") is not True:
        raise RuntimeError("backend /status rejected")
    return {k:value.get(k) for k in ("ok","pid","armed","outbound_owner","pending_missions",
                                    "stop_generation","browser_quiesced_generation")}

def win_job_available():
    return sys.platform=="win32" and hasattr(ctypes,"windll") and hasattr(ctypes.windll.kernel32,"CreateJobObjectW")

class BasicLimits(ctypes.Structure):
    _fields_=[("PerProcessUserTimeLimit",ctypes.c_int64),
      ("PerJobUserTimeLimit",ctypes.c_int64),("LimitFlags",ctypes.c_uint32),
      ("MinimumWorkingSetSize",ctypes.c_size_t),("MaximumWorkingSetSize",ctypes.c_size_t),
      ("ActiveProcessLimit",ctypes.c_uint32),("Affinity",ctypes.c_size_t),
      ("PriorityClass",ctypes.c_uint32),("SchedulingClass",ctypes.c_uint32)]
class IOCounters(ctypes.Structure):
    _fields_=[(k,ctypes.c_uint64) for k in (
      "ReadOperationCount","WriteOperationCount","OtherOperationCount",
      "ReadTransferCount","WriteTransferCount","OtherTransferCount")]
class ExtendedLimits(ctypes.Structure):
    _fields_=[("BasicLimitInformation",BasicLimits),("IoInfo",IOCounters),
      ("ProcessMemoryLimit",ctypes.c_size_t),("JobMemoryLimit",ctypes.c_size_t),
      ("PeakProcessMemoryUsed",ctypes.c_size_t),("PeakJobMemoryUsed",ctypes.c_size_t)]

class OwnedJob:
    """Owns ONLY explicitly assigned canary process; no generic PID kill."""
    def __init__(self):
        if not win_job_available():raise RuntimeError("Windows Job object API unavailable")
        api=ctypes.windll.kernel32
        api.CreateJobObjectW.argtypes=(ctypes.c_void_p,ctypes.c_wchar_p)
        api.CreateJobObjectW.restype=ctypes.c_void_p
        api.SetInformationJobObject.argtypes=(ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32)
        api.SetInformationJobObject.restype=ctypes.c_int
        api.AssignProcessToJobObject.argtypes=(ctypes.c_void_p,ctypes.c_void_p)
        api.AssignProcessToJobObject.restype=ctypes.c_int
        api.CloseHandle.argtypes=(ctypes.c_void_p,)
        api.CloseHandle.restype=ctypes.c_int
        api.TerminateJobObject.argtypes=(ctypes.c_void_p,ctypes.c_uint32)
        api.TerminateJobObject.restype=ctypes.c_int
        self.api=api
        self.handle=api.CreateJobObjectW(None,None)
        if not self.handle:raise OSError("CreateJobObjectW failed")
        lim=ExtendedLimits()
        lim.BasicLimitInformation.LimitFlags=0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not api.SetInformationJobObject(self.handle,9,ctypes.byref(lim),ctypes.sizeof(lim)):
            api.CloseHandle(self.handle);self.handle=None
            raise OSError("JobObject KILL_ON_CLOSE configuration failed")
    def attach(self,proc):
        if not self.api.AssignProcessToJobObject(self.handle,ctypes.c_void_p(int(proc._handle))):
            raise OSError("Unable to assign canary process to owned Windows job")
    def close(self):
        if self.handle:
            self.api.TerminateJobObject(self.handle,1)
            self.api.CloseHandle(self.handle)
            self.handle=None

def candidate(repo,live):
    folder=live/"builds"/("RELAY_PCE8_V16_"+V16_SHA[:12])
    script=folder/"windows-relay"/"windows_relay.py"
    if not folder.is_dir() or not script.is_file():raise RuntimeError("v16 staging unavailable")
    if git(folder,"rev-parse","HEAD")!=V16_SHA:raise RuntimeError("historical v16 SHA mismatch")
    if git(folder,"status","--porcelain"):raise RuntimeError("historical v16 staging dirty")
    raw=script.read_bytes()
    if git_blob(raw)!=V16_BLOB:raise RuntimeError("v16 entrypoint blob mismatch")
    tree=ast.parse(raw.decode("utf-8-sig"))
    literals={n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
    if not {"--config","--state-dir","server","127.0.0.1"}.issubset(literals):
        raise RuntimeError("v16 --config / --state-dir loopback source contract absent")
    text=raw.decode("utf-8-sig")
    if "State(a.state_dir" not in text or "config(a.config)" not in text:
        raise RuntimeError("v16 does not use isolated config/state parameters")
    return {"folder":str(folder),"source":str(script),"source_sha256":sha(script),
            "git_head":V16_SHA,"blob":V16_BLOB}

def validate_launch(argv,st,conf):
    if len(argv)!=8 or argv[1]!="-B" or argv[3:5]!=["--config",str(conf)] or argv[5:7]!=["--state-dir",str(st)] or argv[7]!="server":
        raise RuntimeError("isolated sidecar launch argument contract violated")
    if argv[0]!=sys.executable:raise RuntimeError("not using explicit Python interpreter")
    return True

def self_test():
    base=Path("R:/sandbox-safe");conf=base/"bridge.json";st=base/"state"
    cmd=[sys.executable,"-B","R:/source/windows_relay.py","--config",str(conf),"--state-dir",str(st),"server"]
    validate_launch(cmd,st,conf)
    if len(set(cmd))!=len(cmd):raise RuntimeError("unexpected repeated argument")
    if len({"--config","--state-dir"} & set(cmd))!=2:raise RuntimeError("incomplete isolation")
    return True

def canary(live,record):
    if not win_job_available():raise RuntimeError("Windows safe process containment unavailable")
    if pid_for_port():raise RuntimeError("isolated port already occupied, refuse start")
    # No mount to live config or production state. This directory is unique and never reused.
    base=live/"bin"/("SIDECAR_CANARY_"+
      datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")+"_"+secrets.token_hex(4))
    if base.exists():raise RuntimeError("canary sandbox collision")
    config_dir=base/"private";config_dir.mkdir(parents=True,exist_ok=False)
    state=base/"state";state.mkdir(exist_ok=False)
    config=config_dir/"bridge.json"
    token=secrets.token_urlsafe(48)
    config.write_text(json.dumps({"version":1,"host":"127.0.0.1","port":PORT,"token":token})+"\n",encoding="utf-8")
    script=Path(record["source"])
    args=[sys.executable,"-B",str(script),"--config",str(config),"--state-dir",str(state),"server"]
    validate_launch(args,state,config)
    job=OwnedJob();p=None;logpath=base/"canary-process.log"
    result={"sandbox":str(base),"canary_pid":None,"status_ok":False,"job_contained":False,
            "cleanup_verified":False,"main_relay_modified":False}
    try:
        with logpath.open("wb") as logfile:
            p=subprocess.Popen(args,cwd=str(script.parent),stdin=subprocess.DEVNULL,
                  stdout=logfile,stderr=subprocess.STDOUT,creationflags=0x08000000)
            result["canary_pid"]=p.pid
            job.attach(p)
            result["job_contained"]=True
            deadline=time.monotonic()+7
            while time.monotonic()<deadline:
                if p.poll() is not None:raise RuntimeError("isolated v16 process exited before status check")
                try:
                    status=safe_status(PORT,token,timeout=0.45)
                    if status["pid"]!=p.pid:raise RuntimeError("unexpected PID answered isolated canary")
                    if status["pending_missions"]!=0:raise RuntimeError("canary inherited production missions")
                    result["status"]=status
                    result["status_ok"]=True
                    break
                except (ConnectionError,TimeoutError,urllib.error.URLError,OSError):
                    time.sleep(0.15)
            if not result["status_ok"]:raise RuntimeError("isolated v16 failed to expose /status")
    finally:
        # We never terminate processes other than our specifically created Job Object.
        job.close()
        if p:
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                result["cleanup_error"]="canary child still alive after job close"
        for _ in range(15):
            if not pid_for_port():break
            time.sleep(0.12)
        result["cleanup_verified"]=bool(p and p.poll() is not None and not pid_for_port())
        result["process_log"]=str(logpath)
        result["token_redacted"]=True
        (base/"canary-report.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    if not result["cleanup_verified"]:raise RuntimeError("orphaned isolated canary, operator investigation required")
    if not result["status_ok"]:raise RuntimeError("v16 isolated /status probe did not pass")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--live",type=Path,required=True)
    p.add_argument("--expected-head",required=True)
    p.add_argument("--mode",choices=("preflight","canary"),required=True)
    a=p.parse_args()
    self_test()
    repo=a.repo.resolve();live=a.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:raise RuntimeError("canonical repo/live missing")
    expected_previous=BASE_SHA if a.mode=="preflight" else a.expected_head
    if git(repo,"rev-parse","HEAD")!=expected_previous:raise RuntimeError("unexpected previous canonical SHA")
    if git(repo,"branch","--show-current")!=BRANCH:raise RuntimeError("wrong canonical branch")
    if "monag144/gpt-windows-relay" not in git(repo,"remote","get-url","origin").lower():
        raise RuntimeError("wrong origin")
    if git(repo,"status","--porcelain"):raise RuntimeError("dirty canonical checkout")
    remote=git(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=a.expected_head:raise RuntimeError("GitHub commit changed")
    if a.mode=="preflight":
        git(repo,"pull","--ff-only","origin",BRANCH,timeout=65)
    if git(repo,"rev-parse","HEAD")!=a.expected_head:raise RuntimeError("unverified local source revision")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    ordinal=13 if a.mode=="preflight" else 14
    proof=engineering_preflight(repo,ordinal,series=11)
    if not proof["ok"]:raise RuntimeError("canonical governance blocked")
    if a.mode=="preflight":
        invoke([sys.executable,"-B","-m","unittest","discover","-s",
          str(repo/"windows-relay"/"tests"),"-p","test_pce11_isolated_supervisor.py"],timeout=40)
    stage=candidate(repo,live)
    listeners=pid_for_port()
    if listeners:raise RuntimeError("port 8768 not free")
    if a.mode=="preflight":
        print("PCE11_013_SUPERVISOR_CONTRACT="+json.dumps({
           "id":proof["id"],"repo_sha":a.expected_head,
           "five_control_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
           "staged_source":stage,"job_api_available":win_job_available(),
           "self_test_passed":True,"targeted_unit_tests_passed":True,"port_8768_free":True,
           "private_config_state_supported":True,
           "source_supervisor_missing_is_not_blocker_to_independent_harness":True,
           "process_launched":False,"canary_authorized":False},separators=(",",":")))
    else:
        result=canary(live,stage)
        print("PCE11_014_ISOLATED_CANARY="+json.dumps({
            "id":proof["id"],"source":a.expected_head,
            "isolated_pid":result["canary_pid"],"status_ok":result["status_ok"],
            "job_contained":result["job_contained"],
            "cleanup_verified":result["cleanup_verified"],
            "state_path":result["sandbox"],
            "port_8768_free_after":not pid_for_port(),
            "main_relay_modified":False},separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as e:
        print("PCE11_SUPERVISOR_BLOCKED="+type(e).__name__+": "+str(e)[:280],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
