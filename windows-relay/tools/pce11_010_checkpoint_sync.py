#!/usr/bin/env python3
"""PCE11.010 pre-dispatch audit sync: exact Git commit only, without touching live Relay."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="9d8619fb25cff0e73ddfb47f0c277d055c305741"
AUDIT="docs/audits/AUDIT_2026-10-08T0933Z_PCE11_OPERATIONS_005_009.md"
AUDIT_BLOB="8e0ed9fe2da3c840f3ef1639c21db340aecee507"
ALLOWED={AUDIT,"windows-relay/TASKS.md",
         "windows-relay/tools/pce11_010_live_readiness.py",
         "windows-relay/tools/pce11_010_checkpoint_sync.py"}
MANDATORY=("consumer/control_harness.py","windows-relay/TASKS.md",
           "docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md",
           "docs/windows-relay-established-facts.md","docs/relay-sandwich-procedure.md")

def run(args,timeout=40):
    p=subprocess.run(args,capture_output=True,text=True,encoding="utf-8",
                     errors="replace",timeout=timeout)
    if p.returncode: raise RuntimeError("required Git verification failed (exit "+str(p.returncode)+")")
    return p.stdout.strip()
def blob_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()
def reads(repo):
    result={}
    for rel in MANDATORY:
        p=repo/rel
        if not p.is_file(): raise RuntimeError("mandatory control absent: "+rel)
        raw=p.read_bytes()
        if not raw.strip(): raise RuntimeError("empty control: "+rel)
        result[rel]={"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
    return result
def main(args=None):
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--expected-head",required=True)
    a=p.parse_args(args)
    repo=a.repo.resolve()
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    if not repo.is_dir():raise RuntimeError("no canonical checkout")
    g=lambda *tokens,timeout=40:run([git,"-C",str(repo),*tokens],timeout=timeout)
    before=reads(repo)
    if g("rev-parse","HEAD")!=PREVIOUS:raise RuntimeError("unexpected local HEAD; reconcile, do not overwrite")
    if g("branch","--show-current")!=BRANCH:raise RuntimeError("not on approved PCE011 branch")
    origin=g("remote","get-url","origin").lower()
    if "monag144/gpt-windows-relay" not in origin:raise RuntimeError("unexpected remote repository")
    if g("status","--porcelain"):raise RuntimeError("dirty checkout; refuse sync")
    line=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if len(line)<2 or line[0]!=a.expected_head:raise RuntimeError("remote SHA changed; no sync")
    g("fetch","--no-tags","origin","refs/heads/"+BRANCH,timeout=60)
    fetched=g("rev-parse","FETCH_HEAD")
    if fetched!=a.expected_head:raise RuntimeError("fetched SHA mismatch")
    changes=set(g("diff","--name-only","HEAD","FETCH_HEAD").splitlines())
    if changes-ALLOWED:raise RuntimeError("unexpected paths in governance-only pull: "+str(sorted(changes-ALLOWED))[:180])
    if g("rev-parse","FETCH_HEAD:"+AUDIT)!=AUDIT_BLOB:raise RuntimeError("remote audit blob changed")
    audit_text=g("show","FETCH_HEAD:"+AUDIT)
    if len(audit_text.encode("utf-8"))<300 or not all((".%03d"%i) in audit_text for i in range(5,10)):
        raise RuntimeError("audit missing one of five slot labels")
    if "COMPLETE" not in audit_text or "BLOCKED" not in audit_text:
        raise RuntimeError("unsubstantiated remote checkpoint")
    g("merge-base","--is-ancestor","HEAD","FETCH_HEAD")
    g("merge","--ff-only","FETCH_HEAD",timeout=60)  # exact pinned object without second fetch
    if g("rev-parse","HEAD")!=a.expected_head:raise RuntimeError("postpull head mismatch")
    after=reads(repo)
    module_file=repo/"consumer"/"control_harness.py"
    spec=importlib.util.spec_from_file_location("pce11_governance_sync",module_file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    validated=mod.engineering_preflight(repo,10,series=11)
    att=validated["checkpoints"].get("audit")
    if not validated["ok"] or not att or att["path"]!=AUDIT:
        raise RuntimeError("PCE11.010 preflight did not verify published audit")
    if g("status","--porcelain"):raise RuntimeError("postpull checkout dirty")
    print("PCE11_GOVSYNC_OK="+json.dumps({"old_head":PREVIOUS,"new_head":a.expected_head,
      "changed_paths":sorted(changes),"mandatory_read_hashes":after,
      "audit":{"path":att["path"],"sha256":att["sha256"],"window":att["window"]},
      "next":"PCE11.010 permitted after verified checkpoint; use new unique action ID",
      "live_relay_modified":False},separators=(",",":")))
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as err:
        print("PCE11_GOVSYNC_BLOCKED="+str(err)[:350],file=sys.stderr)
        raise SystemExit(2)
    finally:
        print("Reply to this with the sandwich technique")
