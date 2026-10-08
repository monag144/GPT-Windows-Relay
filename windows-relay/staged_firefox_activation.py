#!/usr/bin/env python3
"""Activate already-staged Firefox content scripts after the relay result is delivered.

This helper MUST run detached and delayed. It never executes a relay packet,
changes operator STOP state, or sends a ChatGPT message.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

FILES = ("content.js", "extension/content.js", "extension-persistent/content.js")
ADDON = "GPT One-Click Go Relay"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def canonical_url(value: str) -> str:
    parsed = urlsplit(value)
    pieces = parsed.path.strip("/").split("/")
    if parsed.scheme != "https" or parsed.netloc != "chatgpt.com" or len(pieces) != 2 or pieces[0] != "c" or not pieces[1]:
        raise ValueError("INVALID_CONVERSATION_URL")
    return "https://chatgpt.com/c/" + pieces[1]


def preflight(manifest_path: Path, live: Path) -> dict:
    manifest_path = manifest_path.resolve(strict=True)
    live = live.resolve(strict=True)
    record = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if record.get("operation") != "PCE10.020" or record.get("status") != "STAGED_AWAITING_EXTENSION_RELOAD":
        raise RuntimeError("STAGE_MANIFEST_NOT_READY")
    rows = record.get("files")
    if not isinstance(rows, list) or sorted(r.get("relative_path") for r in rows) != sorted(FILES):
        raise RuntimeError("STAGE_MANIFEST_FILE_SET_INVALID")
    if len(set(r["relative_path"] for r in rows)) != len(FILES):
        raise RuntimeError("STAGE_MANIFEST_DUPLICATES")
    for row in rows:
        rel = row["relative_path"]
        dest = live / rel
        backup = (manifest_path.parent / rel)
        if not dest.is_file() or not backup.is_file() or dest.is_symlink() or backup.is_symlink():
            raise RuntimeError("STAGE_FILE_MISSING_OR_SYMLINK " + rel)
        if sha(dest) != row["source_sha256"]:
            raise RuntimeError("STAGED_CONTENT_DRIFT " + rel)
        if sha(backup) != row["previous_sha256"]:
            raise RuntimeError("BACKUP_CONTENT_DRIFT " + rel)
    adapter = live / "firefox_adapter.py"
    if not adapter.is_file():
        raise RuntimeError("FIREFOX_ADAPTER_MISSING")
    addon_manifest = json.loads((live / "extension" / "manifest.json").read_text(encoding="utf-8-sig"))
    if addon_manifest.get("name") != ADDON:
        raise RuntimeError("ADDON_IDENTITY_MISMATCH")
    return record


def log(path: Path, label: str, **details):
    row = {"at": utc_now(), "label": label, **details}
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def call_adapter(py: str, live: Path, action: str, log_path: Path, *args: str) -> dict:
    argv = [py, str(live / "firefox_adapter.py"), action, *args]
    p = subprocess.run(
        argv, cwd=str(live), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=90
    )
    log(log_path, "ADAPTER", action=action, rc=p.returncode,
        stdout=p.stdout[-2500:], stderr=p.stderr[-2500:])
    if p.returncode != 0:
        raise RuntimeError("ADAPTER_FAILED " + action + " rc=" + str(p.returncode))
    payload = None
    for line in reversed(p.stdout.splitlines()):
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue
    if not isinstance(payload, dict) or payload.get("ok") is not True or payload.get("action") != action:
        raise RuntimeError("ADAPTER_UNVERIFIED " + action)
    return payload


def fresh_event(events_path: Path, since: datetime, expected_url: str) -> dict | None:
    if not events_path.is_file():
        return None
    for raw in reversed(events_path.read_text(encoding="utf-8", errors="replace").splitlines()[-600:]):
        try:
            row = json.loads(raw)
            if row.get("event") != "content_script_started":
                continue
            event_time = datetime.fromisoformat(str(row.get("time") or "").replace("Z", "+00:00"))
            if event_time.tzinfo is None or event_time < since:
                continue
            detail = row.get("detail") or {}
            if canonical_url(detail.get("href") or "") == expected_url:
                return {"time": row.get("time"), "href": detail["href"], "runtime": detail.get("runtime")}
        except (ValueError, TypeError, KeyError, AttributeError):
            continue
    return None


def restore(record: dict, manifest_path: Path, live: Path):
    for row in record["files"]:
        rel = row["relative_path"]
        dest = live / rel
        temporary = dest.with_name(dest.name + ".pce10-021-rollback")
        if temporary.exists():
            raise RuntimeError("ROLLBACK_TEMP_COLLISION " + str(temporary))
        shutil.copy2(manifest_path.parent / rel, temporary)
        if sha(temporary) != row["previous_sha256"]:
            raise RuntimeError("ROLLBACK_PRECOPY_HASH_DRIFT " + rel)
        os.replace(temporary, dest)
    for row in record["files"]:
        if sha(live / row["relative_path"]) != row["previous_sha256"]:
            raise RuntimeError("ROLLBACK_NOT_EXACT " + row["relative_path"])


def operator_allows_activation(live: Path) -> bool:
    # STOP has priority over even a recovery/rollback attempt.
    if (live / ".relay-paused").exists():
        return False
    state_path = Path(os.environ["LOCALAPPDATA"]) / "GPTWindowsRelay" / "state.json"
    if not state_path.is_file():
        return False
    try:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        return state.get("armed") is True
    except (OSError, ValueError, TypeError):
        return False


def activate(manifest_path: Path, live: Path, py: str, url: str, tab: str, delay: float, wait: float):
    log_path = manifest_path.parent / "activation-events.jsonl"
    verdict_path = manifest_path.parent / "activation-verdict.json"
    record = preflight(manifest_path, live)
    url = canonical_url(url)
    if not tab or tab.strip() != tab:
        raise RuntimeError("INVALID_EXACT_TAB_NAME")
    if not Path(py).is_file():
        raise RuntimeError("PYTHON_INTERPRETER_MISSING")
    log(log_path, "SCHEDULED", delay_seconds=delay, tab=tab, url=url)
    time.sleep(delay)
    # A newer local operation may have changed the files while we waited.
    preflight(manifest_path, live)
    if not operator_allows_activation(live):
        final = {"status": "OPERATOR_STOPPED_NO_ACTION", "at": utc_now(),
                 "runtime_mutation": False, "files_left_staged": True}
        temporary = verdict_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(final, indent=2), encoding="utf-8")
        os.replace(temporary, verdict_path)
        log(log_path, "OPERATOR_STOPPED_NO_ACTION")
        return final
    reload_invoked = False
    managed_pid = None
    try:
        reload_invoked = True
        addon = call_adapter(py, live, "reload-addon", log_path, "--addon-name", ADDON)
        if addon.get("invoked") is not True:
            raise RuntimeError("ADDON_RELOAD_NOT_INVOKED")
        managed_pid = int(addon.get("firefox_pid") or 0)
        if managed_pid <= 0:
            raise RuntimeError("ADDON_RELOAD_MANAGED_PID_MISSING")
        if not operator_allows_activation(live):
            raise RuntimeError("OPERATOR_STOPPED_DURING_ACTIVATION")
        refreshed_after = datetime.now(timezone.utc)
        tab_result = call_adapter(py, live, "refresh-tab", log_path,
                                  "--tab-name", tab, "--firefox-pid", str(managed_pid))
        if (tab_result.get("invoked") is not True or tab_result.get("selected_name") != tab or
                int(tab_result.get("firefox_pid") or 0) != managed_pid):
            raise RuntimeError("CHATGPT_TAB_REFRESH_NOT_VERIFIED")
        events = Path(os.environ["LOCALAPPDATA"]) / "GPTWindowsRelay" / "browser-events.jsonl"
        observed = None
        end = time.monotonic() + wait
        while time.monotonic() < end:
            observed = fresh_event(events, refreshed_after, url)
            if observed:
                break
            time.sleep(1)
        if not observed:
            raise RuntimeError("POST_REFRESH_CONTENT_SCRIPT_EVENT_MISSING")
        for row in record["files"]:
            if sha(live / row["relative_path"]) != row["source_sha256"]:
                raise RuntimeError("POST_ACTIVATION_CONTENT_DRIFT")
        final = {"status": "ACTIVATED_EVENT_CONFIRMED_CANARY_PENDING", "at": utc_now(),
                 "observed": observed, "manifest": str(manifest_path)}
        log(log_path, "ACTIVATION_EVENT_CONFIRMED", observed=observed)
    except BaseException as error:
        log(log_path, "ACTIVATION_FAILED", error=repr(error))
        try:
            restore(record, manifest_path, live)
            log(log_path, "ROLLBACK_FILES_EXACT")
            final = {"status": "ROLLBACK_FILES_EXACT", "error": repr(error),
                     "at": utc_now(), "runtime_rollback_confirmed": False}
            if reload_invoked:
                try:
                    if operator_allows_activation(live):
                        call_adapter(py, live, "reload-addon", log_path, "--addon-name", ADDON)
                        if managed_pid:
                            call_adapter(py, live, "refresh-tab", log_path,
                                         "--tab-name", tab, "--firefox-pid", str(managed_pid))
                        else:
                            raise RuntimeError("ROLLBACK_MANAGED_PID_UNKNOWN")
                    else:
                        raise RuntimeError("OPERATOR_STOPPED_BEFORE_RUNTIME_ROLLBACK")
                    final["runtime_rollback_confirmed"] = True
                    log(log_path, "ROLLBACK_ADDON_AND_TAB_REFRESHED")
                except BaseException as rollback_error:
                    final["rollback_reload_error"] = repr(rollback_error)
                    log(log_path, "ROLLBACK_RUNTIME_UNVERIFIED", error=repr(rollback_error))
        except BaseException as rollback_error:
            final = {"status": "ROLLBACK_FAILED", "error": repr(error),
                     "rollback_error": repr(rollback_error), "at": utc_now()}
            log(log_path, "ROLLBACK_FAILED", error=repr(rollback_error))
    temporary = verdict_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(final, indent=2), encoding="utf-8")
    os.replace(temporary, verdict_path)
    log(log_path, "FINAL", status=final["status"])
    return final


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--live", type=Path, required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--tab-name", required=True)
    ap.add_argument("--delay", type=float, default=25)
    ap.add_argument("--wait", type=float, default=20)
    ap.add_argument("--preflight-only", action="store_true")
    args = ap.parse_args(argv)
    rec = preflight(args.manifest, args.live)
    print(json.dumps({"preflight": "GREEN", "operation": rec["operation"], "files": len(rec["files"])}, sort_keys=True), flush=True)
    if args.preflight_only:
        return 0
    result = activate(args.manifest, args.live, args.python, args.url, args.tab_name, args.delay, args.wait)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result["status"] == "ACTIVATED_EVENT_CONFIRMED_CANARY_PENDING" else 1


if __name__ == "__main__":
    sys.exit(main())
