#!/usr/bin/env python3
"""PCE011: preserve current live bytes in Relay/bin and STAGE old GitHub builds.

No runtime replacement, browser reload, process termination, or credential printing.
May run while current Relay is serving the invoking action.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path

WINDOWS_REPO = "monag144/GPT-Windows-Relay"
LEGACY_URL = "https://github.com/monag144/GPT-Termux-Relay.git"
CANDIDATES = (
    ("RELAY_PCE8_V16", "consumer/r29-firefox-offline-tray",
     "694d47ab89596d5c3801f749caa352b951a2be52"),
    ("ONE_CLICK_GO_R28", "consumer/one-click-go",
     "d5b9db7ad785b5cae8dc3b64219303b9fcfa634a"),
)
SKIP_DIRS = {"bin", "builds", ".git"}
MAX_BYTES = 2 * 1024 ** 3
MAX_FILES = 8000

def git_binary():
    binary=shutil.which("git")
    if binary: return binary
    fallback=Path(os.environ.get("ProgramFiles", "C:/Program Files"))/"Git"/"cmd"/"git.exe"
    if fallback.is_file(): return str(fallback)
    raise RuntimeError("Git required; refusing staging without exact SHA verification")

def command(argv, cwd=None, timeout=160):
    r=subprocess.run(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if r.returncode:
        raise RuntimeError("command failed: "+str(argv[:4])+" exit="+str(r.returncode)
                           +" details="+r.stderr[-400:].replace("\n"," "))
    return r.stdout.strip()

def hashes(path):
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()

def inventory(root):
    found=[]
    if not (root/"windows_relay.py").is_file() or not (root/"extension"/"content.js").is_file():
        raise RuntimeError("live path lacks recognized relay backend/extension source")
    for sub in root.rglob("*"):
        rel=sub.relative_to(root)
        if any(part.lower() in SKIP_DIRS for part in rel.parts): continue
        if sub.is_symlink(): raise RuntimeError("reparse/symlink in live snapshot: "+str(rel))
        if not sub.is_file(): continue
        if len(found)>=MAX_FILES: raise RuntimeError("too many live files; no partial snapshot")
        if sub.stat().st_size>MAX_BYTES: raise RuntimeError("oversize file; no partial snapshot")
        found.append((sub,rel.as_posix(),sub.stat().st_size))
    if not found: raise RuntimeError("live tree unexpectedly empty")
    total=sum(x[2] for x in found)
    if total>MAX_BYTES: raise RuntimeError("live tree exceeds 2GiB bound; no partial snapshot")
    return sorted(found,key=lambda x:x[1]),total

def archive_live(live, stamp):
    target=live/"bin"
    records,total=inventory(live)
    if shutil.disk_usage(live).free < total + 128*1024*1024:
        raise RuntimeError("insufficient free disk for safe snapshot")
    target.mkdir(parents=True,exist_ok=True)
    final=target/("BROKEN_"+stamp+".zip")
    temp=target/("."+final.name+".partial")
    manifest=target/("BROKEN_"+stamp+".manifest.json")
    if any(p.exists() for p in (final,temp,manifest)):
        raise FileExistsError("snapshot collision; never overwrite")
    docs=[]
    try:
        with zipfile.ZipFile(temp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=2,
                             allowZip64=True) as z:
            for path,name,length in records:
                z.write(path,name)
                docs.append({"path":name,"bytes":length,"sha256":hashes(path)})
        with zipfile.ZipFile(temp,"r") as z:
            for record in docs:
                h=hashlib.sha256()
                with z.open(record["path"],"r") as stream:
                    for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
                if h.hexdigest()!=record["sha256"]:
                    raise RuntimeError("snapshot SHA mismatch: "+record["path"])
        os.replace(temp,final)
        result={
            "schema":"pce011-bin-v1","stamp_utc":stamp,"source_path":str(live),
            "archive_path":str(final),"zip_sha256":hashes(final),
            "file_count":len(docs),"total_bytes":total,"files":docs,
            "note":"LOCAL ONLY / CAN INCLUDE PRIVATE CONFIGURATION; DO NOT UPLOAD OR POST RAW"
        }
        manifest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        return {"archive":str(final),"manifest":str(manifest),"files":len(docs),
                "bytes":total,"sha256":result["zip_sha256"]}
    except BaseException:
        if temp.exists(): temp.unlink()
        raise

def stage_one(live,git,label,ref,commit):
    builds=live/"builds"
    builds.mkdir(parents=True,exist_ok=True)
    dest=builds/(label+"_"+commit[:12])
    if dest.exists():
        current=command([git,"-C",str(dest),"rev-parse","HEAD"])
        if current!=commit: raise RuntimeError("existing build directory SHA mismatch: "+label)
        return {"label":label,"head":current,"path":str(dest),"already_present":True}
    part=builds/("."+label+"_"+commit[:12]+".partial")
    if part.exists(): raise RuntimeError("partial staged checkout exists; inspect before retry: "+str(part))
    command([git,"clone","--quiet","--single-branch","--branch",ref,
             "--no-checkout",LEGACY_URL,str(part)],timeout=210)
    command([git,"-C",str(part),"checkout","--quiet","--detach",commit])
    current=command([git,"-C",str(part),"rev-parse","HEAD"])
    if current!=commit: raise RuntimeError("historic checkout SHA mismatch: "+label)
    if not (part/"consumer"/"GO.bat").is_file() or not (part/"windows-relay"/"windows_relay.py").is_file():
        raise RuntimeError("historic source snapshot lacks expected original components")
    os.replace(part,dest)
    return {"label":label,"head":current,"path":str(dest),"already_present":False}

def main(argv=None):
    p=argparse.ArgumentParser(description="Non-destructive Relay bin and legacy candidate staging")
    p.add_argument("--live",type=Path)
    p.add_argument("--repo",type=Path)
    p.add_argument("--expected-head",required=True)
    args=p.parse_args(argv)
    script=Path(__file__).resolve()
    repo=(args.repo or script.parents[2]).resolve()
    live=(args.live or (repo.parent/"Client"/"Relay")).resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live or repo in live.parents or live in repo.parents:
        raise RuntimeError("expected distinct existing canonical checkout and live runtime trees")
    git=git_binary()
    remote=command([git,"-C",str(repo),"remote","get-url","origin"]).lower()
    if WINDOWS_REPO.lower() not in remote: raise RuntimeError("wrong origin: refuse noncanonical source")
    dirty=command([git,"-C",str(repo),"status","--porcelain"])
    if dirty: raise RuntimeError("canonical checkout dirty; preserve work and stop")
    head=command([git,"-C",str(repo),"rev-parse","HEAD"])
    if head!=args.expected_head: raise RuntimeError("local checkout not the verified GitHub SHA")
    stamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    saved=archive_live(live,stamp)
    stages=[]
    for label,ref,commit in CANDIDATES:
        stages.append(stage_one(live,git,label,ref,commit))
    report={"schema":"pce011-stage-v1","source_sha":head,"live_unchanged":True,
            "quarantine":saved,"candidates":stages,
            "next":"Run candidate tests and independent STOP/identity+rollback gates before any activation"}
    report_path=live/"bin"/("STAGING_"+stamp+".json")
    report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("PCE011_STAGING="+json.dumps({
          "report":str(report_path),"bin":saved["archive"],
          "snapshot_files":saved["files"],"candidate_shas":[x["head"] for x in stages],
          "live_unchanged":True},separators=(",",":")))
    return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except (RuntimeError,OSError,ValueError,subprocess.TimeoutExpired) as e:
        print("PCE011_STAGING_BLOCKED="+str(e),file=sys.stderr)
        raise SystemExit(2)
