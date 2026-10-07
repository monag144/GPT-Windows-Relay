from pathlib import Path
import shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[1]
ROLLBACK = Path.home() / "Downloads" / "Dev" / "GPT" / "Client" / "Relay" / "rollback" / f"PCE7.445-hud-state-machine-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
FILES = [
    "hud.py",
    "relay-control.ps1",
    "relay-watchdog-loop.ps1",
    "sync-live.py",
    "tests/test_hud.py",
]

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def write(rel, text):
    (ROOT / rel).write_text(text, encoding="utf-8", newline="\n")

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {n}")
    return text.replace(old, new, 1)

def backup():
    if ROLLBACK.exists():
        raise RuntimeError(f"rollback exists: {ROLLBACK}")
    for rel in FILES:
        src = ROOT / rel
        if not src.is_file():
            raise RuntimeError(f"missing source file: {src}")
        dst = ROLLBACK / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print(f"BACKUP={ROLLBACK}")

def restore():
    for rel in FILES:
        src = ROLLBACK / rel
        dst = ROOT / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    print("ROLLBACK_COMPLETE")

def run(cmd):
    print("RUN:", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)

RELAY_CONTROL = r'''param([ValidateSet('status','start','stop','restart','pause','resume','off','kill')][string]$Action='status')
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$pause=Join-Path $root '.relay-paused'
$off=Join-Path $root '.relay-off'
$kill=Join-Path $root '.relay-kill'
$killHud=Join-Path $root '.relay-kill-hud'
$starting=Join-Path $root '.relay-starting'
$killFailed=Join-Path $root '.relay-kill-failed'
$disconnectReason=Join-Path $root '.relay-disconnect-reason'
$run=Join-Path $root 'run.ps1'
$watchdog=Join-Path $root 'relay-watchdog-loop.ps1'

function Listener {
  Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
}
function GenuineSupervisors {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^powershell(.exe)?$' -and
    $_.CommandLine -match '(?i)-File\s+"?[^"]*\\run\.ps1"?(\s|$)'
  })
}
function GenuineWatchdogs {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^powershell(.exe)?$' -and
    $_.CommandLine -match '(?i)-File\s+"?[^"]*\\relay-watchdog-loop\.ps1"?(\s|$)'
  })
}
function GenuineHudProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^pythonw(.exe)?$' -and
    $_.CommandLine -match '(?i)(^|\s)"?[^"]*hud\.py"?(\s|$)'
  })
}
function GenuineRelayProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -ieq 'GPTWindowsRelay.exe' -or
    ($_.CommandLine -and $_.CommandLine -match '(?i)(^|\s)"?[^"]*windows_relay\.py"?(\s|$)')
  })
}
function KillTree($items) {
  foreach($p in @($items)){
    if($p.ProcessId -and $p.ProcessId -ne $PID){
      taskkill /PID $p.ProcessId /T /F | Out-Null
    }
  }
}
function KillHudOnly {
  foreach($p in @(GenuineHudProcesses)){
    if($p.ProcessId -and $p.ProcessId -ne $PID){
      taskkill /PID $p.ProcessId /F | Out-Null
    }
  }
}
function WriteReason([string]$Text) {
  Set-Content -LiteralPath $disconnectReason -Value $Text -Encoding UTF8
}
function StopBackend {
  New-Item -ItemType File -Force -Path $pause | Out-Null
  $l=Listener
  if($l){taskkill /PID $l.OwningProcess /T /F | Out-Null}
  KillTree (GenuineRelayProcesses)
  KillTree (GenuineSupervisors)
  Start-Sleep -Milliseconds 500
  $after=Listener
  return -not [bool]$after
}
function StartSupervisor {
  if(-not (Listener) -and (GenuineSupervisors).Count -eq 0){
    Start-Process powershell.exe -WindowStyle Normal -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('\"'+$run+'\"')) | Out-Null
  }
}
function StartWatchdog {
  if((GenuineWatchdogs).Count -eq 0 -and (Test-Path -LiteralPath $watchdog)){
    Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('\"'+$watchdog+'\"')) | Out-Null
  }
}
function WaitListener([int]$Seconds=10) {
  $deadline=(Get-Date).AddSeconds($Seconds)
  while((Get-Date) -lt $deadline){
    $l=Listener
    if($l){return $l}
    Start-Sleep -Milliseconds 500
  }
  return $null
}

if($Action -eq 'status'){
  $l=Listener
  if(Test-Path $killFailed){Write-Output ('STATE=KILL_FAILED REASON='+(Get-Content $killFailed -Raw).Trim());exit}
  if(Test-Path $killHud){Write-Output 'STATE=KILLING_HUD';exit}
  if(Test-Path $kill){Write-Output 'STATE=KILLING_RELAY';exit}
  if(Test-Path $off){Write-Output 'STATE=OFF';exit}
  if(Test-Path $pause){Write-Output 'STATE=STOPPED';exit}
  if(Test-Path $starting){Write-Output 'STATE=STARTING';exit}
  if($l){Write-Output ('STATE=RUNNING PID='+$l.OwningProcess);exit}
  Write-Output 'STATE=DISCONNECTED REASON=port 8766 not listening'
  exit
}

if($Action -in @('stop','pause')){
  Remove-Item $off,$kill,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  if(-not (StopBackend)){WriteReason 'port 8766 remained listening after stop';throw 'relay backend did not stop'}
  if($Action -eq 'stop'){Write-Output 'STOPPED'}else{Write-Output 'PAUSED'}
  exit
}

if($Action -eq 'off'){
  Remove-Item $kill,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $off | Out-Null
  if(-not (StopBackend)){WriteReason 'port 8766 remained listening during OFF';throw 'relay backend did not stop'}
  KillTree (GenuineWatchdogs)
  Write-Output 'OFF'
  exit
}

if($Action -eq 'kill'){
  Remove-Item $off,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $pause | Out-Null
  New-Item -ItemType File -Force -Path $kill | Out-Null
  Start-Sleep -Milliseconds 1400
  $backendDead=StopBackend
  KillTree (GenuineWatchdogs)
  Start-Sleep -Milliseconds 300
  $remainingRelay=(GenuineRelayProcesses).Count
  $remainingSup=(GenuineSupervisors).Count
  $remainingWatchdog=(GenuineWatchdogs).Count
  if((-not $backendDead) -or $remainingRelay -gt 0 -or $remainingSup -gt 0 -or $remainingWatchdog -gt 0){
    $liveListener=Listener
    $reason='kill verification failed: listener='+([bool]$liveListener)+' relay='+$remainingRelay+' supervisor='+$remainingSup+' watchdog='+$remainingWatchdog
    Set-Content -LiteralPath $killFailed -Value $reason -Encoding UTF8
    Write-Output ('KILL_FAILED '+$reason)
    exit 1
  }
  New-Item -ItemType File -Force -Path $killHud | Out-Null
  Start-Sleep -Milliseconds 1400
  KillHudOnly
  Write-Output 'KILLED'
  exit
}

if($Action -eq 'restart'){
  Remove-Item $off,$kill,$killHud,$killFailed,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $starting | Out-Null
  [void](StopBackend)
  Remove-Item $pause -Force -ErrorAction SilentlyContinue
  StartWatchdog
  StartSupervisor
  $l=WaitListener 10
  Remove-Item $starting -Force -ErrorAction SilentlyContinue
  if($l){Write-Output ('RUNNING PID='+$l.OwningProcess);exit}
  WriteReason 'port 8766 not listening after restart timeout'
  Write-Output 'DISCONNECTED'
  exit 1
}

if($Action -in @('start','resume')){
  Remove-Item $pause,$off,$kill,$killHud,$killFailed,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $starting | Out-Null
  StartWatchdog
  StartSupervisor
  $l=WaitListener 10
  Remove-Item $starting -Force -ErrorAction SilentlyContinue
  if($l){Write-Output ('RUNNING PID='+$l.OwningProcess);exit}
  WriteReason 'port 8766 not listening after start timeout'
  Write-Output 'DISCONNECTED'
  exit 1
}
'''

