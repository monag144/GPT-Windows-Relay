#!/usr/bin/env python3
from __future__ import annotations
import argparse,ctypes,json,os,re,subprocess,tkinter as tk,urllib.request,threading,queue,sys
from tkinter import messagebox
from datetime import datetime,timezone
from pathlib import Path

# GPT_RELAY_HUD_READABLE_V3
A=Path(os.environ.get("APPDATA",Path.home()))/"GPTWindowsRelay"
L=Path(os.environ.get("LOCALAPPDATA",Path.home()))/"GPTWindowsRelay"
POS=A/"hud-settings.json"
HUD_LAYOUT_VERSION=3
W,COMPACT_H,EXPANDED_H=560,184,386
BG="#202124"; PANEL="#202124"; FG="#f1f3f4"; MUTED="#bdc1c6"; GOOD="#8ab4f8"; WARN="#fdd663"; BAD="#f28b82"; BORDER="#5f6368"

def read_json(p,d):
    try:return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:return d

def age_seconds(value,now=None):
    if not value:return None
    try:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        now=now or datetime.now(timezone.utc)
        return max(0,int((now-dt.astimezone(timezone.utc)).total_seconds()))
    except Exception:return None

def recent_events(limit=450):
    try:lines=(L/"browser-events.jsonl").read_text(encoding="utf-8",errors="replace").splitlines()[-limit:]
    except Exception:return []
    out=[]
    for line in lines:
        try:
            x=json.loads(line)
            if isinstance(x,dict):out.append(x)
        except Exception:pass
    return out

def latest_actions(state):
    rows=[]
    for aid,rec in state.get("processed",{}).items():
        if not isinstance(rec,dict):continue
        stamp=rec.get("finished_at") or rec.get("started_at") or ""
        rows.append((stamp,aid,rec))
    rows.sort(key=lambda x:x[0])
    current=[(aid,r) for _,aid,r in rows if r.get("status")=="INFLIGHT"]
    last=(rows[-1][1],rows[-1][2]) if rows else (None,None)
    return current,last

def event_packet_id(event):
    d=event.get("detail") if isinstance(event.get("detail"),dict) else {}
    return d.get("packet_id") or d.get("mission_id")

def browser_state(events,now=None):
    now=now or datetime.now(timezone.utc)
    wanted={
        "content_script_started","content_port_connected","browser_integration_connected",
        "browser_integration_disconnected","action_received","action_result","scanner_snapshot",
        "relay_packet_discovered","relay_recovery_packet_seen","relay_scanner_stalled",
        "relay_page_refresh_requested","relay_result_delivery_complete"
    }
    relevant=[e for e in events if e.get("event") in wanted]
    runtime=None; browser_id=None
    for e in events:
        d=e.get("detail") if isinstance(e.get("detail"),dict) else {}
        browser_id=d.get("browser_id") or browser_id
        if e.get("event")=="content_script_started":runtime=d.get("runtime") or runtime
    if not relevant:return {"state":"UNKNOWN","event":"none","age":None,"runtime":runtime,"browser_id":browser_id}
    e=relevant[-1]; a=age_seconds(e.get("time"),now)
    if e.get("event")=="browser_integration_disconnected":state="DISCONNECTED"
    else:state="ACTIVE" if a is not None and a<=120 else ("SEEN" if a is not None and a<=300 else "IDLE")
    return {"state":state,"event":str(e.get("event","unknown")),"age":a,"runtime":runtime,"browser_id":browser_id}

PHASES={
    "relay_recovery_packet_seen":("DISCOVERED","valid packet visible; forced recovery inspection"),
    "relay_packet_discovered":("DISCOVERED","packet parsed; settling before execution"),
    "relay_result_replay_suppressed":("REPLAY SUPPRESSED","execution skipped after a result-visibility check"),
    "relay_action_execution_requested":("STARTING","packet handed to extension background"),
    "action_received":("STARTING","extension posted action to Windows relay"),
    "relay_result_received":("RESULT READY","Windows result returned to browser"),
    "action_result":("RESULT READY","extension received Windows result"),
    "relay_result_send_waiting":("WAITING","waiting for ChatGPT send controls"),
    "relay_result_send_ready":("DELIVERING","ChatGPT send control became ready"),
    "relay_result_send_accepted":("WAITING FOR GPT TURN END","result submitted once; automatic resend forbidden"),
    "relay_result_waiting_for_gpt_turn_end":("WAITING FOR GPT TURN END","result submitted once; waiting for exact ChatGPT turn"),
    "relay_result_turn_end_watchdog_expired":("STALLED","submitted result not confirmed; no resend or re-execution"),
    "relay_result_delivery_retry_deferred":("WAITING","result delivery deferred for recovery"),
    "relay_result_delivery_complete":("READY","result visibly delivered"),
    "relay_scanner_stalled":("STALLED","visible packet not consumed within patience window"),
    "relay_page_refresh_requested":("RECOVERING","refreshing ChatGPT after forced reinspection failed"),
    "chatgpt_tool_approval_prompt_detected":("APPROVAL REQUIRED","ChatGPT is waiting for tool approval"),
    "gpt_recovery_advice_observed":("RECOVERY ADVICE","bounded GPT recovery advice visible; awaiting supervisor claim"),
    "gpt_recovery_advice_invalid":("RECOVERY INVALID","invalid recovery advice visible; bounded coaching required"),
    "browser_integration_disconnected":("STALLED","browser integration disconnected"),
    "content_port_connected":("READY","content script connected"),
    "content_script_started":("READY","content script started"),
}

def lifecycle(events,state,now=None):
    now=now or datetime.now(timezone.utc)
    active=state.get("active_action")
    if isinstance(active,dict) and active.get("id"):
        return {"phase":"RUNNING","reason":"Windows process executing","packet_id":active.get("id"),
                "age":age_seconds(active.get("started_at"),now),"event":"backend_inflight"}
    relevant=[e for e in events if e.get("event") in PHASES]
    if not relevant:return {"phase":"READY","reason":"no active relay operation","packet_id":None,"age":None,"event":"none"}
    e=relevant[-1]; phase,reason=PHASES[e.get("event")]
    if e.get("event")=="action_result":
        detail=e.get("detail") if isinstance(e.get("detail"),dict) else {}
        if detail.get("ok") is False:
            phase="ACTION FAILED"
            reason="extension action failed: " + str(detail.get("error") or "unspecified")[:100]
    if e.get("event")=="chatgpt_tool_approval_prompt_detected":
        d=e.get("detail") if isinstance(e.get("detail"),dict) else {}
        reason=f"ChatGPT tool approval • {d.get('provider') or 'unknown app'}"
    return {"phase":phase,"reason":reason,"packet_id":event_packet_id(e),
            "age":age_seconds(e.get("time"),now),"event":e.get("event")}

