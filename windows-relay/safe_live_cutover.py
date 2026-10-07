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
DEFAULT_CUTOVER_TIMEOUT = 45
DEFAULT_ROLLBACK_TIMEOUT = 25
DEFAULT_WAKE_TIMEOUT = 8
_RUN_DEADLINE = None

def set_run_deadline(seconds=None):
    global _RUN_DEADLINE
    _RUN_DEADLINE=None if seconds is None else time.monotonic()+max(0.0,float(seconds))

def budget_left(cap=60):
    if _RUN_DEADLINE is None: return float(cap)
    return max(0.0,min(float(cap),_RUN_DEADLINE-time.monotonic()))

def run(args, cwd=None, timeout=60):
    effective=float(timeout)
    if _RUN_DEADLINE is not None:
        left=_RUN_DEADLINE-time.monotonic()
        if left<=0: raise TimeoutError('operation budget exhausted')
        effective=min(effective,max(0.2,left))
    return subprocess.run([str(x) for x in args], cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=effective, check=False)

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
    critical=['content.js','extension/manifest.json','extension/content.js','extension/service_worker.js','extension-persistent/manifest.json','extension-persistent/content.js','extension-persistent/service_worker.js','windows_relay.py','windows_outbound_worker.py','firefox_adapter.py','firefox_tab_adapter.ps1','relay-control.ps1','relay-watchdog-loop.ps1','relay-watchdog.ps1','hud.py']
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
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    p=subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(live/'relay-watchdog-loop.ps1')],cwd=str(live),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
    time.sleep(0.5)
    if p.poll() is not None: raise RuntimeError('watchdog exited immediately code='+str(p.returncode))
    return p.pid

def wait_hud(py: Path, live: Path, timeout_seconds=20):
    deadline=time.time()+timeout_seconds
    while time.time()<deadline:
        p=run([py,live/'hud.py','--once'],live,20)
        if p.returncode==0: return
        time.sleep(0.5)
    raise RuntimeError('HUD health timeout')

def hud_process_count(live: Path) -> int:
    ps=r"@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^pythonw(.exe)?$' -and $_.CommandLine -and $_.CommandLine -match '(?i)Client\\Relay.*hud\.py' }).Count"
    p=run(['powershell','-NoProfile','-Command',ps],timeout=8)
    if p.returncode: raise RuntimeError('HUD process query failed: '+(p.stderr or p.stdout or '')[-800:])
    try: return int((p.stdout or '0').strip().splitlines()[-1])
    except Exception as exc: raise RuntimeError('HUD process query returned invalid count') from exc

def wait_hud_process(live: Path, timeout_seconds=10):
    deadline=time.time()+timeout_seconds
    while time.time()<deadline:
        count=hud_process_count(live)
        if count==1: return
        if count>1: raise RuntimeError('multiple HUD processes observed: '+str(count))
        time.sleep(0.25)
    raise RuntimeError('HUD GUI process not observed')

def event_line_count(events: Path) -> int:
    if not events.is_file(): return 0
    return len(events.read_text(encoding='utf-8',errors='replace').splitlines())

def wait_v17(events: Path, timeout_seconds=45, start_line=0) -> str:
    deadline=time.time()+timeout_seconds
    while time.time()<deadline:
        if events.is_file():
            lines=events.read_text(encoding='utf-8',errors='replace').splitlines()
            for line in reversed(lines[max(0,int(start_line)):]):
                try: row=json.loads(line)
                except Exception: continue
                if row.get('event')!='content_script_started': continue
                d=row.get('detail') if isinstance(row.get('detail'),dict) else {}
                runtime=str(d.get('runtime') or '')
                if 'delivery-v17-whole-stop-v1' in runtime and 'owner-v1' in runtime: return runtime
        time.sleep(0.25)
    raise RuntimeError('fresh v17 owner runtime not observed')

