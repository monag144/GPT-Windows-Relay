#!/usr/bin/env python3
"""PCE11.021 source-only forensics of persisted consumer failures and migration Git blobs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BRANCH = "pce11/one-click-go-recovery-and-doc-hygiene"
PREVIOUS_HEAD = "ba166ad70b86698bf2ce920c6050fde38cd964ed"
EVIDENCE = "SOURCE_ACCEPTANCE_2026-10-08T101602Z"
MIGRATION = "docs/migration/MIGRATION_2026-10-08T0110Z_TERMUX_WINDOWS_EVIDENCE_MANIFEST.json"
INCIDENT = "docs/incidents/INCIDENT_2026-10-08T1016Z_PCE11_020_CONSUMER_GOVERNANCE_AND_MANIFEST_FAILURES.md"

def run(command, timeout=55):
    p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if p.returncode:
        raise RuntimeError("read-only Git verification failed: " + str(command[:3]) +
                           " rc " + str(p.returncode) + " " + p.stderr[-180:])
    return p.stdout.strip()

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def brief(lines):
    out = []
    for line in lines:
        s = re.sub(r"[A-Za-z]:\\(?:[^\\\r\n ]+\\)*[^\\\r\n ]+", "<windows-path>", line)
        s = re.sub(r"(?i)(token|password|secret|api[_-]?key)(\s*[=:]\s*)[^\s'\"\r\n]+",
                   r"\1\2<redacted>", s)
        out.append(s[:300])
    return out

def failures(stderr):
    """Full raw file is retained; show only exact IDs and last exception lines."""
    lines = stderr.splitlines()
    entries = []
    indexes = [i for i, line in enumerate(lines) if re.match(r"^(FAIL|ERROR): ", line)]
    for j, start in enumerate(indexes):
        stop = indexes[j+1] if j + 1 < len(indexes) else len(lines)
        block = lines[start:stop]
        if len(block) > 70:
            block = block[:70]
        descriptions = [x.strip() for x in block if re.search(r"(AssertionError|ControlHarnessError|FileNotFoundError|PermissionError|KeyError|RuntimeError|^E\s)", x)]
        entries.append({
            "case": lines[start][:240],
            "messages": brief(descriptions[-5:])[:5],
        })
    ran = re.findall(r"(?m)^Ran \d+ tests? in [^\r\n]+", stderr)
    footer = re.findall(r"(?m)^FAILED\s+\([^\r\n]+\)|^OK(?:\s|\r?$)", stderr)
    return {"cases": entries, "reported_test_count": ran[-1] if ran else None,
            "footer": footer[-1] if footer else "not found", "failure_count": len(entries)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--live", required=True, type=Path)
    args = parser.parse_args()
    repo, live = args.repo.resolve(), args.live.resolve()
    if not repo.is_dir() or not live.is_dir() or repo == live:
        raise RuntimeError("canonical Git and live roots must be distinct")
    gitexe = shutil.which("git") or str(
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git" / "cmd" / "git.exe"
    )
    def git(*tokens, timeout=35):
        return run([gitexe, "-C", str(repo), *tokens], timeout)
    if git("rev-parse", "HEAD") != PREVIOUS_HEAD:
        raise RuntimeError("unexpected local .020 source base; do not overwrite")
    if git("branch", "--show-current") != BRANCH:
        raise RuntimeError("unexpected canonical branch")
    if "monag144/gpt-windows-relay" not in git("remote", "get-url", "origin").lower():
        raise RuntimeError("wrong canonical GitHub origin")
    if git("status", "--porcelain"):
        raise RuntimeError("dirty checkout")
    remote = git("ls-remote", "origin", "refs/heads/" + BRANCH).split()
    if len(remote) < 2 or remote[0] != args.expected_head:
        raise RuntimeError("pinned remote SHA changed")
    git("fetch", "--no-tags", "origin", "refs/heads/" + BRANCH, timeout=65)
    if git("rev-parse", "FETCH_HEAD") != args.expected_head:
        raise RuntimeError("fetched Git object differs")
    git("merge-base", "--is-ancestor", "HEAD", "FETCH_HEAD")
    git("merge", "--ff-only", "FETCH_HEAD", timeout=55)
    if git("rev-parse", "HEAD") != args.expected_head or git("status", "--porcelain"):
        raise RuntimeError("canonical checkout not clean at pinned source")
    sys.path.insert(0, str(repo / "consumer"))
    from control_harness import engineering_preflight
    gov = engineering_preflight(repo, 21, series=11)
    if not gov["ok"]:
        raise RuntimeError("mandatory five-file governance incomplete")
    if not (repo / INCIDENT).is_file():
        raise RuntimeError("prior incident not found")

    base = live / "bin" / EVIDENCE
    path = base / "consumer_full.stderr.txt"
    summary = base / "acceptance.json"
    if not path.is_file() or not summary.is_file():
        raise RuntimeError(".020 evidence missing, refuse reconstructed claims")
    original = json.loads(summary.read_text(encoding="utf-8"))
    suites = original.get("unit_suites", [])
    if (original.get("repo_sha") != PREVIOUS_HEAD or
        not any(x.get("suite") == "consumer_full" and not x.get("passed") for x in suites)):
        raise RuntimeError(".020 persisted acceptance provenance inconsistent")
    stderr = path.read_text(encoding="utf-8", errors="replace")
    diag = failures(stderr)

    data = json.loads((repo / MIGRATION).read_text(encoding="utf-8"))
    if data.get("entry_count") != 42 or len(data.get("entries", [])) != 42:
        raise RuntimeError("manifest count changed before analysis")
    mismatches = []
    for entry in data["entries"]:
        rel = entry["destination_path"]
        p = (repo / rel).resolve()
        if not p.is_relative_to(repo) or not p.is_file():
            mismatches.append({"path": rel, "problem": "not in checked-out tree"})
            continue
        try:
            current = git("rev-parse", "HEAD:" + rel)
        except RuntimeError:
            mismatches.append({"path": rel, "problem": "not committed at HEAD"})
            continue
        if current != entry["git_blob_sha1"]:
            mismatches.append({"path": rel, "expected_git_blob": entry["git_blob_sha1"],
                               "current_head_git_blob": current})
    result = {
        "schema": "pce011-consumer-forensics-v1",
        "source_sha": args.expected_head,
        "five_read_sha256": {k:v["sha256"] for k,v in gov["reads"].items()},
        "prior_suite_stderr_sha256": digest(path),
        "prior_suite_failure_details": diag,
        "manifest_entry_count": len(data["entries"]),
        "manifest_mismatches": mismatches,
        "manifest_consistency_unmodified": True,
        "tests_rerun": False, "main_runtime_touched": False, "v16_canary_launched": False,
        "full_source_acceptance": False,
    }
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    dest = live / "bin" / ("CONSUMER_FORENSICS_" + now + ".json")
    if dest.exists():
        raise RuntimeError("report collision")
    dest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    exposed = {
        "report": str(dest),
        "git_sha": args.expected_head,
        "five_reads": result["five_read_sha256"],
        "prior_stderr_sha256": result["prior_suite_stderr_sha256"],
        "consumer_count": diag["reported_test_count"],
        "consumer_summary": diag["footer"],
        "consumer_failures": [{"case":x["case"], "messages":x["messages"][-2:]}
                              for x in diag["cases"][:16]],
        "total_consumer_failure_count": diag["failure_count"],
        "manifest_entry_count": len(data["entries"]),
        "manifest_mismatch_count": len(mismatches),
        "manifest_mismatches": mismatches[:12],
        "canary_launched": False,
    }
    print("PCE11_021_CONSUMER_FORENSICS=" + json.dumps(exposed, separators=(",",":")))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as err:
        print("PCE11_021_BLOCKED=" + type(err).__name__ + ": " + str(err)[:300], file=sys.stderr)
        raise SystemExit(2)
    finally:
        print("Reply to this with the sandwich technique")