WATCHDOG = r'''$ErrorActionPreference='SilentlyContinue'
$root=$PSScriptRoot
$logDir=Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log=Join-Path $logDir 'watchdog.log'
$pause=Join-Path $root '.relay-paused'
$off=Join-Path $root '.relay-off'
$kill=Join-Path $root '.relay-kill'
$run=Join-Path $root 'run.ps1'
$hudPy=Join-Path $root '.venv\Scripts\pythonw.exe'
$hud=Join-Path $root 'hud.py'
# GPT_RELAY_WATCHDOG_HUD_RECONCILIATION_V1
# GPT_RELAY_WATCHDOG_OPERATOR_INTENT_V2
function Log([string]$m){Add-Content -LiteralPath $log -Value ((Get-Date -Format o)+' '+$m)}
function Listener {Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1}
function GenuineSupervisors {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^powershell(.exe)?$' -and
    $_.CommandLine -match '(?i)-File\s+"?[^"]*\\run\.ps1"?(\s|$)'
  })
}
function GenuineHudProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^pythonw(.exe)?$' -and
    $_.CommandLine -match '(?i)(^|\s)"?[^"]*hud\.py"?(\s|$)'
  })
}
function EnsureHud {
  if(-not (Test-Path -LiteralPath $hudPy) -or -not (Test-Path -LiteralPath $hud)){Log 'HUD_LAUNCH_FILES_MISSING';return}
  if((GenuineHudProcesses).Count -gt 0){return}
  Log 'HUD_MISSING starting HUD'
  Start-Process -FilePath $hudPy -WindowStyle Hidden -WorkingDirectory $root -ArgumentList @(('\"' + $hud + '\"')) | Out-Null
}
$created=$false
$mutex=[System.Threading.Mutex]::new($true,'Local\GPTWindowsRelayWatchdog',[ref]$created)
if(-not $created){Log ('WATCHDOG_DUPLICATE_EXIT pid='+$PID);$mutex.Dispose();exit 0}
try {
  Log ('WATCHDOG_START pid='+$PID)
  while($true){
    if(Test-Path -LiteralPath $kill){Log 'WATCHDOG_KILL_LATCH_EXIT';break}
    if(Test-Path -LiteralPath $off){Log 'WATCHDOG_OFF_LATCH_EXIT';break}
    EnsureHud # GPT_RELAY_WATCHDOG_HUD_RECONCILE_CALL_V1
    if(Test-Path -LiteralPath $pause){Start-Sleep -Seconds 2;continue}
    if(Listener){Start-Sleep -Seconds 5;continue}
    $sup=GenuineSupervisors
    if($sup.Count -eq 0){
      Log 'NO_LISTENER_NO_SUPERVISOR starting VISIBLE supervisor'
      Start-Process powershell.exe -WindowStyle Normal -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('\"'+$run+'\"')) | Out-Null
      Start-Sleep -Seconds 5
    } else {
      Log ('NO_LISTENER supervisor_present count='+$sup.Count+' waiting_for_internal_recovery')
      Start-Sleep -Seconds 5
    }
  }
} finally {
  try{$mutex.ReleaseMutex()}catch{}
  $mutex.Dispose()
  Log ('WATCHDOG_EXIT pid='+$PID)
}
'''

