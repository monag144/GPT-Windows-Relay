#!/usr/bin/env python3
"""PCE11.018 read-only, single-run failure diagnostics for .017's full unittest suite.

GitHub-first, source-only checkout FF; durable logs and bounded redacted failure IDs.
Never starts a sidecar; never interacts with production HTTP / STOP / browser / HUD.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BRANCH="pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS="a64d57553db904edb64769e23ba44fe7de7293e1"
SUITE="windows-relay"

def run(args,timeout=35,cwd=None):
    p=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf-8",errors="replace",timeout=timeout)
    if p.returncode:
        raise RuntimeError("source verification failed: "+str(args[:3])+" (rc "+str(p.returncode)+")")
    return p.stdout.strip()

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def scrub(s):
    # Never include bearer tokens, full local paths, credentials, or long opaque strings in transport preview.
    s=re.sub(r"(?i)(token|password|secret|authorization|api[_-]?key)\s*[=:]\s*[\x22\x27]?[\w+/=._-]+",
             r"\1=<redacted>",s)
    s=re.sub(r"[A-Za-z]:\\(?:[^\\\r\n ]+\\)*[^\\\r\n ]+","<windows-path>",s)
    s=re.sub(r"\b[a-f0-9]{64,}\b","<hash>",s,flags=re.I)
    return s[:900]

def extract(stderr):
    # unittest -v uses one line per test; blocks after ====== provide failure name.
    failures=[]
    for m in re.finditer(r"(?m)^(FAIL|ERROR):\s+([^\r\n]+)",stderr):
        failures.append({"type":m.group(1),"name":scrub(m.group(2)[:240])})
    for m in re.finditer(r"(?m)^([^\n]{1,230})\s+\(([^()\n]{1,220})\)\s+\.\.\.\s+(FAIL|ERROR)\s*$",stderr):
        value={"type":m.group(3),"name":scrub((m.group(1)+" ("+m.group(2)+")")[:250])}
        if value not in failures:failures.append(value)
    captures=[]
    lines=stderr.splitlines()
    for idx,line in enumerate(lines):
        if line.startswith("FAIL: ") or line.startswith("ERROR: "):
            # Preserve the actual exception tail rather than only last 700 chars.
            bound=min(len(lines),idx+24)
            snippet=[]
            for k in range(idx+1,bound):
                if k>idx+1 and lines[k].startswith(("FAIL: ","ERROR: ","======")):break
                if lines[k].strip() and not lines[k].startswith(("    File ","  File ")):
                    snippet.append(lines[k])
            captures.append(scrub("\n".join(snippet[-10:])))
    footer=next((line for line in reversed(lines) if re.match(r"^(FAILED|OK)(?:\s|\()",line)),None)
    tests=next((line.strip() for line in reversed(lines) if re.search(r"\bRan \d+ tests?\b",line)),None)
    return {"failure_ids":failures[:24],"failure_count_listed":len(failures),
      "sample_tracebacks":captures[:6],"summary":scrub(footer or "summary missing"),
      "tests_ran":scrub(tests or "test count missing")}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--live",type=Path,required=True)
    p.add_argument("--expected-head",required=True)
    args=p.parse_args()
    repo=args.repo.resolve();live=args.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo==live:
        raise RuntimeError("canonical and live roots not distinct")
    git=shutil.which("git") or str(Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Git"/"cmd"/"git.exe")
    g=lambda *argv,timeout=35:run([git,"-C",str(repo),*argv],timeout)
    if g("rev-parse","HEAD")!=PREVIOUS:raise RuntimeError("unexpected .017 local source revision")
    if g("branch","--show-current")!=BRANCH:raise RuntimeError("wrong GitHub branch")
    if "monag144/gpt-windows-relay" not in g("remote","get-url","origin").lower():
        raise RuntimeError("noncanonical GitHub remote")
    if g("status","--porcelain"):raise RuntimeError("dirty canonical checkout")
    remote=g("ls-remote","origin","refs/heads/"+BRANCH).split()
    if not remote or remote[0]!=args.expected_head:raise RuntimeError("GitHub source pin moved")
    g("pull","--ff-only","origin",BRANCH,timeout=70)
    if g("rev-parse","HEAD")!=args.expected_head or g("status","--porcelain"):
        raise RuntimeError("source pull not pinned and clean")
    sys.path.insert(0,str(repo/"consumer"))
    from control_harness import engineering_preflight
    proof=engineering_preflight(repo,18,series=11)
    if not proof.get("ok"):raise RuntimeError("PCE11.018 preflight blocked")
    # Unique private diagnostic folder: never delete or overwrite previous results.
    stamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    dest=live/"bin"/("SOURCE_SUITE_FORENSICS_"+stamp)
    dest.mkdir(exist_ok=False)
    command=[sys.executable,"-B","-m","unittest","discover","-s","tests","-p","test_*.py","-v"]
    try:
        result=subprocess.run(command,cwd=str(repo/SUITE),stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,encoding="utf-8",errors="replace",text=True,
                timeout=125,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"))
        stdout,stderr=result.stdout,result.stderr
        rc=result.returncode
        timed_out=False
    except subprocess.TimeoutExpired as e:
        stdout=e.stdout or b""
        stderr=e.stderr or b""
        if isinstance(stdout,bytes):stdout=stdout.decode("utf-8",errors="replace")
        if isinstance(stderr,bytes):stderr=stderr.decode("utf-8",errors="replace")
        rc=None;timed_out=True
    (dest/"suite.stdout.txt").write_text(stdout,encoding="utf-8")
    (dest/"suite.stderr.txt").write_text(stderr,encoding="utf-8")
    brief=extract(stderr)
    info={"schema":"pce011-windows-suite-forensics-v1",
        "source_sha":args.expected_head,"governance":proof,
        "command":"python -B -m unittest discover -s tests -p test_*.py -v",
        "suite":SUITE,"exit_code":rc,"timed_out":timed_out,"details":brief,
        "stderr_chars":len(stderr),"stdout_chars":len(stdout),
        "stderr_sha256":sha(dest/"suite.stderr.txt"),
        "stdout_sha256":sha(dest/"suite.stdout.txt"),
        "sidecar_launched":False,"main_listener_touched":False,
        "canary_authorized":False}
    (dest/"summary.json").write_text(json.dumps(info,indent=2)+"\n",encoding="utf-8")
    transport={"report":str(dest/"summary.json"),"git_sha":args.expected_head,
      "five_control_sha256":{k:v["sha256"] for k,v in proof["reads"].items()},
      "exit_code":rc,"timeout":timed_out,"details":brief,
      "stderr_sha256":info["stderr_sha256"],"stderr_characters":len(stderr),
      "source_mutations":"GitHub fast-forward only","canary_authorized":False}
    print("PCE11_018_SUITE_FORENSICS="+json.dumps(transport,separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as e:
        print("PCE11_018_BLOCKED="+type(e).__name__+" "+str(e)[:320],file=sys.stderr)
        raise SystemExit(2)
    finally:print("Reply to this with the sandwich technique")
