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
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
HOME = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "GPTWindowsRelayDesktop"
PROFILE = HOME / "command-courier-runtime.json"
HUD_MODE = HOME / "hud-mode.json"
STARTUP_MANAGER = ROOT / "tools" / "Manage-Command-CourierStartup.ps1"
LAUNCHER = ROOT / "COMMAND-COURIER.cmd"
NATIVE = "native-desktop"
DISABLED = "disabled"
ALLOWED = {NATIVE, DISABLED}
IS_WINDOWS = os.name == "nt"


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



STARTUP_EVENTS = HOME / "command-courier-startup-events.jsonl"


def record_startup_event(event: str, detail: str = ""):
    """Durable, payload-free sign-in diagnostics; never block the application."""
    try:
        HOME.mkdir(parents=True, exist_ok=True)
        entry = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "event": event}
        if detail:
            entry["detail"] = detail[:180]
        with STARTUP_EVENTS.open("a", encoding="utf-8") as log:
            log.write(json.dumps(entry, ensure_ascii=False) + "\n")
            log.flush()
            os.fsync(log.fileno())
    except OSError:
        pass


def start() -> int:
    mode = runtime_mode()
    print("COURIER_RUNTIME=" + mode, flush=True)
    record_startup_event("START_REQUESTED", mode)
    if mode == DISABLED:
        print("COURIER_START=DISABLED_BY_PROFILE")
        record_startup_event("DISABLED_BY_PROFILE")
        return 0
    if not IS_WINDOWS:
        raise RuntimeError("COURIER_DESKTOP_LAUNCH_REQUIRES_WINDOWS_INTERACTIVE_SESSION")

    # Start the canonical HUD FIRST.  At sign-in the native runner's lock,
    # ChatGPT readiness, or process startup can fail independently; none of
    # those conditions should prevent the operator from seeing STOP/OFF.
    import desktop_native_relay as native
    native.select_original_hud()
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
    record_startup_event("ORIGINAL_HUD_RUNNING")

    # Engine startup follows verified HUD availability and respects OFF.
    config = native.configuration()
    if config["off"]:
        print("COURIER_ENGINE=OFF_RETAINED")
        print("COURIER_START=HUD_RUNNING_ENGINE_OFF_RETAINED")
        record_startup_event("HUD_RUNNING_ENGINE_OFF_RETAINED")
        return 0
    native.launch_runner_if_absent()
    if not native.runner_active():
        raise RuntimeError("COURIER_ENGINE_NOT_RUNNING_AFTER_START")
    print("COURIER_ENGINE=RUNNING_SINGLETON_VERIFIED")
    print("COURIER_START=ENGINE_AND_HUD_LINKED")
    record_startup_event("ENGINE_AND_HUD_LINKED")
    return 0



def go() -> int:
    """Activate the selected runtime from an already-visible Command Courier HUD.

    Unlike start(), never reconcile/restart the calling HUD.  This operation
    does not create packets, execute instructions or force delivery.  Future
    destination transports must provide their own explicit adapter.
    """
    mode = runtime_mode()
    print("COURIER_GO_RUNTIME=" + mode, flush=True)
    if mode != NATIVE:
        raise RuntimeError("COURIER_GO_SELECTED_RUNTIME_UNAVAILABLE")
    if not IS_WINDOWS:
        raise RuntimeError("COURIER_GO_REQUIRES_WINDOWS_INTERACTIVE_SESSION")
    import desktop_native_relay as native
    config = native.configuration()
    if config["off"]:
        raise RuntimeError("COURIER_GO_OFF_USE_ARM_FIRST")
    if not config["armed"]:
        raise RuntimeError("COURIER_GO_DISARMED_USE_ARM_FIRST")
    # Existing native singleton performs independent command admission,
    # journal deduplication and delivery; GO never calls its sender.
    native.launch_runner_if_absent()
    report = native.get_status()
    if not report.get("native_running"):
        raise RuntimeError("COURIER_GO_NATIVE_SINGLETON_NOT_CONFIRMED")
    if report.get("native_off") or not report.get("native_armed"):
        raise RuntimeError("COURIER_GO_POLICY_CHANGED_WHILE_ACTIVATING")
    phase = str(report.get("phase") or "UNKNOWN").upper()
    # GO starts/attaches to the courier, not to any one destination.
    # A stuck or uncertain ChatGPT outbox must not block independent sources
    # or file/API recipients. Never claim the old result was submitted.
    if report.get("runner_error_type") or phase == "ERROR":
        raise RuntimeError("COURIER_GO_ENGINE_ERROR")
    if (phase in {"DELIVERY_BLOCKED", "DELIVERY_UNCERTAIN"}
            or report.get("delivery_blocked")):
        print("COURIER_GO=EXECUTION_READY_OUTBOUND_UNRESOLVED")
        return 0
    # The foreground-field adapter does NOT require ChatGPT to be open.
    # Only actual runtime baselining is an activation-in-progress state.
    if phase == "BASELINING":
        print("COURIER_GO=WAITING_FOR_DESTINATION")
        return 0
    if phase not in {"BASELINED", "IDLE", "EXECUTING", "DELIVERING",
                     "FORWARDING_NO_CHATGPT", "AWAITING_TEXT_FIELD",
                     "WAITING_FOR_CHATGPT_APP"}:
        raise RuntimeError("COURIER_GO_UNVERIFIED_RUNTIME_PHASE")
    print("COURIER_GO=NATIVE_RUNTIME_READY")
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


