#!/usr/bin/env python3
"""Read-only-to-production isolated PR34 qualification, launched by old relay.

The caller must fetch and switch to the expected commit in the clean PR34
worktree before invoking. This test itself never restarts any service,
changes the main worktree, or changes native Auto Send.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
MAIN=ROOT.parent/"Windows Relay"
PRIOR_ACTION="PCE20-UNIVERSAL-GUI-QUAL-20261127-016"

def call(cmd,cwd,timeout):
    return subprocess.run(cmd,cwd=str(cwd),capture_output=True,text=True,
                          encoding="utf-8",errors="replace",timeout=timeout)

def git(*args,root=ROOT):
    p=call(["git",*args],root,60)
    if p.returncode:
        raise RuntimeError("GIT_"+args[0]+":"+(p.stderr or p.stdout)[-300:])
    return p.stdout.strip()

def suite(name,where,args):
    p=call([sys.executable,*args],where,180)
    out=p.stdout+"\n"+p.stderr
    counts=re.findall(r"Ran \d+ tests? in [^\r\n]+",out)
    results=re.findall(r"^(?:OK|FAILED[^\r\n]*)$",out,re.M)
    ok=p.returncode==0
    print(name+"="+("PASS" if ok else "FAIL")+"; "+(counts[-1] if counts else "NO_COUNT")+
          "; "+(results[-1] if results else "NO_SUMMARY"),flush=True)
    if not ok:
        # Print concise failure IDs and exception messages, not the entire
        # source excerpt (a 20KB assertion can obscure the useful diagnosis).
        failures=re.findall(r"^(?:FAIL|ERROR):[^\\r\\n]+",out,re.M)
        causes=re.findall(r"^(?:AssertionError|SyntaxError|ModuleNotFoundError|RuntimeError):[^\\r\\n]{0,250}",out,re.M)
        print(name+"_FAILING_TESTS="+" | ".join(failures[:12]),flush=True)
        print(name+"_ASSERTIONS="+" | ".join(causes[:12]),flush=True)
        if not failures and not causes:
            print(name+"_ERROR_TAIL="+out[-750:].replace("\r"," ").replace("\n"," | "),flush=True)
    return ok

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--expected",required=True)
    args=parser.parse_args()
    if ROOT.name!="Windows Relay PR34" or not MAIN.is_dir():
        raise RuntimeError("WRONG_ISOLATED_WORKTREE")
    original=git("rev-parse","HEAD",root=MAIN)
    if git("rev-parse","HEAD")!=args.expected:
        raise RuntimeError("QUALIFICATION_COMMIT_MISMATCH")
    if git("status","--porcelain","--untracked-files=no"):
        raise RuntimeError("TRACKED_WORKTREE_DIRTY")
    print("PR_HEAD="+args.expected,flush=True)
    compiled=call([sys.executable,"-m","py_compile",
        str(ROOT/"windows-relay"/"desktop_native_relay.py"),
        str(ROOT/"windows-relay"/"hud.py"),
        str(ROOT/"windows-relay"/"tests"/"test_universal_runtime_cutover.py")],ROOT,30)
    print("PY_COMPILE="+("PASS" if compiled.returncode==0 else "FAIL"),flush=True)
    if compiled.returncode:
        print("COMPILE_ERROR="+compiled.stderr[-500:],flush=True)
        return 1
    good=suite("RELAY",ROOT,
               ["-m","unittest","discover","-s","windows-relay/tests","-p","test_*.py"])
    good=suite("CONSUMER",ROOT/"consumer",
               ["-m","unittest","discover","-s","tests","-p","test_*.py"]) and good
    earlier=Path(os.environ.get("LOCALAPPDATA",str(Path.home())))/"GPTWindowsRelayDesktop"/"results"/(PRIOR_ACTION+".json")
    if earlier.is_file():
        try:
            record=json.loads(earlier.read_text(encoding="utf-8"))
            print("OP016_STATUS="+str(record.get("status"))+
                  "; EXIT="+str(record.get("exit_code")),flush=True)
            lines=str(record.get("stdout") or "").splitlines()
            print("OP016_TAIL="+" | ".join(lines[-10:])[-1600:],flush=True)
        except (OSError,ValueError) as exc:
            print("OP016_RECEIPT_UNREADABLE="+type(exc).__name__,flush=True)
    else:
        print("OP016_RECEIPT_NOT_FOUND",flush=True)
    if good:
        p=call([sys.executable,str(ROOT/"windows-relay"/"tools"/"qualify_universal_courier_gui.py")],
               ROOT,250)
        out=p.stdout+"\n"+p.stderr
        print("GUI_TEST="+("PASS" if p.returncode==0 else "FAIL_OR_BLOCKED")+
              "; EXIT="+str(p.returncode),flush=True)
        print("GUI_TAIL="+" | ".join(out.splitlines()[-18:])[-2800:],flush=True)
        good=good and p.returncode==0
    else:
        print("GUI_TEST=SKIPPED_OFFLINE_FAILURE",flush=True)
    print("MAIN_HEAD_UNCHANGED="+str(git("rev-parse","HEAD",root=MAIN)==original).upper(),flush=True)
    print("ENGINE_AND_HUD_RESTARTED=NO; AUTO_SEND_UNCHANGED=YES; NO_EXEC_REPLAY=TRUE",flush=True)
    print("PR34_QUALIFICATION="+("PASS" if good else "NOT_YET_PASS"),flush=True)
    return 0 if good else 1

if __name__=="__main__":
    try:
        sys.exit(main())
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
        print("PR34_QUALIFICATION=BLOCKED; REASON="+str(exc)[:450],flush=True)
        sys.exit(2)
