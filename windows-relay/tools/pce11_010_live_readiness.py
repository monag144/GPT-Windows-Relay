#!/usr/bin/env python3
"""PCE11.010 passive runtime ownership readiness: GET /status, EnumWindows, SHA only."""
from __future__ import annotations
import argparse,ctypes,hashlib,json,os,shutil,subprocess,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
AUDIT_REL="docs/audits/AUDIT_2026-10-08T0933Z_PCE11_OPERATIONS_005_009.md"
HUD_PIDS=(13408,4464)
OLD_009="9d8619fb25cff0e73ddfb47f0c277d055c305741"

def cmd(args,timeout=15):
    p=subprocess.run(args,text=True,encoding="utf-8",errors="replace",
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if p.returncode:raise RuntimeError("verification command failed: "+Path(str(args[0])).name)
    return p.stdout.strip()

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def hud_visible_windows():
    """Visible top-level HWND owners only. Never read window title, text or screenshots."""
    result={str(x):{"visible_toplevel_count":0,"classes":[]} for x in HUD_PIDS}
    if os.name!="nt":return {"available":False,"reason":"not Windows"}
    try:
        user=ctypes.windll.user32
        callback_t=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_ssize_t)
        user.EnumWindows.argtypes=(callback_t,ctypes.c_ssize_t)
        user.EnumWindows.restype=ctypes.c_bool
        user.GetWindowThreadProcessId.argtypes=(ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong))
        user.GetWindowThreadProcessId.restype=ctypes.c_ulong
        user.IsWindowVisible.argtypes=(ctypes.c_void_p,)
        user.IsWindowVisible.restype=ctypes.c_bool
        user.GetClassNameW.argtypes=(ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_int)
        user.GetClassNameW.restype=ctypes.c_int
        def visit(hwnd,lparam):
            pid=ctypes.c_ulong(0)
            user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            key=str(pid.value)
            if key in result and user.IsWindowVisible(hwnd):
                buf=ctypes.create_unicode_buffer(120)
                user.GetClassNameW(hwnd,buf,len(buf))
                result[key]["visible_toplevel_count"]+=1
                if buf.value not in result[key]["classes"]:
                    result[key]["classes"].append(buf.value[:72])
            return True
        cb=callback_t(visit)
        if not user.EnumWindows(cb,0):return {"available":False,"reason":"EnumWindows returned false"}
        return {"available":True,"hud_pids":result,
                "notice":"Visible HWND counts do not independently establish duplicate HUD app instances"}
    except (AttributeError,OSError,ValueError) as e:
        return {"available":False,"reason":type(e).__name__}

def backend_status():
    """Authenticated GET without printing/token persistence and without mutating arm state."""
    cfg=Path(os.environ.get("APPDATA",Path.home()))/"GPTWindowsRelay"/"bridge.json"
    if not cfg.is_file():return {"available":False,"reason":"main bridge file unavailable"}
    try:
        info=json.loads(cfg.read_text(encoding="utf-8-sig"))
        if type(info) is not dict or int(info.get("port",0))!=8766 or not info.get("token"):
            return {"available":False,"reason":"untrusted or missing main-port pairing"}
        req=urllib.request.Request("http://127.0.0.1:8766/status",
                     headers={"X-GPT-Windows-Relay-Token":str(info["token"])},
                     method="GET")
        with urllib.request.urlopen(req,timeout=3) as response:
            obj=json.loads(response.read(8192))
        if not isinstance(obj,dict) or obj.get("ok") is not True:
            return {"available":False,"reason":"backend status malformed"}
        fields=("ok","pid","armed","outbound_owner","pending_missions",
                "stop_generation","browser_quiesced_generation")
        return {"available":True,"values":{key:obj.get(key) for key in fields}}
    except Exception as e:
        return {"available":False,"reason":type(e).__name__}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--live",type=Path,required=True)
    p.add_argument("--expected-head",required=True)
    args=p.parse_args()
    repo=args.repo.resolve();live=args.live.resolve()
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    g=lambda *a:cmd([git,"-C",str(repo),*a])
    if not repo.is_dir() or not live.is_dir() or repo==live:raise RuntimeError("source and live trees invalid")
    if g("rev-parse","HEAD")!=args.expected_head or g("branch","--show-current")!=BRANCH:
        raise RuntimeError("not at audited pinned source commit")
    if "monag144/gpt-windows-relay" not in g("remote","get-url","origin").lower():
        raise RuntimeError("wrong GitHub canonical remote")
    if g("status","--porcelain"):raise RuntimeError("source checkout dirty")
    remote=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=args.expected_head:raise RuntimeError("GitHub HEAD changed")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    pre=engineering_preflight(repo,10,series=11)
    audit=pre.get("checkpoints",{}).get("audit",{})
    if not pre["ok"] or audit.get("path")!=AUDIT_REL:
        raise RuntimeError("required second five-slot checkpoint not accepted")
    prior=live/"bin"/"PROCESS_IDENTITY_2026-10-08T093134Z.json"
    if not prior.is_file():raise RuntimeError("PCE11.009 saved evidence missing")
    last=json.loads(prior.read_text(encoding="utf-8"))
    if last.get("schema")!="pce011-current-process-identity-v1" or last.get("git_head")!=OLD_009:
        raise RuntimeError("incorrect PCE11.009 provenance")
    st=backend_status()
    gui=hud_visible_windows()
    recorded_pid=[x["pid"] for x in last["process_matches"] if x.get("historical_role")=="relay-server"]
    sentinels={name:(live/name).exists() for name in
        (".relay-paused",".relay-off",".relay-kill",".relay-kill-hud",".relay-kill-failed")}
    out={"schema":"pce011-live-readiness-v1",
         "time_utc":datetime.now(timezone.utc).isoformat(),
         "repo_sha":args.expected_head,"governance":pre,
         "previous_identity_sha256":digest(prior),"previous_server_pids":recorded_pid,
         "status":st,"visible_windows":gui,"stop_sentinels":sentinels,
         "live_relay_control_sha256":digest(live/"relay-control.ps1") if (live/"relay-control.ps1").is_file() else None,
         "canonical_relay_control_sha256":digest(repo/"windows-relay"/"relay-control.ps1"),
         "browser_identity_verified":False,"loaded_extension_sha_verified":False,
         "stop_equivalence_verified":False,"rollback_verified":False,
         "cutover_authorized":False,
         "limits":"Visible HWND and GET status are only instantaneous read-only diagnostics; no runtime activation"}
    filename=live/"bin"/("LIVE_READINESS_"+datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")+".json")
    if filename.exists():raise FileExistsError("report collision")
    filename.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    brief={"report":str(filename),
       "source_sha":args.expected_head,
       "five_read_sha256":{name:v["sha256"] for name,v in pre["reads"].items()},
       "audit_sha256":audit["sha256"],
       "backend":st,"hud_window_counts":gui,
       "stop_sentinels":sentinels,
       "relay_control_on_disk_matches_source":out["live_relay_control_sha256"]==out["canonical_relay_control_sha256"],
       "live_cutover_authorized":False}
    print("PCE11_010_READINESS="+json.dumps(brief,separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (RuntimeError,OSError,ValueError,KeyError,subprocess.TimeoutExpired) as e:
        print("PCE11_010_BLOCKED="+str(e)[:240],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
