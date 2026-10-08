#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, binascii, copy, hashlib, json, os, re, secrets, shutil, subprocess, sys, tempfile, threading, time, xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

VERSION=1
OPEN='[GPT_WINDOWS_ACTION]'; CLOSE='[/GPT_WINDOWS_ACTION]'
RO='[GPT_WINDOWS_RESULT]'; RC='[/GPT_WINDOWS_RESULT]'
SANDWICH_REMINDER='Reply to this with the sandwich technique'
TURN_DISCIPLINE_REMINDER='MANDATORY NEXT TURN: READ consumer/control_harness.py; READ windows-relay/TASKS.md; READ docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md; READ docs/windows-relay-mission-and-roadmap.md; verify all Windows Relay mutation targets monag144/GPT-Windows-Relay; USE the sandwich technique for every relay action; if you find a harness hole, repair and test the harness before risky mutation.'
FIVE_TURN_AUDIT_REMINDER='FIVE-TURN AUDIT DUE NOW: audit the preceding five engineering turns/operations for harness compliance, incidents/user rescues, repeated or disproven approaches, repository destination, test evidence, rollback discipline, and roadmap drift before continuing.'
OPERATION_DISCIPLINE_REMINDER='Before the next operation: read the canonical source-of-truth index, control harness, TODO list, roadmap, established facts, and relevant incident/handoff records; prove net-new progress; log failures/manual rescues; preserve rollback before mutation; enforce the active PCE series budget (000 through 100 inclusive) and rotate before 101; do not repeat a disproven approach.'
ID_RE=re.compile(r'^[A-Za-z0-9._:-]{1,128}$')
BROWSER_ID_RE=re.compile(r'^[A-Za-z0-9._-]{1,64}$')
PACKET_RE=re.compile(re.escape(OPEN)+r'\s*(\{.*?\})\s*'+re.escape(CLOSE),re.DOTALL)
MAX_CMD=20000; MAX_OUT=30000; PREVIEW_OUT=1800; PREVIEW_ERR=1200; MAX_TIMEOUT=300; DEFAULT_PORT=8766
MAX_MISSION_TEXT=60000; MAX_PENDING_MISSIONS=8
BROWSER_HEARTBEAT_TTL_SECONDS=45.0
MANAGED_SCREENSHOT_RE=re.compile(r'^screenshot-[0-9]{8}T[0-9]{6}-[0-9]{9}\.png$'); MAX_SCREENSHOT_BYTES=12*1024*1024

class RelayError(Exception): pass
class PacketError(RelayError): pass

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def cfg_dir(): return Path(os.environ.get('APPDATA',Path.home()/'.config'))/'GPTWindowsRelay'
def state_dir(): return Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local/state'))/'GPTWindowsRelay'

ATOMIC_REPLACE_ATTEMPTS=8
ATOMIC_REPLACE_BASE_DELAY=0.025
TRANSIENT_REPLACE_WINERRORS={5,32,33}

def _transient_replace_error(e:OSError)->bool:
    return isinstance(e,PermissionError) or getattr(e,'winerror',None) in TRANSIENT_REPLACE_WINERRORS

def atomic_json(path:Path,data:dict[str,Any]):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=str(path.parent),text=True)
    tmp_path=Path(tmp)
    replaced=False
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
        for attempt in range(ATOMIC_REPLACE_ATTEMPTS):
            try:
                os.replace(tmp_path,path)
                replaced=True
                break
            except OSError as e:
                if not _transient_replace_error(e) or attempt+1>=ATOMIC_REPLACE_ATTEMPTS:
                    raise
                delay=min(0.5,ATOMIC_REPLACE_BASE_DELAY*(2**attempt))
                print(f'ATOMIC_REPLACE_RETRY path={path.name} attempt={attempt+1} delay={delay:.3f} error={type(e).__name__}:{str(e)[:160]}',flush=True)
                time.sleep(delay)
        if not replaced:
            raise RelayError(f'atomic replace failed for {path.name}')
    finally:
        if not replaced:
            try: tmp_path.unlink()
            except FileNotFoundError: pass
            except OSError: pass

@dataclass(frozen=True)
class Action:
    id:str; session:str; shell:str; command:str; cwd:str|None; timeout:int; result_mode:str; canonical:str
    @property
    def hash(self): return hashlib.sha256(self.canonical.encode()).hexdigest()

