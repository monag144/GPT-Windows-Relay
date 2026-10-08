#!/usr/bin/env python3
"""PCE11.007: bounded classification of prior REDACTED process inventory, no live action."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREV_HEAD="ed90273e0af0048c5caa09df63835c1659c03c3e"
REPORT_NAME="PASSIVE_TOPOLOGY_2026-10-08T092500Z.json"

def run(args,timeout=25):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        encoding="utf-8",errors="replace",text=True,timeout=timeout)
    if p.returncode:raise RuntimeError("verification subprocess failed: "+str(args[:2])+" exit "+str(p.returncode))
    return p.stdout.strip()

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""): h.update(block)
    return h.hexdigest()

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--repo",type=Path,required=True)
    a.add_argument("--live",type=Path,required=True)
    a.add_argument("--expected-head",required=True)
    opts=a.parse_args()
    root=opts.repo.resolve();live=opts.live.resolve()
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    g=lambda *x:run([git,"-C",str(root),*x])
    if not root.is_dir() or not live.is_dir() or root==live:raise RuntimeError("source/live directory unavailable")
    if g("rev-parse","HEAD")!=PREV_HEAD:raise RuntimeError("local base changed since 006; do not overwrite")
    if g("branch","--show-current")!=BRANCH:raise RuntimeError("wrong branch")
    if "monag144/gpt-windows-relay" not in g("remote","get-url","origin").lower():
        raise RuntimeError("wrong GitHub origin")
    if g("status","--porcelain"):raise RuntimeError("source dirty; abort rather than clobber")
    remote=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=opts.expected_head:raise RuntimeError("remote source SHA changed")
    run([git,"-C",str(root),"pull","--ff-only","origin",BRANCH],timeout=65)
    if g("rev-parse","HEAD")!=opts.expected_head:raise RuntimeError("pulled HEAD did not match remote")
    sys.path.insert(0,str(root/"consumer"))
    from control_harness import engineering_preflight
    preflight=engineering_preflight(root,7,series=11)
    if not preflight["ok"]:raise RuntimeError("control preflight blocked")
    report=live/"bin"/REPORT_NAME
    if not report.is_file():raise RuntimeError("previous passive topology evidence missing")
    data=json.loads(report.read_text(encoding="utf-8"))
    if data.get("schema")!="pce011-passive-topology-v1" or data.get("git_sha")!=PREV_HEAD:
        raise RuntimeError("wrong report version or provenance")
    process=data.get("processes",{})
    if not process.get("available"):raise RuntimeError("prior process snapshot was unavailable")
    items=process.get("targeted",[])
    if not isinstance(items,list) or len(items)>50:raise RuntimeError("unexpected data count")
    idx={int(p["pid"]):p for p in items}
    ppids=process.get("pid_parent_map",{})
    if not isinstance(ppids,dict):raise RuntimeError("missing process ancestry map")
    categorized=[]
    for p in items:
        pid=int(p["pid"]);parent=int(p["ppid"])
        if pid<=0 or parent<0:raise RuntimeError("invalid process identifier")
        related=idx.get(parent,{})
        categorized.append({"pid":pid,"ppid":parent,"image":p["image"],
            "classification":p["role"],"parent_role":related.get("role","other_or_unobserved"),
            "parent_in_snapshot":str(parent) in ppids,
            "path_live":p.get("script_in_live_relay",False),
            "path_canonical":p.get("script_in_canonical_source",False),
            "has_commandline":p.get("has_commandline",False)})
    listener=data.get("ports",{}).get("listeners",{}).get("8766",[])
    pid=int(listener[0]["pid"]) if len(listener)==1 else 0
    matched=idx.get(pid)
    if not matched:raise RuntimeError("listener PID missing from targeted roles")
    roles={}
    for rec in categorized:roles.setdefault(rec["classification"],[]).append(rec)
    checks={"historical_pid":pid,"listener_classified_as":matched["role"],
       "hud_match_count":len(roles.get("hud",[])),
       "server_match_count":len(roles.get("relay-server",[])),
       "duplicate_instances_proven":False,
       "browser_identity_verified":False,"stop_safety_verified":False,
       "cutover_authorized":False}
    print("PCE11_007_ROLE_DETAILS="+json.dumps({"source_sha":opts.expected_head,
      "governance_id":preflight["id"],
      "control_shas":{k:v["sha256"] for k,v in preflight["reads"].items()},
      "source_report":str(report),"source_report_sha256":digest(report),
      "counts":{k:len(v) for k,v in roles.items()},
      "processes":categorized,"conclusions":checks},separators=(",",":")))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as e:
        print("PCE11_007_BLOCKED="+str(e)[:320],file=sys.stderr)
        sys.exit(2)
    finally:print("Reply to this with the sandwich technique")
