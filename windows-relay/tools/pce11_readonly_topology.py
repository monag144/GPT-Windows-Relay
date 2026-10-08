#!/usr/bin/env python3
"""PCE11.006 bounded passive topology/STOP-sentinel inventory. No process or browser mutation."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PARENT="4e8d6ea31207b1f481ba5630c7c8db80347e3317"
WATCH=("8766","8767")

def checked(cmd,seconds=20):
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     encoding="utf-8",errors="replace",text=True,timeout=seconds)
    if r.returncode!=0:raise RuntimeError("command "+Path(str(cmd[0])).name+" failed exit "+str(r.returncode))
    return r.stdout.strip()

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for piece in iter(lambda:f.read(2**20),b""):h.update(piece)
    return h.hexdigest()

def ports():
    exe=shutil.which("netstat")
    if not exe:return {"available":False,"reason":"netstat missing"}
    raw=checked([exe,"-ano","-p","tcp"],12)
    result={str(port):[] for port in WATCH}
    for line in raw.splitlines():
        parts=line.split()
        if len(parts)<5 or parts[0].upper()!="TCP" or parts[3].upper()!="LISTENING":continue
        for port in WATCH:
            if parts[1].rsplit(":",1)[-1]==port and parts[4].isdigit():
                result[port].append({"bind":parts[1].rsplit(":",1)[0],"pid":int(parts[4])})
    return {"available":True,"listeners":result}

PS_QUERY=r"""
$ErrorActionPreference='Stop'
$all=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(python|pythonw|powershell|pwsh|firefox|GPTWindowsRelay)(\.exe)?$'})
$result=@()
foreach($p in $all){
  $cl=[string]$p.CommandLine
  $role='other'
  if($cl -match '(?i)windows_relay\.py'){$role='relay-server'}
  elseif($cl -match '(?i)run-control\.ps1'){$role='relay-supervisor'}
  elseif($cl -match '(?i)relay-watchdog-loop\.ps1'){$role='relay-watchdog'}
  elseif($cl -match '(?i)(^|\\|/| )hud\.py(\s|$|"|$)'){$role='hud'}
  elseif($cl -match '(?i)consumer.*relay.*server'){$role='consumer-candidate'}
  elseif($p.Name -match '(?i)^firefox'){$role='firefox-process'}
  $result+=,[ordered]@{pid=[int]$p.ProcessId;ppid=[int]$p.ParentProcessId;
    image=[string]$p.Name;role=$role;
    script_in_live_relay=[bool]($cl -match '(?i)\\Client\\Relay\\');
    script_in_canonical_source=[bool]($cl -match '(?i)\\GPT-Windows-Relay\\');
    has_commandline=[bool](-not [string]::IsNullOrWhiteSpace($cl))}
}
ConvertTo-Json -InputObject $result -Compress -Depth 3
"""

def processes():
    ps=shutil.which("powershell") or shutil.which("pwsh")
    if not ps:return {"available":False,"reason":"PowerShell absent"}
    try:
        raw=checked([ps,"-NoLogo","-NoProfile","-NonInteractive","-Command",PS_QUERY],20)
        records=json.loads(raw)
        if isinstance(records,dict):records=[records]
        if not isinstance(records,list):raise ValueError("process result not array")
        if len(records)>350:raise RuntimeError("unexpectedly large process snapshot")
        for p in records:
            if not isinstance(p,dict) or not all(x in p for x in ("pid","ppid","image","role")):
                raise RuntimeError("malformed process sample")
        focus=[p for p in records if p.get("role") not in ("other","firefox-process")]
        fox=[p for p in records if p.get("role")=="firefox-process"]
        return {"available":True,"targeted":focus[:50],"firefox_count":len(fox),
                "other_python_powershell_count":len(records)-len(focus)-len(fox),
                "pid_parent_map":{str(p["pid"]):p["ppid"] for p in records}}
    except (RuntimeError,ValueError,subprocess.TimeoutExpired,OSError) as exc:
        return {"available":False,"reason":type(exc).__name__}

def flags(folder):
    return {x:(folder/x).exists() for x in
           (".relay-paused",".relay-off",".relay-kill",".relay-kill-hud",
            ".relay-starting",".relay-kill-failed")}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--live",type=Path,required=True)
    p.add_argument("--expected-head",required=True)
    args=p.parse_args()
    repo=args.repo.resolve();live=args.live.resolve()
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    g=lambda *tokens,seconds=20:checked([git,"-C",str(repo),*tokens],seconds)
    if not repo.is_dir() or not live.is_dir() or repo==live:raise RuntimeError("invalid or conflated repo/live")
    if g("rev-parse","HEAD")!=PARENT:raise RuntimeError("stale source base; reconcile without replay")
    if g("branch","--show-current")!=BRANCH:raise RuntimeError("wrong branch")
    if "monag144/gpt-windows-relay" not in g("remote","get-url","origin").lower():
        raise RuntimeError("untrusted source remote")
    if g("status","--porcelain"):raise RuntimeError("dirty source; no pull")
    remote=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=args.expected_head:raise RuntimeError("new remote revision found")
    g("pull","--ff-only","origin",BRANCH,seconds=65)
    if g("rev-parse","HEAD")!=args.expected_head:raise RuntimeError("sync HEAD mismatch")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight,github_first_workflow_gate
    proof=engineering_preflight(repo,6,series=11)
    if not proof.get("ok"):raise RuntimeError("governance preflight denied")
    if not github_first_workflow_gate({"canonical_repo_confirmed":True,
          "github_commit_sha":args.expected_head,"remote_sha_verified":True,
          "relay_pull_sha_matches_remote":True},"source_acceptance")["ok"]:
        raise RuntimeError("GitHub-first gate denied")
    audit=repo/"docs/audits/AUDIT_2026-10-08T0916Z_PCE11_OPERATIONS_000_004.md"
    if not audit.is_file():raise RuntimeError("missing audited history")
    prior=live/"bin"/"RUNTIME_INVENTORY_2026-10-08T092221Z.json"
    if not prior.is_file():raise RuntimeError("previous PCE11.005B inventory unavailable")
    last=json.loads(prior.read_text(encoding="utf-8"))
    if not last["snapshot"]["verified"] or last["accepted_source_report"]["all_pass"] is not True:
        raise RuntimeError("PCE11.005B provenance missing")
    listeners=ports()
    pinfo=processes()
    now=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    report=live/"bin"/("PASSIVE_TOPOLOGY_"+now+".json")
    if report.exists():raise FileExistsError("new passive evidence filename exists")
    pids={p["pid"] for p in pinfo.get("targeted",[])}
    listener_ids={x["pid"] for v in listeners.get("listeners",{}).values() for x in v}
    missing_pid_records=sorted(listener_ids-pids)
    analysis={
        "schema":"pce011-passive-topology-v1","utc":datetime.now(timezone.utc).isoformat(),
        "git_sha":args.expected_head,"preflight":proof["reads"],"audit_sha256":sha(audit),
        "prior_inventory_sha256":sha(prior),"flags":flags(live),
        "ports":listeners,"processes":pinfo,
        "listener_pids_without_targeted_process_role":missing_pid_records,
        "consumer_8767_present":bool(listeners.get("listeners",{}).get("8767")),
        "live_browser_identity_proven":False,"live_extension_sha_proven":False,
        "stop_quiescence_proven":False,"rollback_restart_proven":False,
        "cutover_authorized":False,"live_mutations":[],
        "note":"Not seeing 8767 does not independently prove standalone Relay at 8766 is broken",
    }
    report.write_text(json.dumps(analysis,indent=2)+"\n",encoding="utf-8")
    roles={p["role"]:sum(1 for q in pinfo.get("targeted",[]) if q["role"]==p["role"])
           for p in pinfo.get("targeted",[])}
    portview=listeners.get("listeners",{})
    print("PCE11_006_PROOF="+json.dumps({
      "read_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
      "prior_inventory_sha256":sha(prior),"report":str(report),
      "main_8766":portview.get("8766",[]),"consumer_8767":portview.get("8767",[]),
      "process_snapshot_available":pinfo["available"],
      "roles":roles,"firefox_processes":pinfo.get("firefox_count"),
      "missing_listener_process_ids":missing_pid_records,
      "flags":analysis["flags"],"cutover_authorized":False
    },separators=(",",":")))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as e:
        print("PCE11_006_BLOCKED="+str(e)[:260],file=sys.stderr)
        sys.exit(2)
    finally:print("Reply to this with the sandwich technique")