def extract(text:str)->Action:
    start=text.find(OPEN); end=text.rfind(CLOSE)
    if start<0 or end<0 or end<=start: raise PacketError('expected exactly one GPT_WINDOWS_ACTION packet')
    if text[:start].strip() or text[end+len(CLOSE):].strip(): raise PacketError('unexpected text outside GPT_WINDOWS_ACTION packet')
    body=text[start+len(OPEN):end].strip()
    try: p=json.loads(body)
    except json.JSONDecodeError as e: raise PacketError(f'invalid JSON: {e}') from e
    if not isinstance(p,dict): raise PacketError('packet JSON must be an object')
    if p.get('version')!=1: raise PacketError('version must be 1')
    if p.get('platform')!='windows': raise PacketError("platform must be exactly 'windows'")
    if str(p.get('action','')).upper()!='EXEC': raise PacketError('only EXEC is supported')
    aid=p.get('id'); session=p.get('session','default')
    if not isinstance(aid,str) or not ID_RE.fullmatch(aid): raise PacketError('invalid id')
    if not isinstance(session,str) or not ID_RE.fullmatch(session): raise PacketError('invalid session')
    cmd=p.get('command'); b64=p.get('command_b64'); lines=p.get('command_lines')
    sources=sum(v is not None for v in (cmd,b64,lines))
    if sources!=1: raise PacketError('provide exactly one of command, command_b64, or command_lines')
    if b64 is not None:
        if not isinstance(b64,str): raise PacketError('command_b64 must be a string')
        try: cmd=base64.b64decode(b64,validate=True).decode('utf-8')
        except (binascii.Error,UnicodeDecodeError,ValueError) as e: raise PacketError('invalid command_b64') from e
    elif lines is not None:
        if not isinstance(lines,list) or not lines or any(not isinstance(line,str) for line in lines):
            raise PacketError('command_lines must be a non-empty array of strings')
        cmd='\n'.join(lines)
    if not isinstance(cmd,str) or not cmd.strip(): raise PacketError('command is required')
    if len(cmd)>MAX_CMD: raise PacketError(f'command exceeds {MAX_CMD} characters')
    shell=str(p.get('shell','powershell')).lower()
    if shell not in {'powershell','pwsh','cmd','python'}: raise PacketError('unsupported shell')
    cwd=p.get('cwd')
    if cwd is not None and (not isinstance(cwd,str) or not cwd.strip()): raise PacketError('invalid cwd')
    timeout=p.get('timeout',60)
    if isinstance(timeout,bool) or not isinstance(timeout,int) or not 1<=timeout<=MAX_TIMEOUT: raise PacketError('invalid timeout')
    result_mode=str(p.get('result_mode','compact')).lower()
    if result_mode not in {'compact','full'}: raise PacketError("result_mode must be 'compact' or 'full'")
    return Action(aid,session,shell,cmd,cwd,timeout,result_mode,json.dumps(p,sort_keys=True,separators=(',',':')))

