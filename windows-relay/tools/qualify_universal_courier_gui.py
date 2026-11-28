#!/usr/bin/env python3
"""Real Windows UIA acceptance test against a disposable native WinForms app.

NO user's chats, Notepad tabs, documents, or production journal are touched.
The test-only GUI is created under a fresh TEMP directory and closed by PID.
The foreground app is restored where Windows permits. Evidence is retained.
This does not restart or reconfigure the active Courier.
"""
from __future__ import annotations
import ctypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"tools"/"UniversalCourierTestWindow.cs"
SENDER=ROOT/"tools"/"Send-Foreground-TextResult.ps1"
HIDDEN=getattr(subprocess,"CREATE_NO_WINDOW",0)

def compiler():
    windir=Path(os.environ.get("WINDIR",r"C:\Windows"))
    options=[windir/"Microsoft.NET"/"Framework64"/"v4.0.30319"/"csc.exe",
             windir/"Microsoft.NET"/"Framework"/"v4.0.30319"/"csc.exe"]
    return next((str(p) for p in options if p.is_file()),None)

def expect(condition,detail):
    if not condition:
        raise RuntimeError(detail)

def run_process(args,workdir,env=None,timeout=30):
    return subprocess.run(args,cwd=str(workdir),env=env,capture_output=True,
                          text=True,encoding="utf-8",errors="replace",
                          creationflags=HIDDEN,timeout=timeout)