def action_detail(state):
    active=state.get("active_action")
    if isinstance(active,dict) and active.get("id"):return active,True
    last=state.get("last_action")
    if isinstance(last,dict) and last.get("id"):return last,False
    current,last_pair=latest_actions(state)
    if current:return {"id":current[-1][0],**current[-1][1]},True
    if last_pair[0]:return {"id":last_pair[0],**last_pair[1]},False
    return None,False

def command_preview(command,limit=92):
    text=re.sub(r"\s+"," ",str(command or "")).strip()
    if not text:return "(command unavailable until relay ingestion)"
    return text if len(text)<=limit else text[:limit-1]+"…"

# GPT_RELAY_HUD_OPERATOR_STOP_START_V1
# The *same* original HUD is reused by the native desktop app transport.
# Browser mode remains unchanged until the native desktop launcher selects it.
NATIVE_MODE_FILE=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'GPTWindowsRelayDesktop'/'hud-mode.json'
def native_mode():
    mode=read_json(NATIVE_MODE_FILE,{})
    return mode.get('transport')=='native-chatgpt-app'

def native_snapshot():
    import desktop_native_relay as native
    report=native.get_status()
    live=bool(report.get('native_running'))
    armed=bool(report.get('native_armed'))
    off=bool(report.get('native_off'))
    phase=str(report.get('phase') or 'UNKNOWN').upper()
    delivery_blocked=bool(report.get('delivery_blocked'))
    delivery_error=str(report.get('last_delivery_error') or '-')
    if off: title='OFF'
    elif not live: title='OFFLINE'
    elif not armed: title='STOPPED'
    elif phase=='WAITING_FOR_CHATGPT_APP': title='WAITING'
    elif phase in ('EXECUTING','DELIVERING'): title='RUNNING'
    elif phase in ('ERROR','DELIVERY_BLOCKED','DELIVERY_UNCERTAIN') or delivery_blocked: title='STALLED'
    else: title='READY'
    state=read_json(native.STATE,{})
    detail,active=action_detail(state)
    aid=str(report.get('last_action') or (detail.get('id') if detail else '') or '-')
    result=str(report.get('last_result') or '-')
    deliveries=state.get('outbound_deliveries',{})
    delivery=(deliveries.get(aid) if isinstance(deliveries,dict) else None)
    delivery_phase=str(delivery.get('phase') or '') if isinstance(delivery,dict) else ''
    cmd=command_preview(detail.get('command') if detail else '')
    exact=(('ID: '+aid+'\nRESULT: '+result+'\nSHELL: '+str(detail.get('shell') or '-')+'\n\n'+str(detail.get('command') or '(command not retained)'))
           if detail else 'ID: '+aid+'\nRESULT: '+result)
    if delivery_blocked:
        exact+='\nDELIVERY BLOCKED: '+delivery_error
    phase_line=(phase+' • '+('running' if live else 'not running')+' • result '+result)
    if delivery_blocked:
        phase_line='DELIVERY BLOCKED • '+delivery_error[:75]
    return {
        'online':live,'title':title,'title_phase':title,
        'backend':('Native '+('ONLINE' if live else 'OFFLINE')+' • '+('OFF' if off else ('ARMED' if armed else 'DISARMED'))),
        'browser':'ChatGPT Windows app • UI Automation • no browser extension',
        'phase':phase_line,
        'action':'CURRENT '+aid if phase=='EXECUTING' else 'LAST '+aid,
        'preview':cmd,'exact':exact,'conversation_lock_enabled':None,'native_mode':True,
        'auto_send':bool(report.get('auto_send')),
        'native_armed':armed, 'native_off':off, 'native_phase':phase,
        'native_delivery_phase':delivery_phase,
    }

def native_control(action):
    if action not in {'start','stop','restart','off','kill'}: raise ValueError('unsupported native control')
    import desktop_native_relay as native
    # The existing original HUD submits native control requests only;
    # its buttons must never arm the Firefox relay in desktop mode.
    python=Path(sys.executable)
    if python.name.lower()=='pythonw.exe': python=python.with_name('python.exe')
    native_action='arm' if action=='start' else action
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
    subprocess.Popen([str(python),'-B',str(Path(native.__file__).resolve()),native_action],
                     cwd=str(Path(native.__file__).resolve().parent),stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
def native_auto_send(enabled):
    import desktop_native_relay as native
    python=Path(sys.executable)
    if python.name.lower()=='pythonw.exe': python=python.with_name('python.exe')
    action='auto-send-on' if enabled else 'auto-send-off'
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
    subprocess.Popen([str(python),'-B',str(Path(native.__file__).resolve()),action],
                     cwd=str(Path(native.__file__).resolve().parent),stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)

def focus_chatgpt_for_forced_delivery():
    """Hand the foreground from the clicked HUD directly to ChatGPT.

    The sender itself is a child process and Windows may reject its focus
    request.  This function runs in the foreground HUD click handler instead.
    It neither restores, resizes nor moves the ChatGPT window.
    """
    if os.name != "nt": return False
    user32=ctypes.windll.user32; kernel32=ctypes.windll.kernel32
    QueryFullProcessImageNameW=kernel32.QueryFullProcessImageNameW
    QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_uint)]
    QueryFullProcessImageNameW.restype=ctypes.c_bool
    kernel32.OpenProcess.argtypes=[ctypes.c_uint,ctypes.c_bool,ctypes.c_uint]
    kernel32.OpenProcess.restype=ctypes.c_void_p
    candidates=[]
    CALLBACK=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
    def visit(hwnd,_):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd): return True
        pid=ctypes.c_uint(); user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        handle=kernel32.OpenProcess(0x1000,False,pid.value)  # QUERY_LIMITED_INFORMATION
        if not handle: return True
        try:
            size=ctypes.c_uint(32768); image=ctypes.create_unicode_buffer(size.value)
            if QueryFullProcessImageNameW(handle,0,image,ctypes.byref(size)) and Path(image.value).name.lower()=="chatgpt.exe":
                candidates.append(hwnd)
        finally:
            kernel32.CloseHandle(handle)
        return True
    user32.EnumWindows(CALLBACK(visit),None)
    return bool(candidates and user32.SetForegroundWindow(candidates[0]))