class State:
    def __init__(self,path:Path):
        self.path=path; self.lock=threading.Lock(); self.browser_seen={}; self.browser_integration={}; self.mission_journal_path=path.with_name('consumer-mission-journal.jsonl'); self.mission_journal_lock=threading.Lock(); self.data={'version':1,'armed':True,'processed':{},'missions':[],'active_action':None,'last_action':None,'updated_at':now()}; self.load()
    def load(self):
        if self.path.exists():
            self.data=json.loads(self.path.read_text(encoding='utf-8'))
            if self.data.get('version')!=1 or not isinstance(self.data.get('processed'),dict): raise RelayError('corrupt state file')
        missions=self.data.setdefault('missions',[])
        if not isinstance(missions,list) or any(not isinstance(x,dict) for x in missions): raise RelayError('corrupt mission queue')
        self.data.setdefault('stop_generation',0)
        self.data.setdefault('browser_quiesced_generation',0)
        owner=self.data.setdefault('outbound_owner','browser')
        if owner not in {'browser','windows'}: raise RelayError('corrupt outbound owner')
        # Any INFLIGHT reservation found during process startup belonged to a
        # previous relay process. Do not re-execute it automatically because
        # the interrupted command may already have produced side effects.
        for v in self.data.get('processed',{}).values():
            if isinstance(v,dict) and v.get('status')=='INFLIGHT':
                v['status']='INTERRUPTED_RESTART'
                v['finished_at']=now()
        self.data.setdefault('active_action',None)
        self.data.setdefault('last_action',None)
        outbound=self.data.setdefault('outbound_deliveries',{})
        if not isinstance(outbound,dict) or any(not isinstance(k,str) or not isinstance(v,dict) for k,v in outbound.items()): raise RelayError('corrupt outbound delivery state')
        valid_phases={'READY','SUBMITTING','PRE_SUBMIT_FAILED','SUBMITTED','SUBMIT_UNCERTAIN'}
        for delivery in outbound.values():
            phase=delivery.get('phase')
            if phase not in valid_phases: raise RelayError('corrupt outbound delivery phase')
            if phase=='SUBMITTING':
                delivery['phase']='SUBMIT_UNCERTAIN'
                delivery['updated_at']=now()
                delivery['restart_recovery']='interrupted_while_submitting'
        self.data['active_action']=None
        self.data['armed']=True; self.save()
    def save(self): atomic_json(self.path,self.data)
    def _mutate_and_save(self,mutate):
        before=copy.deepcopy(self.data)
        mutate()
        try:
            self.save()
        except Exception:
            self.data=before
            raise
    @property
    def outbound_owner(self): return self.data.get('outbound_owner','browser')
    @property
    def armed(self): return bool(self.data.get('armed'))
    def set_armed(self,v:bool):
        with self.lock:
            generation=int(self.data.get('stop_generation',0) or 0)
            def mutate():
                nonlocal generation
                if not v:
                    generation+=1
                    self.data['stop_generation']=generation
                self.data['armed']=v; self.data['updated_at']=now()
            self._mutate_and_save(mutate)
            return generation

    def ack_browser_quiesced(self,generation):
        if type(generation) is not int or generation<=0: return False
        with self.lock:
            current=int(self.data.get('stop_generation',0) or 0)
            if bool(self.data.get('armed')) or generation!=current: return False
            def mutate():
                self.data['browser_quiesced_generation']=generation
                self.data['updated_at']=now()
            self._mutate_and_save(mutate)
            return True

    def operator_stop_status(self):
        with self.lock:
            return {'stop_generation':int(self.data.get('stop_generation',0) or 0),'browser_quiesced_generation':int(self.data.get('browser_quiesced_generation',0) or 0)}
    def lookup(self,aid):
        v=self.data['processed'].get(aid); return v if isinstance(v,dict) else None
    def outbound_lookup(self,aid):
        v=self.data.get('outbound_deliveries',{}).get(aid); return copy.deepcopy(v) if isinstance(v,dict) else None
    def list_claimable_outbound_ids(self):
        # Read-only discovery for the dormant Windows outbound worker.
        # Persisted JSON key order is not a delivery ordering contract, so
        # use created_at + action id for deterministic behavior across restart.
        with self.lock:
            if not bool(self.data.get('armed')): return []
            if self.data.get('outbound_owner','browser')!='windows': return []
            eligible=[]
            for aid,delivery in self.data.get('outbound_deliveries',{}).items():
                if not isinstance(aid,str) or not isinstance(delivery,dict): continue
                if delivery.get('phase') not in {'READY','PRE_SUBMIT_FAILED'}: continue
                if delivery.get('has_attachments') is not False: continue
                eligible.append((str(delivery.get('created_at') or ''),aid))
            eligible.sort(key=lambda item:(item[0],item[1]))
            return [aid for _,aid in eligible]
    def reserve(self,a:Action):
        with self.lock:
            def mutate():
                started=now()
                self.data['processed'][a.id]={'payload_hash':a.hash,'session':a.session,'status':'INFLIGHT','started_at':started}
                self.data['active_action']={
                    'id':a.id,'session':a.session,'shell':a.shell,'cwd':a.cwd,
                    'timeout':a.timeout,'command':a.command,'status':'INFLIGHT','started_at':started
                }
            self._mutate_and_save(mutate)
    def mark(self,a:Action,r:dict[str,Any]):
        with self.lock:
            saved=r.get('saved_result_path')
            if not isinstance(saved,str) or not saved: raise RelayError('saved result path required before outbound journal')
            deliveries=self.data.setdefault('outbound_deliveries',{})
            existing=deliveries.get(a.id)
            if existing is not None and (not isinstance(existing,dict) or existing.get('payload_hash')!=a.hash): raise RelayError('outbound delivery id collision')
            wire_result_path=save_outbound_wire_result(self,a.id,result(r))
            def mutate():
                self.data['processed'][a.id]={'payload_hash':a.hash,'session':a.session,'status':r['status'],'exit_code':r.get('exit_code'),'finished_at':r['finished_at'],'saved_result_path':saved}
                deliveries=self.data.setdefault('outbound_deliveries',{})
                existing=deliveries.get(a.id)
                if existing is None:
                    created=now()
                    deliveries[a.id]={'id':a.id,'payload_hash':a.hash,'session':a.session,'saved_result_path':saved,'wire_result_path':wire_result_path,'result_mode':a.result_mode,'has_attachments':bool(r.get('attachments')),'phase':'READY','created_at':created,'updated_at':created}
                elif not isinstance(existing,dict) or existing.get('payload_hash')!=a.hash:
                    raise RelayError('outbound delivery id collision')
                active=self.data.get('active_action')
                finished={'id':a.id,'session':a.session,'shell':a.shell,'cwd':a.cwd,'timeout':a.timeout,'command':a.command,'status':r['status'],'exit_code':r.get('exit_code'),'finished_at':r['finished_at']}
                self.data['last_action']=finished
                if isinstance(active,dict) and active.get('id')==a.id:self.data['active_action']=None
                while len(self.data['processed'])>500:
                    removable=None
                    for candidate in self.data['processed']:
                        delivery=deliveries.get(candidate)
                        if not isinstance(delivery,dict) or delivery.get('phase') in {'SUBMITTED','SUBMIT_UNCERTAIN'}:
                            removable=candidate; break
                    if removable is None: break
                    self.data['processed'].pop(removable,None)
            self._mutate_and_save(mutate)

    def claim_outbound_delivery(self,aid:str):
        with self.lock:
            claimed=None
            def mutate():
                nonlocal claimed
                if not self.armed: raise RelayError('relay disarmed')
                if self.outbound_owner!='windows': raise RelayError('windows outbound owner required')
                delivery=self.data.get('outbound_deliveries',{}).get(aid)
                if not isinstance(delivery,dict): raise RelayError('outbound delivery unavailable')
                if delivery.get('phase') not in {'READY','PRE_SUBMIT_FAILED'}: raise RelayError('outbound delivery not claimable')
                if delivery.get('has_attachments') is not False: raise RelayError('outbound attachments unsupported by windows sender')
                delivery['phase']='SUBMITTING'
                delivery['attempt_count']=int(delivery.get('attempt_count',0) or 0)+1
                delivery['updated_at']=now()
                delivery['submitting_at']=delivery['updated_at']
                claimed=copy.deepcopy(delivery)
            self._mutate_and_save(mutate)
            return claimed

    def finish_outbound_delivery(self,aid:str,phase:str):
        if phase not in {'PRE_SUBMIT_FAILED','SUBMITTED','SUBMIT_UNCERTAIN'}: raise RelayError('invalid outbound sender outcome')
        with self.lock:
            finished=None
            def mutate():
                nonlocal finished
                delivery=self.data.get('outbound_deliveries',{}).get(aid)
                if not isinstance(delivery,dict) or delivery.get('phase')!='SUBMITTING': raise RelayError('outbound delivery is not submitting')
                delivery['phase']=phase
                delivery['updated_at']=now()
                delivery['sender_finished_at']=delivery['updated_at']
                finished=copy.deepcopy(delivery)
            self._mutate_and_save(mutate)
            return finished

    def journal_mission(self,mission_id:str,phase:str,**detail):
        if not isinstance(mission_id,str) or not ID_RE.fullmatch(mission_id): return
        rec={'time':now(),'mission_id':mission_id,'phase':phase}
        rec.update({k:v for k,v in detail.items() if v is not None})
        with self.mission_journal_lock:
            self.mission_journal_path.parent.mkdir(parents=True,exist_ok=True)
            with self.mission_journal_path.open('a',encoding='utf-8') as f:
                f.write(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n'); f.flush(); os.fsync(f.fileno())

    def journal_browser_event(self,event:str,detail):
        if not isinstance(detail,dict): return
        mid=detail.get('mission_id')
        phases={
            'consumer_mission_text_set':'PROMPT_INJECTED',
            'consumer_mission_send_clicked':'PROMPT_SENT',
            'consumer_mission_user_turn_confirmed':'USER_TURN_CONFIRMED',
            'consumer_mission_client_sync_divergence':'CLIENT_SYNC_DIVERGENCE',
            'consumer_mission_delivery_failed':'RECOVERY_REQUIRED',
            'consumer_mission_composer_not_found':'RECOVERY_REQUIRED'
        }
        phase=phases.get(event)
        if phase and isinstance(mid,str):
            safe={k:v for k,v in detail.items() if k not in {'mission_id'} and isinstance(v,(str,int,float,bool,type(None)))}
            self.journal_mission(mid,phase,event=event,**safe)

    def mark_browser_seen(self,browser_id:str,integration_connected:bool|None=None):
        if not isinstance(browser_id,str) or not BROWSER_ID_RE.fullmatch(browser_id):
            raise RelayError('invalid browser id')
        with self.lock:
            self.browser_seen[browser_id]=time.monotonic()
            if integration_connected is not None:
                self.browser_integration[browser_id]=bool(integration_connected)

    def mark_browser_disconnected(self,browser_id:str):
        if not isinstance(browser_id,str) or not BROWSER_ID_RE.fullmatch(browser_id):
            raise RelayError('invalid browser id')
        with self.lock:
            self.browser_seen.pop(browser_id,None)
            self.browser_integration.pop(browser_id,None)

    def browser_status(self,browser_id:str):
        if not isinstance(browser_id,str) or not BROWSER_ID_RE.fullmatch(browser_id):
            raise RelayError('invalid browser id')
        with self.lock:
            seen=self.browser_seen.get(browser_id)
            integration=bool(self.browser_integration.get(browser_id,False))
        if seen is None:
            return {'browser_id':browser_id,'connected':False,'age_seconds':None,'integration_connected':integration}
        age=max(0.0,time.monotonic()-seen)
        connected=integration and age<=BROWSER_HEARTBEAT_TTL_SECONDS
        return {'browser_id':browser_id,'connected':connected,'age_seconds':round(age,3),'integration_connected':integration}

    def enqueue_mission(self,mission_id:str,text:str,target_browser:str|None=None):
        if not isinstance(mission_id,str) or not ID_RE.fullmatch(mission_id):
            raise RelayError('invalid mission id')
        if not isinstance(text,str) or not text.strip():
            raise RelayError('mission text required')
        if len(text)>MAX_MISSION_TEXT:
            raise RelayError(f'mission exceeds {MAX_MISSION_TEXT} characters')
        if target_browser is not None and (
            not isinstance(target_browser,str) or not BROWSER_ID_RE.fullmatch(target_browser)
        ):
            raise RelayError('invalid target browser')
        with self.lock:
            existing=next((x for x in self.data['missions'] if x.get('id')==mission_id),None)
            if existing:
                if existing.get('text')!=text or existing.get('target_browser')!=target_browser:
                    raise RelayError('mission id collision')
                return {'queued':False,'duplicate':True}
            if len(self.data['missions'])>=MAX_PENDING_MISSIONS:
                raise RelayError('mission queue full')
            def mutate():
                self.data['missions'].append({
                    'id':mission_id,
                    'text':text,
                    'target_browser':target_browser,
                    'queued_at':now(),
                })
                self.data['updated_at']=now()
            self._mutate_and_save(mutate)
            self.journal_mission(mission_id,'CREATED',target_browser=target_browser,chars=len(text))
            return {'queued':True,'duplicate':False}

    def next_mission(self,browser_id:str|None=None):
        if browser_id is not None and (
            not isinstance(browser_id,str) or not BROWSER_ID_RE.fullmatch(browser_id)
        ):
            raise RelayError('invalid browser id')
        with self.lock:
            for mission in self.data['missions']:
                target=mission.get('target_browser')
                if browser_id is None:
                    if target is None:
                        return dict(mission)
                elif target in (None,browser_id):
                    return dict(mission)
            return None

    def pending_mission_count(self):
        with self.lock:
            return len(self.data['missions'])

    def ack_mission(self,mission_id:str):
        if not isinstance(mission_id,str) or not ID_RE.fullmatch(mission_id):
            raise RelayError('invalid mission id')
        with self.lock:
            found=any(x.get('id')==mission_id for x in self.data['missions'])
            if not found: return False
            def mutate():
                self.data['missions']=[x for x in self.data['missions'] if x.get('id')!=mission_id]
                self.data['updated_at']=now()
            self._mutate_and_save(mutate)
            self.journal_mission(mission_id,'ACKNOWLEDGED')
            return True

def resolve_cwd(cwd):
    p=Path(os.path.expandvars(os.path.expanduser(cwd or str(Path.home())))).resolve()
    if not p.is_dir(): raise RelayError(f'cwd does not exist: {p}')
    return p

def shell_argv(a:Action):
    if os.name!='nt': raise RelayError('execution requires Windows')
    if a.shell=='python':
        exe=sys.executable
        if not exe or not Path(exe).exists(): raise RelayError('Python runtime not found')
        return [exe,'-X','utf8','-c',a.command]
    if a.shell=='cmd':
        exe=shutil.which('cmd.exe')
        if not exe: raise RelayError('cmd.exe not found')
        return [exe,'/d','/s','/c',a.command]
    exe=shutil.which('pwsh.exe') if a.shell=='pwsh' else (shutil.which('powershell.exe') or shutil.which('pwsh.exe'))
    if not exe: raise RelayError('PowerShell not found')
    prefix='[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false);$OutputEncoding=[System.Text.UTF8Encoding]::new($false);'
    enc=base64.b64encode((prefix+a.command).encode('utf-16le')).decode('ascii')
    return [exe,'-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',enc]

def trim(s,limit):
    return (s,False) if len(s)<=limit else (s[:limit]+f'\n...[relay truncated {len(s)-limit} characters]...',True)

def filter_powershell_progress_clixml(s, shell):
    if shell not in {"powershell","pwsh"}:
        return s
    marker="#< CLIXML"
    pos=s.rfind(marker)
    if pos<0:
        return s
    prefix=s[:pos]
    xml=s[pos+len(marker):].lstrip("\r\n")
    try:
        root=ET.fromstring(xml)
    except ET.ParseError:
        return s
    removed=False
    for r in list(root):
        if r.tag.rsplit("}",1)[-1]=="Obj" and r.attrib.get("S","").lower()=="progress":
            root.remove(r)
            removed=True
    if not removed:
        return s
    if not list(root):
        return prefix
    return prefix+marker+"\r\n"+ET.tostring(root,encoding="unicode")

def execute(a:Action):
    cwd=resolve_cwd(a.cwd); started=now(); t=time.monotonic(); code=None; out=''; err=''; status='EXEC_ERROR'
    try:
        proc=subprocess.Popen(shell_argv(a),cwd=str(cwd),stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0))
        try:
            ob,eb=proc.communicate(timeout=a.timeout); code=proc.returncode; status='OK' if code==0 else 'COMMAND_FAILED'
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False); ob,eb=proc.communicate(); status='TIMEOUT'
        out=ob.decode('utf-8',errors='replace'); err=eb.decode('utf-8',errors='replace')
        err=filter_powershell_progress_clixml(err,a.shell)
    except (OSError,RelayError) as e: err=str(e)
    return {'version':1,'platform':'windows','id':a.id,'session':a.session,'action':'EXEC','shell':a.shell,'status':status,'exit_code':code,'cwd':str(cwd),'started_at':started,'finished_at':now(),'duration_ms':int((time.monotonic()-t)*1000),'stdout':out,'stderr':err}