def patch_hud():
    text = read("hud.py")
    text = replace_once(
        text,
        'import argparse,ctypes,json,os,re,subprocess,tkinter as tk,urllib.request',
        'import argparse,ctypes,json,os,re,socket,subprocess,tkinter as tk,urllib.request',
        "hud import",
    )
    text = replace_once(
        text,
        'W,COMPACT_H,EXPANDED_H=460,154,356',
        'W,COMPACT_H,EXPANDED_H=560,184,386',
        "hud dimensions",
    )
    old_control = '''# GPT_RELAY_HUD_OPERATOR_STOP_START_V1
def relay_control(action):
    if action not in {"start","stop"}:raise ValueError("unsupported relay control")
    script=Path(__file__).with_name("relay-control.ps1")
    if not script.is_file():raise FileNotFoundError(script)
    flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if os.name=="nt" else 0
    subprocess.Popen(
        ["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(script),action],
        cwd=str(script.parent),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=flags
    )
'''
    new_control = '''# GPT_RELAY_HUD_OPERATOR_CONTROL_V2
def relay_control(action):
    if action not in {"start","stop","restart","off","kill"}:raise ValueError("unsupported relay control")
    script=Path(__file__).with_name("relay-control.ps1")
    if not script.is_file():raise FileNotFoundError(script)
    flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if os.name=="nt" else 0
    subprocess.Popen(
        ["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(script),action],
        cwd=str(script.parent),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=flags
    )
'''
    text = replace_once(text, old_control, new_control, "hud relay_control")
    request_block = '''def request(path,timeout=.65):
    c=cfg(); token=c.get("token"); port=int(c.get("port",8766))
    if not token:raise RuntimeError("pairing unavailable")
    q=urllib.request.Request(f"http://127.0.0.1:{port}{path}",headers={"X-GPT-Windows-Relay-Token":str(token)})
    with urllib.request.urlopen(q,timeout=timeout) as r:return json.loads(r.read().decode())
'''
    helpers = request_block + '''
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

def backend_disconnect_reason(exc=None,root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parent
    saved=marker_text(".relay-disconnect-reason",root)
    if saved:return saved
    c=cfg(); port=int(c.get("port",8766))
    try:
        with socket.create_connection(("127.0.0.1",port),timeout=.20):pass
    except OSError:
        return f"port {port} not listening"
    if exc:return f"status endpoint unavailable • {type(exc).__name__}"
    return "backend unavailable"
'''
    text = replace_once(text, request_block, helpers, "hud helper insertion")
    text = replace_once(text, '    if not online:return "OFFLINE"', '    if not online:return "DISCONNECTED"', "hud headline offline")

    snap_start = text.index("def snapshot():")
    snap_end = text.index("\ndef acquire_mutex():", snap_start)
    new_snapshot = '''def snapshot():
    state=read_json(L/"state.json",{"processed":{}})
    events=recent_events()
    backend_exc=None
    try:
        status=request("/status"); online=bool(status.get("ok")); armed=bool(status.get("armed"))
        pending=int(status.get("pending_missions",0))
        backend=f"Relay {'ONLINE' if online else 'OFFLINE'} • {'ARMED' if armed else 'DISARMED'} • pending {pending}"
    except Exception as exc:
        backend_exc=exc
        online=False; armed=False; pending=0
        backend=f"Relay DISCONNECTED • {backend_disconnect_reason(exc)}"
    browser=browser_state(events)
    life=lifecycle(events,state)
    detail,is_active=action_detail(state)
    intent=control_state()
    title_phase=headline(online,life,browser) if intent=="RUNNING" else intent
    phase_age=life.get("age")
    phase_line=f"{life['phase']} • {life['reason']}"
    if phase_age is not None:phase_line+=f" • {phase_age}s"

    if intent=="STOPPED":
        backend="Relay STOPPED • operator stop"
        phase_line="STOPPED • operator requested stop"
    elif intent=="OFF":
        backend="Relay OFF • backend and watchdog intentionally shut down"
        phase_line="OFF • operator shutdown"
    elif intent=="STARTING":
        backend="Relay STARTING • waiting for port 8766"
        phase_line="STARTING • launching watchdog and backend"
    elif intent=="KILLING RELAY":
        backend="Relay KILLING • force-stopping backend, supervisor and watchdog"
        phase_line="KILLING RELAY • emergency shutdown in progress"
    elif intent=="KILLING HUD":
        backend="Relay KILLED • closing HUD"
        phase_line="KILLING HUD • final shutdown stage"
    elif intent=="KILL FAILED":
        reason=marker_text(".relay-kill-failed") or "verification failed"
        backend=f"Relay KILL FAILED • {reason}"
        phase_line=f"KILL FAILED • {reason}"
    elif not online:
        reason=backend_disconnect_reason(backend_exc)
        backend=f"Relay DISCONNECTED • {reason}"
        phase_line=f"DISCONNECTED • {reason}"

    bid=str(browser.get("browser_id") or "browser").title()
    age=browser.get("age")
    browser_line=f"{bid} {browser['state']} • {browser['event']} • {age if age is not None else '?'}s"
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
        "phase":phase_line,"action":action_line,"preview":preview,"exact":exact,"intent":intent,
    }
'''
    text = text[:snap_start] + new_snapshot + text[snap_end:]

    text = replace_once(
        text,
        'def run_ui():\n    mutex=acquire_mutex()',
        'def run_ui():\n    if (Path(__file__).with_name(".relay-kill")).exists() and not (Path(__file__).with_name(".relay-kill-failed")).exists():return 0\n    mutex=acquire_mutex()',
        "hud kill latch startup",
    )
    old_buttons_start = '    toggle=tk.Button(top,text="▾"'
    old_buttons_end = '    relay=tk.Label(panel,text="Relay …"'
    s = text.index(old_buttons_start)
    e = text.index(old_buttons_end, s)
    new_buttons = '''    toggle=tk.Button(top,text="▾",font=("Segoe UI",9,"bold"),bg=PANEL,fg=MUTED,activebackground="#303134",
                     activeforeground=FG,bd=0,highlightthickness=0,padx=5,pady=0,cursor="hand2")
    toggle.pack(side="right")
    min_btn=tk.Button(top,text="—",font=("Segoe UI",9,"bold"),bg=PANEL,fg=MUTED,activebackground="#303134",
                      activeforeground=FG,bd=0,highlightthickness=0,padx=7,pady=0,cursor="hand2")
    min_btn.pack(side="right",padx=(0,3))

    controls=tk.Frame(panel,bg=PANEL); controls.pack(fill="x",pady=(4,2))
    start_btn=tk.Button(controls,text="START",font=("Segoe UI",8,"bold"),bg="#174ea6",fg=FG,activebackground="#1967d2",
                        activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",
                        command=lambda:relay_control("start"))
    start_btn.pack(side="left",padx=(0,3))
    stop_btn=tk.Button(controls,text="STOP",font=("Segoe UI",8,"bold"),bg="#5f2120",fg=FG,activebackground="#7a2e2b",
                       activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",
                       command=lambda:relay_control("stop"))
    stop_btn.pack(side="left",padx=3)
    restart_btn=tk.Button(controls,text="RESTART",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,activebackground="#5f6368",
                          activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",
                          command=lambda:relay_control("restart"))
    restart_btn.pack(side="left",padx=3)
    off_btn=tk.Button(controls,text="OFF",font=("Segoe UI",8,"bold"),bg="#3c4043",fg=FG,activebackground="#5f6368",
                      activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",
                      command=lambda:relay_control("off"))
    off_btn.pack(side="left",padx=3)
    kill_btn=tk.Button(controls,text="KILL",font=("Segoe UI",8,"bold"),bg="#7f1d1d",fg=FG,activebackground="#991b1b",
                       activeforeground=FG,bd=0,highlightthickness=0,padx=8,pady=1,cursor="hand2",
                       command=lambda:relay_control("kill"))
    kill_btn.pack(side="left",padx=3)
'''
    text = text[:s] + new_buttons + text[e:]

    marker = '    # GPT_RELAY_HUD_NO_HIDDEN_RIGHT_CLICK_EXIT_V1'
    minimize = '''    def minimize_hud():
        save()
        try:
            root.overrideredirect(False)
            root.iconify()
        except tk.TclError:pass
    def restore_borderless(_e=None):
        try:
            if root.state()=="normal":root.after(20,lambda:root.overrideredirect(True))
        except tk.TclError:pass
    min_btn.configure(command=minimize_hud)
    root.bind("<Map>",restore_borderless)

'''
    text = replace_once(text, marker, minimize + marker, "hud minimize insertion")
    old_colors = '    colors={"OFFLINE":BAD,"STALLED":BAD,"RECOVERING":WARN,"APPROVAL REQUIRED":BAD,"RECOVERY ADVICE":WARN,"RECOVERY INVALID":BAD,"WAITING":WARN,"WAITING FOR GPT TURN END":WARN,"DELIVERING":WARN,"RESULT READY":WARN,"STARTING":WARN,"DISCOVERED":WARN,"RUNNING":GOOD,"READY":GOOD,"PAUSED":WARN}'
    new_colors = '    colors={"DISCONNECTED":BAD,"KILL FAILED":BAD,"KILLING RELAY":BAD,"KILLING HUD":BAD,"OFF":MUTED,"STOPPED":WARN,"STALLED":BAD,"RECOVERING":WARN,"APPROVAL REQUIRED":BAD,"RECOVERY ADVICE":WARN,"RECOVERY INVALID":BAD,"WAITING":WARN,"WAITING FOR GPT TURN END":WARN,"DELIVERING":WARN,"RESULT READY":WARN,"STARTING":WARN,"DISCOVERED":WARN,"RUNNING":GOOD,"READY":GOOD}'
    text = replace_once(text, old_colors, new_colors, "hud colors")
    write("hud.py", text)

