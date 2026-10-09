#!/usr/bin/env python3
"""Independent Firefox UI Automation feasibility probe for PCE14.

READ ONLY. Uses the native Windows accessibility tree, not the relay extension.
Only counts and control types cross the process boundary. Never reads names,
values, document text, browser URLs, cookies, tabs' labels, or user messages.
Does not focus, click, paste, type, navigate, or send. This is NOT yet a
user-role observer and cannot certify a real send.
"""
from __future__ import annotations

import csv
import ctypes
import io
import json
import os
import subprocess
from ctypes import wintypes

CLASSES = ("Tab", "TabItem", "Document", "Edit", "Pane", "Window")
MAX_ELEMENTS = 130
MAX_DEPTH = 5


def classify(raw: dict) -> dict:
    """Fail closed: keep only aggregate primitives, strip any UIA text."""
    if not isinstance(raw, dict):
        raise ValueError("UIA response is not an object")
    visited = raw.get("visited")
    depth = raw.get("max_depth")
    if type(visited) is not int or not 0 <= visited <= MAX_ELEMENTS:
        raise ValueError("invalid visited count")
    if type(depth) is not int or not 0 <= depth <= MAX_DEPTH:
        raise ValueError("invalid depth")
    original = raw.get("control_counts")
    if not isinstance(original, dict) or set(original) - set(CLASSES):
        raise ValueError("unexpected control class")
    counts = {}
    for key in CLASSES:
        count = original.get(key, 0)
        if type(count) is not int or not 0 <= count <= visited:
            raise ValueError("invalid aggregate count")
        counts[key] = count
    if sum(counts.values()) > visited:
        raise ValueError("control counters exceed element count")
    return {
        "status": "UIA_AGGREGATES_OBSERVED",
        "visited": visited,
        "max_depth": depth,
        "control_counts": counts,
        "native_window_source": True,
        "content_script_used": False,
        "originating_tab_verified": False,
        "exact_user_message_verified": False,
        "loaded_runtime_attested": False,
        "can_send": False,
    }


def foreground_firefox() -> dict:
    if os.name != "nt":
        return {"status": "NOT_WINDOWS"}
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    hwnd = int(user32.GetForegroundWindow() or 0)
    if not hwnd:
        return {"status": "NO_FOREGROUND_WINDOW"}
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return {"status": "UNKNOWN_FOREGROUND_PID"}
    proc = subprocess.run(
        ["tasklist", "/FI", "PID eq " + str(pid.value), "/FO", "CSV", "/NH"],
        capture_output=True, text=True, timeout=8, check=True)
    try:
        rows = list(csv.reader(io.StringIO(proc.stdout)))
    except csv.Error:
        return {"status": "PROCESS_IDENTITY_UNAVAILABLE"}
    if not any(len(row) >= 2 and row[0].casefold() == "firefox.exe"
               and row[1].strip() == str(pid.value) for row in rows):
        return {"status": "FOREGROUND_NOT_FIREFOX"}
    return {"status": "FOREGROUND_FIREFOX", "hwnd": hwnd, "pid": pid.value}


def uia_command(hwnd: int) -> str:
    """Only insert a validated integer HWND into a constant script."""
    if type(hwnd) is not int or hwnd <= 0:
        raise ValueError("invalid HWND")
    return r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop
$root = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]::new(HWND_LITERAL))
if ($null -eq $root) { throw 'UIA_ROOT_MISSING' }
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$stack = New-Object System.Collections.ArrayList
[void]$stack.Add([pscustomobject]@{Node=$root;Depth=0})
$counts = @{}
$visited = 0
$depthMax = 0
while ($stack.Count -gt 0 -and $visited -lt 130) {
    $index = $stack.Count - 1
    $item = $stack[$index]
    $stack.RemoveAt($index)
    try {
        $node = $item.Node
        $depth = [int]$item.Depth
        $typeName = $node.Current.ControlType.ProgrammaticName
    } catch { continue }
    $visited++
    if ($depth -gt $depthMax) { $depthMax = $depth }
    $allowed = @('Tab','TabItem','Document','Edit','Pane','Window')
    foreach ($typ in $allowed) {
        if ($typeName -eq ('ControlType.' + $typ)) {
            if (-not $counts.ContainsKey($typ)) { $counts[$typ] = 0 }
            $counts[$typ] = [int]$counts[$typ] + 1
            break
        }
    }
    if ($depth -ge 5) { continue }
    try { $child = $walker.GetFirstChild($node) } catch { continue }
    $siblings = 0
    while ($null -ne $child -and $siblings -lt 20) {
        [void]$stack.Add([pscustomobject]@{Node=$child;Depth=$depth+1})
        $siblings++
        try { $child = $walker.GetNextSibling($child) }
        catch { break }
    }
}
[pscustomobject]@{visited=$visited;max_depth=$depthMax;control_counts=$counts} |
    ConvertTo-Json -Compress -Depth 3
""".replace("HWND_LITERAL", str(hwnd))


def inspect(timeout: int = 18) -> dict:
    identity = foreground_firefox()
    if identity["status"] != "FOREGROUND_FIREFOX":
        return {"status": identity["status"], "can_send": False}
    import base64
    encoded = base64.b64encode(uia_command(identity["hwnd"]).encode("utf-16le")).decode("ascii")
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True, text=True, timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        return {"status": "UIA_TIMEOUT", "can_send": False}
    except OSError:
        return {"status": "UIA_UNAVAILABLE", "can_send": False}
    if proc.returncode != 0:
        # Never copy raw UIA exception text or private window labels into reports.
        return {"status": "UIA_QUERY_FAILED", "can_send": False}
    try:
        result = classify(json.loads(proc.stdout.strip()))
    except (ValueError, json.JSONDecodeError):
        return {"status": "UIA_RESPONSE_INVALID", "can_send": False}
    result["foreground_pid"] = identity["pid"]
    result["foreground_hwnd"] = identity["hwnd"]
    return result


def main() -> int:
    report = inspect()
    print("PCE14_UIA_READONLY=" + json.dumps(report, separators=(",", ":")))
    return 0 if report["status"] == "UIA_AGGREGATES_OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
