#!/usr/bin/env python3
"""Read-only function/feature inventory of Main Build vs installed Windows Client.

Does not change source files, Git branches, relay state, Firefox, or processes.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path

home = Path.home()
main = home / "Downloads" / "Dev" / "GPT-Windows-Relay-Main-Build" / "windows-relay"
client = home / "Downloads" / "Dev" / "GPT" / "Client" / "Relay"

pairs = (
    ("hud.py", "HUD"),
    ("relay-control.ps1", "Operator controller"),
    ("windows_relay.py", "Execution backend"),
    ("extension/manifest.json", "Firefox manifest"),
    ("extension/content.js", "Conversation scanner"),
    ("extension/service_worker.js", "Extension worker"),
)

priority = re.compile(
    r"stop|kill|force|retry|recover|owner|rotation|handoff|reserve|claim|"
    r"replay|dedup|packet|refresh|quiesc|ack|pending|queue|approve|"
    r"session|mission|result|browser|armed|pause|persist", re.I
)

def symbols(name: str, source: str) -> set[str]:
    if name.endswith(".py"):
        regex = r"(?m)^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\("
    elif name.endswith(".ps1"):
        regex = r"(?mi)^\s*function\s+([A-Za-z_]\w*)"
    elif name.endswith(".js"):
        regex = r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\("
    else:
        return set()
    return set(re.findall(regex, source))

def ordered_names(items: set[str], limit: int = 22) -> list[str]:
    return sorted(items, key=lambda n: (not bool(priority.search(n)), n.lower()))[:limit]

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]

def feature_markers(source: str) -> dict[str, bool]:
    keys = {
        "legacy_auto_rotation": r"CHAT_ROTATION_EVERY|ENGINEERING_ROTATION_KEY",
        "page_error_new_chat": r"GPT_CHATGPT_PAGE_ERROR_REFRESH_NEW_CHAT_V1",
        "force_scanner_function": r"function\s+forceRecoveryPacketInspect\s*\(",
        "force_message_handler": r"force_scanner_rescan",
        "retry_handler": r"(?:\$Action\s+-eq\s+['\"]retry|relay_control\(['\"]retry['\"]\))",
        "dedup_attempted": r"attempted\.has\(",
        "operator_pause_interlock": r"operatorPaused|operator_stop|WaitBrowserQuiesced",
        "owner_claim": r"checkAndClaimRelayOwner|conversation_identity_missing",
    }
    return {name: bool(re.search(expr, source, re.I)) for name, expr in keys.items()}

print("=== WINDOWS RELAY: READ-ONLY CAPABILITY DIFFERENCES ===")
print("MAIN=" + str(main))
print("CLIENT=" + str(client))
print("NO_DEPLOYMENT_OR_BROWSER_CHANGE=True")

if not main.is_dir() or not client.is_dir():
    print("FAIL: One or both directories are missing.")
    raise SystemExit(2)

for relative, label in pairs:
    a, b = main / relative, client / relative
    print("\n--- " + label + " ---")
    if not a.is_file() or not b.is_file():
        print("MISSING_FILE_MAIN=" + str(a.is_file()) + " CLIENT=" + str(b.is_file()))
        continue
    raw_a, raw_b = a.read_bytes(), b.read_bytes()
    text_a, text_b = raw_a.decode("utf-8-sig", errors="replace"), raw_b.decode("utf-8-sig", errors="replace")
    sym_a, sym_b = symbols(relative, text_a), symbols(relative, text_b)
    print("MAIN_SHA256_PREFIX=" + sha(raw_a))
    print("CLIENT_SHA256_PREFIX=" + sha(raw_b))
    print("SAME_BYTES=" + str(raw_a == raw_b))
    print("MAIN_FUNCTIONS=" + str(len(sym_a)) + " CLIENT_FUNCTIONS=" + str(len(sym_b)))
    print("MAIN_ONLY_FUNCTIONS=" + json.dumps(ordered_names(sym_a - sym_b)))
    print("CLIENT_ONLY_FUNCTIONS=" + json.dumps(ordered_names(sym_b - sym_a)))
    markers_a, markers_b = feature_markers(text_a), feature_markers(text_b)
    marker_differences = {k: {"main": markers_a[k], "client": markers_b[k]}
                          for k in markers_a if markers_a[k] != markers_b[k]}
    print("FEATURE_MARKER_DIFFERENCES=" + json.dumps(marker_differences, sort_keys=True))
    if relative.endswith(".ps1"):
        pattern = r"ValidateSet\(([^)]{1,250})\)"
        ma = re.search(pattern, text_a, re.I)
        mb = re.search(pattern, text_b, re.I)
        print("MAIN_CONTROL_ACTIONS=" + (ma.group(1) if ma else "NOT_FOUND"))
        print("CLIENT_CONTROL_ACTIONS=" + (mb.group(1) if mb else "NOT_FOUND"))
    if relative.endswith("manifest.json"):
        try:
            m1, m2 = json.loads(text_a), json.loads(text_b)
            for field in ("name", "version", "permissions", "host_permissions"):
                if m1.get(field) != m2.get(field):
                    print("MANIFEST_DIFFERENCE_" + field.upper() + "=" +
                          json.dumps({"main": m1.get(field), "client": m2.get(field)}))
        except json.JSONDecodeError as exc:
            print("MANIFEST_PARSE_ERROR=" + str(exc))
    if relative == "hud.py":
        for build, source in (("MAIN", text_a), ("CLIENT", text_b)):
            buttons = re.findall(r'tk\.Button\([^)]{0,180}text\s*=\s*["\']([A-Z ]{2,20})["\']', source)
            print(build + "_BUTTON_DECLARATIONS=" + json.dumps(sorted(set(buttons))))

print("\nASSESSMENT=STATIC_DIFF_ONLY_NOT_A_LIVE_RELEASE_TEST")
print("DO_NOT_COPY_ENTIRE_MAIN_BUILD_OVER_CLIENT=True")
print("PROCESSES_RESTARTED=False")
print("FILES_WRITTEN=False")
