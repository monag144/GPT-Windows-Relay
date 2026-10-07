#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, binascii, copy, hashlib, json, os, re, secrets, shutil, subprocess, sys, tempfile, threading, time, xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

VERSION=1
OPEN='[GPT_WINDOWS_ACTION]'; CLOSE='[/GPT_WINDOWS_ACTION]'
RO='[GPT_WINDOWS_RESULT]'; RC='[/GPT_WINDOWS_RESULT]'
ID_RE=re.compile(r'^[A-Za-z0-9._:-]{1,128}$')
PACKET_RE=re.compile(re.escape(OPEN)+r'\s*(\{.*?\})\s*'+re.escape(CLOSE),re.DOTALL)
MAX_CMD=20000; MAX_OUT=30000; PREVIEW_OUT=1800; PREVIEW_ERR=1200; MAX_TIMEOUT=300; DEFAULT_PORT=8766
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
        self.path=path; self.lock=threading.Lock(); self.data={'version':1,'armed':True,'processed':{},'updated_at':now()}; self.load()
    def load(self):
        if self.path.exists():
            self.data=json.loads(self.path.read_text(encoding='utf-8'))
            if self.data.get('version')!=1 or not isinstance(self.data.get('processed'),dict): raise RelayError('corrupt state file')
        # Any INFLIGHT reservation found during process startup belonged to a
        # previous relay process. Do not re-execute it automatically because
        # the interrupted command may already have produced side effects.
        for v in self.data.get('processed',{}).values():
            if isinstance(v,dict) and v.get('status')=='INFLIGHT':
                v['status']='INTERRUPTED_RESTART'
                v['finished_at']=now()
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
    def armed(self): return bool(self.data.get('armed'))
    def set_armed(self,v:bool):
        with self.lock:
            def mutate():
                self.data['armed']=v; self.data['updated_at']=now()
            self._mutate_and_save(mutate)
    def lookup(self,aid):
        v=self.data['processed'].get(aid); return v if isinstance(v,dict) else None
    def reserve(self,a:Action):
        with self.lock:
            def mutate():
                self.data['processed'][a.id]={'payload_hash':a.hash,'session':a.session,'status':'INFLIGHT','started_at':now()}
            self._mutate_and_save(mutate)
    def mark(self,a:Action,r:dict[str,Any]):
        with self.lock:
            def mutate():
                self.data['processed'][a.id]={'payload_hash':a.hash,'session':a.session,'status':r['status'],'exit_code':r.get('exit_code'),'finished_at':r['finished_at'],'saved_result_path':r.get('saved_result_path')}
                while len(self.data['processed'])>500: self.data['processed'].pop(next(iter(self.data['processed'])))
            self._mutate_and_save(mutate)

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

def present_result(a:Action,r:dict[str,Any],saved_path:str)->dict[str,Any]:
    out=str(r.get('stdout','')); err=str(r.get('stderr',''))
    if a.result_mode=='full':
        out_view,ot=trim(out,MAX_OUT); err_view,et=trim(err,MAX_OUT)
    else:
        out_view,ot=trim(out,PREVIEW_OUT); err_view,et=trim(err,PREVIEW_ERR)
    presented=dict(r)
    presented['result_mode']=a.result_mode
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

def result(r): return RO+'\n'+json.dumps(r,indent=2,ensure_ascii=False)+'\n'+RC

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
    return result(presented)

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
    def log_message(self,fmt,*args):
        path=getattr(self,'path','')
        if path=='/status' or path.startswith('/browser-status'): return
        print('%s - %s'%(self.log_date_time_string(),fmt%args),flush=True)
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
        if self.path=='/status': return self.sendj(200,{'ok':True,'version':1,'platform':'windows','armed':self.server.state.armed,'pid':os.getpid()})
        if self.path.startswith('/browser-status'):
            m=re.search(r'(?:[?&])browser_id=([^&]+)',self.path)
            browser_id=(m.group(1) if m else '').strip().lower()
            connected=False; age=None; last_event=None
            if browser_id=='firefox':
                events=self.server.state.path.parent/'browser-events.jsonl'
                if events.is_file():
                    wanted={'content_port_connected','content_script_started','action_received','action_result','scanner_snapshot','relay_result_received','relay_result_delivery_complete'}
                    for line in reversed(events.read_text(encoding='utf-8',errors='replace').splitlines()[-500:]):
                        try: rec=json.loads(line)
                        except Exception: continue
                        if rec.get('event') not in wanted: continue
                        last_event=rec.get('event')
                        try:
                            dt=datetime.fromisoformat(str(rec.get('time','')).replace('Z','+00:00'))
                            if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
                            age=max(0,int((datetime.now(timezone.utc)-dt.astimezone(timezone.utc)).total_seconds()))
                        except Exception: age=None
                        connected=age is not None and age<=120
                        break
            return self.sendj(200,{'ok':True,'browser_id':browser_id,'connected':connected,'age_seconds':age,'last_event':last_event,'source':'development_event_health'})
        prefix='/managed-screenshot/'
        if self.path.startswith(prefix):
            try:
                name=self.path[len(prefix):]; path=managed_screenshot_path(self.server.state,name); return self.sendb(200,path.read_bytes(),'image/png',name)
            except RelayError as e: return self.sendj(404,{'ok':False,'error':'managed_screenshot_unavailable','detail':str(e)})
        return self.sendj(404,{'ok':False,'error':'not_found'})
    def do_POST(self):
        if not self.auth(): return self.sendj(401,{'ok':False,'error':'unauthorized'})
        try:
            p=self.body()
            if self.path=='/managed-screenshot-delete':
                name=p.get('name'); path=managed_screenshot_path(self.server.state,name,require_exists=False); existed=path.is_file(); path.unlink(missing_ok=True); return self.sendj(200,{'ok':True,'deleted':existed,'name':name})
            if self.path=='/arm':
                if not isinstance(p.get('armed'),bool): raise RelayError('armed must be boolean')
                requested=p['armed']
                print(f'ARM_STATE_CHANGE requested={requested} origin={self.headers.get("Origin","")[:120]} user_agent={self.headers.get("User-Agent","")[:160]}',flush=True)
                self.server.state.set_armed(requested); return self.sendj(200,{'ok':True,'armed':requested})
            if self.path=='/browser-event':
                event=p.get('event')
                detail=p.get('detail')
                if not isinstance(event,str) or not 1<=len(event)<=80: raise RelayError('invalid browser event')
                rec={'time':now(),'event':event,'detail':detail}
                events=self.server.state.path.parent/'browser-events.jsonl'
                with self.server.state.lock:
                    events.parent.mkdir(parents=True,exist_ok=True)
                    with events.open('a',encoding='utf-8') as ef:
                        ef.write(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')
                print(f'BROWSER_EVENT {event}',flush=True)
                return self.sendj(200,{'ok':True})
            if self.path!='/action': return self.sendj(404,{'ok':False,'error':'not_found'})
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
