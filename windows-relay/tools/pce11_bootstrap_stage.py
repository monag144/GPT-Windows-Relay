#!/usr/bin/env python3
"""PCE011 GitHub-first staging bootstrap. Never replaces the running Relay."""
from __future__ import annotations
import importlib.util, json, os, shutil, subprocess, sys
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
EXPECTED=globals().get("PCE11_EXPECTED_SHA")
if not isinstance(EXPECTED,str) or len(EXPECTED)!=40:
    raise RuntimeError("PCE011 exact GitHub SHA not provided")
HOME=Path.home()
REPO=HOME/"Downloads"/"Dev"/"GPT"/"GPT-Windows-Relay"
LIVE=HOME/"Downloads"/"Dev"/"GPT"/"Client"/"Relay"
GIT=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")

def git(*args,check=True,timeout=90):
    r=subprocess.run([GIT,"-C",str(REPO),*args],capture_output=True,text=True,
                     encoding="utf-8",errors="replace",timeout=timeout)
    if check and r.returncode:
        raise RuntimeError("git "+str(args[:2])+" exit="+str(r.returncode)
                           +" "+r.stderr[-240:].replace("\n"," "))
    return r

def start():
    if not REPO.is_dir() or not LIVE.is_dir():
        raise RuntimeError("Codex-mapped canonical checkout or live Relay not found; no mutation")
    origin=git("remote","get-url","origin").stdout.lower()
    if "monag144/gpt-windows-relay" not in origin:
        raise RuntimeError("wrong repo origin; do not modify Termux or another repository")
    if git("status","--porcelain").stdout.strip():
        raise RuntimeError("local Windows checkout dirty; preserve changes, do not switch")
    remote=git("ls-remote","origin","refs/heads/"+BRANCH).stdout.split()
    if not remote or remote[0]!=EXPECTED:
        raise RuntimeError("GitHub branch SHA changed since command was authored")
    git("fetch","origin",timeout=90)
    local=git("show-ref","--verify","--quiet","refs/heads/"+BRANCH,check=False)
    if local.returncode==0: git("switch",BRANCH)
    else: git("switch","--create",BRANCH,"--track","origin/"+BRANCH)
    git("pull","--ff-only","origin",BRANCH,timeout=90)
    if git("rev-parse","HEAD").stdout.strip()!=EXPECTED:
        raise RuntimeError("local HEAD did not match remotely verified source SHA")
    harness=REPO/"consumer"/"control_harness.py"
    spec=importlib.util.spec_from_file_location("pce11_harness",harness)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    governance=module.engineering_preflight(REPO,1,series=11)
    print("PCE011_GOVERNANCE="+json.dumps({
        "id":governance["id"],"reads":governance["reads"]},separators=(",",":")))
    tool=REPO/"windows-relay"/"tools"/"pce11_quarantine_stage.py"
    r=subprocess.run([sys.executable,"-B",str(tool),
        "--repo",str(REPO),"--live",str(LIVE),"--expected-head",EXPECTED],
        capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=235)
    if r.stdout.strip(): print(r.stdout.strip())
    if r.returncode: raise RuntimeError("safe staging blocked: "+r.stderr[-350:].replace("\n"," "))
    print("PCE011_VERDICT=BIN_ARCHIVED;V16_AND_R28_STAGED;LIVE_RELAY_NOT_REPLACED")
    print("PCE011_NEXT=RUN_SOURCE_TESTS_AND_COMPARE_CANDIDATES_BEFORE_LIVE_CUTOVER")

try:
    start()
except Exception as error:
    print("PCE011_VERDICT=BLOCKED_SAFELY reason="+str(error)[:350])
    raise
finally:
    print("Reply to this with the sandwich technique")
