#!/usr/bin/env python3
"""PCE011.002 candidate source acceptance. Does NOT touch the loaded Relay."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
REFERENCES={"RELAY_PCE8_V16":"694d47ab89596d5c3801f749caa352b951a2be52",
            "ONE_CLICK_GO_R28":"d5b9db7ad785b5cae8dc3b64219303b9fcfa634a"}
RESULT_PATTERN=re.compile(r"Ran (\d+) tests? in ([0-9.]+)s")
RUN_DEADLINE=None
def utc():return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
def git(gitbin,folder,*args,timeout=30):
    r=subprocess.run([gitbin,"-C",str(folder),*args],text=True,capture_output=True,timeout=timeout)
    if r.returncode: raise RuntimeError("git "+str(args[:3])+" failed (exit "+str(r.returncode)+")")
    return r.stdout.strip()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(2**20),b""):h.update(chunk)
    return h.hexdigest()
def run(label,command,cwd,env,root,timeout=36):
    t=time.monotonic()
    if RUN_DEADLINE is not None:
        if RUN_DEADLINE-t < 3:
            return {"label":label,"status":"BLOCKED","reason":"bounded test operation deadline reached"}
        timeout=min(timeout,max(2,int(RUN_DEADLINE-t)-1))
    try:
        r=subprocess.run(command,cwd=cwd,env=env,text=True,encoding="utf-8",
                         errors="replace",capture_output=True,timeout=timeout)
        out=r.stdout+"\n"+r.stderr
        status="PASS" if r.returncode==0 else "FAIL"
        code=r.returncode
    except subprocess.TimeoutExpired:
        out="TIMEOUT after "+str(timeout)+"s"
        status="TIMEOUT"
        code=None
    except OSError as err:
        out=type(err).__name__+": "+str(err)
        status="BLOCKED"
        code=None
    log=root/(label+".log")
    log.write_text(out,encoding="utf-8")
    found=RESULT_PATTERN.findall(out)
    result={"label":label,"status":status,"exit_code":code,"seconds":round(time.monotonic()-t,2),
            "test_count":int(found[-1][0]) if found else None,
            "log_path":str(log),"log_sha256":sha(log)}
    if status!="PASS":
        result["failure_excerpt"]=out[-700:].replace("\r"," ").replace("\n"," ")[:700]
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--expected-head",required=True)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--live",type=Path,required=True)
    parser.add_argument("--ordinal",type=int,default=2)
    opts=parser.parse_args()
    repo=opts.repo.resolve()
    live=opts.live.resolve()
    gitbin=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    if not repo.is_dir() or not live.is_dir(): raise RuntimeError("mapped paths absent; STOP")
    remote=git(gitbin,repo,"remote","get-url","origin").lower()
    if "monag144/gpt-windows-relay" not in remote: raise RuntimeError("wrong Windows source origin")
    if git(gitbin,repo,"branch","--show-current")!=BRANCH: raise RuntimeError("unexpected local branch")
    if git(gitbin,repo,"status","--porcelain"): raise RuntimeError("dirty canonical tree; no pull")
    remote_head=git(gitbin,repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote_head or remote_head[0]!=opts.expected_head: raise RuntimeError("unexpected remote branch tip")
    git(gitbin,repo,"pull","--ff-only","origin",BRANCH,timeout=45)
    if git(gitbin,repo,"rev-parse","HEAD")!=opts.expected_head: raise RuntimeError("fast-forward SHA mismatch")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight,github_first_workflow_gate
    preflight=engineering_preflight(repo,opts.ordinal,series=11)
    gate=github_first_workflow_gate(
        {"canonical_repo_confirmed":True,"github_commit_sha":opts.expected_head,
         "remote_sha_verified":True,"relay_pull_sha_matches_remote":True},"source_acceptance")
    if not gate["ok"]:raise RuntimeError("source workflow gate denied "+str(gate["blockers"]))
    print("PCE11_GOVERNANCE="+json.dumps({"id":preflight["id"],"reads":preflight["reads"]},separators=(",",":")))
    manifests=sorted((live/"bin").glob("BROKEN_*.manifest.json"),reverse=True)
    if not manifests: raise RuntimeError("PCE11.001 bin archive manifest missing")
    manifest=json.loads(manifests[0].read_text(encoding="utf-8"))
    archive=Path(manifest["archive_path"])
    if not archive.is_file() or sha(archive)!=manifest["zip_sha256"]:
        raise RuntimeError("original Relay backup SHA mismatch")
    if manifest.get("file_count",0)<1: raise RuntimeError("empty original Relay backup")
    old_reports=sorted((live/"bin").glob("SOURCE_GATES_*/source-gates.json"),reverse=True)
    if old_reports:
        prior=json.loads(old_reports[0].read_text(encoding="utf-8"))
        print("PCE11_PRIOR_SOURCE_GATES="+json.dumps({"report":str(old_reports[0]),"source_sha":prior.get("source_sha"),
            "jobs":[{"label":x.get("label"),"status":x.get("status"),"test_count":x.get("test_count"),
                     "failure_excerpt":str(x.get("failure_excerpt",""))[:210]} for x in prior.get("results",[])]},
            separators=(",",":")))
    paths={}
    for label,exact in REFERENCES.items():
        d=live/"builds"/(label+"_"+exact[:12])
        if not d.is_dir() or git(gitbin,d,"rev-parse","HEAD")!=exact:
            raise RuntimeError("candidate "+label+" missing or wrong checkout SHA")
        if git(gitbin,d,"status","--porcelain"):raise RuntimeError("candidate dirty: "+label)
        paths[label]=d
    evidence=live/"bin"/("SOURCE_GATES_"+utc())
    evidence.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"]="1"
    env["PYTHONNOUSERSITE"]="1"
    global RUN_DEADLINE
    RUN_DEADLINE=time.monotonic()+210
    results=[]
    results.append(run("pce11-harness",[
        sys.executable,"-B","-m","unittest","discover","-s","tests",
        "-p","test_control_harness.py","-v"],repo/"consumer",env,evidence,timeout=20))
    results.append(run("pce11-staging",[
        sys.executable,"-B","-m","unittest","discover","-s","tests",
        "-p","test_pce11_quarantine_stage.py","-v"],repo/"windows-relay",env,evidence,timeout=20))
    results.append(run("pce11-benchmarks",[
        sys.executable,"-B","-m","unittest","discover","-s","tests",
        "-p","test_benchmark_runner.py","-v"],repo/"benchmarks",env,evidence,timeout=20))
    for label,folder in paths.items():
        for section in ("windows-relay","consumer"):
            results.append(run(label+"-"+section.replace("-","_"),[
                sys.executable,"-B","-m","unittest","discover","-s","tests",
                "-p","test_*.py"],folder/section,env,evidence,timeout=45))
        node=shutil.which("node")
        if node:
            for ix,js in enumerate(("windows-relay/content.js",
                "windows-relay/extension/content.js",
                "windows-relay/extension/service_worker.js",
                "windows-relay/extension-persistent/content.js",
                "windows-relay/extension-persistent/service_worker.js")):
                results.append(run(label+"-JS"+str(ix),[node,"--check",str(folder/js)],
                                   folder,env,evidence,timeout=8))
        else:
            results.append({"label":label+"-JS","status":"BLOCKED","reason":"node not installed"})
        ps=shutil.which("pwsh") or shutil.which("powershell")
        if ps:
            powershell_file=folder/"windows-relay"/"firefox_tab_adapter.ps1"
            literal=str(powershell_file).replace("'","''")
            ast=("$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile('"+
                 literal+"',[ref]$t,[ref]$e)|Out-Null;if($e.Count -gt 0){$e|ForEach-Object{Write-Error $_.Message};exit 1}")
            results.append(run(label+"-PS_Ast",[ps,"-NoLogo","-NoProfile","-NonInteractive","-Command",ast],
                               folder,env,evidence,timeout=12))
        else:
            results.append({"label":label+"-PS_Ast","status":"BLOCKED","reason":"PowerShell not installed"})
    record={"schema":"pce011-source-gates-v1","source_sha":opts.expected_head,
            "preflight":preflight,"backup_sha256":manifest["zip_sha256"],
            "backup_file_count":manifest["file_count"],
            "candidates":{k:REFERENCES[k] for k in paths},
            "results":results,"live_untouched":True}
    report=evidence/"source-gates.json"
    report.write_text(json.dumps(record,indent=2,default=str)+"\n",encoding="utf-8")
    concise=[{k:item.get(k) for k in ("label","status","test_count","seconds","failure_excerpt")
             if k in item} for item in results]
    print("PCE11_SOURCE_GATES="+json.dumps({"report":str(report),"source_sha":opts.expected_head,
        "backup_verified":True,"candidate_sha_verified":True,
        "all_source_checks_pass":all(x["status"]=="PASS" for x in results),
        "results":concise},separators=(",",":")))
    return 0 if all(x["status"]=="PASS" for x in results) else 2
if __name__=="__main__":
    try:sys.exit(main())
    except (RuntimeError,ValueError,OSError,subprocess.TimeoutExpired) as err:
        print("PCE11_002_BLOCKED="+str(err)[:320])
        sys.exit(2)
    finally:
        print("Reply to this with the sandwich technique")
