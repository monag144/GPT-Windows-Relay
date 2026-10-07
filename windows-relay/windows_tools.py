#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time

GPT_WINDOWS_CLIPBOARD_V1 = True
GPT_WINDOWS_UIA_FIELD_ENTRY_V1 = True
GPT_WINDOWS_UIA_CONTROL_ADAPTER_V1 = True
GPT_WINDOWS_SCREENSHOT_CAPTURE_V1 = True
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

if os.name == "nt":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
    user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p


def _require_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("Windows clipboard primitives require Windows")


def _open_clipboard(retries: int = 40, delay: float = 0.025) -> None:
    _require_windows()
    for _ in range(retries):
        if user32.OpenClipboard(None):
            return
        time.sleep(delay)
    raise OSError(ctypes.get_last_error(), "OpenClipboard failed after retries")


def clipboard_read_text() -> str | None:
    _open_clipboard()
    try:
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return None
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            raise OSError(ctypes.get_last_error(), "GetClipboardData failed")
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            raise OSError(ctypes.get_last_error(), "GlobalLock failed")
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def clipboard_write_text(text: str) -> None:
    if not isinstance(text, str):
        raise TypeError("clipboard text must be str")
    raw = (text + "\x00").encode("utf-16-le")
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(raw)) if os.name == "nt" else None
    if not handle:
        _require_windows()
        raise MemoryError("GlobalAlloc failed")
    ownership_transferred = False
    try:
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            raise OSError(ctypes.get_last_error(), "GlobalLock failed")
        try:
            ctypes.memmove(ptr, raw, len(raw))
        finally:
            kernel32.GlobalUnlock(handle)
        _open_clipboard()
        try:
            if not user32.EmptyClipboard():
                raise OSError(ctypes.get_last_error(), "EmptyClipboard failed")
            if not user32.SetClipboardData(CF_UNICODETEXT, handle):
                raise OSError(ctypes.get_last_error(), "SetClipboardData failed")
            ownership_transferred = True
        finally:
            user32.CloseClipboard()
    finally:
        if not ownership_transferred:
            kernel32.GlobalFree(handle)


def clipboard_clear() -> None:
    _open_clipboard()
    try:
        if not user32.EmptyClipboard():
            raise OSError(ctypes.get_last_error(), "EmptyClipboard failed")
    finally:
        user32.CloseClipboard()


