"""2026-10-12 Windows Relay + repository health inspection (read-only).

No app launch, remote fetch, test invocation, credential read, backup, or
filesystem mutation. Use Python -B to suppress bytecode writes.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RELAY = REPO / "windows-relay"
TAG = "windows-relay-v0.3.18-live-verified-20261012"
PINNED_SHA = "f00307494a83338d29b4c35dd6264e71fa142dbd"
BRANCH = "wip/windows-relay-rebuilt-resynced-2047-101026"
RELEASE_ID = "gpt-windows-relay@local"


def run(args, cwd=REPO, timeout=60):
    return subprocess.run(
        [str(x) for x in args], cwd=str(cwd), capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=timeout,
        check=False,
    )


def git(*args):
    result = run(["git", *args])
    return result.stdout.strip() if result.returncode == 0 else None


def scan_markdown_links(text, path, tracked):
    missing = []
    for match in re.finditer(r"\]\(([^\n)]+)\)", text):
        target = match.group(1).split("#", 1)[0].split("?", 1)[0].strip()
        if not target or re.match(r"(?i)^(?:https?://|mailto:|data:|#)", target):
            continue
        target = target.strip("<>")
        dest = (path.parent / target).resolve()
        try:
            rel = dest.relative_to(REPO)
        except ValueError:
            missing.append(f"{path.relative_to(REPO)} -> OUTSIDE_REPO")
            continue
        if rel.as_posix() not in tracked and not dest.is_file():
            missing.append(f"{path.relative_to(REPO)} -> {target}")
    return missing


def check_powershell(paths):
    exe = shutil.which("powershell.exe") or shutil.which("pwsh")
    if not exe:
        return {"state": "UNAVAILABLE", "count": len(paths), "errors": []}
    # The AST parser never evaluates or runs any inspected PowerShell script.
    program = r"""
