#!/usr/bin/env python3
"""PCE11.011 read-only live-vs-source control policy forensics; no STOP or runtime edit."""
from __future__ import annotations
import argparse,base64,difflib,hashlib,json,os,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="8fd2b7f09f81446b3cb0af226f32250308779f5d"
CHECKPOINT="docs/audits/AUDIT_2026-10-08T0933Z_PCE11_OPERATIONS_005_009.md"
PREVIOUS_REPORT="LIVE_READINESS_2026-10-08T093733Z.json"
POLICY_FEATURES={
    "stop_pause_branch":"$Action -in @('stop','pause')",
    "browser_quiescence_wait":"WaitBrowserQuiesced",
    "stop_disarm_request":"SetBackendArm $false",
    "stop_result_verification":"BROWSER_QUIESCENCE=",
    "stop_process_termination":"taskkill /PID",
    "stop_sentinel":".relay-paused",
    "emergency_kill_branch":"$Action -eq 'kill'",
    "hud_kill":"KillHudOnly",
    "manual_retry_branch":"$Action -eq 'retry'",
    "resume_branch":"$Action -eq 'resume'",
    "watchdog_supervision":"GenuineWatchdogs",
}
KEYWORDS=("stop","pause","quies","arm","kill","watchdog","retry","resume","hud","status")

def shell(args,timeout=35):
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if r.returncode:raise RuntimeError("verification failed: "+Path(str(args[0])).name+" exit "+str(r.returncode))
    return r.stdout.strip()

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def self_test():
    a=["a","pause","STOP"];b=["a","PAUSE","STOP","kill"]
    details=diff_metadata(a,b)
    if len(details)!=2 or details[0]["a_range"]!=[2,2] or details[1]["b_range"]!=[4,4]:
        raise RuntimeError("diff metadata self-test failed")
    if details[0]["keywords"]!=["pause"]:raise RuntimeError("feature keyword test failed")

def diff_metadata(a,b):
    ops=difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes()
    out=[]
    for action,i,j,k,l in ops:
        if action=="equal":continue
        impact="\n".join(a[i:j]+b[k:l]).lower()
        out.append({"kind":action,
           "a_range":[i+1,j],"b_range":[k+1,l],
           "old_block_sha256":hashlib.sha256("\n".join(a[i:j]).encode()).hexdigest(),
           "new_block_sha256":hashlib.sha256("\n".join(b[k:l]).encode()).hexdigest(),
           "keywords":[keyword for keyword in KEYWORDS if keyword in impact]})
    return out

