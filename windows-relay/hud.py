#!/usr/bin/env python3
from __future__ import annotations
import argparse,ctypes,json,os,re,subprocess,tkinter as tk,urllib.request
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
        "relay_packet_discovered","relay_packet_settle_stale_rearmed","relay_recovery_packet_seen","relay_scanner_stalled",
        "relay_page_refresh_requested","relay_result_delivery_complete","relay_engineering_action_render_collapsed"
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
    "relay_packet_settle_stale_rearmed":("RECOVERING","stale settle lease expired; packet re-armed"),
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
    "relay_engineering_action_render_collapsed":("RENDER COLLAPSED","PCE action presentation collapsed; execution unverified, replay blocked"),
    "relay_page_refresh_requested":("RECOVERING","refreshing ChatGPT after forced reinspection failed"),
    "chatgpt_tool_approval_prompt_detected":("APPROVAL REQUIRED","ChatGPT is waiting for tool approval"),
    "gpt_recovery_advice_observed":("RECOVERY ADVICE","bounded GPT recovery advice visible; awaiting supervisor claim"),
    "gpt_recovery_advice_invalid":("RECOVERY INVALID","invalid recovery advice visible; bounded coaching required"),
    "browser_integration_disconnected":("STALLED","browser integration disconnected"),
    "content_port_connected":("READY","content script connected"),
    "content_script_started":("READY","content script started"),
}

# GPT_WINDOWS_DISCOVERY_STALL_AGE_GATE_V1
DISCOVERY_STALL_SECONDS=45

def lifecycle(events,state,now=None):
    now=now or datetime.now(timezone.utc)
    active=state.get("active_action")
    if isinstance(active,dict) and active.get("id"):
        return {"phase":"RUNNING","reason":"Windows process executing","packet_id":active.get("id"),
                "age":age_seconds(active.get("started_at"),now),"event":"backend_inflight"}
    relevant=[e for e in events if e.get("event") in PHASES]
    if not relevant:return {"phase":"READY","reason":"no active relay operation","packet_id":None,"age":None,"event":"none"}
    e=relevant[-1]; phase,reason=PHASES[e.get("event")]
    event_age=age_seconds(e.get("time"),now)
    if phase=="DISCOVERED" and event_age is not None and event_age>=DISCOVERY_STALL_SECONDS:
        phase="STALLED"
        reason="discovered packet not executed after "+str(int(event_age))+"s; recovery evidence required"
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
def relay_control(action):
    if action not in {"start","stop","restart","retry","off","kill"}:raise ValueError("unsupported relay control")
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
    if life["phase"] in {"WAITING","WAITING FOR GPT TURN END","DELIVERING","RESULT READY","STARTING","DISCOVERED","REPLAY SUPPRESSED","APPROVAL REQUIRED","RECOVERY ADVICE","RECOVERY INVALID","RENDER COLLAPSED"}:return life["phase"]
    if browser["state"]=="DISCONNECTED":return "STALLED"
    return "READY"

def snapshot():
    state=read_json(L/"state.json",{"processed":{}})
    events=recent_events()
    try:
        status=request("/status"); online=bool(status.get("ok")); armed=bool(status.get("armed"))
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
        "phase":phase_line,"action":action_line,"preview":preview,"exact":exact,
    }

def acquire_mutex():
    if os.name!="nt":return 1
    k=ctypes.windll.kernel32; h=k.CreateMutexW(None,False,"Local\\GPTWindowsRelayHUD")
    return None if (not h or k.GetLastError()==183) else h