def safe_result_filename(aid:str)->str:
    # Protocol IDs may contain ':' but Windows filenames may not.
    safe=re.sub(r'[^A-Za-z0-9._-]','_',str(aid))
    return safe+'.json'

def save_outbound_wire_result(state:State,aid:str,wire:str)->str:
    if not isinstance(wire,str) or not wire: raise RelayError('outbound wire result required')
    root=state.path.parent/'outbound'; root.mkdir(parents=True,exist_ok=True)
    target=root/(Path(safe_result_filename(aid)).stem+'.txt')
    fd,tmp=tempfile.mkstemp(prefix='.'+target.name+'.',dir=str(root)); tmp=Path(tmp); replaced=False
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(wire.encode('utf-8')); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,target); replaced=True
    finally:
        if not replaced:
            try: tmp.unlink()
            except OSError: pass
    return str(target.resolve())

def validated_outbound_wire_path(state:State,aid:str,delivery:dict[str,Any])->Path:
    value=delivery.get('wire_result_path')
    if not isinstance(value,str) or not value: raise RelayError('outbound wire result unavailable')
    root=(state.path.parent/'outbound').resolve(); path=Path(value).resolve()
    if path.parent!=root or not path.is_file(): raise RelayError('outbound wire result unavailable')
    try: wire=path.read_text(encoding='utf-8')
    except (OSError,UnicodeDecodeError) as exc: raise RelayError('outbound wire result unreadable') from exc
    if not wire or len(wire)>250000 or aid not in wire: raise RelayError('outbound wire result invalid')
    return path

