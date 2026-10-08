#!/usr/bin/env python3
"""PCE11.015 offline acceptance of reviewed Win32 job containment. No process launch."""
from __future__ import annotations
import argparse,ast,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="3c7e754701eeca33a65693aa9cabd8b783800efc"
AUDIT="docs/audits/AUDIT_2026-10-08T0951Z_PCE11_OPERATIONS_010_014.md"
PROBE_FILES=("windows-relay/tools/pce11_win32_containment.py",
             "windows-relay/tests/test_pce11_win32_containment.py",
             "windows-relay/tools/pce11_013_isolated_supervisor.py",
             "windows-relay/tests/test_pce11_isolated_supervisor.py")
UNIT_TEST_PATTERNS=("test_pce11_isolated_supervisor.py","test_pce11_win32_containment.py")

def run(args,timeout=45):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf-8",errors="replace",timeout=timeout)
    return p
def ok(args,timeout=45):
    r=run(args,timeout)
    if r.returncode:raise RuntimeError("Command failed: "+Path(str(args[0])).name+" rc="+str(r.returncode)+" "+r.stderr[-400:])
    return r.stdout.strip()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def features(root):
    contain=(root/PROBE_FILES[0]).read_text(encoding="utf-8")
    source=(root/PROBE_FILES[2]).read_text(encoding="utf-8")
    checks={
        "native_suspended_create":all(x in contain for x in (
            "CREATE_SUSPENDED","CreateProcessW","AssignProcessToJobObject","ResumeThread")),
        "private_job_cleanup":all(x in contain for x in (
            "TerminateJobObject","TerminateProcess","JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE")),
        "launcher_does_not_touch_relay":all(x not in contain for x in (
            "taskkill","127.0.0.1:8766","relay-control.ps1","firefox.exe")),
        "old_canary_held":'raise RuntimeError("canary disabled until suspended-start containment is tested")' in source
    }
    if not all(checks.values()):raise RuntimeError("source safety contract failed: "+str(checks))
    for path in PROBE_FILES:
        ast.parse((root/path).read_text(encoding="utf-8-sig"),filename=path)
    return checks
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--live",type=Path,required=True)
    parser.add_argument("--expected-head",required=True)
    a=parser.parse_args()
    root=a.repo.resolve();live=a.live.resolve()
    if not root.is_dir() or not live.is_dir() or root==live:raise RuntimeError("missing source/live")
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    g=lambda *params,timeout=30:ok([git,"-C",str(root),*params],timeout=timeout)
    if g("rev-parse","HEAD")!=PREVIOUS:raise RuntimeError("not at verified PCE11.015 audited base")
    if g("branch","--show-current")!=BRANCH:raise RuntimeError("unapproved branch")
    if "monag144/gpt-windows-relay" not in g("remote","get-url","origin").lower():
        raise RuntimeError("wrong remote")
    if g("status","--porcelain"):raise RuntimeError("dirty source")
    remote=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=a.expected_head:raise RuntimeError("remote HEAD not pinned")
    g("pull","--ff-only","origin",BRANCH,timeout=75)
    if g("rev-parse","HEAD")!=a.expected_head or g("status","--porcelain"):
        raise RuntimeError("source fast-forward failed or checkout dirty")
    sys.path.insert(0,str(root/"consumer"))
    from control_harness import engineering_preflight
    proof=engineering_preflight(root,15,series=11)
    check=proof.get("checkpoints",{}).get("audit",{})
    if check.get("path")!=AUDIT or check.get("window")!=[10,14]:
        raise RuntimeError("PCE11.015 5-operation audited checkpoint unverified")
    safety=features(root)
    tests=[]
    for pattern in UNIT_TEST_PATTERNS:
        args=[sys.executable,"-B","-m","unittest","discover","-s","tests","-p",pattern,"-v"]
        result=subprocess.run(args,cwd=str(root/"windows-relay"),
                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                   encoding="utf-8",errors="replace",timeout=65)
        passed=result.returncode==0 and "OK" in result.stderr
        if not passed:
            raise RuntimeError("targeted unit tests failed "+pattern+": "+result.stderr[-800:])
        tests.append({"pattern":pattern,"passed":True,
          "test_count":int(result.stderr.split("Ran ")[-1].split(" test")[0]) if "Ran " in result.stderr else None})
    g("diff","--check")
    evidence={
        "schema":"pce011-static-containment-gate-v1",
        "time_utc":datetime.now(timezone.utc).isoformat(),
        "sha":a.expected_head,"reads":proof["reads"],"audit":check,
        "tested_sources":{p:sha(root/p) for p in PROBE_FILES},
        "safety":safety,"tests":tests,
        "production_process_launched":False,"sidecar_process_launched":False,
        "canary_launch_authorized":False,"browser_affected":False}
    dest=live/"bin"/("CONTAINMENT_GATE_"+datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")+".json")
    if dest.exists():raise FileExistsError("evidence collision")
    dest.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    print("PCE11_015_STATIC_CONTAINMENT="+json.dumps({
      "report":str(dest),"remote_source_sha":a.expected_head,
      "reads_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
      "audit_window":check["window"],"safety_contract":safety,
      "unit_tests":tests,"run_did_not_start_process":True,
      "canary_mode_disabled":True,"live_cutover_authorized":False
    },separators=(",",":")))
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as err:
        print("PCE11_015_BLOCKED="+type(err).__name__+" "+str(err)[:350],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