def field_set_text(window_title: str, text: str, *, field_name: str | None = None, automation_id: str | None = None, process_id: int | None = None) -> dict:
    _require_windows()
    if not isinstance(window_title, str) or not window_title:
        raise ValueError("window_title is required")
    if not isinstance(text, str):
        raise TypeError("field text must be str")
    if not field_name and not automation_id:
        raise ValueError("field_name or automation_id is required")
    script = Path(__file__).with_name("uia_text_entry.ps1")
    if not script.is_file():
        raise FileNotFoundError(script)
    args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-WindowTitle", window_title, "-TextBase64", base64.b64encode(text.encode("utf-8")).decode("ascii")]
    if field_name:
        args += ["-FieldName", field_name]
    if automation_id:
        args += ["-AutomationId", automation_id]
    if process_id is not None:
        args += ["-ProcessId", str(int(process_id))]
    cp = subprocess.run(args, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if cp.returncode:
        raise RuntimeError((cp.stderr or cp.stdout or "field-set failed").strip())
    lines = [line for line in cp.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("field-set returned no result")
    result = json.loads(lines[-1])
    if result.get("ok") is not True or result.get("readback_match") is not True:
        raise RuntimeError("field-set verification failed")
    return result



_UIA_CONTROL_TYPES = {"Button", "CheckBox", "RadioButton", "ComboBox", "ListItem", "TabItem", "MenuItem", "Hyperlink", "TreeItem"}

def _uia_control_action(window_title: str, action: str, *, control_type: str | None = None, control_name: str | None = None, automation_id: str | None = None, process_id: int | None = None, desired_state: bool | None = None, max_results: int = 50) -> dict:
    _require_windows()
    if not isinstance(window_title, str) or not window_title:
        raise ValueError("window_title is required")
    if action not in {"inspect", "invoke", "select", "set-toggle"}:
        raise ValueError("unsupported UIA control action")
    if control_type is not None and control_type not in _UIA_CONTROL_TYPES:
        raise ValueError("unsupported control_type")
    if action != "inspect" and not control_type:
        raise ValueError("control_type is required for mutating actions")
    if action != "inspect" and not control_name and not automation_id:
        raise ValueError("control_name or automation_id is required for mutating actions")
    if action == "set-toggle" and desired_state is None:
        raise ValueError("desired_state is required for set-toggle")
    if not isinstance(max_results, int) or max_results < 1 or max_results > 200:
        raise ValueError("max_results must be 1..200")
    script = Path(__file__).with_name("uia_control_action.ps1")
    if not script.is_file():
        raise FileNotFoundError(script)
    args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-WindowTitle", window_title, "-Action", action, "-MaxResults", str(max_results)]
    if control_type:
        args += ["-ControlType", control_type]
    if control_name:
        args += ["-ControlName", control_name]
    if automation_id:
        args += ["-AutomationId", automation_id]
    if process_id is not None:
        args += ["-ProcessId", str(int(process_id))]
    if desired_state is not None:
        args += ["-DesiredState", "on" if desired_state else "off"]
    cp = subprocess.run(args, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if cp.returncode:
        raise RuntimeError((cp.stderr or cp.stdout or "UIA control action failed").strip())
    lines = [line for line in cp.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("UIA control action returned no result")
    result = json.loads(lines[-1])
    if result.get("ok") is not True:
        raise RuntimeError("UIA control action verification failed")
    return result

def control_inspect(window_title: str, *, control_type: str | None = None, control_name: str | None = None, automation_id: str | None = None, process_id: int | None = None, max_results: int = 50) -> dict:
    return _uia_control_action(window_title, "inspect", control_type=control_type, control_name=control_name, automation_id=automation_id, process_id=process_id, max_results=max_results)

def control_invoke(window_title: str, *, control_type: str, control_name: str | None = None, automation_id: str | None = None, process_id: int | None = None) -> dict:
    return _uia_control_action(window_title, "invoke", control_type=control_type, control_name=control_name, automation_id=automation_id, process_id=process_id)

def control_select(window_title: str, *, control_type: str, control_name: str | None = None, automation_id: str | None = None, process_id: int | None = None) -> dict:
    return _uia_control_action(window_title, "select", control_type=control_type, control_name=control_name, automation_id=automation_id, process_id=process_id)

def control_set_toggle(window_title: str, checked: bool, *, control_type: str = "CheckBox", control_name: str | None = None, automation_id: str | None = None, process_id: int | None = None) -> dict:
    if not isinstance(checked, bool):
        raise TypeError("checked must be bool")
    return _uia_control_action(window_title, "set-toggle", control_type=control_type, control_name=control_name, automation_id=automation_id, process_id=process_id, desired_state=checked)


def screenshot_dir() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GPTWindowsRelay" / "screenshots"
    root.mkdir(parents=True, exist_ok=True)
    return root


def cleanup_screenshots(*, max_files: int = 20, max_age_hours: float = 24.0) -> dict:
    if max_files < 1 or max_age_hours <= 0:
        raise ValueError("screenshot retention bounds must be positive")
    root = screenshot_dir()
    now = time.time(); removed=[]
    files = [p for p in root.glob("*.png") if p.is_file()]
    for p in files:
        try:
            if now - p.stat().st_mtime > max_age_hours * 3600:
                p.unlink(); removed.append(str(p))
        except FileNotFoundError:
            pass
    remain = sorted((p for p in root.glob("*.png") if p.is_file()), key=lambda p:p.stat().st_mtime, reverse=True)
    for p in remain[max_files:]:
        try: p.unlink(); removed.append(str(p))
        except FileNotFoundError: pass
    return {"removed": len(removed), "remaining": len([p for p in root.glob("*.png") if p.is_file()]), "max_files": max_files, "max_age_hours": max_age_hours}


def screenshot_capture(target: str, *, window_title: str | None = None, process_id: int | None = None, x: int | None = None, y: int | None = None, width: int | None = None, height: int | None = None, max_files: int = 20, max_age_hours: float = 24.0) -> dict:
    _require_windows()
    if target not in {"screen","window","region"}: raise ValueError("target must be screen, window, or region")
    if target == "window" and not window_title: raise ValueError("window_title is required for window capture")
    if target == "region" and (width is None or height is None or width <= 0 or height <= 0): raise ValueError("positive width/height required for region capture")
    cleanup_screenshots(max_files=max_files,max_age_hours=max_age_hours)
    root=screenshot_dir(); stamp=time.strftime("%Y%m%dT%H%M%S",time.gmtime()); out=root/f"screenshot-{stamp}-{time.time_ns()%1000000000:09d}.png"
    script=Path(__file__).with_name("screenshot_capture.ps1")
    args=["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(script),"-Target",target,"-Output",str(out)]
    if window_title: args += ["-WindowTitle",window_title]
    if process_id is not None: args += ["-ProcessId",str(int(process_id))]
    if target == "region": args += ["-X",str(int(x or 0)),"-Y",str(int(y or 0)),"-Width",str(int(width)),"-Height",str(int(height))]
    cp=subprocess.run(args,text=True,capture_output=True,encoding="utf-8",errors="replace")
    if cp.returncode: raise RuntimeError((cp.stderr or cp.stdout or "screenshot capture failed").strip())
    lines=[line for line in cp.stdout.splitlines() if line.strip()]
    if not lines: raise RuntimeError("screenshot capture returned no result")
    result=json.loads(lines[-1])
    if result.get("ok") is not True or not out.is_file(): raise RuntimeError("screenshot capture verification failed")
    raw=out.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"): raise RuntimeError("screenshot is not a PNG")
    result.update({"mime":"image/png","bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"managed":True})
    result["chatgpt_attachment"]={"kind":"image","name":out.name,"mime":"image/png"}
    retention=cleanup_screenshots(max_files=max_files,max_age_hours=max_age_hours); result["retention"]=retention
    return result

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Explicit Windows interaction primitives")
    sub = ap.add_subparsers(dest="command", required=True)
    rd = sub.add_parser("clipboard-read")
    rd.add_argument("--json", action="store_true")
    wr = sub.add_parser("clipboard-write")
    g = wr.add_mutually_exclusive_group(required=True)
    g.add_argument("--text")
    g.add_argument("--stdin", action="store_true")
    sub.add_parser("clipboard-clear")
    fs = sub.add_parser("field-set")
    fs.add_argument("--window-title", required=True)
    fs.add_argument("--field-name")
    fs.add_argument("--automation-id")
    fs.add_argument("--process-id", type=int)
    fg = fs.add_mutually_exclusive_group(required=True)
    fg.add_argument("--text")
    fg.add_argument("--stdin", action="store_true")
    for cmd in ("control-inspect", "control-invoke", "control-select", "control-check", "control-uncheck"):
        cp = sub.add_parser(cmd)
        cp.add_argument("--window-title", required=True)
        cp.add_argument("--control-type", choices=sorted(_UIA_CONTROL_TYPES))
        cp.add_argument("--control-name")
        cp.add_argument("--automation-id")
        cp.add_argument("--process-id", type=int)
        cp.add_argument("--max-results", type=int, default=50)
    sc = sub.add_parser("screenshot-capture")
    sc.add_argument("--target", choices=["screen","window","region"], required=True)
    sc.add_argument("--window-title")
    sc.add_argument("--process-id", type=int)
    sc.add_argument("--x", type=int); sc.add_argument("--y", type=int); sc.add_argument("--width", type=int); sc.add_argument("--height", type=int)
    sc.add_argument("--max-files", type=int, default=20); sc.add_argument("--max-age-hours", type=float, default=24.0)
    sub.add_parser("screenshot-cleanup").add_argument("--max-files", type=int, default=20)
    ns = ap.parse_args(argv)
    if ns.command == "clipboard-read":
        value = clipboard_read_text()
        if ns.json:
            print(json.dumps({"text": value, "has_text": value is not None}, ensure_ascii=False))
        elif value is not None:
            print(value, end="")
        return 0
    if ns.command == "clipboard-write":
        value = sys.stdin.read() if ns.stdin else ns.text
        clipboard_write_text(value)
        print(json.dumps({"ok": True, "chars": len(value)}, ensure_ascii=False))
        return 0
    if ns.command == "field-set":
        value = sys.stdin.read() if ns.stdin else ns.text
        result = field_set_text(ns.window_title, value, field_name=ns.field_name, automation_id=ns.automation_id, process_id=ns.process_id)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if ns.command == "control-inspect":
        print(json.dumps(control_inspect(ns.window_title, control_type=ns.control_type, control_name=ns.control_name, automation_id=ns.automation_id, process_id=ns.process_id, max_results=ns.max_results), ensure_ascii=False)); return 0
    if ns.command == "control-invoke":
        print(json.dumps(control_invoke(ns.window_title, control_type=ns.control_type, control_name=ns.control_name, automation_id=ns.automation_id, process_id=ns.process_id), ensure_ascii=False)); return 0
    if ns.command == "control-select":
        print(json.dumps(control_select(ns.window_title, control_type=ns.control_type, control_name=ns.control_name, automation_id=ns.automation_id, process_id=ns.process_id), ensure_ascii=False)); return 0
    if ns.command in {"control-check", "control-uncheck"}:
        print(json.dumps(control_set_toggle(ns.window_title, ns.command == "control-check", control_type=ns.control_type or "CheckBox", control_name=ns.control_name, automation_id=ns.automation_id, process_id=ns.process_id), ensure_ascii=False)); return 0
    if ns.command == "screenshot-capture":
        result=screenshot_capture(ns.target,window_title=ns.window_title,process_id=ns.process_id,x=ns.x,y=ns.y,width=ns.width,height=ns.height,max_files=ns.max_files,max_age_hours=ns.max_age_hours)
        print(json.dumps(result,ensure_ascii=False)); return 0
    if ns.command == "screenshot-cleanup":
        print(json.dumps(cleanup_screenshots(max_files=ns.max_files),ensure_ascii=False)); return 0
    clipboard_clear()
    print(json.dumps({"ok": True, "cleared": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