def routes(action: str, *, route_id: str | None = None,
           source: str | None = None, to_dir: str | None = None,
           to_http: str | None = None, bearer_token_env: str | None = None) -> int:
    """Configure transport-neutral forwarding without changing the native HUD."""
    import courier_forwarder as forwarder
    if action == "status":
        print("COURIER_TEXT_FORWARDING_STATUS=" +
              json.dumps(forwarder.status(HOME), sort_keys=True))
    elif action == "set":
        if not route_id or not source or (bool(to_dir) == bool(to_http)):
            raise ValueError("COURIER_ROUTE_ID_SOURCE_AND_ONE_DESTINATION_REQUIRED")
        forwarder.configure_route(HOME, route_id, source,
                                  "directory" if to_dir else "http",
                                  to_dir or to_http,
                                  bearer_token_env=bearer_token_env)
        print("COURIER_TEXT_ROUTE_CONFIGURED=" + route_id)
        print("COURIER_TEXT_ROUTE_ACTIVATION=WHEN_ARMED_AND_AUTO_SEND_ON")
    elif action in ("enable", "disable"):
        forwarder.set_enabled(HOME, action == "enable")
        print("COURIER_TEXT_FORWARDING=" + ("ENABLED" if action == "enable" else "DISABLED"))
    else:
        raise ValueError("COURIER_ROUTE_ACTION_INVALID")
    return 0


def read_copied_text() -> str:
    """Read text deliberately placed on the Windows clipboard by the user.

    No screen scanning, synthetic Ctrl+C, or interaction with other apps.
    The temporary Tk clipboard reader has no visible window or HUD.
    """
    import tkinter as tk
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
    except tk.TclError as exc:
        raise RuntimeError("COURIER_CLIPBOARD_TEXT_UNAVAILABLE_COPY_TEXT_FIRST") from exc
    finally:
        if root is not None:
            root.destroy()
    return text


def test_fire(route_id: str | None = None, *, clipboard: bool = False) -> int:
    """Debug the actual configured local file route; never send to ChatGPT UI."""
    if runtime_mode() != NATIVE:
        raise RuntimeError("COURIER_TEST_FIRE_NATIVE_PROFILE_REQUIRED")
    import desktop_native_relay as native
    import courier_test_fire as debug
    state = native.get_status()
    if clipboard:
        report = debug.send_copied_text(
            HOME, state, read_copied_text(), route_id=route_id)
    else:
        report = debug.fire(HOME, state, route_id=route_id)
    print("COURIER_TEST_FIRE=" + json.dumps(report, sort_keys=True))
    return 0


def startup(action: str) -> int:
    """Only the current user's Startup shortcut is changed, on explicit request."""
    if not IS_WINDOWS:
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
    sub.add_parser("go")
    fire = sub.add_parser("test-fire", help="Temporary debug: real file-route test with receipt")
    fire.add_argument("--route", dest="fire_route", help="Explicit configured directory route")
    fire.add_argument("--clipboard", action="store_true",
                      help="Forward only text you deliberately copied with Ctrl+C")
    sub.add_parser("status")
    profile = sub.add_parser("profile")
    profile.add_argument("mode", nargs="?", choices=sorted(ALLOWED))
    login = sub.add_parser("startup")
    login.add_argument("action", choices=("install", "remove", "status"))
    route = sub.add_parser("route", help="Configured text source to file or HTTP destination")
    route_sub = route.add_subparsers(dest="route_action", required=True)
    setting = route_sub.add_parser("set")
    setting.add_argument("--id", required=True)
    setting.add_argument("--source", required=True)
    target = setting.add_mutually_exclusive_group(required=True)
    target.add_argument("--to-dir")
    target.add_argument("--to-http")
    setting.add_argument("--bearer-token-env")
    route_sub.add_parser("status")
    route_sub.add_parser("enable")
    route_sub.add_parser("disable")
    args = parser.parse_args(argv)
    try:
        if args.command in (None, "start"):
            return start()
        if args.command == "go":
            return go()
        if args.command == "status":
            return status()
        if args.command == "test-fire":
            return test_fire(args.fire_route, clipboard=args.clipboard)
        if args.command == "profile":
            if args.mode is not None:
                select_runtime(args.mode)
            else:
                print("COURIER_RUNTIME=" + runtime_mode())
            return 0
        if args.command == "startup":
            return startup(args.action)
        if args.command == "route":
            return routes(args.route_action,
                          route_id=getattr(args, "id", None),
                          source=getattr(args, "source", None),
                          to_dir=getattr(args, "to_dir", None),
                          to_http=getattr(args, "to_http", None),
                          bearer_token_env=getattr(args, "bearer_token_env", None))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        if args.command in (None, "start"):
            record_startup_event("START_FAILED", type(exc).__name__ + ":" + str(exc))
        print("COURIER_ERROR=" + str(exc), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
