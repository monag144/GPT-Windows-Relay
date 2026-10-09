import os,sys,json,hashlib,subprocess,ctypes,shutil, time
from pathlib import Path
root=Path.home()/'Downloads'/'Dev'/'GPT'/'GPT-Windows-Relay'
test=Path.home()/'Downloads'/'Dev'/'GPT'/'Client'/'Relay'/'test'
base='a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a'
remote='3b0a0884ca037634139362d07a043d3911927b25'
doc='docs/handoffs/HANDOFF_2026-10-09T2315Z_PCE14_TO_PCE15_STRICT_GRADING_SEMANTIC_BROWSER_REUSE.md'
blob='70dc49d242b4e3259feb8b81e814d10c664233ee'
shascript='e2ff24ca5b893fa6259bfdc2000872e581a512c13405cdcd6a9bc1c051b9223a'
protected='docs/audits/AUDIT_2026-10-09T0808Z_PCE12_OPERATIONS_010_014.md'
evsha='3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab'
intent=test/'PCE14_TO_PCE15_HANDOFF_ONCE.intent.json'
target=test/'Copy Contents.txt'
script=test/'Copy-Contents-To-ChatGPT.ps1'
workerpath=test/'PCE14_TO_PCE15_ONE_SHOT_WORKER.py'
log=test/'PCE14_TO_PCE15_one_shot_worker.log'
def git(*a):
 r=subprocess.run(['git','-C',str(root),*a],capture_output=True,timeout=30)
 if r.returncode:raise RuntimeError('GIT_'+a[0]+' '+r.stderr.decode(errors='replace')[:90])
 return r.stdout