def outbound_result_file(state:State,aid:str)->str:
    delivery=state.outbound_lookup(aid)
    if not isinstance(delivery,dict): raise RelayError('outbound delivery unavailable')
    return str(validated_outbound_wire_path(state,aid,delivery))

def read_outbound_wire_result(state:State,aid:str)->str:
    return Path(outbound_result_file(state,aid)).read_text(encoding='utf-8')

def save_full_result(state:State,r:dict[str,Any])->str:
    results=state.path.parent/'results'
    results.mkdir(parents=True,exist_ok=True)
    path=results/safe_result_filename(str(r['id']))
    payload=dict(r)
    payload['stdout_chars']=len(str(r.get('stdout','')))
    payload['stderr_chars']=len(str(r.get('stderr','')))
    atomic_json(path,payload)
    return str(path.resolve())

def result_attachments(stdout:str)->list[dict[str,str]]:
    found=[]
    for line in reversed(str(stdout).splitlines()):
        try: obj=json.loads(line)
        except (json.JSONDecodeError,TypeError): continue
        a=obj.get("chatgpt_attachment") if isinstance(obj,dict) else None
        if not isinstance(a,dict): continue
        name=a.get("name"); mime=a.get("mime")
        if a.get("kind")=="image" and mime=="image/png" and isinstance(name,str) and MANAGED_SCREENSHOT_RE.fullmatch(name):
            found.append({"kind":"image","name":name,"mime":"image/png"})
            break
    return found

