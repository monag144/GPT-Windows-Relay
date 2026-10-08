#!/usr/bin/env python3
"""PCE11.020 pre-dispatch audit+review sync: exact Git commit only, without touching live Relay."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="e9872b6b45bb0ffbf6013d80038134bc602e53b8"
AUDIT="docs/audits/AUDIT_2026-10-08T1012Z_PCE11_OPERATIONS_015_019.md"
REVIEW="docs/reviews/REVIEW_2026-10-08T1013Z_PCE11_OPERATIONS_000_019.md"
AUDIT_BLOB="0cb891391ec7afef9c303356405ee9d49a804bdf"
REVIEW_BLOB="8226827b80aee944ae9500af26bc1d13f132e964"
ALLOWED={AUDIT,REVIEW,"windows-relay/TASKS.md",
         "windows-relay/TASKS_2026-10-08T1011Z_PCE11_PRE020_FULL_SNAPSHOT.md",
         "windows-relay/tools/pce11_020_checkpoint_acceptance.py",
         "windows-relay/tools/pce11_020_checkpoint_sync.py"}
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
    if len(audit_text.encode("utf-8"))<300 or not all((".%03d"%i) in audit_text for i in range(15,20)):
        raise RuntimeError("audit missing one of five slot labels")
    if "COMPLETE" not in audit_text or "BLOCKED" not in audit_text:
        raise RuntimeError("unsubstantiated remote checkpoint")
    if g("rev-parse","FETCH_HEAD:"+REVIEW)!=REVIEW_BLOB:
        raise RuntimeError("remote review blob changed")
    review_text=g("show","FETCH_HEAD:"+REVIEW)
    if not all(("PCE11.%03d"%i) in review_text for i in range(20)):
        raise RuntimeError("twenty-turn review missing one or more ordinal labels")
    if "COMPLETE" not in review_text or "BLOCKED" not in review_text:
        raise RuntimeError("unsubstantiated twenty-turn review")
    g("merge-base","--is-ancestor","HEAD","FETCH_HEAD")
    g("merge","--ff-only","FETCH_HEAD",timeout=60)  # exact pinned object without second fetch
    if g("rev-parse","HEAD")!=a.expected_head:raise RuntimeError("postpull head mismatch")
    after=reads(repo)
    module_file=repo/"consumer"/"control_harness.py"
    spec=importlib.util.spec_from_file_location("pce11_governance_sync",module_file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    validated=mod.engineering_preflight(repo,20,series=11)
    att=validated["checkpoints"].get("audit")
    rview=validated["checkpoints"].get("review")
    if not validated["ok"] or not att or att["path"]!=AUDIT or not rview or rview["path"]!=REVIEW:
        raise RuntimeError("PCE11.020 preflight did not verify both published checkpoints")
    if (repo/"windows-relay"/"TASKS.md").stat().st_size>10240:
        raise RuntimeError("TASKS.md still violates documentation size limit")
    if g("status","--porcelain"):raise RuntimeError("postpull checkout dirty")
    print("PCE11_GOVSYNC_OK="+json.dumps({"old_head":PREVIOUS,"new_head":a.expected_head,
      "changed_paths":sorted(changes),"mandatory_read_hashes":after,
      "audit":{"path":att["path"],"sha256":att["sha256"],"window":att["window"]},
      "review":{"path":rview["path"],"sha256":rview["sha256"],"window":rview["window"]},
      "next":"PCE11.020 permitted after both audited checkpoints; use new unique action ID",
      "live_relay_modified":False},separators=(",",":")))
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as err:
        print("PCE11_GOVSYNC_BLOCKED="+str(err)[:350],file=sys.stderr)
        raise SystemExit(2)
    finally:
        print("Reply to this with the sandwich technique")