def syntax_parse(paths):
    pwsh=shutil.which("powershell") or shutil.which("pwsh") or "powershell.exe"
    results={}
    for key,path in paths.items():
        literal=str(path).replace("'","''")
        ps=("$ErrorActionPreference='Stop'; "
            "$tokens=$null; $errors=$null; "
            "[void][System.Management.Automation.Language.Parser]::ParseFile('"
            +literal+"',[ref]$tokens,[ref]$errors); "
            "@{error_count=@($errors).Count} | ConvertTo-Json -Compress")
        encoded=base64.b64encode(ps.encode("utf-16le")).decode("ascii")
        try:
            obj=json.loads(shell([pwsh,"-NoProfile","-NonInteractive","-EncodedCommand",encoded],timeout=22))
            results[key]={"available":True,"syntax_error_count":int(obj["error_count"])}
        except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
            results[key]={"available":False,"reason":type(e).__name__}
    return results

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--expected-head",required=True)
    ns=ap.parse_args()
    self_test()
    repo=ns.repo.resolve();live=ns.live.resolve()
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    g=lambda *args,timeout=35:shell([git,"-C",str(repo),*args],timeout=timeout)
    if not repo.is_dir() or not live.is_dir() or repo==live:raise RuntimeError("wrong root")
    if g("rev-parse","HEAD")!=PREVIOUS:raise RuntimeError("unexpected local HEAD")
    if g("branch","--show-current")!=BRANCH:raise RuntimeError("unexpected branch")
    if "monag144/gpt-windows-relay" not in g("remote","get-url","origin").lower():
        raise RuntimeError("not canonical GitHub origin")
    if g("status","--porcelain"):raise RuntimeError("dirty checkout")
    remote=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=ns.expected_head:raise RuntimeError("remote SHA changed")
    g("pull","--ff-only","origin",BRANCH,timeout=65)
    if g("rev-parse","HEAD")!=ns.expected_head:raise RuntimeError("pulled SHA mismatch")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    proof=engineering_preflight(repo,11,series=11)
    if not proof["ok"]:raise RuntimeError("PCE11.011 governance incomplete")
    audit=repo/CHECKPOINT
    if not audit.is_file():raise RuntimeError("history checkpoint absent")
    previous=live/"bin"/PREVIOUS_REPORT
    if not previous.is_file():raise RuntimeError("previous PCE11.010 readiness missing")
    old=json.loads(previous.read_text(encoding="utf-8"))
    if old.get("schema")!="pce011-live-readiness-v1" or old.get("repo_sha")!=PREVIOUS:
        raise RuntimeError("prior live evidence untrusted")
    current_state=old.get("status",{}).get("values",{})
    live_ctrl=live/"relay-control.ps1"
    source_ctrl=repo/"windows-relay"/"relay-control.ps1"
    if not live_ctrl.is_file() or not source_ctrl.is_file():
        raise RuntimeError("control script missing")
    before=live_ctrl.read_text(encoding="utf-8-sig").splitlines()
    after=source_ctrl.read_text(encoding="utf-8-sig").splitlines()
    hunks=diff_metadata(before,after)
    features={k:{"live":v.lower() in "\n".join(before).lower(),
                 "source":v.lower() in "\n".join(after).lower()}
              for k,v in POLICY_FEATURES.items()}
    syntax=syntax_parse({"live":live_ctrl,"canonical":source_ctrl})
    stopgen=current_state.get("stop_generation")
    ackgen=current_state.get("browser_quiesced_generation")
    status={"armed":current_state.get("armed"),
            "pending_missions_count":current_state.get("pending_missions"),
            "stop_generation":stopgen,"last_quiesced_generation":ackgen,
            "latest_stop_generation_quiesced":bool(type(stopgen) is int and stopgen>0 and stopgen==ackgen),
            "current_stop_verified":False}
    output={"schema":"pce011-control-drift-v1",
      "time_utc":datetime.now(timezone.utc).isoformat(),
      "source_sha":ns.expected_head,"mandatory_reads":proof["reads"],
      "checkpoint_sha256":sha(audit),"prior_readiness_sha256":sha(previous),
      "original_live_control_sha256":sha(live_ctrl),
      "canonical_control_sha256":sha(source_ctrl),
      "line_counts":{"live":len(before),"canonical":len(after)},
      "diff_hunks":hunks,"feature_presence":features,"powershell_syntax":syntax,
      "status_at_010":status,"browser_identity_verified":False,
      "loaded_extension_verified":False,"last_STOP_proven_safe":False,
      "pending_missions_untouched":True,
      "rollback_canary_proven":False,"live_cutover_authorized":False}
    now=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    dest=live/"bin"/("CONTROL_DRIFT_"+now+".json")
    if dest.exists():raise FileExistsError("report path collision")
    dest.write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    exposed={"report":str(dest),"read_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
      "live_control_sha256":output["original_live_control_sha256"],
      "source_control_sha256":output["canonical_control_sha256"],
      "hunk_count":len(hunks),
      "changed_line_ranges":[{"old":x["a_range"],"source":x["b_range"],"topics":x["keywords"]} for x in hunks[:24]],
      "feature_mismatches":[k for k,v in features.items() if v["live"]!=v["source"]],
      "syntax":syntax,"prior_status":status,"cutover_authorized":False}
    print("PCE11_011_CONTROL_DRIFT="+json.dumps(exposed,separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as e:
        print("PCE11_011_BLOCKED="+type(e).__name__+" "+str(e)[:270],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
