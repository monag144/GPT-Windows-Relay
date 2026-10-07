from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
LIVE = Path.home() / "Downloads" / "Dev" / "GPT" / "Client" / "Relay"
GIT = Path(r"C:\Program Files\Git\cmd\git.exe")
PY = LIVE / ".venv" / "Scripts" / "python.exe"
PYW = LIVE / ".venv" / "Scripts" / "pythonw.exe"
CONTROL = LIVE / "relay-control.ps1"
HUD = LIVE / "hud.py"
KNOWN_GOOD = "5df3838"  # new-repo migration baseline containing the PCE7 control-plane source

# PCE7.446 is deliberately a narrow control-plane cutover. Browser delivery,
# job-application modules, extension bundles, and other live runtime files are
# outside this deployment boundary.
RUNTIME_FILES = (
    "hud.py",
    "relay-control.ps1",
    "relay-watchdog-loop.ps1",
    "STOP-RELAY.bat",
)


def run(args, *, cwd=None, check=True, capture=False):
    printable = " ".join(str(x) for x in args)
    print(f"RUN: {printable}", flush=True)
    cp = subprocess.run(
        [str(x) for x in args],
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=capture,
        check=False,
    )
    if capture:
        if cp.stdout:
            print(cp.stdout.rstrip())
        if cp.stderr:
            print(cp.stderr.rstrip(), file=sys.stderr)
    if check and cp.returncode != 0:
        raise RuntimeError(f"command failed rc={cp.returncode}: {printable}")
    return cp


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def listener_pid(port=8766):
    cp = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        text=True,
        capture_output=True,
        check=False,
    )
    needle = f"127.0.0.1:{port}"
    for line in cp.stdout.splitlines():
        if needle in line and "LISTENING" in line.upper():
            try:
                return int(line.split()[-1])
            except (ValueError, IndexError):
                pass
    return None


def hud_process_count():
    ps = r'''
$items=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
  $_.Name -match '^pythonw(\.exe)?$' -and
  $_.CommandLine -match '(?i)hud\.py'
})
Write-Output $items.Count
'''
    cp = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        return int((cp.stdout or "0").strip().splitlines()[-1])
    except Exception:
        return 0


def stop_hud_processes():
    ps = r'''
$items=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
  $_.Name -match '^pythonw(\.exe)?$' -and
  $_.CommandLine -match '(?i)hud\.py'
})
foreach($p in $items){
  Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
'''
    run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps])


def start_hud():
    if not PYW.is_file() or not HUD.is_file():
        raise RuntimeError("HUD launch files missing")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        [str(PYW), "hud.py"],
        cwd=str(LIVE),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    deadline = time.time() + 5
    while time.time() < deadline:
        if hud_process_count() > 0:
            print("HUD=RUNNING")
            return
        time.sleep(0.25)
    raise RuntimeError("HUD did not start")


def control(action, expected=None):
    cp = run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            CONTROL,
            action,
        ],
        capture=True,
        check=False,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"relay-control {action} failed rc={cp.returncode}")
    text = (cp.stdout or "").strip()
    if expected and expected not in text:
        raise RuntimeError(
            f"relay-control {action} expected {expected!r}, got {text!r}"
        )
    return text


def verify_source():
    if not SOURCE.is_dir() or not LIVE.is_dir():
        raise RuntimeError("source or live relay directory missing")
    if not PY.is_file():
        raise RuntimeError(f"live Python missing: {PY}")

    status = subprocess.run(
        [str(GIT), "status", "--porcelain"],
        cwd=SOURCE.parent,
        text=True,
        capture_output=True,
        check=False,
    )
    if status.returncode != 0:
        raise RuntimeError("git status failed")
    if status.stdout.strip():
        raise RuntimeError("source working tree is dirty")

    ancestor = subprocess.run(
        [str(GIT), "merge-base", "--is-ancestor", KNOWN_GOOD, "HEAD"],
        cwd=SOURCE.parent,
        check=False,
    )
    if ancestor.returncode != 0:
        raise RuntimeError(
            f"HEAD does not contain known-good state-machine commit {KNOWN_GOOD}"
        )

    for rel in RUNTIME_FILES:
        if not (SOURCE / rel).is_file():
            raise RuntimeError(f"source runtime file missing: {rel}")

    # Validate the complete source tree before crossing the live boundary.
    run(
        [PY, "-m", "unittest", "discover", "-s", "tests", "-q"],
        cwd=SOURCE,
    )
    print("SOURCE_TESTS=GREEN")


def stage_runtime(stage: Path):
    for rel in RUNTIME_FILES:
        src = SOURCE / rel
        dst = stage / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if sha256(src) != sha256(dst):
            raise RuntimeError(f"staging hash mismatch: {rel}")
    print("STAGE=GREEN")


