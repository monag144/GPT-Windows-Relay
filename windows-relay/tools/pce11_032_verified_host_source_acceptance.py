#!/usr/bin/env python3
"""PCE11.032 corrected source-only acceptance of Win32 HTTP-host ancestry and exact private Job proof.

GitHub fast-forward exact pinned source; validate .026 forensic, five controls,
new canary regression tests, full Windows+consumer suites, 4 JavaScript syntax
gates, original backup, source mirror and historic v16 blob. No v16 startup.
"""
from __future__ import annotations
import argparse,ast,hashlib,json,os,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="a2546f1f28017032dc46a336bcbfe5803bde9322"
FAILED_PREVIOUS="SOURCE_HOST_IDENTITY_ACCEPTANCE_2026-10-08T105718Z"
PREVIOUS_PROOF="PCE11_030_LINEAGE_20261008T105116Z/lineage-report.json"
EXPECTED_HISTORIC_BLOB="414b74121b1a5a5f2a049ebc84097223e7b5e69f"

def check(argv,timeout=45,cwd=None):
    p=subprocess.run(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:raise RuntimeError("Git validation failed: "+str(argv[:3])+" code "+str(p.returncode))
    return p.stdout.strip()
def g(root,*args,timeout=45):
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    return check([git,"-C",str(root),*args],timeout)
def sha(file):
    h=hashlib.sha256()
    with Path(file).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def suite(py,root,pattern,label,output):
    p=subprocess.run([py,"-B","-m","unittest","discover","-s","tests",
           "-p",pattern,"-v"],cwd=str(root),stdout=subprocess.PIPE,
           stderr=subprocess.PIPE,text=True,encoding="utf-8",errors="replace",
           timeout=145,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"))
    stderr=output/(label+".stderr.txt");stdout=output/(label+".stdout.txt")
    stderr.write_text(p.stderr,encoding="utf-8");stdout.write_text(p.stdout,encoding="utf-8")
    found=re.search(r"(?m)^Ran (\d+) tests? in",p.stderr)
    failing=re.findall(r"(?m)^(?:FAIL|ERROR): ([^\r\n]+)",p.stderr)
    record={"name":label,"exit_code":p.returncode,
       "tests":int(found.group(1)) if found else None,
       "passed":p.returncode==0 and re.search(r"(?m)^OK(?:\s|$)",p.stderr) is not None,
       "failure_cases":failing[:5],"stderr_sha256":sha(stderr)}
    return record
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--expected-head",required=True)
    a=ap.parse_args()
    repo=a.repo.resolve();live=a.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:raise RuntimeError("independent source and live roots required")
    if g(repo,"rev-parse","HEAD")!=PREVIOUS:raise RuntimeError("unexpected .031 source HEAD")
    if g(repo,"branch","--show-current")!=BRANCH:raise RuntimeError("wrong source branch")
    if "monag144/gpt-windows-relay" not in g(repo,"remote","get-url","origin").lower():
        raise RuntimeError("noncanonical GitHub origin")
    if g(repo,"status","--porcelain"):raise RuntimeError("dirty source checkout")
    remote=g(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if len(remote)<2 or remote[0]!=a.expected_head:
        raise RuntimeError("remote branch moved from pinned source")
    g(repo,"fetch","--no-tags","origin","refs/heads/"+BRANCH,timeout=65)
    if g(repo,"rev-parse","FETCH_HEAD")!=a.expected_head:raise RuntimeError("wrong fetched source")
    g(repo,"merge-base","--is-ancestor","HEAD","FETCH_HEAD")
    g(repo,"merge","--ff-only","FETCH_HEAD",timeout=60)
    if g(repo,"rev-parse","HEAD")!=a.expected_head or g(repo,"status","--porcelain"):
        raise RuntimeError("source checkout changed outside pinned ff-only")

    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    pre=engineering_preflight(repo,32,series=11)
    if not pre.get("ok"):raise RuntimeError("mandatory engineering preflight failed")
    last=live/"bin"/FAILED_PREVIOUS/"acceptance.json"
    if not last.is_file():raise RuntimeError("prior PCE11.031 failure evidence missing")
    failed=json.loads(last.read_text(encoding="utf-8"))
    if (failed.get("schema")!="pce011-031-native-host-identity-v1"
        or failed.get("sha")!=PREVIOUS
        or failed.get("source_acceptance_passed") is not False
        or failed.get("unit_suites",[{}])[0].get("name")!="target_v16"
        or failed["unit_suites"][0].get("passed") is not False):
        raise RuntimeError("PCE11.031 one-test failure report was not recognized")
    base=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))
    prior=base/"GPTWindowsRelay"/"ops"/PREVIOUS_PROOF
    if not prior.is_file():raise RuntimeError("PCE11.030 native process evidence absent")
    d=json.loads(prior.read_text(encoding="utf-8"))
    if (d.get("schema")!="pce011-030-native-python-lineage-v1"
        or d.get("source_sha")!=PREVIOUS or d.get("success") is not True
        or d.get("host_direct_child_of_launcher") is not True
        or d.get("launcher_in_exact_private_job") is not True
        or d.get("host_is_in_exact_private_job") is not True
        or d.get("observed_host_exit_after_job_close") is not True
        or d.get("job_kill_verified") is not True
        or d.get("main_preserved") is not True
        or d.get("port8768_free_after") is not True
        or d.get("no_relay_service_started") is not True):
        raise RuntimeError("native launcher/host exact Job containment proof not accepted")

    src=repo/"windows-relay"/"tools"/"pce11_016_v16_health_canary.py"
    helper=repo/"windows-relay"/"tools"/"pce11_private_host_identity.py"
    txt=src.read_text(encoding="utf-8-sig")
    identity=helper.read_text(encoding="utf-8-sig")
    ast.parse(txt,filename=str(src))
    ast.parse(identity,filename=str(helper))
    flags={
      "observed_pid":'result["observed_status_pid"]=status.get("pid")' in txt,
      "observed_missions":'result["observed_pending_missions"]=status.get("pending_missions")' in txt,
      "listener_ownership":'owners=port_pids(SIDECAR_PORT)' in txt,
      "exact_host_attestation":'host=attest_private_host(status["pid"],p.pid,p.job)' in txt,
      "direct_parent_query":"NtQueryInformationProcess" in identity,
      "exact_job_membership":"IsProcessInJob" in identity,
      "held_handle_exit":"host.wait_for_exit()" in txt,
      "host_cleanup":"host.close()" in txt,
      "host_executable_verification":"QueryFullProcessImageNameW" in identity,
      "legacy_numbered_canary_disabled":"obsolete .018 canary entrypoint disabled" in txt,
      "separate_mission_validation":"isolated sidecar reported nonzero or malformed mission count" in txt}
    if not all(flags.values()):raise RuntimeError("HTTP host owner attestation gate missing")
    when=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out=live/"bin"/("SOURCE_HOST_IDENTITY_ACCEPTANCE_032_"+when)
    out.mkdir(exist_ok=False)
    report={"schema":"pce011-032-native-host-identity-v1","sha":a.expected_head,
      "five_reads":pre["reads"],"host_identity_guards":flags,
      "unit_suites":[],"javascript_checks":[],"original_archive":None,
      "historic_v16_blob":None,"content_mirror_equal":None,
      "source_acceptance_passed":False,
      "isolated_v16_launched":False,"production_mutated":False,
      "next_canary_automatically_authorized":False}
    try:
        suites=(
          ("target_v16",repo/"windows-relay","test_pce11_v16_health_canary.py"),
          ("target_host_identity",repo/"windows-relay","test_pce11_private_host_identity.py"),
          ("target_containment",repo/"windows-relay","test_pce11_win32_containment.py"),
          ("windows_full",repo/"windows-relay","test_*.py"),
          ("consumer_full",repo/"consumer","test_*.py"))
        minima={"target_v16":12,"target_host_identity":9,"target_containment":12,
                "windows_full":493,"consumer_full":119}
        for label,root,pattern in suites:
            result=suite(sys.executable,root,pattern,label,out)
            report["unit_suites"].append(result)
            if not result["passed"] or int(result["tests"] or 0)<minima[label]:
                raise RuntimeError("source suite failed or lost tests "+label+
                    " "+str(result["failure_cases"])[:200])
        node=shutil.which("node")
        if not node:raise RuntimeError("Node is absent for JS syntax validation")
        js=("windows-relay/extension/content.js",
            "windows-relay/extension/service_worker.js",
            "windows-relay/extension-persistent/content.js",
            "windows-relay/extension-persistent/service_worker.js")
        for rel in js:
            file=repo/rel
            if not file.is_file():raise RuntimeError("missing JS "+rel)
            p=subprocess.run([node,"--check",str(file)],capture_output=True,
                  text=True,encoding="utf-8",errors="replace",timeout=25)
            report["javascript_checks"].append({"file":rel,"passed":p.returncode==0})
            if p.returncode:raise RuntimeError("JS syntax rejected "+rel)
        a1=repo/js[0];a2=repo/js[2]
        report["content_mirror_equal"]=sha(a1)==sha(a2)
        if not report["content_mirror_equal"]:raise RuntimeError("extension content mirrors diverged")
        sys.path.insert(0,str(repo/"windows-relay"/"tools"))
        import pce11_016_v16_health_canary as health
        import pce11_013_isolated_supervisor as legacy
        archive=health.check_archive(live)
        stage=legacy.candidate(repo,live)
        if stage["normalized_worktree_blob"]!=EXPECTED_HISTORIC_BLOB:
            raise RuntimeError("original v16 source provenance changed")
        if health.port_pids(8768):raise RuntimeError("sidecar port occupied, no launch")
        report["original_archive"]=archive
        report["historic_v16_blob"]=stage["normalized_worktree_blob"]
        g(repo,"diff","--check")
        report["source_acceptance_passed"]=True
    except BaseException as exc:
        report["failure"]=type(exc).__name__+": "+str(exc)[:350]
    finally:
        path=out/"acceptance.json"
        path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    brief={
      "report":str(path),"git_sha":a.expected_head,
      "five_read_sha256":{k:v["sha256"] for k,v in pre["reads"].items()},
      "host_identity_guards":flags,
      "suites":[{"name":x["name"],"tests":x["tests"],"passed":x["passed"],
                 "failure_cases":x["failure_cases"]} for x in report["unit_suites"]],
      "js_syntax":report["javascript_checks"],
      "archive_verified":bool(report["original_archive"]),
      "historical_source_verified":bool(report["historic_v16_blob"]),
      "acceptance_passed":report["source_acceptance_passed"],
      "failure":report.get("failure"),
      "v16_launched":False,"live_replaced":False,"canary_relaunch_authorized":False}
    print("PCE11_032_HOST_IDENTITY_ACCEPTANCE="+json.dumps(brief,separators=(",",":")))
    return 0 if report["source_acceptance_passed"] else 2

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as ex:
        print("PCE11_032_BLOCKED="+type(ex).__name__+": "+str(ex)[:320],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