def native_composer_clear():
    """Explicit editor-only recovery; never touches the saved delivery journal.

    The PowerShell owner verifies the exact ChatGPT window and composer and
    returns a distinct no-send receipt. Run this from a HUD worker thread.
    """
    import desktop_native_relay as native
    status=native.get_status()
    if status.get("native_running") and status.get("phase")=="DELIVERING":
        raise RuntimeError("COMPOSER_CLEAR_REFUSE_DURING_NATIVE_DELIVERY")
    script=Path(__file__).resolve().parent/"tools"/"Send-ChatGPT-DesktopHeartbeat.ps1"
    if not script.is_file():raise RuntimeError("Native ChatGPT composer helper unavailable")
    powershell="powershell.exe"
    flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if os.name=="nt" else 0
    proc=subprocess.run([powershell,"-NoLogo","-NoProfile","-ExecutionPolicy","Bypass",
                         "-STA","-File",str(script),"-ClearComposerOnly"],
                        cwd=str(script.parent),capture_output=True,text=True,
                        encoding="utf-8",errors="replace",timeout=20,check=False,
                        creationflags=flags)
    if proc.returncode or "RESULT=COMPOSER_CLEARED_NO_SEND" not in proc.stdout:
        diagnostic=next((line.partition("=")[2] for line in proc.stdout.splitlines()
                         if line.startswith("HEARTBEAT_ERROR=")),None)
        raise RuntimeError((diagnostic or "COMPOSER_CLEAR_NOT_CONFIRMED")[:180])
    return "COMPOSER_CLEARED_NO_SEND"


def native_delivery_control(command,action_id=None):
    import desktop_native_relay as native
    python=Path(sys.executable)
    if python.name.lower()=='pythonw.exe': python=python.with_name('python.exe')
    argv=[str(python),'-B',str(Path(native.__file__).resolve()),command]
    if action_id:argv.append(action_id)
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
    subprocess.Popen(argv,cwd=str(Path(native.__file__).resolve().parent),stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
def courier_hud_cli(*args):
    """Run the existing Command Courier controller without blocking the Tk UI.

    Called by a worker thread only. Never controls the browser relay or uses
    a second HUD. Startup mutations require explicit HUD checkbox interaction.
    """
    controller=Path(__file__).resolve().with_name("command_courier.py")
    if not controller.is_file():
        raise RuntimeError("Command Courier coordinator missing")
    python=Path(sys.executable)
    if python.name.lower()=="pythonw.exe":python=python.with_name("python.exe")
    flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if os.name=="nt" else 0
    result=subprocess.run(
        [str(python),"-B",str(controller),*args],
        cwd=str(controller.parent),capture_output=True,text=True,
        encoding="utf-8",errors="replace",timeout=40,check=False,
        creationflags=flags,
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "Courier command failed").strip()[-220:])
    return result.stdout

def courier_hud_startup_details():
    """Read actual owned shortcut and future-launch runtime, never infer from HUD."""
    shortcut=courier_hud_cli("startup","status")
    if "COURIER_USER_STARTUP=INSTALLED_OWNED" in shortcut:
        installed=True
    elif "COURIER_USER_STARTUP=NOT_INSTALLED" in shortcut:
        installed=False
    else:
        raise RuntimeError("COURIER_STARTUP_STATUS_UNRECOGNIZED")
    profile=courier_hud_cli("profile").strip()
    prefix="COURIER_RUNTIME="
    matched=[line[len(prefix):] for line in profile.splitlines() if line.startswith(prefix)]
    if len(matched)!=1 or matched[0] not in ("native-desktop","disabled"):
        raise RuntimeError("COURIER_RUNTIME_STATUS_UNRECOGNIZED")
    return {"installed":installed,"runtime":matched[0]}

def courier_hud_apply(action, value):
    """Mutate login startup or next-launch runtime, then verify real state."""
    if action=="startup":
        if value:
            # A working shortcut is installed first; the runtime is enabled
            # only after the link's ownership/target was safely verified.
            courier_hud_cli("startup","install")
            courier_hud_cli("profile","native-desktop")
        else:
            courier_hud_cli("startup","remove")
    elif action=="runtime" and value in ("native-desktop","disabled"):
        courier_hud_cli("profile",value)
    else:
        raise ValueError("COURIER_HUD_SETTINGS_ACTION_INVALID")
    return courier_hud_startup_details()