def patch_sync_live():
    text = read("sync-live.py")
    old = '''    "hud.py",
    "START-HUD.bat",
    "windows_relay.py",
'''
    new = '''    "hud.py",
    "START-HUD.bat",
    "START-RELAY.bat",
    "STOP-RELAY.bat",
    "relay-control.ps1",
    "relay-watchdog-loop.ps1",
    "run.ps1",
    "windows_relay.py",
'''
    text = replace_once(text, old, new, "sync-live control plane")
    write("sync-live.py", text)

def patch_tests():
    text = read("tests/test_hud.py")
    start = text.index(" def test_operator_stop_is_presented_as_stopped")
    end = text.index("\n\nif __name__=='__main__':unittest.main()", start)
    replacement = r''' def test_operator_control_state_machine(self):
  from pathlib import Path
  from tempfile import TemporaryDirectory
  with TemporaryDirectory() as d:
   root=Path(d)
   self.assertEqual(hud.control_state(root),'RUNNING')
   (root/'.relay-starting').touch(); self.assertEqual(hud.control_state(root),'STARTING'); (root/'.relay-starting').unlink()
   (root/'.relay-paused').touch(); self.assertEqual(hud.control_state(root),'STOPPED'); (root/'.relay-paused').unlink()
   (root/'.relay-off').touch(); self.assertEqual(hud.control_state(root),'OFF'); (root/'.relay-off').unlink()
   (root/'.relay-kill').touch(); self.assertEqual(hud.control_state(root),'KILLING RELAY')
   (root/'.relay-kill-hud').touch(); self.assertEqual(hud.control_state(root),'KILLING HUD')
   (root/'.relay-kill-failed').write_text('verification failed',encoding='utf-8'); self.assertEqual(hud.control_state(root),'KILL FAILED')

 def test_no_backend_is_disconnected(self):
  self.assertEqual(hud.headline(False,{'phase':'READY'},{'state':'ACTIVE'}),'DISCONNECTED')

 def test_hud_exposes_start_stop_restart_off_kill_and_minimize(self):
  from pathlib import Path
  source=(Path(hud.__file__).resolve().parent/'hud.py').read_text(encoding='utf-8')
  for action in ('start','stop','restart','off','kill'):
   self.assertIn(f'command=lambda:relay_control("{action}")',source)
  self.assertIn('min_btn.configure(command=minimize_hud)',source)
  self.assertIn('root.iconify()',source)
  self.assertIn('KILLING RELAY',source)
  self.assertIn('KILLING HUD',source)
  self.assertIn('DISCONNECTED',source)

 def test_control_plane_supports_intent_and_hard_kill(self):
  from pathlib import Path
  root=Path(hud.__file__).resolve().parent
  control=(root/'relay-control.ps1').read_text(encoding='utf-8')
  self.assertIn("'off','kill'",control)
  for marker in ('.relay-off','.relay-kill','.relay-kill-hud','.relay-starting','.relay-kill-failed'):
   self.assertIn(marker,control)
  self.assertIn('function GenuineWatchdogs',control)
  self.assertIn('function GenuineRelayProcesses',control)
  self.assertIn("Write-Output 'OFF'",control)
  self.assertIn("Write-Output 'KILLED'",control)
  self.assertIn("Write-Output 'DISCONNECTED'",control)

 def test_watchdog_respects_off_and_kill_before_hud_reconcile(self):
  from pathlib import Path
  text=(Path(hud.__file__).resolve().parent/'relay-watchdog-loop.ps1').read_text(encoding='utf-8')
  call='EnsureHud # GPT_RELAY_WATCHDOG_HUD_RECONCILE_CALL_V1'
  self.assertLess(text.index("if(Test-Path -LiteralPath $kill)"),text.index(call))
  self.assertLess(text.index("if(Test-Path -LiteralPath $off)"),text.index(call))
  self.assertIn('WATCHDOG_KILL_LATCH_EXIT',text)
  self.assertIn('WATCHDOG_OFF_LATCH_EXIT',text)

 def test_sync_live_deploys_entire_control_plane(self):
  from pathlib import Path
  text=(Path(hud.__file__).resolve().parent/'sync-live.py').read_text(encoding='utf-8')
  for rel in ('START-RELAY.bat','STOP-RELAY.bat','relay-control.ps1','relay-watchdog-loop.ps1','run.ps1'):
   self.assertIn(f'"{rel}"',text)
'''
    text = text[:start] + replacement + text[end:]
    write("tests/test_hud.py", text)