def run_ui():
    # Keep the HUD available to show kill/offline state; only the relay is stopped by its latch.
    mutex=acquire_mutex()
    if os.name=="nt" and mutex is None:return 0
    root=tk.Tk(); root.title("GPT Relay HUD"); root.overrideredirect(True); root.resizable(False,False)
    root.attributes("-topmost",True); root.configure(bg=BG)
    try:root.attributes("-alpha",0.97)
    except tk.TclError:pass
    pos=read_json(POS,{})
    sw=root.winfo_screenwidth()
    if int(pos.get("layout_version",0) or 0)>=HUD_LAYOUT_VERSION:
        x=int(pos.get("x",max(12,sw-W-18))); y=int(pos.get("y",18))
    else:
        x=max(12,sw-W-18); y=18
    expanded=False
    root.geometry(f"{W}x{COMPACT_H}+{x}+{y}")

    panel=tk.Frame(root,bg=PANEL,highlightbackground=BORDER,highlightthickness=1,padx=12,pady=7)
    panel.pack(fill="both",expand=True)
    top=tk.Frame(panel,bg=PANEL); top.pack(fill="x")
    title=tk.Label(top,text="READY",font=("Segoe UI",12,"bold"),bg=PANEL,fg=GOOD,anchor="w")
    title.pack(side="left",fill="x",expand=True)
    toggle=tk.Button(top,text="▾",font=("Segoe UI",9,"bold"),bg=PANEL,fg=MUTED,activebackground="#303134",
                     activeforeground=FG,bd=0,highlightthickness=0,padx=5,pady=0,cursor="hand2")
    toggle.pack(side="right")
    min_btn=tk.Button(top,text="—",font=("Segoe UI",9,"bold"),bg=PANEL,fg=MUTED,activebackground="#303134",activeforeground=FG,bd=0,highlightthickness=0,padx=7,pady=0,cursor="hand2")
    min_btn.pack(side="right",padx=(0,3))
    controls=tk.Frame(panel,bg=PANEL); controls.pack(fill="x",pady=(4,2))
    start_btn=tk.Button(controls,text="START",font=("Segoe UI",8,"bold"),bg="#174ea6",fg=FG,activebackground="#1967d2",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("start")); start_btn.pack(side="left",padx=(0,3))
    stop_btn=tk.Button(controls,text="STOP",font=("Segoe UI",8,"bold"),bg="#5f2120",fg=FG,activebackground="#7a2e2b",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("stop")); stop_btn.pack(side="left",padx=3)
    restart_btn=tk.Button(controls,text="RESTART",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,activebackground="#5f6368",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("restart")); restart_btn.pack(side="left",padx=3)
    retry_btn=tk.Button(controls,text="RETRY",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,activebackground="#5f6368",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("retry")); retry_btn.pack(side="left",padx=3)
    off_btn=tk.Button(controls,text="OFF",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,activebackground="#5f6368",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("off")); off_btn.pack(side="left",padx=3)
    kill_btn=tk.Button(controls,text="KILL",font=("Segoe UI",8,"bold"),bg="#7f1d1d",fg=FG,activebackground="#991b1b",activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",command=lambda:relay_control("kill")); kill_btn.pack(side="left",padx=3)
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

    details_frame=tk.Frame(panel,bg=PANEL)
    details=tk.Text(details_frame,height=10,wrap="word",font=("Consolas",8),bg="#17181a",fg=FG,
                    insertbackground=FG,relief="flat",padx=7,pady=6)
    details.pack(fill="both",expand=True)
    details.configure(state="disabled")

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

    def set_details(text):
        details.configure(state="normal"); details.delete("1.0","end"); details.insert("1.0",text or "No relay instruction available.")
        details.configure(state="disabled")

    def toggle_details():
        nonlocal expanded
        expanded=not expanded
        if expanded:
            details_frame.pack(fill="both",expand=True,pady=(7,0))
            toggle.configure(text="▴")
            root.geometry(f"{W}x{EXPANDED_H}+{root.winfo_x()}+{root.winfo_y()}")
        else:
            details_frame.pack_forget(); toggle.configure(text="▾")
            root.geometry(f"{W}x{COMPACT_H}+{root.winfo_x()}+{root.winfo_y()}")
    toggle.configure(command=toggle_details)

    colors={"OFFLINE":BAD,"DISCONNECTED":BAD,"KILL FAILED":BAD,"KILLING RELAY":BAD,"KILLING HUD":BAD,"OFF":MUTED,"STOPPED":WARN,"STALLED":BAD,"RECOVERING":WARN,"APPROVAL REQUIRED":BAD,"RECOVERY ADVICE":WARN,"RECOVERY INVALID":BAD,"WAITING":WARN,"WAITING FOR GPT TURN END":WARN,"DELIVERING":WARN,"RESULT READY":WARN,"STARTING":WARN,"DISCOVERED":WARN,"REPLAY SUPPRESSED":WARN,"RUNNING":GOOD,"READY":GOOD,"PAUSED":WARN}
    def refresh():
        snap=snapshot()
        title.configure(text=snap["title"],fg=colors.get(snap.get("title_phase",snap["title"]),GOOD))
        relay.configure(text=snap["backend"]); browser.configure(text=snap["browser"])
        phase.configure(text=snap["phase"]); action.configure(text=snap["action"][:86])
        preview.configure(text=snap["preview"])
        set_details(snap["exact"])
        root.after(1000,refresh)
    refresh(); root.mainloop(); return 0

def main(argv=None):
    ap=argparse.ArgumentParser(description="GPT Windows Relay HUD")
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