$ErrorActionPreference='Stop'
$bad=0
foreach($p in $args){
  $tokens=$null
  $errors=$null
  [System.Management.Automation.Language.Parser]::ParseFile($p,[ref]$tokens,[ref]$errors) | Out-Null
  if($errors.Count -gt 0){
    foreach($err in $errors){
      Write-Output ('PARSE_ERROR '+[IO.Path]::GetFileName($p)+' line='+$err.Extent.StartLineNumber+' '+$err.ErrorId)
    }
    $bad+=$errors.Count
  }
}
if($bad -gt 0){exit 1}
"""
    # -Command string + arguments separated by '-' are supported by Windows
    # PowerShell, but use env-independent script concatenation to avoid
    # interpreting any source script or relying on local temporary files.
    quoted = ",".join("'" + str(p).replace("'", "''") + "'" for p in paths)
    code = "$paths=@(" + quoted + ");" + program.replace("foreach($p in $args)", "foreach($p in $paths)")
    result = run([exe, "-NoProfile", "-NonInteractive", "-Command", code], timeout=90)
    return {
        "state": "PASS" if result.returncode == 0 else "FAIL",
        "count": len(paths),
        "errors": result.stdout.strip().splitlines()[:25] +
                  result.stderr.strip().splitlines()[:10],
    }


def sweep():
    report = {"basis": "2026-10-12", "checkout": "single canonical windows-relay/",
              "mode": "READ_ONLY_NO_BACKUP_NO_RUNTIME_CHANGE", "warnings": [],
              "failures": [], "checks": {}}
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    origin = git("remote", "get-url", "origin")
    report["git"] = {
        "branch": branch, "head": head,
        "expected_branch": BRANCH,
        "origin_matches": origin is not None and
                          "monag144/GPT-Windows-Relay" in origin,
    }
    if branch != BRANCH:
        report["warnings"].append("checkout on unexpected branch")
    if not report["git"]["origin_matches"]:
        report["failures"].append("origin is not the Windows Relay repository")
    head_tag = git("rev-parse", TAG + "^{commit}")
    report["git"]["verified_tag_target"] = head_tag
    if head_tag is None:
        report["warnings"].append("verified tag not fetched locally; remote tag may still exist")
    elif head_tag != PINNED_SHA:
        report["failures"].append("verified Git tag resolves to unexpected commit")

    tracked_text = git("ls-files", "-z")
    if tracked_text is None:
        report["failures"].append("git ls-files unavailable")
        return report
    # -z records, unlike ordinary text, use null separators.
    tracked_result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=str(REPO),
        capture_output=True, check=False,
    )
    names = [name.decode("utf-8", "replace") for name in tracked_result.stdout.split(b"\0") if name]
    tracked = set(names)
    report["checks"]["tracked_files"] = len(names)
    if any(p.startswith(("Prototype/", "STUPID BACKUPS DO NOT USE/", "windows-relay/runtime/")) for p in names):
        report["failures"].append("duplicate source tree is Git tracked")

    manifest_path = RELAY / "extension-persistent" / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        identity = manifest.get("browser_specific_settings", {}).get("gecko", {}).get("id")
        report["checks"]["canonical_extension"] = {
            "version": manifest.get("version"), "gecko_id": identity,
        }
        if identity != RELEASE_ID or manifest.get("version") != "0.3.18":
            report["failures"].append("canonical persistent Firefox identity/version mismatch")
    except (OSError, ValueError) as exc:
        report["failures"].append("persistent manifest unreadable: " + type(exc).__name__)

    expected = [
        "windows-relay/windows_relay.py", "windows-relay/hud.py",
        "windows-relay/relay-control.ps1",
        "windows-relay/relay-watchdog-loop.ps1",
        "windows-relay/START-GPT-WINDOWS-RELAY.bat",
        "windows-relay/extension-persistent/service_worker.js",
        "windows-relay/extension-persistent/content.js",
    ]
    for p in expected:
        if p not in tracked or not (REPO / p).is_file():
            report["failures"].append("canonical tracked source missing: " + p)

    py_count = js_count = json_count = md_count = 0
    json_errors, js_errors, py_errors, md_broken = [], [], [], []
    node = shutil.which("node")
    for name in names:
        path = REPO / name
        if not path.is_file():
            report["failures"].append("tracked file absent from disk: " + name)
            continue
        ext = path.suffix.lower()
        if ext == ".py":
            py_count += 1
            try:
                compile(path.read_bytes(), name, "exec")
            except (SyntaxError, UnicodeError, OSError) as exc:
                py_errors.append(name + ": " + type(exc).__name__)
        elif ext == ".json":
            json_count += 1
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
            except (ValueError, OSError) as exc:
                json_errors.append(name + ": " + type(exc).__name__)
        elif ext in {".js", ".cjs"}:
            js_count += 1
            if node:
                try:
                    x = run([node, "--check", path], timeout=15)
                    if x.returncode:
                        js_errors.append(name + ": " + (x.stderr.splitlines() or ["node syntax failure"])[-1])
                except subprocess.TimeoutExpired:
                    js_errors.append(name + ": node syntax check timeout")
        elif ext == ".md":
            md_count += 1
            try:
                md_broken.extend(scan_markdown_links(path.read_text(encoding="utf-8"),
                                                     path, tracked))
            except (OSError, UnicodeError):
                report["warnings"].append("documentation unreadable: " + name)
    report["checks"]["python_syntax"] = {"files": py_count, "errors": py_errors[:25]}
    report["checks"]["javascript_syntax"] = {
        "files": js_count, "node_available": bool(node), "errors": js_errors[:25],
    }
    report["checks"]["json_syntax"] = {"files": json_count, "errors": json_errors[:25]}
    report["checks"]["markdown_links"] = {
        "files": md_count, "unresolved_count": len(md_broken), "samples": md_broken[:35],
    }
    for label, issues in (("Python", py_errors), ("JavaScript", js_errors), ("JSON", json_errors)):
        if issues:
            report["failures"].append(label + " parse errors: " + str(len(issues)))
    if not node:
        report["warnings"].append("Node.js unavailable; JavaScript syntax not executed")
    if md_broken:
        report["warnings"].append("unresolved Markdown local links: " + str(len(md_broken)))

    ps_paths = [REPO / n for n in names if n.lower().endswith((".ps1", ".psm1"))]
    try:
        report["checks"]["powershell_ast"] = check_powershell(ps_paths)
    except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
        report["checks"]["powershell_ast"] = {
            "state": "ERROR", "count": len(ps_paths), "type": type(exc).__name__,
        }
    if report["checks"]["powershell_ast"]["state"] in {"FAIL", "ERROR"}:
        report["failures"].append("PowerShell AST parse failed")

    historic = ("STUPID BACKUPS DO NOT USE", "windows-relay/backups",
                "windows-relay/rollback", "windows-relay/runtime")
    present = [x for x in historic if (REPO / x).exists()]
    report["checks"]["legacy_local_paths_present"] = present
    if present:
        report["warnings"].append("legacy untracked local paths remain; no deletion attempted")
    dirty = git("status", "--porcelain", "--untracked-files=normal") or ""
    report["checks"]["dirty_or_untracked_git_entries"] = len(dirty.splitlines()) if dirty else 0
    report["outcome"] = "SOURCE_HEALTH_ISSUES" if report["failures"] else (
        "SOURCE_HEALTH_WARNINGS" if report["warnings"] else "SOURCE_HEALTH_PASS"
    )
    return report


def main():
    ap = argparse.ArgumentParser(description="Read-only Windows Relay repository health sweep")
    ap.add_argument("--json", action="store_true", help="Machine-readable report to stdout only")
    args = ap.parse_args()
    result = sweep()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