def managed_screenshot_path(state:State,name:str,require_exists:bool=True)->Path:
    if not isinstance(name,str) or not MANAGED_SCREENSHOT_RE.fullmatch(name): raise RelayError("invalid managed screenshot name")
    root=(state.path.parent/"screenshots").resolve(); path=(root/name).resolve()
    if path.parent!=root: raise RelayError("managed screenshot escaped root")
    if require_exists:
        if not path.is_file(): raise RelayError("managed screenshot not found")
        size=path.stat().st_size
        if not 1<=size<=MAX_SCREENSHOT_BYTES: raise RelayError("managed screenshot size invalid")
    return path

def present_result_mode(result_mode:str,r:dict[str,Any],saved_path:str)->dict[str,Any]:
    if result_mode not in {'compact','full'}: raise RelayError('invalid stored result mode')
    out=str(r.get('stdout','')); err=str(r.get('stderr',''))
    if result_mode=='full':
        out_view,ot=trim(out,MAX_OUT); err_view,et=trim(err,MAX_OUT)
    else:
        out_view,ot=trim(out,PREVIEW_OUT); err_view,et=trim(err,PREVIEW_ERR)
    presented=dict(r)
    presented['result_mode']=result_mode
    presented['saved_result_path']=saved_path
    presented['stdout_chars']=len(out)
    presented['stderr_chars']=len(err)
    presented['stdout']=out_view
    presented['stderr']=err_view
    presented['stdout_truncated']=ot
    presented['stderr_truncated']=et
    attachments=result_attachments(out)
    if attachments: presented['attachments']=attachments
    return presented

def present_result(a:Action,r:dict[str,Any],saved_path:str)->dict[str,Any]:
    return present_result_mode(a.result_mode,r,saved_path)

def engineering_operation_ordinal(action_id:Any)->int|None:
    text=str(action_id or '')
    m=re.match(r'^PCE\d+\.(\d+)(?:[A-Za-z]*)?(?:[-.]|$)',text,re.I)
    if not m:
        m=re.match(r'^PCE\d+(?:[-.]BOOT)?[-.]?OP(\d+)(?:[A-Za-z]*)?(?:[-.]|$)',text,re.I)
    if not m:
        return None
    value=int(m.group(1))
    return value if 0<=value<=100 else None

def _turn_discipline_lines(action_id:Any=None)->list[str]:
    lines=[OPERATION_DISCIPLINE_REMINDER,TURN_DISCIPLINE_REMINDER]
    ordinal=engineering_operation_ordinal(action_id)
    if ordinal is not None and ordinal>0 and ordinal%5==0:
        lines.append(FIVE_TURN_AUDIT_REMINDER)
    else:
        lines.append('FIVE-TURN AUDIT CADENCE: audit the previous five engineering turns/operations at least every fifth PCE operation.')
    return lines

def _with_sandwich_reminder(value:Any,action_id:Any=None)->str:
    text=str(value or '').rstrip()
    if text.endswith(SANDWICH_REMINDER):
        return text
    prefix=(text+'\n' if text else '')
    return prefix+'\n'.join(_turn_discipline_lines(action_id))+'\n'+SANDWICH_REMINDER

def result(r):
    presented=dict(r)
    presented['stdout']=_with_sandwich_reminder(presented.get('stdout',''),presented.get('id'))
    return RO+'\n'+json.dumps(presented,indent=2,ensure_ascii=False)+'\n'+RC

def materialize_outbound_result_file(state:State,aid:str)->dict[str,Any]:
    delivery=state.outbound_lookup(aid)
    if not isinstance(delivery,dict): raise RelayError('outbound delivery unavailable')
    path=validated_outbound_wire_path(state,aid,delivery)
    wire=path.read_text(encoding='utf-8')
    return {'result_file':str(path),'text_chars':len(wire),'attachments':[] if delivery.get('has_attachments') is False else ['blocked']}

def replay_saved_result(a:Action,prior:dict[str,Any])->str|None:
    saved=prior.get('saved_result_path')
    if not isinstance(saved,str) or not saved:
        return None
    path=Path(saved)
    if not path.is_file():
        return None
    try:
        raw=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,json.JSONDecodeError):
        return None
    if not isinstance(raw,dict) or raw.get('id')!=a.id:
        return None
    presented=present_result(a,raw,str(path.resolve()))
    presented['replayed']=True
    return result(presented)

