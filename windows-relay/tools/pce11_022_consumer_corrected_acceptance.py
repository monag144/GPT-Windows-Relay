#!/usr/bin/env python3
"""PCE11.022 source-only consumer historical fixture and migration provenance acceptance.

Checks .018 evidence; tests one failing protocol test, full Windows + consumer,
PCE11 contained-runner tests, JS syntax, extension mirror, archive and staged
v16 provenance. No service launch, STOP, browser or pending mission access.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,subprocess,sys,time,zipfile
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
AUDIT_REL="docs/audits/AUDIT_2026-10-08T1012Z_PCE11_OPERATIONS_015_019.md"
REVIEW_REL="docs/reviews/REVIEW_2026-10-08T1013Z_PCE11_OPERATIONS_000_019.md"
PREVIOUS="f0f74b4614f6dfe317ea5fb5d3e9aaebf13e8fe0"
FORENSICS="CONSUMER_FORENSICS_2026-10-08T101845Z.json"
INCIDENT_TEST="test_protocol.Tests.test_every_serialized_result_stdout_enforces_turn_discipline_and_sandwich"
EXPECTED_FAILURE_STDERR_SHA="db34a10dfe0cb1afe29b0cc4abde343e6820a63a6ced9a69271b45f810049928"
HISTORIC_BLOB="414b74121b1a5a5f2a049ebc84097223e7b5e69f"

def command(argv,cwd=None,timeout=40):
    p=subprocess.run(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                     encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:raise RuntimeError("source verification subprocess failed "+str(argv[:3])+" rc="+str(p.returncode))
    return p.stdout.strip()
def git(root,*items,timeout=40):
    exe=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    return command([exe,"-C",str(root),*items],timeout=timeout)
def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def run_case(repo,output_dir,label,argv,cwd,timeout=105):
    result=subprocess.run(argv,cwd=str(cwd),stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          text=True,encoding="utf-8",errors="replace",timeout=timeout,
                          env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"))
    out=output_dir/(label+".stdout.txt");err=output_dir/(label+".stderr.txt")
    out.write_text(result.stdout,encoding="utf-8")
    err.write_text(result.stderr,encoding="utf-8")
    m=re.search(r"(?m)^Ran (\d+) tests? in",result.stderr)
    count=int(m.group(1)) if m else None
    ok=result.returncode==0 and re.search(r"(?m)^OK(?:\s|$)",result.stderr) is not None
    failures=[x[:160] for x in re.findall(r"(?m)^(?:FAIL|ERROR):\s+(.+)$",result.stderr)][:6]
    record={"suite":label,"passed":ok,"exit_code":result.returncode,
            "tests_ran":count,"stderr_sha256":digest(err),"stdout_sha256":digest(out),
            "failure_ids":failures}
    return record
def build_cases(repo):
    py=sys.executable
    work=repo/"windows-relay"
    for name,flags,folder in (
      ("target_protocol",[py,"-B","-m","unittest","discover","-s","tests","-p","test_protocol.py","-v"],work),
      ("windows_full",[py,"-B","-m","unittest","discover","-s","tests","-p","test_*.py","-v"],work),
      ("consumer_governance",[py,"-B","-m","unittest","discover","-s","tests","-p","test_engineering_governance.py","-v"],repo/"consumer"),
      ("consumer_migration",[py,"-B","-m","unittest","discover","-s","tests","-p","test_migration_evidence_manifest.py","-v"],repo/"consumer"),
      ("consumer_full",[py,"-B","-m","unittest","discover","-s","tests","-p","test_*.py","-v"],repo/"consumer")):
        yield name,flags,folder
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--expected-head",required=True)
    a=ap.parse_args()
    repo=a.repo.resolve();live=a.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("canonical and live tree missing/overlap")
    if git(repo,"rev-parse","HEAD")!=PREVIOUS:raise RuntimeError("unexpected .021 source base; reconcile, do not overwrite")
    if git(repo,"branch","--show-current")!=BRANCH:raise RuntimeError("wrong branch")
    if "monag144/gpt-windows-relay" not in git(repo,"remote","get-url","origin").lower():
        raise RuntimeError("wrong repository")
    if git(repo,"status","--porcelain"):raise RuntimeError("dirty source")
    rem=git(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if not rem or rem[0]!=a.expected_head:raise RuntimeError("remote HEAD mismatch")
    git(repo,"pull","--ff-only","origin",BRANCH,timeout=80)
    if git(repo,"rev-parse","HEAD")!=a.expected_head or git(repo,"status","--porcelain"):
        raise RuntimeError("untrusted source checkout after FF")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    pre=engineering_preflight(repo,22,series=11)
    if not pre["ok"]:raise RuntimeError("required controls unverified")
    historical=(repo/AUDIT_REL,repo/REVIEW_REL)
    if not all(path.is_file() for path in historical):
        raise RuntimeError("prior audited checkpoints absent")
    provenance=live/"bin"/FORENSICS
    if not provenance.is_file():raise RuntimeError(".021 persisted forensic report missing")
    prior=json.loads(provenance.read_text(encoding="utf-8"))
    if prior.get("source_sha")!=PREVIOUS or prior.get("manifest_entry_count")!=42 or prior.get("tests_rerun") is not False:
        raise RuntimeError("previous forensic source provenance invalid")
    # Evidence integrity checks first: no replay of failed .017/.018 actions.
    incident=live/"bin"/"SOURCE_SUITE_FORENSICS_2026-10-08T100608Z"/"suite.stderr.txt"
    if not incident.is_file() or digest(incident)!=EXPECTED_FAILURE_STDERR_SHA:
        raise RuntimeError("PCE11.018 failing suite evidence absent/changed")
    source=(repo/"windows-relay"/"windows_relay.py").read_text(encoding="utf-8-sig")
    if source.count("monag144/GPT-Windows-Relay") < 1:
        raise RuntimeError("exact canonical repo reminder still missing")
    if "OPERATION_DISCIPLINE_REMINDER=" not in source:
        raise RuntimeError("governance stdout reminder removed")
    stamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    evidence=live/"bin"/("SOURCE_ACCEPTANCE_"+stamp)
    evidence.mkdir(exist_ok=False)
    result={"schema":"pce011-022-source-acceptance-v1","repo_sha":a.expected_head,
      "mandatory_controls":pre["reads"],"canonical_reminder_restored":True,
      "prior_failed_suite_sha256":EXPECTED_FAILURE_STDERR_SHA,
      "unit_suites":[],"javascript_checks":[],"archive":None,"historic_v16":None,
      "full_acceptance":False,"no_new_process":True,"canary_authorized":False}
    try:
        # Smallest regression first, then complete suites, never omit a failed test.
        for name,argv,cwd in build_cases(repo):
            case=run_case(repo,evidence,name,argv,cwd,timeout=135)
            result["unit_suites"].append(case)
            if not case["passed"]:
                raise RuntimeError("test suite failed: "+name+" cases="+str(case["failure_ids"]))
        node=shutil.which("node")
        if not node:raise RuntimeError("Node.js unavailable for JS syntax validation")
        scripts=["windows-relay/extension/content.js",
                 "windows-relay/extension/service_worker.js",
                 "windows-relay/extension-persistent/content.js",
                 "windows-relay/extension-persistent/service_worker.js"]
        for path in scripts:
            p=repo/path
            if not p.is_file():raise RuntimeError("missing extension source "+path)
            check=subprocess.run([node,"--check",str(p)],stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,text=True,encoding="utf-8",
                                 errors="replace",timeout=25)
            result["javascript_checks"].append({"file":path,
                "passed":check.returncode==0,"sha256":digest(p)})
            if check.returncode:raise RuntimeError("JS syntax rejected "+path)
        if digest(repo/scripts[0])!=digest(repo/scripts[2]):
            raise RuntimeError("Firefox extension mirrored content diverged")
        sys.path.insert(0,str(repo/"windows-relay"/"tools"))
        import pce11_013_isolated_supervisor as legacy
        import pce11_win32_containment as containment
        stage=legacy.candidate(repo,live)
        if stage["normalized_worktree_blob"]!=HISTORIC_BLOB:
            raise RuntimeError("historical v16 file changed")
        if not containment.containment_contract_self_test():
            raise RuntimeError("contained launch ordering regression")
        import pce11_016_v16_health_canary as health
        result["archive"]=health.check_archive(live)
        result["historic_v16"]={"blob":stage["normalized_worktree_blob"],
                              "head":stage["git_head"]}
        if health.port_pids(8768):
            raise RuntimeError("v16 sidecar port was already active")
        git(repo,"diff","--check")
        result["full_acceptance"]=True
    except BaseException as e:
        result["failure"]=type(e).__name__+": "+str(e)[:350]
    finally:
        report=evidence/"acceptance.json"
        report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    compact={"report":str(report),"repo_sha":a.expected_head,
        "read_sha256":{k:v["sha256"] for k,v in pre["reads"].items()},
        "unit_suites":[{"name":x["suite"],"tests":x["tests_ran"],
             "passed":x["passed"],"failed_ids":x["failure_ids"]} for x in result["unit_suites"]],
        "js_checks":len(result["javascript_checks"]),"archive_verified":bool(result["archive"]),
        "historic_source_verified":bool(result["historic_v16"]),
        "source_acceptance_passed":result["full_acceptance"],
        "sidecar_launched":False,"live_cutover_authorized":False,
        "failure":result.get("failure")}
    print("PCE11_022_ACCEPTANCE="+json.dumps(compact,separators=(",",":")))
    return 0 if result["full_acceptance"] else 2

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        print("PCE11_022_BLOCKED="+type(exc).__name__+": "+str(exc)[:250],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
