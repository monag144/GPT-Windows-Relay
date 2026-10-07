#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
RELEASE_PATH = HERE / "release.json"
APPDATA = Path(os.environ.get("APPDATA", Path.home() / ".config"))
SETTINGS_PATH = APPDATA / "GPTWindowsRelayConsumer" / "consumer-settings.json"

CONSUMER_FILES = (
    "GO.bat",
    "bootstrap.ps1",
    "launch_chatgpt.ps1",
    "consumer_app.py",
    "mission_transport.py",
    "control_harness.py",
    "browser_manager.py",
    "recovery_supervisor.py",
    "updater.py",
    "requirements.txt",
    "README.txt",
    "release.json",
)

RUNTIME_FILES = (
    "windows_relay.py",
    "run.ps1",
    "content.js",
    "chromium_extension_setup.ps1",
    "firefox_adapter.py",
    "firefox_tab_adapter.ps1",
    "screenshot_capture.ps1",
    "uia_control_action.ps1",
    "uia_text_entry.ps1",
    "windows_tools.py",
    "windows_workflow.py",
    "relay-control.ps1",
    "hud.py",
)


class UpdateError(RuntimeError):
    pass


def load_release(path: Path = RELEASE_PATH) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError(f"Could not read release metadata: {exc}") from exc
    if not isinstance(data, dict):
        raise UpdateError("Invalid release metadata.")
    for key in ("version", "repository", "branch"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise UpdateError(f"Release metadata is missing {key}.")
    return data


def _load_settings() -> dict:
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_settings(data: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, SETTINGS_PATH)


def set_source_checkout(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve()
    if not (root / ".git").exists():
        raise UpdateError("Selected update source is not a Git checkout.")
    if not (root / "consumer" / "release.json").is_file():
        raise UpdateError("Selected Git checkout does not contain the One-Click consumer source.")
    settings = _load_settings()
    settings["update_source_checkout"] = str(root)
    _save_settings(settings)
    return root


def configured_source_checkout() -> Path | None:
    raw = _load_settings().get("update_source_checkout")
    if not isinstance(raw, str) or not raw:
        return None
    root = Path(raw).expanduser()
    if (root / ".git").exists() and (root / "consumer" / "release.json").is_file():
        return root.resolve()
    return None


def version_tuple(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.strip().split("."))
    except ValueError as exc:
        raise UpdateError(f"Invalid version: {value}") from exc


def release_key(data: dict) -> tuple[tuple[int, ...], int]:
    revision = data.get("revision", 0)
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise UpdateError("Invalid release revision.")
    return version_tuple(data["version"]), revision


def release_label(data: dict) -> str:
    revision = data.get("revision", 0)
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise UpdateError("Invalid release revision.")
    return f"{data['version']} r{revision}" if revision else str(data["version"])


def _git_root() -> Path | None:
    probe = HERE
    for candidate in (probe, *probe.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _git_exe() -> str | None:
    explicit = Path(r"C:\Program Files\Git\cmd\git.exe")
    if explicit.is_file():
        return str(explicit)
    return shutil.which("git.exe") or shutil.which("git")


def _run_git(root: Path, *args: str) -> str:
    git = _git_exe()
    if not git:
        raise UpdateError("This source checkout needs Git for in-place updates.")
    proc = subprocess.run(
        [git, "-C", str(root), *args],
        text=True,
        capture_output=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise UpdateError((proc.stderr or proc.stdout or "Git update failed.").strip())
    return proc.stdout.strip()


def update_source_checkout(root: Path) -> dict:
    dirty = _run_git(root, "status", "--porcelain")
    if dirty:
        raise UpdateError("Source checkout has local changes. Commit or stash them before using Update.")
    branch = _run_git(root, "branch", "--show-current")
    if not branch:
        raise UpdateError("Source checkout is in detached-HEAD state.")
    remote = _run_git(root, "remote", "get-url", "origin")
    release_before = load_release(root / "consumer" / "release.json")
    before_commit = _run_git(root, "rev-parse", "HEAD")

    # Poll the actual configured Git remote before pulling. This is deliberately
    # separate from the pull so update results can prove both actions happened.
    remote_line = _run_git(root, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    if not remote_line:
        raise UpdateError(f"Git remote did not return branch {branch}.")
    remote_head_before = remote_line.split()[0]

    pull = _run_git(root, "pull", "--ff-only", "origin", branch)
    after_commit = _run_git(root, "rev-parse", "HEAD")
    release_after = load_release(root / "consumer" / "release.json")
    return {
        "mode": "git",
        "repository": remote,
        "branch": branch,
        "before": release_label(release_before),
        "after": release_label(release_after),
        "before_version": release_before["version"],
        "after_version": release_after["version"],
        "before_revision": release_before.get("revision", 0),
        "after_revision": release_after.get("revision", 0),
        "before_commit": before_commit,
        "after_commit": after_commit,
        "remote_head_before": remote_head_before,
        "changed": before_commit != after_commit,
        "detail": pull,
        "version": release_after["version"],
        "revision": release_after.get("revision", 0),
        "display_version": release_label(release_after),
        "remote_polled": True,
        "pull_attempted": True,
    }


def _clone_private_update_source(local: dict, destination: Path) -> Path:
    git = _git_exe()
    if not git:
        raise UpdateError(
            "This update source is private and requires Git with existing GitHub credentials."
        )
    repo = local["repository"].strip("/")
    branch = local["branch"]
    url = f"https://github.com/{repo}.git"
    proc = subprocess.run(
        [git, "clone", "--depth", "1", "--single-branch", "--branch", branch, url, str(destination)],
        text=True, capture_output=True, timeout=120,
    )
    if proc.returncode != 0:
        raise UpdateError(
            "Private GitHub update source could not be accessed with this machine's Git credentials: "
            + (proc.stderr or proc.stdout or "Git clone failed.").strip()
        )
    return destination


def _private_git_release_metadata(local: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="gpt-oneclick-private-check-") as tmp_raw:
        root = _clone_private_update_source(local, Path(tmp_raw) / "source")
        return load_release(root / "consumer" / "release.json")


def remote_release_metadata(local: dict) -> dict:
    repo = local["repository"].strip("/")
    branch = local["branch"]
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/consumer/release.json"
    req = urllib.request.Request(url, headers={"User-Agent": "GPT-OneClick-Go-Updater"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8-sig"))
    except urllib.error.HTTPError as exc:
        if exc.code not in (401, 403, 404):
            raise UpdateError(f"Could not check for updates: {exc}") from exc
        data = _private_git_release_metadata(local)
    except Exception as exc:
        raise UpdateError(f"Could not check for updates: {exc}") from exc
    if not isinstance(data, dict):
        raise UpdateError("Remote release metadata is invalid.")
    return data


def check_for_update() -> dict:
    root = _git_root()
    if root is not None:
        current = load_release(root / "consumer" / "release.json")
        branch = _run_git(root, "branch", "--show-current")
        remote = _run_git(root, "remote", "get-url", "origin")
        remote_line = _run_git(root, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
        remote_head = remote_line.split()[0] if remote_line else None
        return {
            "mode": "git",
            "current": current,
            "current_display": release_label(current),
            "source": {"branch": branch, "repository": remote},
            "available": None,
            "remote_head": remote_head,
            "remote_polled": True,
        }

    current = load_release()
    remote = remote_release_metadata(current)
    return {
        "mode": "package",
        "current": current,
        "current_display": release_label(current),
        "available": remote,
        "available_display": release_label(remote),
        "update_available": release_key(remote) > release_key(current),
        "remote_polled": True,
    }


def _safe_extract(zf: zipfile.ZipFile, destination: Path) -> None:
    destination = destination.resolve()
    for member in zf.infolist():
        target = (destination / member.filename).resolve()
        if target != destination and destination not in target.parents:
            raise UpdateError("Update archive contains an unsafe path.")
    zf.extractall(destination)


def _copy_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise UpdateError(f"Update archive is missing {source.name}.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = destination.with_name(destination.name + ".oneclick-update")
    try:
        shutil.copy2(source, staged)
        os.replace(staged, destination)
    finally:
        try:
            staged.unlink()
        except FileNotFoundError:
            pass


def _install_from_source_tree(source_root: Path) -> dict:
    source_consumer = source_root / "consumer"
    source_runtime = source_root / "windows-relay"
    target_runtime = HERE / "runtime"
    new_release = load_release(source_consumer / "release.json")

    for name in CONSUMER_FILES:
        _copy_file(source_consumer / name, HERE / name)

    for name in RUNTIME_FILES:
        # content.js remains in RUNTIME_FILES for the package/runtime contract,
        # but its bytes come only from the canonical consumer extension below.
        if name == "content.js":
            continue
        _copy_file(source_runtime / name, target_runtime / name)

    source_ext = source_runtime / "extension"
    target_ext = target_runtime / "extension"
    canonical_content = source_ext / "content.js"
    if not (source_ext / "manifest.json").is_file() or not canonical_content.is_file():
        raise UpdateError("Update source is missing the browser extension.")
    target_ext.mkdir(parents=True, exist_ok=True)
    for src in source_ext.rglob("*"):
        if not src.is_file() or src.name == "config.js":
            continue
        rel = src.relative_to(source_ext)
        _copy_file(src, target_ext / rel)

    # GPT_UPDATER_CANONICAL_CONTENT_SOURCE_V1
    # Keep runtime/content.js only as a compatibility copy derived from the
    # canonical consumer extension. Never overwrite extension/content.js with
    # the stale relay-root compatibility file.
    _copy_file(canonical_content, target_runtime / "content.js")
    try:
        (target_ext / "config.js").unlink()
    except FileNotFoundError:
        pass
    return new_release


def _updater_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        return b""


def _second_phase_source_sync(source_root: Path, updater_changed: bool) -> dict | None:
    """Let a newly installed updater sync files unknown to the previous updater."""
    if not updater_changed:
        return None

    installed_updater = HERE / "updater.py"
    proc = subprocess.run(
        [sys.executable, str(installed_updater), "sync-source", str(source_root)],
        text=True,
        capture_output=True,
        timeout=120,
        cwd=str(HERE),
    )
    if proc.returncode != 0:
        raise UpdateError(
            "The new updater could not finish its second-phase file sync: "
            + (proc.stderr or proc.stdout or "unknown error").strip()
        )
    for line in reversed(proc.stdout.splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("ok"):
            return payload
    raise UpdateError("The new updater returned no second-phase sync confirmation.")


def update_linked_package(root: Path) -> dict:
    local = load_release()
    git_result = update_source_checkout(root)
    new_release = load_release(root / "consumer" / "release.json")
    if release_key(new_release) < release_key(local):
        raise UpdateError("Refusing to install an older linked source release.")

    source_updater = root / "consumer" / "updater.py"
    updater_changed = _updater_bytes(source_updater) != _updater_bytes(HERE / "updater.py")
    installed = _install_from_source_tree(root)
    second_phase = _second_phase_source_sync(root, updater_changed)

    return {
        "mode": "linked_git_package",
        "before": release_label(local),
        "after": release_label(installed),
        "before_version": local["version"],
        "after_version": installed["version"],
        "before_revision": local.get("revision", 0),
        "after_revision": installed.get("revision", 0),
        "display_version": release_label(installed),
        "changed": release_key(installed) != release_key(local),
        "source_checkout": str(root),
        "git_changed": bool(git_result.get("changed")),
        "remote_polled": bool(git_result.get("remote_polled")),
        "pull_attempted": bool(git_result.get("pull_attempted")),
        "remote_head_before": git_result.get("remote_head_before"),
        "after_commit": git_result.get("after_commit"),
        "second_phase_sync": bool(second_phase),
    }


def _install_private_git_package(local: dict, remote: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="gpt-oneclick-private-update-") as tmp_raw:
        source_root = _clone_private_update_source(local, Path(tmp_raw) / "source")
        new_release = load_release(source_root / "consumer" / "release.json")
        if (
            new_release.get("repository") != remote.get("repository")
            or new_release.get("branch") != remote.get("branch")
            or release_key(new_release) != release_key(remote)
        ):
            raise UpdateError("Private Git update release metadata does not match the update check.")
        if release_key(new_release) < release_key(local):
            raise UpdateError("Refusing to install an older consumer release.")
        source_updater = source_root / "consumer" / "updater.py"
        updater_changed = _updater_bytes(source_updater) != _updater_bytes(HERE / "updater.py")
        _install_from_source_tree(source_root)
        second_phase = _second_phase_source_sync(source_root, updater_changed)
    return {
        "mode": "private_git_package",
        "before": release_label(local),
        "after": release_label(new_release),
        "before_version": local["version"],
        "after_version": new_release["version"],
        "before_revision": local.get("revision", 0),
        "after_revision": new_release.get("revision", 0),
        "display_version": release_label(new_release),
        "changed": release_key(new_release) != release_key(local),
        "repository": local["repository"],
        "branch": local["branch"],
        "remote_polled": True,
        "git_authenticated_fallback": True,
        "second_phase_sync": bool(second_phase),
    }


def update_package() -> dict:
    local = load_release()
    remote = remote_release_metadata(local)
    repo = local["repository"].strip("/")
    branch = local["branch"]
    archive_url = f"https://codeload.github.com/{repo}/zip/refs/heads/{branch}"

    with tempfile.TemporaryDirectory(prefix="gpt-oneclick-update-") as tmp_raw:
        tmp = Path(tmp_raw)
        archive = tmp / "update.zip"
        req = urllib.request.Request(archive_url, headers={"User-Agent": "GPT-OneClick-Go-Updater"})
        try:
            with urllib.request.urlopen(req, timeout=60) as response, archive.open("wb") as out:
                shutil.copyfileobj(response, out)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403, 404):
                return _install_private_git_package(local, remote)
            raise UpdateError(f"Could not download update: {exc}") from exc
        except Exception as exc:
            raise UpdateError(f"Could not download update: {exc}") from exc

        extract = tmp / "extract"
        extract.mkdir()
        try:
            with zipfile.ZipFile(archive) as zf:
                _safe_extract(zf, extract)
        except (OSError, zipfile.BadZipFile) as exc:
            raise UpdateError(f"Downloaded update archive is invalid: {exc}") from exc

        roots = [p for p in extract.iterdir() if p.is_dir()]
        if len(roots) != 1:
            raise UpdateError("Could not identify update archive root.")
        source_root = roots[0]
        new_release = load_release(source_root / "consumer" / "release.json")
        if (
            new_release.get("repository") != remote.get("repository")
            or new_release.get("branch") != remote.get("branch")
            or release_key(new_release) != release_key(remote)
        ):
            raise UpdateError("Downloaded archive release metadata does not match the update check.")
        if release_key(new_release) < release_key(local):
            raise UpdateError("Refusing to install an older consumer release.")

        source_updater = source_root / "consumer" / "updater.py"
        updater_changed = _updater_bytes(source_updater) != _updater_bytes(HERE / "updater.py")
        _install_from_source_tree(source_root)
        second_phase = _second_phase_source_sync(source_root, updater_changed)

    return {
        "mode": "package",
        "before": release_label(local),
        "after": release_label(new_release),
        "before_version": local["version"],
        "after_version": new_release["version"],
        "before_revision": local.get("revision", 0),
        "after_revision": new_release.get("revision", 0),
        "display_version": release_label(new_release),
        "changed": release_key(new_release) != release_key(local),
        "repository": repo,
        "branch": branch,
        "remote_polled": True,
        "download_attempted": True,
        "second_phase_sync": bool(second_phase),
    }


def perform_update() -> dict:
    root = _git_root()
    if root is not None:
        return update_source_checkout(root)
    linked = configured_source_checkout()
    if linked is not None:
        return update_linked_package(linked)
    return update_package()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check", "update", "link-source", "sync-source"))
    parser.add_argument("path", nargs="?")
    args = parser.parse_args()
    try:
        if args.command == "check":
            result = check_for_update()
        elif args.command == "link-source":
            if not args.path:
                raise UpdateError("link-source requires a checkout path.")
            result = {"linked": str(set_source_checkout(args.path))}
        elif args.command == "sync-source":
            if not args.path:
                raise UpdateError("sync-source requires a source tree path.")
            source_root = Path(args.path).expanduser().resolve()
            installed = _install_from_source_tree(source_root)
            result = {
                "ok": True,
                "mode": "second_phase_source_sync",
                "version": installed["version"],
                "revision": installed.get("revision", 0),
                "display_version": release_label(installed),
            }
        else:
            result = perform_update()
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except UpdateError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
