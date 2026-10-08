#!/usr/bin/env python3
"""PCE11.012: STATIC readiness of historic isolated v16 relay sidecar + rollback; never start services."""
from __future__ import annotations
import argparse,ast,hashlib,json,os,shutil,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS_HEAD="5eb22d6433a57e16f780b626de3a57317abbafd4"
HISTORIC={"PCE8_V16":"694d47ab89596d5c3801f749caa352b951a2be52",
          "ONE_CLICK_GO_R28":"d5b9db7ad785b5cae8dc3b64219303b9fcfa634a"}
MAIN_PORT=8766
SIDECAR_PORT=8768
SOURCE_REL="windows-relay/windows_relay.py"

def run(argv,timeout=30):
    p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:raise RuntimeError("verification command failed: "+Path(str(argv[0])).name)
    return p.stdout.strip()
def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()
def statfile(p):
    return {"exists":p.is_file(),"sha256":digest(p) if p.is_file() else None,
            "bytes":p.stat().st_size if p.is_file() else None}
def analyze_entrypoint(py):
    if not py.is_file():return {"present":False,"isolated_config_supported":False,"isolated_state_supported":False}
    source=py.read_text(encoding="utf-8-sig")
    syntax=ast.parse(source,filename=str(py))
    literals={n.value for n in ast.walk(syntax) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
    flags={"config_flag":"--config" in literals,
           "state_dir_flag":"--state-dir" in literals,
           "server_mode":"server" in literals,
           "config_arg_used":"a.config" in source or "args.config" in source,
           "state_arg_used":"a.state_dir" in source or "args.state_dir" in source,
           "loopback_host":"127.0.0.1" in literals or "127.0.0.1" in source,
           "private_state_construct":"State(a.state_dir" in source or "State(args.state_dir" in source}
    return {"present":True,"python_ast_ok":True,"source_sha256":digest(py),
      "flags":flags,
      "isolated_config_supported":flags["config_flag"] and flags["config_arg_used"] and flags["loopback_host"],
      "isolated_state_supported":flags["state_dir_flag"] and flags["state_arg_used"] and flags["private_state_construct"],
      "runtime_side_effects_not_checked":True}
def occupied_ports():
    exe=shutil.which("netstat")
    if not exe:return {"available":False,"reason":"netstat not on PATH"}
    listeners={str(x):[] for x in (MAIN_PORT,SIDECAR_PORT)}
    for line in run([exe,"-ano","-p","tcp"],timeout=15).splitlines():
        bits=line.split()
        if len(bits)<5 or bits[0].upper()!="TCP" or bits[3].upper()!="LISTENING":continue
        port=bits[1].rsplit(":",1)[-1]
        if port in listeners and bits[-1].isdigit():
            listeners[port].append(int(bits[-1]))
    return {"available":True,"listening_pids":listeners}
def archive(archive_root):
    mfiles=sorted(archive_root.glob("BROKEN_*.manifest.json"),reverse=True)
    if not mfiles:raise RuntimeError("original archive manifest missing")
    manifest=json.loads(mfiles[0].read_text(encoding="utf-8"))
    if not isinstance(manifest,dict) or "archive_path" not in manifest:
        raise RuntimeError("invalid original manifest")
    zip_path=Path(manifest["archive_path"])
    if not zip_path.is_file():raise RuntimeError("original zip absent")
    same=digest(zip_path)==manifest["zip_sha256"]
    if not same:raise RuntimeError("original zip failed SHA256")
    with zipfile.ZipFile(zip_path) as z:
        all_entries=z.infolist()
        nfiles=sum(not i.is_dir() for i in all_entries)
        all_names=[e.filename.replace("\\","/") for e in all_entries]
        readable_names={"relay_control":any(n.endswith("/relay-control.ps1") or n=="relay-control.ps1" for n in all_names),
                        "server":any(n.endswith("/windows_relay.py") or n=="windows_relay.py" for n in all_names),
                        "watchdog":any(n.endswith("/relay-watchdog-loop.ps1") or n=="relay-watchdog-loop.ps1" for n in all_names)}
    if manifest.get("file_count")!=nfiles:raise RuntimeError("manifest count vs ZIP mismatch")
    return {"original_file_count":nfiles,"zip_sha256":manifest["zip_sha256"],
            "zip_verified":True,"critical_restorable_paths":readable_names,
            "restore_test_performed":False}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--live",type=Path,required=True)
    ap.add_argument("--expected-head",required=True)
    a=ap.parse_args()
    repo=a.repo.resolve();live=a.live.resolve()
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    g=lambda dir,*args,timeout=25:run([git,"-C",str(dir),*args],timeout=timeout)
    if not repo.is_dir() or not live.is_dir() or repo==live:raise RuntimeError("source/live missing or overlap")
    if g(repo,"rev-parse","HEAD")!=PREVIOUS_HEAD or g(repo,"branch","--show-current")!=BRANCH:
        raise RuntimeError("wrong local checked-out source base")
    if "monag144/gpt-windows-relay" not in g(repo,"remote","get-url","origin").lower():
        raise RuntimeError("noncanonical GitHub origin")
    if g(repo,"status","--porcelain"):raise RuntimeError("dirty canonical checkout")
    remote=g(repo,"ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=a.expected_head:raise RuntimeError("remote SHA differs")
    g(repo,"pull","--ff-only","origin",BRANCH,timeout=70)
    if g(repo,"rev-parse","HEAD")!=a.expected_head:raise RuntimeError("unexpected pulled SHA")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    gov=engineering_preflight(repo,12,series=11)
    if not gov.get("ok"):raise RuntimeError("governance denied")
    previous=live/"bin"/"CONTROL_DRIFT_2026-10-08T094030Z.json"
    if not previous.is_file():raise RuntimeError("PCE11.011 evidence missing")
    observed=json.loads(previous.read_text(encoding="utf-8"))
    if observed.get("schema")!="pce011-control-drift-v1" or observed.get("source_sha")!=PREVIOUS_HEAD:
        raise RuntimeError("PCE11.011 report provenance differs")
    zip_result=archive(live/"bin")
    ports=occupied_ports()
    candidates={}
    for name,sha in HISTORIC.items():
        folder=live/"builds"/( ("RELAY_"+name if name=="PCE8_V16" else name)+"_"+sha[:12])
        # Preserve all candidate trees, including if one historic layout differs.
        if not folder.is_dir(): candidates[name]={"stage_exists":False,"expected_folder":str(folder),"blockers":["historic stage folder missing"]};continue
        if g(folder,"rev-parse","HEAD")!=sha:raise RuntimeError("historic "+name+" commit SHA mismatched")
        if g(folder,"status","--porcelain"):raise RuntimeError("historic "+name+" stage unexpectedly dirty")
        wr=folder/"windows-relay"
        py=wr/"windows_relay.py"
        analyzed=analyze_entrypoint(py)
        mandatory=["windows_relay.py","relay-control.ps1","run-control.ps1","relay-watchdog-loop.ps1"]
        files={p:statfile(wr/p) for p in mandatory}
        blockers=[]
        if not analyzed.get("isolated_config_supported"):blockers.append("no verified isolated --config")
        if not analyzed.get("isolated_state_supported"):blockers.append("no verified isolated --state-dir")
        if not files["windows_relay.py"]["exists"]:blockers.append("no staged relay server")
        if not files["run-control.ps1"]["exists"]:blockers.append("no source supervisor script")
        candidates[name]={"stage_exists":True,"HEAD":sha,"source_root":str(wr),
           "entrypoint":analyzed,"critical_files":files,
           "static_isolation_candidate":not blockers,"blockers":blockers}
    blockers=[]
    v=candidates.get("PCE8_V16",{})
    if not v.get("static_isolation_candidate"):blockers.append("PCE8 v16 source isolation contract unproved")
    if not zip_result["zip_verified"]:blockers.append("original backup not verified")
    if not all(zip_result["critical_restorable_paths"].values()):blockers.append("original ZIP missing a critical restore path")
    if not ports.get("available"):blockers.append("cannot establish sidecar port status")
    elif ports["listening_pids"]["8768"]:blockers.append("sidecar port 8768 already listening")
    details={
       "schema":"pce011-isolated-sidecar-readiness-v1","captured_utc":datetime.now(timezone.utc).isoformat(),
       "git_sha":a.expected_head,"governance":gov,
       "prior_drift_sha256":digest(previous),"archive":zip_result,
       "ports":ports,"historic_candidates":candidates,
       "static_source_checks_passed":not blockers,
       "sidecar_execution_authorized":False,
       "no_main_runtime_mutation":True,
       "next":"If source isolation candidate passes, design one-shot process-isolated canary with dedicated config/state, port, strict PID capture, exit-on-failure and no browser or side effects.",
       "blockers":blockers}
    now=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    output=live/"bin"/("SIDECAR_READINESS_"+now+".json")
    if output.exists():raise FileExistsError("report filename collision")
    output.write_text(json.dumps(details,indent=2)+"\n",encoding="utf-8")
    print("PCE11_012_READINESS="+json.dumps({
      "report":str(output),"sha":a.expected_head,
      "read_sha256":{k:v["sha256"] for k,v in gov["reads"].items()},
      "archive":zip_result,"port_status":ports,
      "candidate_checks":{k:{"exists":v.get("stage_exists"),
          "static_isolation_candidate":v.get("static_isolation_candidate"),
          "blockers":v.get("blockers")} for k,v in candidates.items()},
      "blockers":blockers,"sidecar_execution_authorized":False
    },separators=(",",":")))
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,zipfile.BadZipFile,subprocess.TimeoutExpired) as e:
        print("PCE11_012_BLOCKED="+type(e).__name__+": "+str(e)[:270],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