def make_backup():
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    rb = LIVE / "rollback" / f"PCE7.446-live-precutover-{stamp}"
    if rb.exists():
        raise RuntimeError(f"rollback already exists: {rb}")

    (rb / "files").mkdir(parents=True)
    (rb / "markers").mkdir(parents=True)

    present = []
    for rel in RUNTIME_FILES:
        src = LIVE / rel
        if src.is_file():
            dst = rb / "files" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            present.append(rel)

    markers = []
    for src in LIVE.glob(".relay-*"):
        if src.is_file():
            shutil.copy2(src, rb / "markers" / src.name)
            markers.append(src.name)

    manifest = {
        "runtime_files": list(RUNTIME_FILES),
        "present_files": present,
        "markers": markers,
    }
    (rb / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(f"LIVE_BACKUP={rb}")
    return rb


def deploy_runtime(stage: Path):
    stop_hud_processes()
    for rel in RUNTIME_FILES:
        src = stage / rel
        dst = LIVE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if sha256(SOURCE / rel) != sha256(dst):
            raise RuntimeError(f"live/source hash mismatch: {rel}")
    print("LIVE_FILES=SOURCE_EXACT")


def restore_backup(rb: Path):
    stop_hud_processes()
    manifest = json.loads((rb / "manifest.json").read_text(encoding="utf-8"))
    present = set(manifest.get("present_files", []))

    for rel in RUNTIME_FILES:
        dst = LIVE / rel
        src = rb / "files" / rel
        if rel in present:
            if not src.is_file():
                raise RuntimeError(f"rollback file missing: {rel}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif dst.exists():
            dst.unlink()

    for marker in LIVE.glob(".relay-*"):
        if marker.is_file():
            marker.unlink(missing_ok=True)
    for src in (rb / "markers").glob("*"):
        if src.is_file():
            shutil.copy2(src, LIVE / src.name)

    print("LIVE_FILES_RESTORED")


def prove_kill():
    control("kill", "KILLED")
    if listener_pid() is not None:
        raise RuntimeError("KILL left port 8766 listening")
    if hud_process_count() != 0:
        raise RuntimeError("KILL left HUD process running")
    print("KILL_ACCEPTANCE=GREEN")

    # A deliberate START must clear the kill latch and make the relay usable again.
    control("start", "RUNNING PID=")
    control("status", "STATE=RUNNING")
    start_hud()


def acceptance():
    start_hud()

    control("stop", "STOPPED")
    control("status", "STATE=STOPPED")

    control("off", "OFF")
    control("status", "STATE=OFF")

    control("start", "RUNNING PID=")
    control("status", "STATE=RUNNING")

    control("restart", "RUNNING PID=")
    control("status", "STATE=RUNNING")

    prove_kill()

    control("stop", "STOPPED")
    control("status", "STATE=STOPPED")

    if listener_pid() is not None:
        raise RuntimeError("port 8766 still listening after final STOP")

    cp = run([PY, HUD, "--once"], cwd=LIVE, capture=True)
    snap = json.loads((cp.stdout or "").strip().splitlines()[-1])
    if snap.get("intent") != "STOPPED" or snap.get("title_phase") != "STOPPED":
        raise RuntimeError(f"HUD snapshot not STOPPED: {snap}")
    if hud_process_count() < 1:
        raise RuntimeError("HUD process missing after final STOP")

    print("PCE7.446_LIVE_ACCEPTANCE_GREEN")
    print("FINAL_STATE=STOPPED")
    print("HUD=RUNNING_WITH_NEW_CONTROLS")


def restore_old_hud():
    try:
        start_hud()
    except Exception as exc:
        print(f"RESTORED_HUD_RESTART_FAILED={exc}", file=sys.stderr)


def main():
    verify_source()

    # The pre-cutover contract is the intentional STOPPED state. Do not overwrite
    # a live relay that unexpectedly came back.
    if listener_pid() is not None:
        raise RuntimeError("ABORT: port 8766 is listening before live cutover")

    rollback = make_backup()

    try:
        rollback_root = LIVE / "rollback"
        rollback_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="PCE7.446-stage-",
            dir=str(rollback_root),
        ) as tmp:
            stage = Path(tmp)
            stage_runtime(stage)
            deploy_runtime(stage)
            acceptance()

        print(f"ROLLBACK={rollback}")
        return 0
    except Exception as exc:
        print(f"PCE7.446_FAILED={exc}", file=sys.stderr)
        try:
            if CONTROL.is_file():
                subprocess.run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(CONTROL),
                        "stop",
                    ],
                    text=True,
                    check=False,
                )
        except Exception:
            pass
        restore_backup(rollback)
        restore_old_hud()
        print("PCE7.446_ROLLBACK_COMPLETE", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