def process(packet:str,state:State):
    a=extract(packet); prior=state.lookup(a.id)
    if prior:
        same=prior.get('payload_hash')==a.hash
        if not same:
            return result({'version':1,'platform':'windows','id':a.id,'session':a.session,'action':'EXEC','status':'ID_COLLISION','exit_code':None,'finished_at':now(),'stdout':'','stderr':'This command id was already used for a different payload; execution refused.','prior':prior})
        if prior.get('status')=='INFLIGHT':
            return result({'version':1,'platform':'windows','id':a.id,'session':a.session,'action':'EXEC','status':'DUPLICATE_INFLIGHT','exit_code':None,'finished_at':now(),'stdout':'','stderr':'This command is still executing; retry the same id to recover its eventual result.','prior':prior})
        replayed=replay_saved_result(a,prior)
        if replayed is not None:
            return replayed
        return result({'version':1,'platform':'windows','id':a.id,'session':a.session,'action':'EXEC','status':prior.get('status','DUPLICATE_IGNORED'),'exit_code':prior.get('exit_code'),'finished_at':prior.get('finished_at',now()),'stdout':'','stderr':'The command was previously processed, but its saved result is unavailable; it was not executed again.','prior':prior})
    state.reserve(a)
    r=execute(a)
    saved_path=save_full_result(state,r)
    presented=present_result(a,r,saved_path)
    state.mark(a,presented)
    return read_outbound_wire_result(state,a.id)

def config(path:Path):
    if not path.exists(): atomic_json(path,{'version':1,'host':'127.0.0.1','port':DEFAULT_PORT,'token':secrets.token_urlsafe(32)})
    d=json.loads(path.read_text(encoding='utf-8-sig'))
    if d.get('host')!='127.0.0.1' or not isinstance(d.get('port'),int) or not isinstance(d.get('token'),str) or len(d['token'])<32: raise RelayError('invalid bridge config')
    return d

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,addr,token,state): super().__init__(addr,Handler); self.token=token; self.state=state
    def handle_error(self,request,client_address):
        et,ev,_=sys.exc_info()
        if isinstance(ev,(BrokenPipeError,ConnectionResetError,ConnectionAbortedError,OSError)):
            print(f'CLIENT_CONNECTION_ABORT {client_address}: {type(ev).__name__}: {str(ev)[:160]}',flush=True)
            return
        print(f'REQUEST_HANDLER_ERROR {client_address}: {getattr(et,"__name__",str(et))}: {str(ev)[:500]}',flush=True)