def relay_control(action):
    if native_mode():
        native_control(action)
        return
    if action not in {"start","stop","restart","off","kill"}:raise ValueError("unsupported relay control")
    script=Path(__file__).with_name("relay-control.ps1")
    if not script.is_file():raise FileNotFoundError(script)
    flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if os.name=="nt" else 0
    subprocess.Popen(
        ["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(script),action],
        cwd=str(script.parent),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=flags
    )

def cfg():return read_json(A/"bridge.json",{})
def request(path,timeout=.65):
    c=cfg(); token=c.get("token"); port=int(c.get("port",8766))
    if not token:raise RuntimeError("pairing unavailable")
    q=urllib.request.Request(f"http://127.0.0.1:{port}{path}",headers={"X-GPT-Windows-Relay-Token":str(token)})
    with urllib.request.urlopen(q,timeout=timeout) as r:return json.loads(r.read().decode())

def set_conversation_lock(enabled):
    if type(enabled) is not bool:raise ValueError("lock setting must be boolean")
    c=cfg(); token=c.get("token"); port=int(c.get("port",8766))
    if not token:raise RuntimeError("pairing unavailable")
    body=json.dumps({"enabled":enabled}).encode("utf-8")
    req=urllib.request.Request(
        f"http://127.0.0.1:{port}/conversation-lock",data=body,method="POST",
        headers={"Content-Type":"application/json","X-GPT-Windows-Relay-Token":str(token)})
    with urllib.request.urlopen(req,timeout=125) as response:
        result=json.loads(response.read().decode("utf-8"))
    if result.get("ok") is not True:raise RuntimeError("owner lock change declined")
    return result

def control_state(root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parent
    if (root/".relay-kill-failed").exists():return "KILL FAILED"
    if (root/".relay-kill-hud").exists():return "KILLING HUD"
    if (root/".relay-kill").exists():return "KILLING RELAY"
    if (root/".relay-off").exists():return "OFF"
    if (root/".relay-paused").exists():return "STOPPED"
    if (root/".relay-starting").exists():return "STARTING"
    return "RUNNING"

def marker_text(name,root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parent
    try:return (root/name).read_text(encoding="utf-8-sig").strip()
    except Exception:return ""

def operation_label(packet_id):
    m=re.search(r"(?i)\bA\d+\.\d+\b",str(packet_id or ""))
    return m.group(0).upper() if m else str(packet_id or "")[:32]

def headline(online,life,browser):
    if not online:return "OFFLINE"
    if life["phase"]=="STALLED":return "STALLED"
    if life["phase"]=="RECOVERING":return "RECOVERING"
    if life["phase"]=="RUNNING":return "RUNNING"
    if life["phase"] in {"WAITING","WAITING FOR GPT TURN END","DELIVERING","RESULT READY","ACTION FAILED","STARTING","DISCOVERED","REPLAY SUPPRESSED","APPROVAL REQUIRED","RECOVERY ADVICE","RECOVERY INVALID"}:return life["phase"]
    if browser["state"]=="DISCONNECTED":return "STALLED"
    return "READY"

def snapshot():
    if native_mode():return native_snapshot()
    state=read_json(L/"state.json",{"processed":{}})
    events=recent_events()
    owner_lock=None
    try:
        status=request("/status"); online=bool(status.get("ok")); armed=bool(status.get("armed"))
        owner_lock=status.get("conversation_lock_enabled") if type(status.get("conversation_lock_enabled")) is bool else None
        pending=int(status.get("pending_missions",0))
        backend=f"Relay {'ONLINE' if online else 'OFFLINE'} • {'ARMED' if armed else 'DISARMED'} • pending {pending}"
    except Exception:
        online=False; armed=False; backend="Relay OFFLINE"
    browser=browser_state(events)
    life=lifecycle(events,state)
    detail,is_active=action_detail(state)
    intent=control_state()
    title_phase=headline(online,life,browser) if intent=="RUNNING" else intent
    bid=str(browser.get("browser_id") or "browser").title()
    age=browser.get("age")
    browser_line=f"{bid} {browser['state']} • {browser['event']} • {age if age is not None else '?'}s"
    phase_age=life.get("age")
    phase_line=f"{life['phase']} • {life['reason']}"
    if phase_age is not None:phase_line+=f" • {phase_age}s"
    if intent=="STOPPED":
        backend="Relay STOPPED • operator stop"; phase_line="STOPPED • operator requested stop"
    elif intent=="OFF":
        backend="Relay OFF • backend and watchdog intentionally shut down"; phase_line="OFF • operator shutdown"
    elif intent=="STARTING":
        backend="Relay STARTING • waiting for port 8766"; phase_line="STARTING • launching watchdog and backend"
    elif intent=="KILLING RELAY":
        backend="Relay KILLING • force-stopping backend, supervisor and watchdog"; phase_line="KILLING RELAY • emergency shutdown in progress"
    elif intent=="KILLING HUD":
        backend="Relay KILLED • closing HUD"; phase_line="KILLING HUD • final shutdown stage"
    elif intent=="KILL FAILED":
        reason=marker_text(".relay-kill-failed") or "verification failed"
        backend=f"Relay KILL FAILED • {reason}"; phase_line=f"KILL FAILED • {reason}"
    packet_id=life.get("packet_id")
    if detail and (is_active or not packet_id):packet_id=detail.get("id") or packet_id
    title=title_phase
    if title_phase=="DISCOVERED" and packet_id:title=f"DISCOVERED {operation_label(packet_id)}"
    action_line=("CURRENT " if is_active else "PACKET ")+str(packet_id or "-")
    if not is_active and detail and not life.get("packet_id"):
        action_line=f"LAST {detail.get('id','-')} / {detail.get('status','-')}"
    preview=command_preview(detail.get("command") if detail else "")
    exact=""
    if detail:
        exact=(
            f"ID: {detail.get('id','-')}\n"
            f"STATUS: {detail.get('status','-')}\n"
            f"SHELL: {detail.get('shell','-')}\n"
            f"CWD: {detail.get('cwd') or '(default)'}\n"
            f"TIMEOUT: {detail.get('timeout','-')}s\n\n"
            f"{detail.get('command') or '(command unavailable)'}"
        )
    elif packet_id:
        exact=f"ID: {packet_id}\n\nExact command is not available until the packet reaches the Windows relay."
    return {
        "online":online,"title":title,"title_phase":title_phase,"backend":backend,"browser":browser_line,
        "phase":phase_line,"action":action_line,"preview":preview,"exact":exact,"conversation_lock_enabled":owner_lock,
    }

def acquire_mutex():
    if os.name!="nt":return 1
    k=ctypes.windll.kernel32; h=k.CreateMutexW(None,False,"Local\\GPTWindowsRelayHUD")
    return None if (not h or k.GetLastError()==183) else h

def run_ui():
    # Keep the HUD available to show kill/offline state; only the relay is stopped by its latch.
    mutex=acquire_mutex()
    if os.name=="nt" and mutex is None:return 0
    root=tk.Tk(); root.title("Command Courier"); root.overrideredirect(True); root.resizable(False,False)
    root.attributes("-topmost",True); root.configure(bg=BG)
    try:root.attributes("-alpha",0.97)
    except tk.TclError:pass
    pos=read_json(POS,{})
    sw=root.winfo_screenwidth()
    if int(pos.get("layout_version",0) or 0)>=HUD_LAYOUT_VERSION:
        x=int(pos.get("x",max(12,sw-W-18))); y=int(pos.get("y",18))
    else:
        x=max(12,sw-W-18); y=18
    # A HUD location saved on a previous machine/monitor may be completely
    # outside the present desktop. Preserve valid secondary-monitor positions.
    # Only recover coordinates whose centre is outside every active monitor.
    if os.name=="nt":
        try:
            from ctypes import wintypes
            class HUDPoint(ctypes.Structure):
                _fields_=[("x",wintypes.LONG),("y",wintypes.LONG)]
            u32=ctypes.windll.user32
            u32.MonitorFromPoint.argtypes=[HUDPoint,ctypes.c_uint]
            u32.MonitorFromPoint.restype=ctypes.c_void_p
            if not u32.MonitorFromPoint(HUDPoint(x+W//2,y+COMPACT_H//2),0):
                x=max(12,sw-W-18); y=18
        except (OSError,ValueError,OverflowError,AttributeError,TypeError):
            pass
    expanded=False
    settings_open=False
    root.geometry(f"{W}x{COMPACT_H}+{x}+{y}")

    panel=tk.Frame(root,bg=PANEL,highlightbackground=BORDER,highlightthickness=1,padx=12,pady=7)
    panel.pack(fill="both",expand=True)
    top=tk.Frame(panel,bg=PANEL); top.pack(fill="x")
    title=tk.Label(top,text="READY",font=("Segoe UI",12,"bold"),bg=PANEL,fg=GOOD,anchor="w")
    title.pack(side="left",fill="x",expand=True)
    toggle=tk.Button(top,text="▾",font=("Segoe UI",9,"bold"),bg=PANEL,fg=MUTED,activebackground="#303134",
                     activeforeground=FG,bd=0,highlightthickness=0,padx=5,pady=0,cursor="hand2")
    toggle.pack(side="right")
    gear_btn=tk.Button(top,text="⚙",font=("Segoe UI Symbol",12),bg=PANEL,fg=MUTED,
                       activebackground="#303134",activeforeground=FG,bd=0,
                       highlightthickness=0,padx=5,pady=0,cursor="hand2")
    gear_btn.pack(side="right",padx=(0,4))
    # Separate optional protection from START / STOP / RESTART / OFF / KILL.
    owner_lock_btn=tk.Button(top,text="OWNER LOCK: ?",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,
                             activebackground="#5f6368",activeforeground=FG,bd=0,
                             highlightthickness=0,padx=7,pady=1,cursor="hand2")
    owner_lock_btn.pack(side="right",padx=(0,5))
    min_btn=tk.Button(top,text="—",font=("Segoe UI",9,"bold"),bg=PANEL,fg=MUTED,activebackground="#303134",activeforeground=FG,bd=0,highlightthickness=0,padx=7,pady=0,cursor="hand2")
    min_btn.pack(side="right",padx=(0,3))
    controls=tk.Frame(panel,bg=PANEL); controls.pack(fill="x",pady=(4,2))
    start_btn=tk.Button(controls,text="START",font=("Segoe UI",8,"bold"),bg="#174ea6",fg=FG,activebackground="#1967d2",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("start")); start_btn.pack(side="left",padx=(0,3))
    stop_btn=tk.Button(controls,text="STOP",font=("Segoe UI",8,"bold"),bg="#5f2120",fg=FG,activebackground="#7a2e2b",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("stop")); stop_btn.pack(side="left",padx=3)
    restart_btn=tk.Button(controls,text="RESTART",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,activebackground="#5f6368",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("restart")); restart_btn.pack(side="left",padx=3)
    off_btn=tk.Button(controls,text="OFF",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,activebackground="#5f6368",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("off")); off_btn.pack(side="left",padx=3)
    kill_btn=tk.Button(controls,text="KILL",font=("Segoe UI",8,"bold"),bg="#7f1d1d",fg=FG,activebackground="#991b1b",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("kill")); kill_btn.pack(side="left",padx=3)
    # Keep the original FORCE CLEAR slot. Composer clear, outbound abort,
    # resend and queue removal are different operations, never aliases.
    force_frame=tk.Frame(panel,bg=PANEL); force_frame.place(x=278,y=34,anchor="nw")
    force_clear_btn=tk.Button(force_frame,text="FORCE CLEAR",font=("Segoe UI",8,"bold"),bg="#7f1d1d",fg=FG,activebackground="#991b1b",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2")
    force_clear_btn.grid(row=0,column=0,sticky="w",pady=(0,2))
    clear_queue_var=tk.BooleanVar(value=False)
    clear_queue_check=tk.Checkbutton(force_frame,text="CLEAR QUEUE",variable=clear_queue_var,font=("Segoe UI",8,"bold"),bg=PANEL,fg=WARN,activebackground=PANEL,activeforeground=WARN,selectcolor=PANEL,highlightthickness=0,padx=7,cursor="hand2")
    clear_queue_check.grid(row=0,column=1,sticky="w",padx=(7,0))
    force_command_btn=tk.Button(force_frame,text="FORCE RESEND",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,activebackground="#5f6368",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2")
    force_command_btn.grid(row=1,column=0,sticky="w")
    force_abort_btn=tk.Button(force_frame,text="ABORT SEND",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,activebackground="#5f6368",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2")
    force_abort_btn.grid(row=1,column=1,sticky="w",padx=(7,0))
    relay=tk.Label(panel,text="Relay …",font=("Segoe UI",9),bg=PANEL,fg=FG,anchor="w")
    relay.pack(fill="x",pady=(1,0))
    browser=tk.Label(panel,text="Browser …",font=("Segoe UI",9),bg=PANEL,fg=FG,anchor="w")
    browser.pack(fill="x")
    phase=tk.Label(panel,text="Phase …",font=("Segoe UI",9),bg=PANEL,fg=FG,anchor="w")
    phase.pack(fill="x")
    action=tk.Label(panel,text="Action …",font=("Segoe UI",8),bg=PANEL,fg=MUTED,anchor="w")
    action.pack(fill="x")
    preview=tk.Label(panel,text="…",font=("Consolas",8),bg=PANEL,fg=MUTED,anchor="w")
    preview.pack(fill="x")
    footer=tk.Frame(panel,bg=PANEL); footer.pack(fill="x",pady=(2,0))
    # GO is the primary launcher for the selected Command Courier runtime.
    # Place it first to keep it on the far right of the existing compact footer.
    go_btn=tk.Button(footer,text="GO",font=("Segoe UI",11,"bold"),bg="#188038",fg=FG,
                     activebackground="#137333",activeforeground=FG,bd=0,highlightthickness=0,
                     padx=17,pady=2,cursor="hand2")
    go_btn.pack(side="right",padx=(5,0))
    auto_send_btn=tk.Button(footer,text="Auto Send: OFF",font=("Segoe UI",8,"bold"),bg="#7f1d1d",fg=FG,
                            activebackground="#991b1b",activeforeground=FG,bd=0,highlightthickness=0,
                            padx=6,pady=1,cursor="hand2")
    auto_send_btn.pack(side="right")
    # The HUD checkbox controls a single linked sign-in entry point:
    # Command Courier starts/reuses the native engine and existing HUD.
    startup_var=tk.BooleanVar(value=False)
    startup_check=tk.Checkbutton(footer,text="Start with Windows",variable=startup_var,
                                 font=("Segoe UI",8,"bold"),bg=PANEL,fg=FG,
                                 activebackground=PANEL,activeforeground=FG,
                                 disabledforeground=MUTED,selectcolor=PANEL,
                                 highlightthickness=0,padx=3,cursor="hand2",state="disabled")
    startup_check.pack(side="left")
    # The second force button shares the status area vertically.  Keep this
    # frame above the later-packed labels so FORCE COMMAND remains visible.
    force_frame.lift()

    details_frame=tk.Frame(panel,bg=PANEL)
    details=tk.Text(details_frame,height=10,wrap="word",font=("Consolas",8),bg="#17181a",fg=FG,
                    insertbackground=FG,relief="flat",padx=7,pady=6)
    details.pack(fill="both",expand=True)
    details.configure(state="disabled")

    # Settings are embedded into the same HUD window; no extra top-level UI.
    settings_frame=tk.Frame(panel,bg=PANEL)
    tk.Label(settings_frame,text="Command Courier • Settings",font=("Segoe UI",10,"bold"),
             bg=PANEL,fg=FG,anchor="w").pack(fill="x",pady=(3,3))
    settings_row=tk.Frame(settings_frame,bg=PANEL)
    settings_row.pack(fill="x")
    tk.Label(settings_row,text="Runtime at next sign-in:",font=("Segoe UI",9),
             bg=PANEL,fg=FG).pack(side="left",padx=(0,8))
    runtime_choice=tk.StringVar(value="native-desktop")
    runtime_native=tk.Radiobutton(settings_row,text="Native desktop",variable=runtime_choice,
                                  value="native-desktop",bg=PANEL,fg=FG,
                                  activebackground=PANEL,activeforeground=FG,
                                  selectcolor=PANEL,highlightthickness=0)
    runtime_native.pack(side="left")
    runtime_disabled=tk.Radiobutton(settings_row,text="Disabled",variable=runtime_choice,
                                    value="disabled",bg=PANEL,fg=FG,
                                    activebackground=PANEL,activeforeground=FG,
                                    selectcolor=PANEL,highlightthickness=0)
    runtime_disabled.pack(side="left")
    apply_runtime_btn=tk.Button(settings_frame,text="Apply runtime for next launch",
                                 font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,
                                 activebackground="#5f6368",activeforeground=FG,
                                 bd=0,padx=8,pady=3,cursor="hand2")
    apply_runtime_btn.pack(anchor="w",pady=(6,3))
    settings_startup_check=tk.Checkbutton(settings_frame,text="Start HUD and engine with Windows sign-in",
                                           variable=startup_var,font=("Segoe UI",9),
                                           bg=PANEL,fg=FG,activebackground=PANEL,
                                           activeforeground=FG,disabledforeground=MUTED,
                                           selectcolor=PANEL,highlightthickness=0,
                                           state="disabled")
    settings_startup_check.pack(anchor="w")
    settings_status=tk.Label(settings_frame,text="Startup status: checking…",
                              font=("Segoe UI",8),bg=PANEL,fg=MUTED,
                              justify="left",anchor="w",wraplength=W-35)
    settings_status.pack(fill="x",pady=(5,2))
    tk.Label(settings_frame,text="At user sign-in, not before login. STOP/OFF remain authoritative.",
             font=("Segoe UI",8),bg=PANEL,fg=MUTED,anchor="w").pack(fill="x")

    drag={"x":0,"y":0}
    def down(e):drag["x"]=e.x_root-root.winfo_x(); drag["y"]=e.y_root-root.winfo_y()
    def move(e):root.geometry(f"+{e.x_root-drag['x']}+{e.y_root-drag['y']}")
    def save(_e=None):
        try:
            POS.parent.mkdir(parents=True,exist_ok=True)
            POS.write_text(json.dumps({"layout_version":HUD_LAYOUT_VERSION,"x":root.winfo_x(),"y":root.winfo_y()},indent=2),encoding="utf-8")
        except Exception:pass
    for widget in (root,panel,top,title,relay,browser,phase,action,preview):
        widget.bind("<ButtonPress-1>",down); widget.bind("<B1-Motion>",move); widget.bind("<ButtonRelease-1>",save)
    def minimize_hud():
        save()
        try:
            root.overrideredirect(False); root.iconify()
        except tk.TclError:pass
    def restore_borderless(_e=None):
        try:
            if root.state()=="normal":root.after(20,lambda:root.overrideredirect(True))
        except tk.TclError:pass
    min_btn.configure(command=minimize_hud)
    root.bind("<Map>",restore_borderless)
    # GPT_RELAY_HUD_NO_HIDDEN_RIGHT_CLICK_EXIT_V1

    details_cache={"text":None}
    def set_details(text):
        # Never erase a selection every second when the receipt has not changed.
        value=text or "No relay instruction available."
        if value==details_cache["text"]:return
        details_cache["text"]=value
        details.configure(state="normal"); details.delete("1.0","end"); details.insert("1.0",value)
        details.configure(state="disabled")

    def redraw_expanded_pane():
        details_frame.pack_forget()
        settings_frame.pack_forget()
        if expanded:
            active_frame=settings_frame if settings_open else details_frame
            active_frame.pack(fill="both",expand=True,pady=(7,0))
        toggle.configure(text="▴" if expanded else "▾")
        gear_btn.configure(bg="#3c4043" if settings_open else PANEL,
                           fg=FG if settings_open else MUTED)
        root.geometry(f"{W}x{EXPANDED_H if expanded else COMPACT_H}+{root.winfo_x()}+{root.winfo_y()}")
    def toggle_details():
        nonlocal expanded,settings_open
        expanded=not expanded
        if not expanded:settings_open=False
        redraw_expanded_pane()
    def toggle_settings():
        nonlocal expanded,settings_open
        if not native_mode():return
        settings_open=not settings_open
        if settings_open:expanded=True
        redraw_expanded_pane()
        if settings_open:request_courier_status()
    toggle.configure(command=toggle_details)
    gear_btn.configure(command=toggle_settings)

    lock_state={"enabled":None,"busy":False,"error":None}
    lock_results=queue.Queue()
    def change_owner_lock():
        if native_mode():return
        if lock_state["busy"] or lock_state["enabled"] is None:return
        target=not lock_state["enabled"]
        lock_state["busy"]=True
        lock_state["error"]=None
        def worker():
            try:
                response=set_conversation_lock(target)
                lock_results.put(("ok",response))
            except Exception as exc:
                lock_results.put(("error",type(exc).__name__))
        threading.Thread(target=worker,daemon=True).start()
    owner_lock_btn.configure(command=change_owner_lock)

    # Startup is owned by Command Courier. The checkbox is a verified control,
    # not an optimistic flag: never show checked before confirming the link and
    # selected runtime. Do not wait for PowerShell on the Tk event loop.
    courier_results=queue.Queue()
    courier_state={"known":False,"installed":False,"runtime":"native-desktop",
                   "busy":False,"error":None,"queried":False}
    def update_courier_settings_widgets():
        enabled=bool(courier_state["known"] and courier_state["installed"]
                     and courier_state["runtime"]=="native-desktop")
        startup_var.set(enabled)
        editable=bool(native_mode() and courier_state["known"] and not courier_state["busy"])
        startup_check.configure(state="normal" if editable else "disabled")
        settings_startup_check.configure(state="normal" if editable else "disabled")
        selection_state="normal" if editable else "disabled"
        runtime_native.configure(state=selection_state)
        runtime_disabled.configure(state=selection_state)
        apply_runtime_btn.configure(state=selection_state)
        if courier_state["busy"]:
            status_line="Windows startup: checking / applying…"
        elif courier_state["error"]:
            status_line="Windows startup: ERROR • "+courier_state["error"][:110]
        elif not courier_state["known"]:
            status_line="Windows startup: status unavailable"
        elif courier_state["installed"] and courier_state["runtime"]=="native-desktop":
            status_line="Windows startup: ON • HUD + engine at user sign-in"
        elif courier_state["installed"]:
            status_line="Windows startup: shortcut installed; runtime disabled"
        else:
            status_line="Windows startup: OFF • no Command Courier shortcut"
        settings_status.configure(text=status_line,fg=BAD if courier_state["error"] else MUTED)
        gear_btn.configure(fg=BAD if courier_state["error"] else
                           (FG if settings_open else MUTED))
    def start_courier_worker(action,value=None):
        if courier_state["busy"]:return
        courier_state["queried"]=True
        courier_state["busy"]=True
        courier_state["error"]=None
        update_courier_settings_widgets()
        def worker():
            try:
                if action=="status":details=courier_hud_startup_details()
                else:details=courier_hud_apply(action,value)
                courier_results.put(("ok",details,None))
            except Exception as exc:
                # Mutations can fail after changing only one of profile/link.
                # Re-read actual state rather than silently presenting success.
                try:details=courier_hud_startup_details()
                except Exception:details=None
                courier_results.put(("error",details,str(exc)[:180]))
        threading.Thread(target=worker,daemon=True).start()
    def request_courier_status():
        start_courier_worker("status")
    def on_startup_check():
        wanted=bool(startup_var.get())
        # Do not treat Tk's immediate visual toggle as confirmation.
        update_courier_settings_widgets()
        if native_mode():start_courier_worker("startup",wanted)
    def apply_runtime_selection():
        if native_mode():start_courier_worker("runtime",runtime_choice.get())
    startup_check.configure(command=on_startup_check)
    settings_startup_check.configure(command=on_startup_check)
    apply_runtime_btn.configure(command=apply_runtime_selection)
    update_courier_settings_widgets()

    # The legacy consumer/GO.bat remains a separate browser-specific client.
    # This HUD GO calls the Command Courier runtime adapter, never the browser
    # backend, sender, or the original HUD reconciler (which could kill us).
    go_results=queue.Queue()
    go_state={"busy":False,"error":None,"ready":False,"waiting":False}
    def on_go():
        if not native_mode() or go_state["busy"]:return
        go_state["busy"]=True
        go_state["error"]=None
        go_state["ready"]=False
        go_state["waiting"]=False
        go_btn.configure(text="GO…",state="disabled")
        def worker():
            try:
                output=courier_hud_cli("go")
                if "COURIER_GO=NATIVE_RUNTIME_READY" in output:
                    go_results.put(("ok",None))
                elif "COURIER_GO=WAITING_FOR_DESTINATION" in output:
                    go_results.put(("waiting",None))
                else:
                    raise RuntimeError("Command Courier runtime was not confirmed")
            except Exception as exc:
                go_results.put(("error",str(exc)[-220:]))
        threading.Thread(target=worker,name="command-courier-go",daemon=True).start()
    go_btn.configure(command=on_go)

    native_view={"snap":None}
    def native_action_id():
        snap=native_view.get("snap") or {}
        return str(snap.get("action") or "").removeprefix("LAST ").removeprefix("CURRENT ").strip()
    def show_force_command():
        aid=native_action_id()
        if not native_mode() or not aid or aid=='-':return
        # This resubmits a saved result, not a CMD command.  A prior receipt
        # may have reached the conversation even when the journal says failed.
        if not messagebox.askyesno("Force Resend",
            "Resend saved result " + aid + "?\n\n"
            "This can duplicate a result already received by ChatGPT and may "
            "overwrite an existing ChatGPT draft. Reconcile a known receipt "
            "instead. Continue only if the result was not delivered.",
            parent=root):
            return
        if not focus_chatgpt_for_forced_delivery():
            messagebox.showerror("Force Resend","ChatGPT could not be brought to the foreground. No delivery retry was started.",parent=root)
            return
        # Let Windows finish foreground activation before the child sender
        # performs its independent foreground verification.
        root.after(180,lambda:native_delivery_control("force-delivery",aid))
    # FORCE CLEAR is an explicit, confirmed editor-only operation. It is not
    # FORCE RESEND, ABORT SEND or CLEAR QUEUE; it never releases a result hold.
    clear_results=queue.Queue()
    clear_busy={"value":False}
    def force_clear_composer():
        snap=native_view.get("snap") or {}
        if not native_mode() or clear_busy["value"] or snap.get("native_phase")=="DELIVERING":return
        if not messagebox.askyesno("Force Clear ChatGPT Composer",
                "Discard the current unsent ChatGPT composer text?\n\n"
                "This cannot be undone. No relay packet will be sent, retried "
                "or deleted. Continue?",parent=root):
            return
        if not focus_chatgpt_for_forced_delivery():
            messagebox.showerror("Force Clear",
                "ChatGPT could not be focused; nothing was cleared.",parent=root)
            return
        clear_busy["value"]=True
        force_clear_btn.configure(state="disabled",text="CLEARING…")
        def worker():
            try:clear_results.put(("ok",native_composer_clear()))
            except Exception as exc:clear_results.put(("error",str(exc)[-180:]))
        threading.Thread(target=worker,name="courier-composer-clear",daemon=True).start()
    def force_abort():
        aid=native_action_id()
        if not native_mode() or not aid or aid=='-':return
        if messagebox.askyesno("Abort Send","Abort unsent delivery "+aid+"?\nThe saved result remains, but this delivery will not retry.",parent=root):
            native_delivery_control("abort-delivery",aid)
    def clear_pending_queue():
        if not clear_queue_var.get():return
        clear_queue_var.set(False)
        if native_mode() and messagebox.askyesno("Clear Entire Queue","Delete all pending native delivery records and holds?\nExecuted command results are retained.",parent=root):
            native_delivery_control("clear-pending-deliveries")
    force_command_btn.configure(command=show_force_command)
    force_clear_btn.configure(command=force_clear_composer)
    force_abort_btn.configure(command=force_abort)
    clear_queue_check.configure(command=clear_pending_queue)
    def toggle_auto_send():
        if not native_mode():return
        native_auto_send(not bool(auto_send_btn.cget('text')=='Auto Send: ON'))
    auto_send_btn.configure(command=toggle_auto_send)

    colors={"OFFLINE":BAD,"DISCONNECTED":BAD,"KILL FAILED":BAD,"KILLING RELAY":BAD,"KILLING HUD":BAD,"OFF":MUTED,"STOPPED":WARN,"STALLED":BAD,"RECOVERING":WARN,"APPROVAL REQUIRED":BAD,"RECOVERY ADVICE":WARN,"RECOVERY INVALID":BAD,"WAITING":WARN,"WAITING FOR GPT TURN END":WARN,"DELIVERING":WARN,"RESULT READY":WARN,"STARTING":WARN,"DISCOVERED":WARN,"REPLAY SUPPRESSED":WARN,"RUNNING":GOOD,"READY":GOOD,"PAUSED":WARN}
    def refresh():
        while not lock_results.empty():
            kind,value=lock_results.get_nowait()
            lock_state["busy"]=False
            if kind=="ok":
                lock_state["enabled"]=value["conversation_lock_enabled"]
                lock_state["error"]=None
            else:
                lock_state["error"]=value
        while not courier_results.empty():
            kind,details,error=courier_results.get_nowait()
            courier_state["busy"]=False
            courier_state["error"]=error
            if isinstance(details,dict):
                courier_state["known"]=True
                courier_state["installed"]=bool(details["installed"])
                courier_state["runtime"]=details["runtime"]
                runtime_choice.set(details["runtime"])
            elif kind=="error":
                courier_state["known"]=False
            update_courier_settings_widgets()
        while not clear_results.empty():
            kind,value=clear_results.get_nowait()
            clear_busy["value"]=False
            if kind=="error":
                messagebox.showerror("Force Clear",value,parent=root)
        while not go_results.empty():
            kind,error=go_results.get_nowait()
            go_state["busy"]=False
            go_state["error"]=error if kind=="error" else None
            go_state["ready"]=(kind=="ok")
            go_state["waiting"]=(kind=="waiting")
            if kind=="error":
                messagebox.showerror("Command Courier GO",error,parent=root)
        if native_mode() and not courier_state["queried"]:
            request_courier_status()
        snap=snapshot()
        if snap.get('native_mode'):
            native_view["snap"]=snap
            owner_lock_btn.configure(text='OWNER LOCK: N/A',state='disabled',bg='#3c4043')
            gear_btn.configure(state='normal')
            armed=bool(snap.get('native_armed'))
            start_btn.configure(text="ARMED" if armed else "ARM",
                                state="disabled" if armed else "normal",
                                bg="#188038" if armed else "#174ea6",
                                activebackground="#137333" if armed else "#1967d2")
            destination_ready=(snap.get("native_phase") in
                               ("BASELINED","IDLE","EXECUTING","DELIVERING"))
            go_btn.configure(text="GO…" if go_state["busy"] else
                             ("GO ✓" if go_state["ready"] and snap["online"] and
                              armed and destination_ready else
                              "WAIT" if go_state["waiting"] and not destination_ready else "GO"),
                             state="disabled" if go_state["busy"] or not armed or snap.get("native_off")
                                   else "normal",
                             bg="#188038" if armed and not snap.get("native_off") else "#3c4043",
                             activebackground="#137333")
            enabled=bool(snap.get('auto_send'))
            auto_send_btn.configure(text='Auto Send: ON' if enabled else 'Auto Send: OFF',
                                    bg='#137333' if enabled else '#7f1d1d',
                                    activebackground='#188038' if enabled else '#991b1b',state='normal')
            delivery_phase=snap.get('native_delivery_phase')
            force_clear_btn.configure(text="CLEARING…" if clear_busy["value"] else "FORCE CLEAR",
                                      state="disabled" if clear_busy["value"] or
                                            snap.get("native_phase")=="DELIVERING" else "normal")
            force_command_btn.configure(state='normal' if delivery_phase=='PRE_SUBMIT_FAILED' else 'disabled')
            force_abort_btn.configure(state='normal' if delivery_phase in ('READY','PRE_SUBMIT_FAILED') else 'disabled')
            clear_queue_check.configure(state='normal')
            title.configure(text=snap['title'],fg=colors.get(snap.get('title_phase',snap['title']),GOOD))
            relay.configure(text=snap['backend']); browser.configure(text=snap['browser'])
            phase.configure(text=snap['phase']); action.configure(text=snap['action'][:86])
            preview.configure(text=snap['preview']); set_details(snap['exact'])
            root.after(1000,refresh)
            return
        gear_btn.configure(state='disabled')
        start_btn.configure(text="START",state="normal",bg="#174ea6",
                            activebackground="#1967d2")
        go_btn.configure(text="GO",state="disabled",bg="#3c4043")
        startup_check.configure(state='disabled')
        settings_startup_check.configure(state='disabled')
        auto_send_btn.configure(text='Auto Send: OFF',bg='#7f1d1d',activebackground='#991b1b',state='disabled')
        force_clear_btn.configure(text="FORCE CLEAR",state='disabled')
        force_command_btn.configure(state='disabled'); force_abort_btn.configure(state='disabled'); clear_queue_check.configure(state='disabled')
        if isinstance(snap.get("conversation_lock_enabled"),bool):
            lock_state["enabled"]=snap["conversation_lock_enabled"]
        elif not snap["online"]:
            lock_state["enabled"]=None
        if lock_state["busy"]:
            label="OWNER LOCK: CONFIRM..."
        elif lock_state["error"]:
            label="OWNER LOCK: ERROR"
        elif lock_state["enabled"] is None:
            label="OWNER LOCK: ?"
        else:
            label="OWNER LOCK: "+("ON" if lock_state["enabled"] else "OFF")
        owner_lock_btn.configure(text=label,state="disabled" if lock_state["busy"] or lock_state["enabled"] is None else "normal",
                                 bg="#5f2120" if lock_state["enabled"] else "#3c4043")
        title.configure(text=snap["title"],fg=colors.get(snap.get("title_phase",snap["title"]),GOOD))
        relay.configure(text=snap["backend"]); browser.configure(text=snap["browser"])
        phase.configure(text=snap["phase"]); action.configure(text=snap["action"][:86])
        preview.configure(text=snap["preview"])
        set_details(snap["exact"])
        root.after(1000,refresh)
    refresh(); root.mainloop(); return 0

def main(argv=None):
    ap=argparse.ArgumentParser(description="Command Courier — original Windows HUD")
    ap.add_argument("--once",action="store_true",help="print one JSON snapshot and exit")
    ns=ap.parse_args(argv)
    if ns.once:
        print(json.dumps(snapshot(),ensure_ascii=True,separators=(",",":")))
        return 0
    return run_ui()

if __name__=="__main__":raise SystemExit(main())

# GPT_RELAY_HUD_LIFECYCLE_V1
# GPT_RELAY_HUD_EXACT_INSTRUCTION_V1
# GPT_RELAY_HUD_STALL_REASON_V1
