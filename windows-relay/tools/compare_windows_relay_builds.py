#!/usr/bin/env python3
"""Read-only local Windows Relay checkout-to-Client comparison.
Does not change files, processes, browser tabs, extension data, or relay state.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

home = Path.home()
main_root = home / "Downloads" / "Dev" / "GPT-Windows-Relay-Main-Build"
main = main_root / "windows-relay"
client = home / "Downloads" / "Dev" / "GPT" / "Client" / "Relay"
expected_head_at_preparation = "16856b6ebffc8430c430c01b2b5aed05b3dbd7dc"

def git_dir(repo):
    ptr = repo / ".git"
    if ptr.is_dir():
        return ptr
    if ptr.is_file():
        txt = ptr.read_text(encoding="utf-8", errors="replace").strip()
        if txt.lower().startswith("gitdir:"):
            return (repo / txt.split(":", 1)[1].strip()).resolve()
    return None

def git_ref(gitdir, ref):
    p = gitdir / Path(ref)
    if p.is_file():
        return p.read_text(encoding="ascii", errors="replace").strip()
    packed = gitdir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="ascii", errors="replace").splitlines():
            fields = line.split()
            if len(fields) == 2 and fields[1] == ref:
                return fields[0]
    return None

def local_head(repo):
    g = git_dir(repo)
    if g is None or not (g / "HEAD").is_file():
        return "UNAVAILABLE (no readable .git)"
    content = (g / "HEAD").read_text(encoding="ascii", errors="replace").strip()
    if content.startswith("ref:"):
        branch = content.split(":", 1)[1].strip()
        resolved = git_ref(g, branch)
        return f"{resolved or 'UNRESOLVED'} ({branch})"
    return content

def info(path):
    if not path.is_file():
        return None
    data = path.read_bytes()
    return (hashlib.sha256(data).hexdigest()[:16], len(data))

parts = [
    ("hud.py", "HUD interface"),
    ("relay-control.ps1", "Operator controller"),
    ("windows_relay.py", "Relay backend"),
    ("firefox_adapter.py", "Firefox adapter"),
    ("extension/manifest.json", "Firefox manifest"),
    ("extension/content.js", "Conversation scanner"),
    ("extension/service_worker.js", "Extension worker"),
]

print("=== GPT WINDOWS RELAY: READ-ONLY BUILD COMPARISON ===")
print("MAIN_BUILD_DIR=" + str(main))
print("CLIENT_DIR=" + str(client))
print("MAIN_BUILD_PRESENT=" + str(main.is_dir()))
print("CLIENT_PRESENT=" + str(client.is_dir()))
print("LOCAL_CHECKOUT_HEAD=" + local_head(main_root))
print("GITHUB_HEAD_VERIFIED_WHEN_SCRIPT_PREPARED=" + expected_head_at_preparation)
print("NOTE=Local checkout HEAD may not match current GitHub main; GitHub Desktop can Fetch/Pull.")
print()
print("FILE COMPARISON (SHA256 first 16 digits)")
for name, label in parts:
    a = info(main / name)
    b = info(client / name)
    if a is None:
        status = "MAIN_NOT_FOUND"
    elif b is None:
        status = "CLIENT_NOT_FOUND"
    elif a == b:
        status = "IDENTICAL"
    else:
        status = "DIFFERENT"
    print(f"{label}: {status} | MAIN={a or 'missing'} | CLIENT={b or 'missing'}")

print()
for tag, root in (("MAIN", main), ("CLIENT", client)):
    m = root / "extension" / "manifest.json"
    if m.is_file():
        try:
            manifest = json.loads(m.read_text(encoding="utf-8-sig"))
            print(f"{tag}_EXTENSION_NAME={manifest.get('name','?')!s}")
            print(f"{tag}_EXTENSION_VERSION={manifest.get('version','?')!s}")
        except (OSError, ValueError) as exc:
            print(f"{tag}_MANIFEST_ERROR={type(exc).__name__}")

print()
print("PORT_8766_LISTENERS (read-only netstat)")
try:
    proc = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        capture_output=True,
        text=True,
        timeout=6,
        check=False,
    )
    listeners = []
    for line in proc.stdout.splitlines():
        tokens = line.split()
        if len(tokens) >= 5 and tokens[1].endswith(":8766") and tokens[3].upper() == "LISTENING":
            listeners.append(" ".join(tokens[:5]))
    if listeners:
        for row in listeners[:8]:
            print(row)
    else:
        print("NO_8766_LISTENER_DETECTED")
except Exception as exc:
    print(f"NETSTAT_UNAVAILABLE={type(exc).__name__}")

print()
print("READ_ONLY=True")
print("CLIENT_FILES_CHANGED=False")
print("RELAY_OR_FIREFOX_RESTARTED=False")
print("BROWSER_LOADED_EXTENSION_VERSION=NOT_VERIFIED_BY_THIS_TEST")
print("CUTOVER_AUTHORIZED=False")