def main():
    if os.name!="nt":
        print("GUI_QUALIFICATION=BLOCKED; REASON=WINDOWS_REQUIRED")
        return 2
    if not (FIXTURE.is_file() and SENDER.is_file()):
        print("GUI_QUALIFICATION=BLOCKED; REASON=TEST_FIXTURE_MISSING")
        return 2
    if not compiler() or not shutil.which("powershell.exe"):
        print("GUI_QUALIFICATION=BLOCKED; REASON=CSC_OR_POWERSHELL_UNAVAILABLE")
        return 2
    user32=ctypes.windll.user32
    user32.FindWindowW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p]
    user32.FindWindowW.restype=ctypes.c_void_p
    user32.GetForegroundWindow.restype=ctypes.c_void_p
    user32.GetWindowThreadProcessId.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
    user32.GetWindowThreadProcessId.restype=ctypes.c_ulong
    user32.PostMessageW.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_void_p]
    user32.SetForegroundWindow.argtypes=[ctypes.c_void_p]
    user32.SetForegroundWindow.restype=ctypes.c_bool
    original=user32.GetForegroundWindow()
    root=Path(tempfile.mkdtemp(prefix="pce20-courier-gui-"))
    exe=root/"UniversalCourierTestWindow.exe"
    build=run_process([compiler(),"/nologo","/target:winexe",
              "/reference:System.Windows.Forms.dll",
              "/reference:System.Drawing.dll",
              "/out:"+str(exe),str(FIXTURE)],root,timeout=35)
    if build.returncode or not exe.is_file():
        print("GUI_QUALIFICATION=BLOCKED; REASON=FIXTURE_BUILD_FAILED")
        print("COMPILER_ERROR="+(build.stdout+" "+build.stderr).strip()[-900:])
        print("EVIDENCE_DIR="+str(root))
        return 2
    local=root/"isolated-localappdata"
    home=local/"GPTWindowsRelayDesktop"
    outbox=home/"outbox"
    outbox.mkdir(parents=True,exist_ok=True)
    (home/"desktop-control.json").write_text(json.dumps({
        "version":1,"armed":True,"off":False,"auto_send":True,
        "trust_visible_desktop_packets":False}),encoding="utf-8")
    env=dict(os.environ)
    env["LOCALAPPDATA"]=str(local)
    cases=[
        ("EMPTY_SEND",True,False),
        ("NONEMPTY_SEND",True,True),
        ("EMPTY_EDITOR",False,False),
        ("NONEMPTY_EDITOR",False,True),
    ]
    results=[]
    try:
        for name,has_send,prefilled in cases:
            case=root/name
            case.mkdir()
            test_id="COURIER-QA-"+uuid.uuid4().hex
            nonce="NATIVE-RECEIPT-"+uuid.uuid4().hex
            payload="Universal Courier UIA qualification "+uuid.uuid4().hex
            initial=("PREEXISTING HUMAN TEXT "+uuid.uuid4().hex) if prefilled else ""
            wire=outbox/(test_id+".txt")
            wire.write_text(payload,encoding="utf-8")
            sidecar=outbox/(test_id+".receipt.json")
            sidecar.write_text(json.dumps({
                "id":test_id,"receipt":nonce,
                "text_sha256":hashlib.sha256(wire.read_bytes()).hexdigest()
            }),encoding="utf-8")
            title="COURIER TEST "+test_id
            gui=None
            summary={"case":name,"status":"FAIL","sender_rc":None,
                     "sender_result":"","clicks":None,"editor_ok":False,
                     "message_ok":False}
            try:
                gui=subprocess.Popen([str(exe),title,str(case),initial,
                                      "send" if has_send else "editor"],
                                     cwd=str(root),creationflags=HIDDEN,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                hwnd=0
                for i in range(100):
                    hwnd=int(user32.FindWindowW(None,title) or 0)
                    if hwnd and (case/"ready.txt").is_file() and int(user32.GetForegroundWindow() or 0)==hwnd:
                        break
                    if gui.poll() is not None:
                        break
                    time.sleep(0.12)
                expect(hwnd and (case/"ready.txt").is_file(),"FIXTURE_WINDOW_NOT_READY")
                pid=ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
                expect(pid.value==gui.pid,"WINDOW_OWNER_MISMATCH_REFUSE_INPUT")
                expect(int(user32.GetForegroundWindow() or 0)==hwnd,
                       "FIXTURE_NOT_FOREGROUND_REFUSE_INPUT")
                args=["powershell.exe","-NoLogo","-NoProfile",
                      "-NonInteractive","-ExecutionPolicy","Bypass","-STA",
                      "-File",str(SENDER),"-NativeResultPath",str(wire),
                      "-NativeActionId",test_id,
                      "-NativeReceiptMarker",nonce,
                      "-PlainText","-ManualForceSend"]
                sender=run_process(args,ROOT,env=env,timeout=32)
                output=sender.stdout+"\n"+sender.stderr
                (case/"sender-output.txt").write_text(output,encoding="utf-8")
                summary["sender_rc"]=sender.returncode
                summary["sender_result"]=" | ".join(x.strip() for x in output.splitlines()
                                  if x.startswith(("RESULT=","SENDER_STAGE=","HEARTBEAT_ERROR=")))[-1100:]
                if sender.returncode or not summary["sender_result"]:
                    summary["sender_stderr_tail"]=sender.stderr[-1200:]
                    summary["sender_stdout_tail"]=sender.stdout[-700:]
            except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
                summary["error"]=type(exc).__name__+":"+str(exc)[:180]
            finally:
                if gui is not None:
                    hwnd=int(user32.FindWindowW(None,title) or 0)
                    if hwnd:
                        pid=ctypes.c_ulong()
                        user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
                        if pid.value==gui.pid:
                            user32.PostMessageW(hwnd,0x0010,None,None)
                    try:
                        gui.wait(timeout=7)
                    except subprocess.TimeoutExpired:
                        gui.terminate()  # Only the newly spawned test fixture.
                        gui.wait(timeout=5)
                time.sleep(0.15)
            final=(case/"final-editor.txt").read_text(encoding="utf-8") if (case/"final-editor.txt").is_file() else None
            sent=(case/"sent.txt").read_text(encoding="utf-8") if (case/"sent.txt").is_file() else ""
            clicks_text=(case/"clicks.txt").read_text(encoding="utf-8") if (case/"clicks.txt").is_file() else None
            clicks=int(clicks_text) if clicks_text and clicks_text.isdigit() else -1
            summary["clicks"]=clicks
            if prefilled:
                summary["editor_ok"]=final==initial
                summary["message_ok"]=sent==""
                accepted=(summary["sender_rc"]==0 and
                          "SENDER_STAGE=FOREGROUND_EDITOR_NOT_VERIFIABLY_EMPTY" in summary["sender_result"] and
                          "RESULT=FOREGROUND_NO_TARGET" in summary["sender_result"] and
                          summary["editor_ok"] and summary["message_ok"] and clicks==0)
            elif has_send:
                summary["editor_ok"]=final==""
                summary["message_ok"]=sent.rstrip("\r\n")==payload
                accepted=(summary["sender_rc"]==0 and
                          "RESULT=HEARTBEAT_SUBMITTED" in summary["sender_result"] and
                          summary["editor_ok"] and summary["message_ok"] and clicks==1)
            else:
                summary["editor_ok"]=final==payload
                summary["message_ok"]=sent==""
                accepted=(summary["sender_rc"]==0 and
                          "RESULT=TEXT_INSERTED_VERIFIED" in summary["sender_result"] and
                          summary["editor_ok"] and summary["message_ok"] and clicks==0)
            summary["status"]="PASS" if accepted else "FAIL"
            results.append(summary)
            fault=str(summary.get("error") or summary.get("sender_stderr_tail") or
                      (summary.get("sender_stdout_tail") if not accepted else "") or "")
            print(name+"="+summary["status"]+"; clicks="+str(clicks)+
                  "; editor_ok="+str(summary["editor_ok"])+
                  "; rc="+str(summary["sender_rc"])+
                  "; sender="+summary["sender_result"][-300:].replace("\n"," | ")+
                  ("; diagnostic="+fault[-380:].replace("\n"," | ") if fault else ""),
                  flush=True)
    finally:
        foreground_restored=bool(original and user32.SetForegroundWindow(original))
        print("PREVIOUS_FOREGROUND_RESTORED="+str(foreground_restored).upper(),flush=True)
    (root/"qualification-results.json").write_text(json.dumps({
        "test":"Universal Courier real WinForms foreground UIA",
        "time_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "cases":results},indent=2),encoding="utf-8")
    good=len(results)==len(cases) and all(r["status"]=="PASS" for r in results)
    print("GUI_QUALIFICATION="+("PASS" if good else "FAIL"),flush=True)
    print("CASE_COUNT="+str(len(results))+"; PASSED="+str(sum(x["status"]=="PASS" for x in results)),flush=True)
    print("EVIDENCE_DIR="+str(root),flush=True)
    print("NO_PRODUCTION_STATE_OR_USER_DOCUMENT_MUTATION=TRUE",flush=True)
    return 0 if good else 1

if __name__=="__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("GUI_QUALIFICATION=BLOCKED; REASON="+type(exc).__name__+":"+str(exc)[:200])
        sys.exit(2)
