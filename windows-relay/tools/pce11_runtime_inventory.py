#!/usr/bin/env python3
"""PCE11.005: SOURCE FF pull, governed READ-ONLY runtime/candidate inventory.
No process kill, STOP, browser/tab/extension control, retry or live code edits.
Only local output mutation: a new redacted evidence JSON under existing Relay/bin.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BRANCH = "pce11/one-click-go-recovery-and-doc-hygiene"
HISTORIC = {
    "RELAY_PCE8_V16": "694d47ab89596d5c3801f749caa352b951a2be52",
    "ONE_CLICK_GO_R28": "d5b9db7ad785b5cae8dc3b64219303b9fcfa634a",
}
CODE_PATHS = (
    "windows_relay.py", "hud.py", "firefox_tab_adapter.ps1",
    "extension/content.js", "extension/service_worker.js",
    "extension-persistent/content.js", "extension-persistent/service_worker.js",
    "relay-control.ps1",
)

def git_bin():
    return shutil.which("git") or str(
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git" / "cmd" / "git.exe")

def cmd(args, timeout=35):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if p.returncode:
        raise RuntimeError("required command failed (exit="+str(p.returncode)+", tool="+str(Path(args[0]).name)+")")
    return p.stdout.strip()

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def file_record(path):
    if not path.is_file(): return {"exists":False}
    return {"exists":True, "sha256":digest(path), "bytes":path.stat().st_size}

def safe_netstat():
    binary=shutil.which("netstat")
    if not binary:
        return {"available":False,"reason":"netstat not on PATH"}
    lines=cmd([binary,"-ano","-p","tcp"],timeout=12).splitlines()
    data={}
    for port in (8766,8767):
        recs=[]
        for line in lines:
            bits=line.split()
            if len(bits)<5 or bits[0].upper()!="TCP" or bits[3].upper()!="LISTENING":
                continue
            addr=bits[1].rsplit(":",1)
            if len(addr)!=2 or addr[1]!=str(port):continue
            pid=bits[-1]
            if not pid.isdigit(): continue
            recs.append({"address":addr[0],"pid":int(pid)})
        data[str(port)]=recs
    return {"available":True,"listening":data}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--live",type=Path,required=True)
    parser.add_argument("--expected-head",required=True)
    args=parser.parse_args(argv)
    repo=args.repo.resolve()
    live=args.live.resolve()
    git=git_bin()
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("mapped repository or live Relay missing/identical")
    get=lambda folder,*arg:cmd([git,"-C",str(folder),*arg])
    origin=get(repo,"remote","get-url","origin").lower()
    if "monag144/gpt-windows-relay" not in origin:raise RuntimeError("wrong canonical remote")
    if get(repo,"branch","--show-current")!=BRANCH:
        raise RuntimeError("unexpected branch; no live modifications")
    if get(repo,"status","--porcelain"):
        raise RuntimeError("dirty canonical checkout; preserve and diagnose")
    remote=cmd([git,"-C",str(repo),"ls-remote","origin","refs/heads/"+BRANCH]).split()
    if not remote or remote[0]!=args.expected_head:
        raise RuntimeError("remote GitHub SHA differs from pinned expected SHA")
    cmd([git,"-C",str(repo),"pull","--ff-only","origin",BRANCH],timeout=70)
    if get(repo,"rev-parse","HEAD")!=args.expected_head:
        raise RuntimeError("local branch SHA mismatch after fast-forward")
    sys.path.insert(0,str(repo/"consumer"))
    import control_harness
    proof=control_harness.engineering_preflight(repo,5,series=11)
    if not proof.get("ok") or "audit" not in proof["checkpoints"]:
        raise RuntimeError("five-operation audit missing or not verified")
    print("PCE11_005_GOVERNANCE="+json.dumps({
        "id":proof["id"],"reads":proof["reads"],"audit":proof["checkpoints"]["audit"]
    },separators=(",",":")))

    manifests=sorted((live/"bin").glob("BROKEN_*.manifest.json"),reverse=True)
    if not manifests:raise RuntimeError("original ZIP manifest missing")
    m=json.loads(manifests[0].read_text(encoding="utf-8"))
    archive=Path(m["archive_path"]).resolve()
    if not archive.is_file() or digest(archive)!=m["zip_sha256"]:
        raise RuntimeError("original backup integrity failure; BLOCKED")
    recorded={row["path"]:row for row in m.get("files",[])}
    live_records={}
    for name in CODE_PATHS:
        item=file_record(live/name)
        saved=recorded.get(name)
        item["archived_match"]=(item.get("sha256")==saved.get("sha256")) if saved else None
        live_records[name]=item

    candidates={}
    for label,sha in HISTORIC.items():
        folder=live/"builds"/(label+"_"+sha[:12])
        if not folder.is_dir() or get(folder,"rev-parse","HEAD")!=sha:
            raise RuntimeError("candidate checkout missing or changed: "+label)
        if get(folder,"status","--porcelain"):
            raise RuntimeError("candidate checkout dirty: "+label)
        files={}
        for name in CODE_PATHS:
            item=file_record(folder/"windows-relay"/name)
            item["same_as_live"]=bool(item.get("sha256") and item["sha256"]==live_records[name].get("sha256"))
            files[name]=item
        candidates[label]={"git_head":sha,"clean":True,"files":files}

    old=live/"bin"/"SOURCE_GATES_2026-10-08T091457Z"/"source-gates.json"
    if not old.is_file():raise RuntimeError("PCE11.004 acceptance report missing")
    acceptance=json.loads(old.read_text(encoding="utf-8"))
    checks=acceptance.get("results",[])
    source_ok=(acceptance.get("source_sha")=="c4eeca6b3ad1c20bbd9abbca4b255822efcb2e3f"
       and len(checks)==19 and all(c.get("status")=="PASS" for c in checks))
    if not source_ok:
        raise RuntimeError("PCE11.004 acceptance report contents do not match claimed green")

    try:ports=safe_netstat()
    except (OSError,RuntimeError,subprocess.TimeoutExpired) as exc:
        ports={"available":False,"reason":type(exc).__name__}
    evidence={
        "schema":"pce011-runtime-inventory-v1",
        "captured_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_sha":args.expected_head,
        "preflight":{"reads":proof["reads"],"audit":proof["checkpoints"]["audit"]},
        "snapshot":{"zip_sha256":m["zip_sha256"],"count":m["file_count"],"verified":True},
        "accepted_source_report":{"sha256":digest(old),"job_count":len(checks),"all_pass":source_ok},
        "live_files":live_records,"candidates":candidates,"listening":ports,
        "read_only_live":True,
        "excluded":["NO_EXTENSION_RELOAD","NO_BROWSER_CONTROL","NO_PROCESS_KILL",
                    "NO_STOP","NO_REPLAY","NO_LIVE_PATCH","NO_CLAIM_LOADED_RUNTIME_SHA"],
        "next_gate":"verify STOP, exact browser URL/PID and independently supervised rollback before any cutover",
    }
    stamped=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out=live/"bin"/("RUNTIME_INVENTORY_"+stamped+".json")
    if out.exists(): raise FileExistsError("inventory timestamp collision")
    out.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    diff=[name for name,item in live_records.items() if item.get("archived_match") is False]
    summary={
        "report":str(out),"source_sha":args.expected_head,
        "backup_verified":True,"source_green":True,
        "candidate_sha_verified":True,
        "live_archive_differences":diff,
        "ports":ports,
        "current_loaded_extension_verified":False,
        "current_browser_conversation_identity_verified":False,
        "live_cutover_authorized":False,
    }
    print("PCE11_005_INVENTORY="+json.dumps(summary,separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (RuntimeError,OSError,ValueError,subprocess.TimeoutExpired) as exc:
        print("PCE11_005_BLOCKED="+type(exc).__name__+": "+str(exc)[:260],file=sys.stderr)
        raise SystemExit(2)
    finally:
        print("Reply to this with the sandwich technique")
