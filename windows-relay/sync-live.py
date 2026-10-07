#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import socket
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_LIVE = Path.home() / "Downloads" / "Dev" / "GPT" / "Client" / "Relay"

FILES = [
    "windows_tools.py",
    "windows_workflow.py",
    "firefox_adapter.py",
    "firefox_tab_adapter.ps1",
    "resume_profile.py",
    "job_application_helper.py",
    "uia_text_entry.ps1",
    "uia_control_action.ps1",
    "screenshot_capture.ps1",
    "hud.py",
    "START-HUD.bat",
    "START-RELAY.bat",
    "STOP-RELAY.bat",
    "relay-control.ps1",
    "relay-watchdog-loop.ps1",
    "run.ps1",
    "windows_relay.py",
    "content.js",
    "install-browser-fix.ps1",
    "install-signed-extension-policy.ps1",
    "firefox-policy-template.json",
    "build-extension-xpi.ps1",
    "sign-extension.ps1",
    "extension/content.js",
    "extension/service_worker.js",
    "extension/manifest.json",
    "extension-persistent/content.js",
    "extension-persistent/service_worker.js",
    "extension-persistent/manifest.json",
    "extension-persistent/popup.html",
    "extension-persistent/popup.js",
]


def copy_file(src_root: Path, dst_root: Path, rel: str, backup: Path) -> None:
    src = src_root / rel
    dst = dst_root / rel
    if not src.is_file():
        raise FileNotFoundError(f"missing source file: {src}")
    if dst.exists():
        safe = rel.replace("/", "_").replace("\\", "_")
        shutil.copy2(dst, backup / f"{safe}.bak")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_xpi(live: Path) -> Path:
    src = live / "extension-persistent"
    manifest = (src / "manifest.json").read_text(encoding="utf-8")
    import json
    version = json.loads(manifest)["version"]
    out = live / "dist" / f"gpt-windows-relay-{version}.xpi"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in src.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(src).as_posix())
    return out



def listener_pid(port: int = 8766) -> int | None:
    cp = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        text=True,
        capture_output=True,
        check=False,
    )
    needle = f"127.0.0.1:{port}"
    for line in cp.stdout.splitlines():
        if needle in line and "LISTENING" in line.upper():
            parts = line.split()
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                pass
    return None


def restart_backend_under_supervisor(port: int = 8766) -> None:
    pid = listener_pid(port)
    if pid is None:
        print("BACKEND_RESTART=NO_LISTENER_FOUND")
        return

    print(f"BACKEND_OLD_PID={pid}")
    subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
        check=False,
    )

    deadline = time.time() + 15
    while time.time() < deadline:
        time.sleep(0.5)
        new_pid = listener_pid(port)
        if new_pid is not None and new_pid != pid:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    pass
            except OSError:
                continue
            print(f"BACKEND_NEW_PID={new_pid}")
            print("BACKEND_RESTART=GREEN")
            return
    print("BACKEND_RESTART=NOT_CONFIRMED")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", type=Path, default=DEFAULT_LIVE)
    ap.add_argument("--restart-backend", action="store_true")
    args = ap.parse_args()
    live = args.live.resolve()

    if not live.is_dir():
        raise SystemExit(f"live relay missing: {live}")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = live / "backups" / f"sync-live-{stamp}"
    backup.mkdir(parents=True, exist_ok=True)

    for rel in FILES:
        copy_file(HERE, live, rel, backup)

    src_tests = HERE / "tests"
    dst_tests = live / "tests"
    shutil.rmtree(dst_tests, ignore_errors=True)
    shutil.copytree(src_tests, dst_tests)

    py = live / ".venv" / "Scripts" / "python.exe"
    if not py.is_file():
        raise SystemExit(f"relay Python missing: {py}")

    print(f"BACKUP={backup}")
    print("RUNNING_TESTS=True", flush=True)
    subprocess.run(
        [str(py), "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=live,
        check=True,
    )

    xpi = build_xpi(live)

    content = (live / "extension" / "content.js").read_text(encoding="utf-8")
    worker = (live / "extension" / "service_worker.js").read_text(encoding="utf-8")
    print(f"V11_STAGED={'GPT_WINDOWS_EVENT_DRIVEN_SCANNER_V11' in content}")
    print(f"STABLE_MAIN_STAGED={'GPT_WINDOWS_STABLE_MAIN_OBSERVER_V1' in content}")
    print(f"CODEBLOCK_PARSER_STAGED={'GPT_WINDOWS_CODEBLOCK_PACKET_EXTRACTION_V1' in content}")
    print(f"CURRENT_ROLE_SELECTORS_STAGED={'GPT_WINDOWS_CURRENT_CHATGPT_ROLE_SELECTORS_V1' in content}")
    print(f"HANDOFF_SCROLL_V5_STAGED={'GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V5' in content}")
    print(f"SCROLL_TELEMETRY_V5_STAGED={'GPT_WINDOWS_SCROLL_TELEMETRY_V5' in content}")
    print(f"WORKER_DRIVEN_SCROLL_STAGED={'GPT_WINDOWS_WORKER_DRIVEN_SCROLL_CONTROL_V1' in content}")
    print(f"TRUE_CONTENT_START_TELEMETRY_STAGED={'GPT_WINDOWS_TRUE_CONTENT_START_TELEMETRY_V1' in content}")
    print(f"RESULT_DELIVERY_RECOVERY_STAGED={'GPT_WINDOWS_RESULT_DELIVERY_RECOVERY_V1' in content}")
    print(f"RESULT_ANTISPAM_V2_STAGED={'GPT_WINDOWS_RESULT_ANTISPAM_V2' in content}")
    print(f"SEND_READINESS_GATE_STAGED={'GPT_WINDOWS_SEND_READINESS_GATE_V1' in content}")
    print(f"PREINJECTION_IDLE_GATE_STAGED={'GPT_WINDOWS_PREINJECTION_IDLE_GATE_V1' in content}")
    print(f"RELAY_DRAFT_RECOVERY_STAGED={'GPT_WINDOWS_RELAY_DRAFT_RECOVERY_V1' in content}")
    print(f"DRAFT_SINGLE_OWNER_V2_STAGED={'GPT_WINDOWS_RELAY_DRAFT_SINGLE_OWNER_V2' in content}")
    print(f"GENERATION_START_ACK_V1_STAGED={'GPT_WINDOWS_GENERATION_START_ACK_V1' in content}")
    print(f"DEFERRED_ACTION_QUEUE_V1_STAGED={'GPT_WINDOWS_DEFERRED_ACTION_QUEUE_V1' in content}")
    runtime_identity_marker="runtime:'v11-scroll-v5-delivery-v8'"
    print(f"RUNTIME_IDENTITY_STAGED={runtime_identity_marker in content}")
    print(f"PERSISTENT_PORT_STAGED={'GPT_WINDOWS_PERSISTENT_BACKGROUND_PORT_V1' in content}")
    print(f"BROWSER_TELEMETRY_STAGED={'content_port_connected' in worker and 'action_received' in worker}")
    print(f"XPI={xpi}")
    if args.restart_backend:
        restart_backend_under_supervisor()
    print("SYNC_LIVE=GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
