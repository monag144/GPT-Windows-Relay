#!/usr/bin/env python3
"""Command Courier: runtime-selectable launcher for the existing relay and HUD.

This coordinator is deliberately separate from command execution and the HUD.
The login shortcut always points here; changing the local runtime profile
changes what it starts without replacing or reinstalling the application.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
HOME = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "GPTWindowsRelayDesktop"
PROFILE = HOME / "command-courier-runtime.json"
HUD_MODE = HOME / "hud-mode.json"
STARTUP_MANAGER = ROOT / "tools" / "Manage-Command-CourierStartup.ps1"
LAUNCHER = ROOT / "COMMAND-COURIER.cmd"
NATIVE = "native-desktop"
DISABLED = "disabled"
ALLOWED = {NATIVE, DISABLED}


def runtime_mode() -> str:
    """Read explicit preference, falling back to an existing selected HUD mode."""
    if PROFILE.is_file():
        record = json.loads(PROFILE.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or record.get("version") != 1 or record.get("runtime") not in ALLOWED:
            raise RuntimeError("COURIER_RUNTIME_PROFILE_INVALID")
        return record["runtime"]
    try:
        marker = json.loads(HUD_MODE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return DISABLED
    except (ValueError, OSError):
        raise RuntimeError("COURIER_EXISTING_HUD_MODE_UNREADABLE")
    return NATIVE if marker.get("transport") == "native-chatgpt-app" else DISABLED


def select_runtime(value: str):
    if value not in ALLOWED:
        raise ValueError("COURIER_RUNTIME_INVALID")
    HOME.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".courier-profile-", suffix=".tmp", dir=HOME)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as writer:
            json.dump({"version": 1, "runtime": value}, writer, sort_keys=True)
            writer.flush()
            os.fsync(writer.fileno())
        os.replace(temporary, PROFILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print("COURIER_RUNTIME_SELECTED=" + value)
    print("COURIER_PROFILE_APPLIES=NEXT_START_NO_RUNNING_PROCESS_MODIFIED")


def start() -> int:
    mode = runtime_mode()
    print("COURIER_RUNTIME=" + mode, flush=True)
    if mode == DISABLED:
        print("COURIER_START=DISABLED_BY_PROFILE")
        return 0
    if os.name != "nt":
        raise RuntimeError("COURIER_DESKTOP_LAUNCH_REQUIRES_WINDOWS_INTERACTIVE_SESSION")

    # The original engine owns the native singleton and arming settings.
    # A stopped or OFF engine is never implicitly re-armed by login startup.
    import desktop_native_relay as native
    native.select_original_hud()
    config = native.configuration()
    if config["off"]:
        print("COURIER_ENGINE=OFF_RETAINED")
    else:
        native.launch_runner_if_absent()
        if not native.runner_active():
            raise RuntimeError("COURIER_ENGINE_NOT_RUNNING_AFTER_START")
        print("COURIER_ENGINE=RUNNING_SINGLETON_VERIFIED")

    # The existing PowerShell reconciler launches exactly the original HUD.
    # It never modifies the Firefox/browser backend and never starts a mini HUD.
    powershell = shutil.which("powershell.exe")
    if not powershell:
        raise RuntimeError("COURIER_POWERSHELL_MISSING_FOR_HUD")
    response = subprocess.run(
        [powershell, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(ROOT / "tools" / "Reconcile-OriginalDesktopHUD.ps1")],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=45, check=False,
    )
    if response.returncode:
        raise RuntimeError("COURIER_HUD_START_FAILED: " + (response.stderr or response.stdout)[-800:])
    if "ORIGINAL_HUD_RUNNING_COUNT=1" not in response.stdout:
        raise RuntimeError("COURIER_HUD_SINGLETON_NOT_CONFIRMED")
    print("COURIER_HUD=ORIGINAL_TOP_RIGHT_RUNNING")
    print("COURIER_START=ENGINE_AND_HUD_LINKED")
    return 0


def status() -> int:
    mode = runtime_mode()
    print("COURIER_RUNTIME=" + mode)
    if mode != NATIVE:
        print("COURIER_STATUS=INACTIVE_PROFILE")
        return 0
    import desktop_native_relay as native
    print("COURIER_ENGINE_STATUS=" + json.dumps(native.get_status(), sort_keys=True))
    print("COURIER_HUD_MODE=" + str(HUD_MODE.is_file()))
    return 0


def startup(action: str) -> int:
    """Only the current user's Startup shortcut is changed, on explicit request."""
    if os.name != "nt":
        raise RuntimeError("COURIER_STARTUP_REQUIRES_WINDOWS")
    powershell = shutil.which("powershell.exe")
    if not powershell:
        raise RuntimeError("COURIER_POWERSHELL_MISSING")
    command = [powershell, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-File", str(STARTUP_MANAGER), "-Action", action,
               "-LauncherPath", str(LAUNCHER)]
    response = subprocess.run(command, cwd=str(ROOT), capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=30, check=False)
    if response.stdout:
        print(response.stdout.rstrip())
    if response.returncode:
        raise RuntimeError("COURIER_STARTUP_" + action.upper() + "_FAILED: " + response.stderr[-600:])
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Command Courier | relay and HUD linked, runtime selectable")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("start")
    sub.add_parser("status")
    profile = sub.add_parser("profile")
    profile.add_argument("mode", nargs="?", choices=sorted(ALLOWED))
    login = sub.add_parser("startup")
    login.add_argument("action", choices=("install", "remove", "status"))
    args = parser.parse_args(argv)
    try:
        if args.command in (None, "start"):
            return start()
        if args.command == "status":
            return status()
        if args.command == "profile":
            if args.mode is not None:
                select_runtime(args.mode)
            else:
                print("COURIER_RUNTIME=" + runtime_mode())
            return 0
        if args.command == "startup":
            return startup(args.action)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print("COURIER_ERROR=" + str(exc), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