def gs(*a):return git(*a).decode().strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
def gb(d):return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
try:
 back=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'GPTWindowsRelay'/'ops'/'GOVSYNC13-AUDIT-RESTORE-20261009-01'/'PCE12_010_014_preserved.md'
 if gs('rev-parse','HEAD')!=base or gs('branch','--show-current')!='pce11/one-click-go-recovery-and-doc-hygiene' or 'monag144/gpt-windows-relay' not in gs('remote','get-url','origin').lower().removesuffix('.git') or gs('status','--porcelain','-uall').splitlines()!=['?? '+protected] or sha(root/protected)!=evsha or sha(back)!=evsha:raise RuntimeError('GOVERNANCE_OR_PROTECTED_AUDIT_INVALID')
 sys.path.insert(0,str(root))
 from consumer.control_harness import engineering_preflight
 pf=engineering_preflight(root,29,series=14)
 if not pf['ok']:raise RuntimeError('PCE14_PREFLIGHT_FAILED')
 if intent.exists():raise RuntimeError('EXISTING_ONCE_INTENT_NO_REPLAY')
 if sha(script)!=shascript:raise RuntimeError('USER_VALIDATED_SCRIPT_SHA_DRIFT')
 if any(p.exists() for p in [test.parent/'.relay-paused',root/'windows-relay'/'.relay-paused']):raise RuntimeError('OPERATOR_STOP')
 gethwnd='(Get-Process firefox -ErrorAction Stop|Where-Object {$_.MainWindowHandle -ne 0}|Select-Object -First 1).MainWindowHandle'
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',gethwnd],capture_output=True,text=True,timeout=10)
 first=int(p.stdout.strip()) if p.returncode==0 and p.stdout.strip().isdigit() else 0
 front=int(ctypes.windll.user32.GetForegroundWindow())
 if not first or first!=front:raise RuntimeError('FIRST_FIREFOX_IS_NOT_FOREGROUND')
 print('PCE14_FOREGROUND_MATCH='+str(first),flush=True)
 git('fetch','--no-tags','origin','refs/heads/pce11/one-click-go-recovery-and-doc-hygiene')
 git('merge-base','--is-ancestor',remote,'FETCH_HEAD')
 content=git('show',remote+':'+doc)
 if gb(content)!=blob or gs('rev-parse',remote+':'+doc)!=blob or b'[GPT_ENGINEERING_ROTATION_HANDOFF_V1]' not in content or b'[END_GPT_ENGINEERING_ROTATION_HANDOFF_V1]' not in content:raise RuntimeError('HANDOFF_DOCUMENT_INTEGRITY')
 refs={'windows-relay/firefox_tab_adapter.ps1':'4e95463a39deb2644849a78f1a371388a156080c','windows-relay/agent011_current_tab_new_chat.ps1':'bfde67ddeae43acc3ae0df6aa4f405a001c075ce','windows-relay/semantic_agent_rotation.ps1':'469be0491a0c810aa407bac87abbd9a0e64a63ed'}
 originals={}
 for name,h in refs.items():
  b=git('show',base+':'+name)
  if gb(b)!=h:raise RuntimeError('SEMANTIC_REFERENCE_HASH_MISMATCH:'+name)
  originals[name]=b
 worker='''import json,os,subprocess,ctypes,time,hashlib\nfrom pathlib import Path\ntime.sleep(8)\ntest=Path(__file__).resolve().parent\nintent=test/'PCE14_TO_PCE15_HANDOFF_ONCE.intent.json'\nrecord=json.loads(intent.read_text(encoding='utf-8'))\ndef sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'\ntry:\n    hwnd=int(ctypes.windll.user32.GetForegroundWindow())\n    ps='(Get-Process firefox -ErrorAction Stop|Where-Object {$_.MainWindowHandle -ne 0}|Select-Object -First 1).MainWindowHandle'\n    q=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],capture_output=True,text=True,timeout=10)\n    selected=int(q.stdout.strip()) if q.returncode==0 and q.stdout.strip().isdigit() else 0\n    if hwnd!=record['hwnd'] or selected!=hwnd:raise RuntimeError('FOREGROUND_FIREFOX_CHANGED')\n    if (test.parent/'.relay-paused').exists():raise RuntimeError('OPERATOR_PAUSED')\n    src=test/'Copy-Contents-To-ChatGPT.ps1'\n    if sha(src)!=record['launcher_sha256'] or sha(test/'Copy Contents.txt')!=record['handoff_sha256']:raise RuntimeError('SOURCE_HASH_CHANGED')\n    record['phase']='SCRIPT_LAUNCH_INTENT_NO_RETRY'\n    intent.write_text(json.dumps(record,indent=2)+'\\n',encoding='utf-8')\n    r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(src)],capture_output=True,text=True,timeout=55,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),cwd=str(test))\n    record['exit_code']=r.returncode\n    record['phase']='SCRIPT_RETURNED_OK_DELIVERY_NOT_INDEPENDENTLY_VERIFIED' if r.returncode==0 else 'SCRIPT_RETURNED_ERROR_SUBMISSION_UNCERTAIN'\nexcept BaseException as e:\n    record['phase']='HALTED_BEFORE_SCRIPT' if record.get('phase')!='SCRIPT_LAUNCH_INTENT_NO_RETRY' else 'SCRIPT_OUTCOME_UNCERTAIN'\n    record['error_type']=type(e).__name__\n    record['error']=str(e)[:120]\nfinally:\n    record['delivery']='NOT_INDEPENDENTLY_VERIFIED'\n    intent.write_text(json.dumps(record,indent=2)+'\\n',encoding='utf-8')\n    print('PCE14_HANDOFF_WORKER='+json.dumps({'phase':record['phase'],'exit_code':record.get('exit_code'),'error':record.get('error'),'delivery':record['delivery']}),flush=True)\n'''
 compile(worker,'PCE14_ONCE_WORKER','exec')
 test.mkdir(parents=True,exist_ok=True)
 if target.is_file():
  archive=test/'handoff-backups';archive.mkdir(exist_ok=True);shutil.copy2(target,archive/('Copy-Contents-before-PCE15-'+str(time.time_ns())+'.txt'))
 pending=test/'Copy Contents.txt.pce14-stage'
 with pending.open('xb') as out:out.write(content)
 os.replace(pending,target)
 if target.read_bytes()!=content:raise RuntimeError('HANDOFF_WRITE_VERIFICATION_FAILED')
 semantic=test/'semantic-backend-reference';semantic.mkdir(exist_ok=True)
 for name,data in originals.items():
  dest=semantic/Path(name).name
  if dest.exists() and gb(dest.read_bytes())!=refs[name]:raise RuntimeError('PREEXISTING_SEMANTIC_REFERENCE_DRIFT')
  if not dest.exists():dest.write_bytes(data)
 (semantic/'README.txt').write_text('Historical semantic UIAutomation click/paste/Send backend, source-hash pinned. Reference only; handoff invokes the previously working unchanged script.\n',encoding='utf-8')
 workerpath.write_text(worker,encoding='utf-8')
 if gs('rev-parse','HEAD')!=base or gs('status','--porcelain','-uall').splitlines()!=['?? '+protected] or sha(root/protected)!=evsha or sha(back)!=evsha:raise RuntimeError('POST_WRITE_CANONICAL_GUARD_FAILED')
 if int(ctypes.windll.user32.GetForegroundWindow())!=first:raise RuntimeError('FOREGROUND_CHANGED_BEFORE_RESERVATION')
 journal={'id':'PCE14-HANDOFF-TO-PCE15-THIRD-ONE-SHOT-20261009','phase':'INTENT_RESERVED_NO_RETRY','hwnd':first,'handoff_sha256':sha(target),'launcher_sha256':shascript,'semantic_backend_count':len(originals),'delivery':'NOT_INDEPENDENTLY_VERIFIED'}
 with intent.open('x',encoding='utf-8') as out:json.dump(journal,out,indent=2)
 with log.open('ab') as out:
  process=subprocess.Popen([sys.executable,'-B',str(workerpath)],cwd=str(test),stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)|getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0),close_fds=True)
 print('PCE14_HANDOFF_STAGED_AND_LAUNCHED='+json.dumps({'file':str(target),'bytes':len(content),'sha256':sha(target),'semantic_sources_staged':len(originals),'worker_pid':process.pid,'intent':str(intent),'log':str(log),'delivery':'NOT_INDEPENDENTLY_VERIFIED'},separators=(',',':')),flush=True)
except Exception as e:
 print('PCE14_HANDOFF_BLOCKED='+type(e).__name__+':'+str(e)[:180],flush=True)
 raise
finally:
 print('Reply to this with the sandwich technique',flush=True)