def write_report(path: Path, payload: dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    os.replace(tmp,path)

def start_legacy_hud(live: Path):
    pyw=live/'.venv'/'Scripts'/'pythonw.exe'; hud=live/'hud.py'
    p=subprocess.Popen([str(pyw),str(hud)],cwd=str(live),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(0.35)
    if p.poll() is not None: raise RuntimeError('legacy HUD exited immediately with code '+str(p.returncode))
    wait_hud_process(live,5)
    return p.pid

def wake(py: Path, live: Path, firefox_pid: int, message: str):
    p=run([py,live/'firefox_adapter.py','send-chatgpt-prompt','--prompt-text',message,'--firefox-pid',str(firefox_pid)],live,45)
    if p.returncode:
        raise RuntimeError('wake prompt failed: '+(p.stderr or p.stdout or '')[-1200:])
    try:
        data=json.loads((p.stdout or '').strip())
    except Exception as exc:
        raise RuntimeError('wake prompt returned invalid JSON') from exc
    if data.get('ok') is not True or data.get('action')!='send-chatgpt-prompt' or data.get('confirmed') is not True:
        raise RuntimeError('wake prompt not confirmed: '+json.dumps(data,ensure_ascii=False)[:1200])
    return data

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--packet-id',required=True)
    ap.add_argument('--backup',required=True,type=Path)
    ap.add_argument('--canonical',required=True,type=Path)
    ap.add_argument('--live',required=True,type=Path)
    ap.add_argument('--chat-contains',default='PC Engineering 8')
    ap.add_argument('--task-name',default=DEFAULT_TASK_NAME)
    ap.add_argument('--gate-timeout',type=int,default=45)
    ap.add_argument('--grace-seconds',type=int,default=5)
    ap.add_argument('--cutover-timeout',type=int,default=DEFAULT_CUTOVER_TIMEOUT)
    ap.add_argument('--rollback-timeout',type=int,default=DEFAULT_ROLLBACK_TIMEOUT)
    ap.add_argument('--wake-timeout',type=int,default=DEFAULT_WAKE_TIMEOUT)
    ns=ap.parse_args()
    local=Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData'/'Local'))
    state=local/'GPTWindowsRelay';events=state/'browser-events.jsonl'
    log=state/(ns.packet_id+'-cutover.jsonl');report=state/(ns.packet_id+'-cutover-report.json')
    py=ns.live/'.venv'/'Scripts'/'python.exe';mutated=False;firefox_pid=None;steps=[]
    outcome={'ok':False,'error':'helper did not finalize','steps':steps}
    def note(step,**kw):
        row={'time':time.time(),'step':step,**kw};steps.append(row);append_jsonl(log,row)
    def best_effort(label,fn):
        try: fn();note(label,ok=True);return True
        except BaseException as e: note(label,ok=False,error=type(e).__name__+': '+str(e));return False
    try:
        note('helper_started')
        if not wait_for_send_accepted(events,ns.packet_id,ns.gate_timeout): raise RuntimeError('relay_result_send_accepted not observed')
        note('send_accepted_observed');time.sleep(max(0,min(ns.grace_seconds,10)))
        if not canonical_matches(ns.live,ns.canonical): raise RuntimeError('live tree is not staged canonical')
        set_run_deadline(ns.cutover_timeout);mutated=True
        restart_backend(ns.live);note('backend_restarted')
        kill_matching('watchdog');kill_matching('hud');start_watchdog(ns.live);wait_hud(py,ns.live,min(12,max(1,int(budget_left(12)))));wait_hud_process(ns.live,min(8,max(1,int(budget_left(8)))));note('hud_rotated')
        firefox_pid=discover_firefox_pid(py,ns.live)
        baseline=event_line_count(events)
        reload_existing_addon(py,ns.live,firefox_pid,OLD_ADDON_NAME);note('addon_reloaded',pid=firefox_pid,event_baseline=baseline)
        refresh_chat(py,ns.live,firefox_pid,ns.chat_contains);note('chat_refreshed')
        runtime=wait_v17(events,min(20,max(1,int(budget_left(20)))),baseline);note('v17_seen',runtime=runtime)
        if not canonical_matches(ns.live,ns.canonical): raise RuntimeError('post-cutover canonical hash mismatch')
        outcome={'ok':True,'runtime':runtime,'steps':steps}
        write_report(report,outcome);note('success_report_written')
        set_run_deadline(ns.wake_timeout)
        best_effort('success_wake',lambda:wake(py,ns.live,firefox_pid,'[PCE8_AUTOMATION] Safe live cutover completed. Canonical v17 + whole-stop + owner-v1 is live. Continue with the first owner-proof operation.'))
    except BaseException as exc:
        reason=type(exc).__name__+': '+str(exc);note('failed',error=reason)
        rollback_errors=[]
        if mutated:
            set_run_deadline(ns.rollback_timeout);note('rollback_started',budget_seconds=ns.rollback_timeout)
            try: restore_snapshot(ns.live,ns.backup);note('rollback_files_restored')
            except BaseException as e: rollback_errors.append('files:'+repr(e));note('rollback_files_failed',error=repr(e))
            best_effort('rollback_backend_restart',lambda:restart_backend(ns.live))
            try:
                exact=snapshot_matches(ns.live,ns.backup);note('rollback_snapshot_verified',exact=exact)
                if not exact: rollback_errors.append('snapshot_hash_mismatch')
            except BaseException as e: rollback_errors.append('verify:'+repr(e));note('rollback_verify_failed',error=repr(e))
            best_effort('rollback_stop_watchdog',lambda:kill_matching('watchdog'))
            best_effort('rollback_stop_hud',lambda:kill_matching('hud'))
            best_effort('rollback_watchdog_started',lambda:start_watchdog(ns.live))
            best_effort('rollback_hud_ready',lambda:wait_hud_process(ns.live,min(8,max(1,int(budget_left(8))))))
            try:
                firefox_pid=discover_firefox_pid(py,ns.live);note('rollback_firefox_discovered',pid=firefox_pid)
                loaded=False
                for name in (NEW_ADDON_NAME,OLD_ADDON_NAME):
                    try:
                        reload_existing_addon(py,ns.live,firefox_pid,name);note('rollback_addon_reloaded',name=name);loaded=True;break
                    except BaseException as e: note('rollback_addon_reload_attempt_failed',name=name,error=repr(e))
                if not loaded: rollback_errors.append('addon_reload_failed')
                best_effort('rollback_chat_refreshed',lambda:refresh_chat(py,ns.live,firefox_pid,ns.chat_contains))
            except BaseException as e: rollback_errors.append('firefox:'+repr(e));note('rollback_firefox_failed',error=repr(e))
        outcome={'ok':False,'error':reason,'rollback_errors':rollback_errors,'steps':steps}
        set_run_deadline(None);write_report(report,outcome);note('failure_report_written')
        if firefox_pid:
            set_run_deadline(ns.wake_timeout)
            best_effort('failure_wake',lambda:wake(py,ns.live,firefox_pid,'[PCE8_AUTOMATION] Safe live cutover failed; rollback is finalized or bounded. Inspect the cutover report before another runtime mutation.'))
    finally:
        set_run_deadline(None)
        note('helper_finalizing')
        try:
            p=subprocess.run(['schtasks','/Delete','/TN',ns.task_name,'/F'],text=True,capture_output=True,timeout=5,check=False)
            note('task_cleanup',returncode=p.returncode)
        except BaseException as e: note('task_cleanup_failed',error=repr(e))
        outcome['steps']=steps
        try: write_report(report,outcome)
        except BaseException as e: append_jsonl(log,{'time':time.time(),'step':'final_report_failed','error':repr(e)})
    return 0

if __name__=='__main__': raise SystemExit(main())