class Handler(BaseHTTPRequestHandler):
    server:Server
    def log_message(self,fmt,*args): print('%s - %s'%(self.log_date_time_string(),fmt%args),flush=True)
    def auth(self): return secrets.compare_digest(self.headers.get('X-GPT-Windows-Relay-Token',''),self.server.token)
    def cors_origin(self):
        origin=self.headers.get('Origin','')
        if origin.startswith('moz-extension://') or origin.startswith('chrome-extension://') or origin == 'https://chatgpt.com':
            return origin
        return None
    def cors_headers(self):
        origin=self.cors_origin()
        if origin:
            self.send_header('Access-Control-Allow-Origin',origin)
            self.send_header('Vary','Origin')
            self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers','Content-Type, X-GPT-Windows-Relay-Token')
            self.send_header('Access-Control-Max-Age','600')
    def sendj(self,code,p):
        b=json.dumps(p,ensure_ascii=False).encode('utf-8')
        try:
            self.send_response(code)
            self.cors_headers()
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            self.wfile.flush()
            return True
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError,OSError) as e:
            # Browser/tab navigation and extension fetch cancellation can abort a localhost
            # connection after the command has already completed.  This is not a relay fault.
            print(f'CLIENT_DISCONNECTED {type(e).__name__}: {str(e)[:160]}',flush=True)
            return False
    def sendb(self,code,data:bytes,mime:str,name:str):
        try:
            self.send_response(code); self.cors_headers(); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(data))); self.send_header('Content-Disposition',f'inline; filename="{name}"'); self.end_headers(); self.wfile.write(data); self.wfile.flush(); return True
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError,OSError) as e:
            print(f'CLIENT_DISCONNECTED {type(e).__name__}: {str(e)[:160]}',flush=True); return False
    def do_OPTIONS(self):
        if not self.cors_origin():
            self.send_response(403); self.send_header('Content-Length','0'); self.end_headers(); return
        self.send_response(204); self.cors_headers(); self.send_header('Content-Length','0'); self.end_headers()
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if not 1<=n<=250000: raise RelayError('invalid request size')
        p=json.loads(self.rfile.read(n).decode());
        if not isinstance(p,dict): raise RelayError('request must be object')
        return p
    def do_GET(self):
        if not self.auth(): return self.sendj(401,{'ok':False,'error':'unauthorized'})
        parts=urlsplit(self.path); request_path=parts.path
        if request_path=='/status':
            stop=self.server.state.operator_stop_status()
            return self.sendj(200,{'ok':True,'version':1,'platform':'windows','armed':self.server.state.armed,'outbound_owner':self.server.state.outbound_owner,'pid':os.getpid(),'pending_missions':self.server.state.pending_mission_count(),**stop})
        if request_path in ('/browser-heartbeat','/browser-status'):
            query=parse_qs(parts.query); browser_id=query.get('browser_id',[None])[0]
            try:
                if request_path=='/browser-heartbeat':
                    raw=query.get('integration_connected',[None])[0]
                    integration=None if raw is None else str(raw).lower() in {'1','true','yes','on'}
                    self.server.state.mark_browser_seen(browser_id,integration)
                status=self.server.state.browser_status(browser_id)
            except RelayError as e:
                return self.sendj(400,{'ok':False,'error':'invalid_browser','detail':str(e)})
            return self.sendj(200,{'ok':True,**status})
        if request_path=='/mission-next':
            browser_id=parse_qs(parts.query).get('browser_id',[None])[0]
            try: mission=self.server.state.next_mission(browser_id)
            except RelayError as e: return self.sendj(400,{'ok':False,'error':'invalid_browser','detail':str(e)})
            return self.sendj(200,{'ok':True,'mission':mission})
        prefix='/managed-screenshot/'
        if request_path.startswith(prefix):
            try:
                name=request_path[len(prefix):]; path=managed_screenshot_path(self.server.state,name); return self.sendb(200,path.read_bytes(),'image/png',name)
            except RelayError as e: return self.sendj(404,{'ok':False,'error':'managed_screenshot_unavailable','detail':str(e)})
        return self.sendj(404,{'ok':False,'error':'not_found'})
    def do_POST(self):
        if not self.auth(): return self.sendj(401,{'ok':False,'error':'unauthorized'})
        request_path=urlsplit(self.path).path
        try:
            p=self.body()
            if request_path=='/managed-screenshot-delete':
                name=p.get('name'); path=managed_screenshot_path(self.server.state,name,require_exists=False); existed=path.is_file(); path.unlink(missing_ok=True); return self.sendj(200,{'ok':True,'deleted':existed,'name':name})
            if request_path=='/arm':
                if not isinstance(p.get('armed'),bool): raise RelayError('armed must be boolean')
                requested=p['armed']
                print(f'ARM_STATE_CHANGE requested={requested} origin={self.headers.get("Origin","")[:120]} user_agent={self.headers.get("User-Agent","")[:160]}',flush=True)
                generation=self.server.state.set_armed(requested); return self.sendj(200,{'ok':True,'armed':requested,'stop_generation':generation})
            if request_path=='/browser-event':
                event=p.get('event')
                detail=p.get('detail')
                if not isinstance(event,str) or not 1<=len(event)<=80: raise RelayError('invalid browser event')
                rec={'time':now(),'event':event,'detail':detail}
                events=self.server.state.path.parent/'browser-events.jsonl'
                with self.server.state.lock:
                    events.parent.mkdir(parents=True,exist_ok=True)
                    with events.open('a',encoding='utf-8') as ef:
                        ef.write(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')
                if event=='browser_operator_quiesced_all' and isinstance(detail,dict):
                    self.server.state.ack_browser_quiesced(detail.get('stop_generation'))
                self.server.state.journal_browser_event(event,detail)
                browser_id=detail.get('browser_id') if isinstance(detail,dict) else None
                if isinstance(browser_id,str):
                    try:
                        if event=='browser_integration_disconnected':
                            self.server.state.mark_browser_disconnected(browser_id)
                        elif event in {'browser_integration_connected','content_port_connected'}:
                            self.server.state.mark_browser_seen(browser_id,True)
                        else:
                            self.server.state.mark_browser_seen(browser_id)
                    except RelayError:
                        pass
                print(f'BROWSER_EVENT {event}',flush=True)
                return self.sendj(200,{'ok':True})
            if request_path=='/mission':
                mission_id=p.get('id'); text=p.get('text'); target_browser=p.get('target_browser')
                result=self.server.state.enqueue_mission(mission_id,text,target_browser)
                print(f'CONSUMER_MISSION_QUEUED id={mission_id} browser={target_browser} chars={len(text) if isinstance(text,str) else 0}',flush=True)
                return self.sendj(200,{'ok':True,'id':mission_id,'target_browser':target_browser,**result})
            if request_path=='/mission-ack':
                mission_id=p.get('id'); acknowledged=self.server.state.ack_mission(mission_id)
                if acknowledged: print(f'CONSUMER_MISSION_ACK id={mission_id}',flush=True)
                return self.sendj(200,{'ok':True,'id':mission_id,'acknowledged':acknowledged})
            if request_path!='/action': return self.sendj(404,{'ok':False,'error':'not_found'})
            if not self.server.state.armed: return self.sendj(423,{'ok':False,'error':'relay_disarmed'})
            packet=p.get('packet')
            if not isinstance(packet,str): raise RelayError('packet required')
            return self.sendj(200,{'ok':True,'result':process(packet,self.server.state)})
        except PacketError as e: self.sendj(400,{'ok':False,'error':'packet_rejected','detail':str(e)})
        except Exception as e: self.sendj(400,{'ok':False,'error':type(e).__name__,'detail':str(e)[:500]})

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',type=Path,default=cfg_dir()/'bridge.json'); ap.add_argument('--state-dir',type=Path,default=state_dir()); sub=ap.add_subparsers(dest='mode',required=True); sub.add_parser('server'); sub.add_parser('stdin'); a=ap.parse_args(); st=State(a.state_dir/'state.json')
    if a.mode=='stdin': st.set_armed(True); print(process(sys.stdin.read(),st)); return 0
    c=config(a.config); st.set_armed(True); s=Server(('127.0.0.1',c['port']),c['token'],st); print(f'GPT Windows Relay listening on 127.0.0.1:{c["port"]} — ARMED',flush=True)
    try: s.serve_forever(.25)
    except KeyboardInterrupt: pass
    finally: s.server_close()
    return 0

if __name__=='__main__': raise SystemExit(main())

# GPT_ONE_CLICK_BROWSER_QUEUE_TARGET_V1
# GPT_ONE_CLICK_BROWSER_STATUS_V1

# GPT_WINDOWS_HUD_EXACT_ACTION_STATE_V1
