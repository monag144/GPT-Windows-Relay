from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

OLD_ADDON_NAME = "GPT Windows Relay"
NEW_ADDON_NAME = "GPT One-Click Go Relay"
DEFAULT_TASK_NAME = "GPTWindowsRelay-SafeLiveCutover"

def run(args, cwd=None, timeout=60):
    return subprocess.run([str(x) for x in args], cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout, check=False)

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def append_jsonl(path: Path, row: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a",encoding="utf-8") as f: f.write(json.dumps(row,ensure_ascii=False)+"\n")

def event_matches_send_accepted(path: Path, packet_id: str) -> bool:
    if not path.is_file(): return False
    for line in reversed(path.read_text(encoding="utf-8",errors="replace").splitlines()[-2500:]):
        try: row=json.loads(line)
        except Exception: continue
        if row.get("event") != "relay_result_send_accepted": continue
        detail=row.get("detail") if isinstance(row.get("detail"),dict) else {}
        if detail.get("packet_id") == packet_id: return True
    return False

def wait_for_send_accepted(path: Path, packet_id: str, timeout_seconds: int) -> bool:
    deadline=time.time()+timeout_seconds
    while time.time()<deadline:
        if event_matches_send_accepted(path,packet_id): return True
        time.sleep(0.25)
    return event_matches_send_accepted(path,packet_id)

def restore_snapshot(live: Path, backup: Path):
    manifest=json.loads((backup/'manifest.json').read_text(encoding='utf-8'))
    for rec in manifest:
        dst=live/rec['rel']; src=backup/'files'/rec['rel']
        if rec['existed'] and src.is_file():
            dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
        elif not rec['existed'] and dst.exists(): dst.unlink()

def snapshot_matches(live: Path, backup: Path) -> bool:
    manifest=json.loads((backup/'manifest.json').read_text(encoding='utf-8'))
    for rec in manifest:
        dst=live/rec['rel']
        if rec['existed']:
            if not dst.is_file() or sha256(dst)!=rec['before_sha']: return False
        elif dst.exists(): return False
    return True

def canonical_matches(live: Path, canonical: Path) -> bool:
    critical=['content.js','extension/content.js','extension/service_worker.js','extension-persistent/content.js','extension-persistent/service_worker.js','windows_relay.py','windows_outbound_worker.py','firefox_adapter.py','firefox_tab_adapter.ps1','relay-control.ps1','relay-watchdog-loop.ps1','relay-watchdog.ps1','hud.py']
    return all((canonical/r).is_file() and (live/r).is_file() and sha256(canonical/r)==sha256(live/r) for r in critical)

def discover_firefox_pid(py: Path, live: Path) -> int:
    p=run([py,live/'firefox_adapter.py','list-tabs'],live,30)
    if p.returncode: raise RuntimeError('Firefox list-tabs failed: '+(p.stderr or p.stdout or '')[-1200:])
    data=json.loads((p.stdout or '').strip().splitlines()[-1])
    return int(data['firefox_pid'])

def reload_existing_addon(py: Path, live: Path, firefox_pid: int, addon_name: str):
    p=run([py,live/'firefox_adapter.py','reload-addon','--addon-name',addon_name,'--firefox-pid',str(firefox_pid)],live,45)
    if p.returncode: raise RuntimeError('reload-addon failed: '+(p.stderr or p.stdout or '')[-1200:])

def refresh_chat(py: Path, live: Path, firefox_pid: int, chat_contains: str):
    p=run([py,live/'firefox_adapter.py','refresh-tab','--contains',chat_contains,'--firefox-pid',str(firefox_pid)],live,30)
    if p.returncode: raise RuntimeError('ChatGPT refresh failed: '+(p.stderr or p.stdout or '')[-1200:])

def restart_backend(live: Path):
    p=run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',live/'relay-control.ps1','restart'],live,60)
    if p.returncode: raise RuntimeError('relay restart failed: '+(p.stderr or p.stdout or '')[-1600:])

def kill_matching(kind: str):
    if kind=='hud':
        name='^pythonw(.exe)?$'; match=r'(?i)Client\\Relay.*hud\.py'
    else:
        name='^powershell(.exe)?$'; match=r'(?i)Client\\Relay\\relay-watchdog-loop\.ps1'
    ps="Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.Name -match '"+name+"' -and $_.CommandLine -and $_.CommandLine -match '"+match+"'}|ForEach-Object{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}"
    run(['powershell','-NoProfile','-Command',ps],timeout=25)

def start_watchdog(live: Path):
    root=str(live).replace("'","''"); wd=str(live/'relay-watchdog-loop.ps1').replace("'","''")
    ps="$r='"+root+"';$w='"+wd+"';Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $r -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('\\\"'+$w+'\\\"'))|Out-Null"
    p=run(['powershell','-NoProfile','-Command',ps],timeout=25)
    if p.returncode: raise RuntimeError('watchdog launch failed')

def wait_hud(py: Path, live: Path, timeout_seconds=20):
    deadline=time.time()+timeout_seconds
    while time.time()<deadline:
        p=run([py,live/'hud.py','--once'],live,20)
        if p.returncode==0: return
        time.sleep(0.5)
    raise RuntimeError('HUD health timeout')

def wait_v17(events: Path, timeout_seconds=45) -> str:
    deadline=time.time()+timeout_seconds
    while time.time()<deadline:
        if events.is_file():
            for line in reversed(events.read_text(encoding='utf-8',errors='replace').splitlines()[-1800:]):
                try: row=json.loads(line)
                except Exception: continue
                if row.get('event')!='content_script_started': continue
                d=row.get('detail') if isinstance(row.get('detail'),dict) else {}
                runtime=str(d.get('runtime') or '')
                if 'delivery-v17-whole-stop-v1' in runtime and 'owner-v1' in runtime: return runtime
        time.sleep(0.5)
    raise RuntimeError('v17 owner runtime not observed')

def wake(py: Path, live: Path, firefox_pid: int, message: str):
    run([py,live/'firefox_adapter.py','send-chatgpt-prompt','--prompt-text',message,'--firefox-pid',str(firefox_pid)],live,45)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--packet-id',required=True)
    ap.add_argument('--backup',required=True,type=Path)
    ap.add_argument('--canonical',required=True,type=Path)
    ap.add_argument('--live',required=True,type=Path)
    ap.add_argument('--chat-contains',default='PC Engineering 8')
    ap.add_argument('--task-name',default=DEFAULT_TASK_NAME)
    ap.add_argument('--gate-timeout',type=int,default=120)
    ap.add_argument('--grace-seconds',type=int,default=10)
    ns=ap.parse_args()
    local=Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData'/'Local'))
    state=local/'GPTWindowsRelay'; events=state/'browser-events.jsonl'
    log=state/(ns.packet_id+'-cutover.jsonl'); report=state/(ns.packet_id+'-cutover-report.json')
    py=ns.live/'.venv'/'Scripts'/'python.exe'; mutated=False; firefox_pid=None; steps=[]
    def note(step,**kw):
        row={'time':time.time(),'step':step,**kw}; steps.append(row); append_jsonl(log,row)
    try:
        note('helper_started')
        if not wait_for_send_accepted(events,ns.packet_id,ns.gate_timeout): raise RuntimeError('relay_result_send_accepted not observed')
        note('send_accepted_observed'); time.sleep(ns.grace_seconds)
        if not canonical_matches(ns.live,ns.canonical): raise RuntimeError('live tree is not staged canonical')
        mutated=True; restart_backend(ns.live); note('backend_restarted')
        kill_matching('watchdog'); kill_matching('hud'); start_watchdog(ns.live); wait_hud(py,ns.live); note('hud_rotated')
        firefox_pid=discover_firefox_pid(py,ns.live)
        reload_existing_addon(py,ns.live,firefox_pid,OLD_ADDON_NAME); note('addon_reloaded',pid=firefox_pid)
        refresh_chat(py,ns.live,firefox_pid,ns.chat_contains); note('chat_refreshed')
        runtime=wait_v17(events); note('v17_seen',runtime=runtime)
        if not canonical_matches(ns.live,ns.canonical): raise RuntimeError('post-cutover canonical hash mismatch')
        report.write_text(json.dumps({'ok':True,'runtime':runtime,'steps':steps},indent=2),encoding='utf-8')
        wake(py,ns.live,firefox_pid,'[PCE8_AUTOMATION] Safe live cutover completed. Canonical v17 + whole-stop + owner-v1 is live. Continue with the first owner-proof operation.')
    except Exception as exc:
        reason=type(exc).__name__+': '+str(exc); note('failed',error=reason)
        if mutated:
            try:
                restore_snapshot(ns.live,ns.backup); restart_backend(ns.live); note('snapshot_restored')
                kill_matching('watchdog'); kill_matching('hud'); run(['cmd','/c',ns.live/'START-HUD.bat'],ns.live,20)
                firefox_pid=discover_firefox_pid(py,ns.live)
                for name in (NEW_ADDON_NAME,OLD_ADDON_NAME):
                    p=run([py,ns.live/'firefox_adapter.py','reload-addon','--addon-name',name,'--firefox-pid',str(firefox_pid)],ns.live,45)
                    if p.returncode==0: break
                refresh_chat(py,ns.live,firefox_pid,ns.chat_contains)
                if not snapshot_matches(ns.live,ns.backup): note('rollback_hash_warning')
            except Exception as rb: note('rollback_failed',error=repr(rb))
        report.write_text(json.dumps({'ok':False,'error':reason,'steps':steps},indent=2),encoding='utf-8')
        if firefox_pid:
            wake(py,ns.live,firefox_pid,'[PCE8_AUTOMATION] Safe live cutover failed; rollback was attempted. Inspect the cutover report before another runtime mutation.')
    finally:
        run(['schtasks','/Delete','/TN',ns.task_name,'/F'],timeout=20)
    return 0

if __name__=='__main__': raise SystemExit(main())