def main():
    head = subprocess.check_output([r"C:\Program Files\Git\cmd\git.exe","rev-parse","HEAD"], cwd=ROOT, text=True).strip()
    if not head:
        raise RuntimeError("unable to resolve HEAD")
    status = subprocess.check_output([r"C:\Program Files\Git\cmd\git.exe","status","--porcelain"], cwd=ROOT, text=True)
    if status.strip():
        raise RuntimeError("working tree is not clean before PCE7.445")
    backup()
    try:
        write("relay-control.ps1", RELAY_CONTROL)
        write("relay-watchdog-loop.ps1", WATCHDOG)
        patch_hud()
        patch_sync_live()
        patch_tests()
        py = Path.home() / "Downloads" / "Dev" / "GPT" / "Client" / "Relay" / ".venv" / "Scripts" / "python.exe"
        run([str(py), "-m", "unittest", "discover", "-s", "tests", "-p", "test_hud.py", "-q"])
        run([str(py), "-m", "unittest", "discover", "-s", "tests", "-q"])
        run([r"C:\Program Files\Git\cmd\git.exe", "diff", "--check"])
        print("PCE7.445_SOURCE_GREEN")
        subprocess.run([r"C:\Program Files\Git\cmd\git.exe","status","--short","--"] + FILES, cwd=ROOT, check=False)
    except Exception:
        restore()
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"PCE7.445_FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
