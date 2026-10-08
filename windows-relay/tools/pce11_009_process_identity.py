#!/usr/bin/env python3
"""PCE11.009: audit saved process IDs against a fresh snapshot. Never mutate live processes."""
from __future__ import annotations
import argparse,base64,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
OLD_HEAD="46d390ad9d54d0bf721428156af42253efae70c8"
PREVIOUS_SHA="735cea44ba871da2e11074f38dfedf4b3e79c52f414416b0ff020d5bbf75856e"

def run(args,timeout=35):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                     encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode!=0:raise RuntimeError("child command failed: "+Path(str(args[0])).name+" exit "+str(p.returncode)+" "+p.stderr.strip()[:120])
    return p.stdout.strip()

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as source:
        for piece in iter(lambda:source.read(1<<20),b""):h.update(piece)
    return h.hexdigest()

def fresh_processes(ids):
    exe=shutil.which("powershell") or shutil.which("pwsh") or "powershell.exe"
    id_list=",".join(str(x) for x in ids)
    script=r"""
$ErrorActionPreference = 'Stop'
$ids=@(%s)
$rows=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
  $ids -contains [int]$_.ProcessId
} | ForEach-Object {
  $cmdline=([string]$_.CommandLine).ToLowerInvariant()
  [pscustomobject]@{
    pid=[int]$_.ProcessId
    ppid=[int]$_.ParentProcessId
    image=[string]$_.Name
    created=[string]$_.CreationDate
    hud_script=[bool]$cmdline.Contains('hud.py')
    server_script=[bool]$cmdline.Contains('windows_relay.py')
    supervisor=[bool]$cmdline.Contains('run-control.ps1')
    watchdog=[bool]$cmdline.Contains('relay-watchdog-loop.ps1')
    consumer=[bool]$cmdline.Contains('gptwindowsrelayconsumer')
    live_path=[bool]$cmdline.Contains('client\relay')
  }
})
ConvertTo-Json -InputObject $rows -Compress -Depth 4
"""%id_list
    encoded=base64.b64encode(script.encode("utf-16le")).decode("ascii")
    stdout=run([exe,"-NoProfile","-NonInteractive","-EncodedCommand",encoded],timeout=30)
    if not stdout or not stdout.lstrip().startswith("["):
        raise RuntimeError("PowerShell did not return expected JSON array")
    parsed=json.loads(stdout)
    if not isinstance(parsed,list) or len(parsed)>len(ids):raise RuntimeError("malformed process report")
    valid=set(ids)
    for item in parsed:
        if not isinstance(item,dict) or set(("pid","ppid","image","created"))-set(item):
            raise RuntimeError("process record missing mandatory fields")
        if item["pid"] not in valid or not item["created"]:
            raise RuntimeError("unexpected process identity/creation record")
    return parsed

def fresh_ports():
    exe=shutil.which("netstat")
    if not exe: return {"available":False,"reason":"netstat missing"}
    result={"8766":[],"8767":[]}
    for line in run([exe,"-ano","-p","tcp"],timeout=15).splitlines():
        parts=line.split()
        if len(parts)<5 or parts[0].upper()!="TCP" or parts[3].upper()!="LISTENING":continue
        address=parts[1].rsplit(":",1)
        if len(address)<2 or address[1] not in result or not parts[4].isdigit():continue
        result[address[1]].append({"bind":address[0],"pid":int(parts[4])})
    return {"available":True,"listeners":result}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",required=True,type=Path)
    parser.add_argument("--live",required=True,type=Path)
    parser.add_argument("--expected-head",required=True)
    opts=parser.parse_args()
    repo=opts.repo.resolve();live=opts.live.resolve()
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    g=lambda *x,timeout=30:run([git,"-C",str(repo),*x],timeout=timeout)
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("canonical repo or live tree missing")
    if g("rev-parse","HEAD")!=OLD_HEAD or g("branch","--show-current")!=BRANCH:
        raise RuntimeError("unexpected canonical checkout revision")
    if "monag144/gpt-windows-relay" not in g("remote","get-url","origin").lower():
        raise RuntimeError("unexpected GitHub remote")
    if g("status","--porcelain"):raise RuntimeError("dirty checkout; do not overwrite")
    remote=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=opts.expected_head:raise RuntimeError("published GitHub SHA changed")
    g("pull","--ff-only","origin",BRANCH,timeout=70)
    if g("rev-parse","HEAD")!=opts.expected_head:raise RuntimeError("local SHA mismatch")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    gov=engineering_preflight(repo,9,series=11)
    if not gov.get("ok"):raise RuntimeError("preflight failed")
    previous=live/"bin"/"PASSIVE_TOPOLOGY_2026-10-08T092500Z.json"
    if not previous.is_file() or digest(previous)!=PREVIOUS_SHA:
        raise RuntimeError("previous complete topology evidence not verified")
    stored=json.loads(previous.read_text(encoding="utf-8"))
    if stored.get("schema")!="pce011-passive-topology-v1":raise RuntimeError("unexpected saved evidence schema")
    old=stored["processes"]["targeted"]
    if not isinstance(old,list) or len(old)<3 or len(old)>50:
        raise RuntimeError("unexpected prior targeted-process count")
    ids=sorted({int(rec["pid"]) for rec in old})
    if any(i<=0 for i in ids):raise RuntimeError("invalid previous PID")
    current=fresh_processes(ids)
    ports=fresh_ports()
    current_by_id={int(p["pid"]):p for p in current}
    rows=[]
    for item in old:
        pid=int(item["pid"]);new=current_by_id.get(pid)
        role=item["role"];ppid=int(item["ppid"])
        rows.append({"pid":pid,"historical_role":role,"historical_ppid":ppid,
           "current":new,"still_present":new is not None,
           "parent_pid_unchanged":bool(new and new["ppid"]==ppid),
           "image_name_unchanged":bool(new and new["image"].casefold()==item["image"].casefold())})
    previous_ports=stored["ports"]["listeners"]
    report={"schema":"pce011-current-process-identity-v1",
        "captured_utc":datetime.now(timezone.utc).isoformat(),
        "git_head":opts.expected_head,"read_sha256":{k:v["sha256"] for k,v in gov["reads"].items()},
        "previous_topology_sha256":PREVIOUS_SHA,
        "previous_listeners":previous_ports,"current_listeners":ports,
        "process_matches":rows,
        "exclusions":["no_stop","no_process_termination","no_browser_control",
                      "no_reload","no_live_file_edit","no_restart"],
        "duplicate_instance_confirmation":"NOT_PROVEN",
        "cutover_authorized":False}
    stamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    dest=live/"bin"/("PROCESS_IDENTITY_"+stamp+".json")
    if dest.exists():raise RuntimeError("diagnostic file collision")
    dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    short=[{"pid":x["pid"],"role":x["historical_role"],
            "parent":x["historical_ppid"],
            "current_parent":x["current"]["ppid"] if x["current"] else None,
            "image":x["current"]["image"] if x["current"] else None,
            "still_present":x["still_present"],
            "hud":x["current"]["hud_script"] if x["current"] else None,
            "server":x["current"]["server_script"] if x["current"] else None}
           for x in rows]
    print("PCE11_009_PROOF="+json.dumps({
        "id":gov["id"],"repo_sha":opts.expected_head,
        "report":str(dest),"previous_sha256":PREVIOUS_SHA,
        "current_listeners":ports,
        "processes":short,"checkpoint":gov["checkpoints"],
        "cutover_authorized":False},separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as err:
        print("PCE11_009_BLOCKED="+type(err).__name__+" "+str(err)[:290],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
