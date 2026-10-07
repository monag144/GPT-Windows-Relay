#!/usr/bin/env python3
"""Independent consumer recovery supervisor.

This process deliberately lives outside the browser extension and relay request
transport.  It observes both, records evidence, and performs only a small
whitelist of deterministic repairs.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any
import urllib.error
import urllib.request

import browser_manager

APPDATA = Path(os.environ.get("APPDATA", Path.home() / ".config"))
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local"))
CONFIG_DIR = APPDATA / "GPTWindowsRelayConsumer"
STATE_DIR = LOCALAPPDATA / "GPTWindowsRelayConsumer"
BRIDGE_PATH = CONFIG_DIR / "bridge.json"
RELAY_STATE_PATH = STATE_DIR / "state.json"
EVENT_PATH = STATE_DIR / "browser-events.jsonl"
SUPERVISOR_STATE_PATH = STATE_DIR / "recovery-supervisor.json"
EVIDENCE_PATH = STATE_DIR / "recovery-evidence.jsonl"
SCREENSHOT_DIR = STATE_DIR / "recovery-evidence"
SINGLETON_NAME = r"Local\GPTOneClickRecoverySupervisor"

POLL_SECONDS = 2.0
DISCOVERY_STALL_SECONDS = 20.0
MAX_REPAIR_ATTEMPTS = 3
REPAIR_COOLDOWN_SECONDS = 15.0
GPT_RECOVERY_TIMEOUT_SECONDS = 120.0
GPT_RECOVERY_ALLOWED_ACTIONS = {"rebuild_browser_integration", "audited_update", "restart_relay"}
APPROVAL_EVENTS = {"chatgpt_tool_approval_prompt_detected"}
CHATGPT_UI_ERROR_EVENT = "chatgpt_ui_error_detected"
CHATGPT_UI_ERROR_CLEAR_EVENT = "chatgpt_ui_error_cleared"
PROGRESS_EVENTS = {
    "relay_action_execution_requested",
    "relay_result_send_attempt",
    "relay_result_send_clicked",
    "relay_result_send_confirmed",
    "relay_result_delivery_complete",
}
# GPT_CONSUMER_INDEPENDENT_RECOVERY_SUPERVISOR_V1
# GPT_CONSUMER_RECOVERY_WHITELIST_V1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent), text=True)
    tmp = Path(raw)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


# GPT_CONSUMER_DURABLE_RECOVERY_OBLIGATION_V1
def _set_recovery_state(
    incident_id: str,
    phase: str,
    *,
    snapshot: Snapshot | None = None,
    classification: str | None = None,
    deadline_epoch: float | None = None,
    action: str | None = None,
    detail: str | None = None,
) -> None:
    state = _read_json(SUPERVISOR_STATE_PATH)
    recovery: dict[str, Any] = {
        "incident_id": incident_id,
        "phase": phase,
        "updated_at": utc_now(),
    }
    if classification:
        recovery["classification"] = classification
    if deadline_epoch is not None:
        recovery["deadline_epoch"] = deadline_epoch
    if action:
        recovery["action"] = action
    if detail:
        recovery["detail"] = detail[:500]
    if snapshot is not None:
        recovery["browser_id"] = snapshot.browser_id
        recovery["operation_id"] = snapshot.active_operation or snapshot.discovered_packet or snapshot.last_operation
    state["version"] = 1
    state["updated_at"] = utc_now()
    state["recovery"] = recovery
    _atomic_json(SUPERVISOR_STATE_PATH, state)


def _relay_get(path: str, timeout: float = 1.0) -> dict[str, Any]:
    cfg = _read_json(BRIDGE_PATH)
    port = cfg.get("port")
    token = cfg.get("token")
    if not isinstance(port, int) or not isinstance(token, str) or not token:
        raise RuntimeError("consumer relay configuration unavailable")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        headers={"X-GPT-Windows-Relay-Token": token},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode("utf-8"))
    return value if isinstance(value, dict) else {}


def _recent_events(limit: int = 96) -> list[dict[str, Any]]:
    try:
        lines = EVENT_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    except OSError:
        return []
    result: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def _event_packet(event: dict[str, Any]) -> str | None:
    detail = event.get("detail")
    if not isinstance(detail, dict):
        return None
    value = detail.get("packet_id") or detail.get("id")
    return value if isinstance(value, str) and value else None


def _parse_event_time(event: dict[str, Any]) -> float | None:
    value = event.get("time")
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _last_relevant_event(events: list[dict[str, Any]], browser_id: str | None) -> dict[str, Any] | None:
    for event in reversed(events):
        detail = event.get("detail")
        if browser_id and isinstance(detail, dict):
            tagged = detail.get("browser_id")
            if isinstance(tagged, str) and tagged != browser_id:
                continue
        return event
    return None


def _discovery_stuck(events: list[dict[str, Any]], now_epoch: float, browser_id: str | None) -> tuple[bool, str | None, float | None]:
    discovery_index = -1
    packet_id: str | None = None
    discovered_at: float | None = None
    for index in range(len(events) - 1, -1, -1):
        event = events[index]
        detail = event.get("detail")
        if browser_id and isinstance(detail, dict):
            tagged = detail.get("browser_id")
            if isinstance(tagged, str) and tagged != browser_id:
                continue
        if event.get("event") == "relay_packet_discovered":
            discovery_index = index
            packet_id = _event_packet(event)
            discovered_at = _parse_event_time(event)
            break
    if discovery_index < 0 or discovered_at is None:
        return False, packet_id, None
    for later in events[discovery_index + 1 :]:
        if later.get("event") in PROGRESS_EVENTS and (packet_id is None or _event_packet(later) in (None, packet_id)):
            return False, packet_id, max(0.0, now_epoch - discovered_at)
    age = max(0.0, now_epoch - discovered_at)
    return age >= DISCOVERY_STALL_SECONDS, packet_id, age


@dataclass
class Snapshot:
    sampled_at: str
    relay_online: bool
    armed: bool | None
    pending_missions: int | None
    browser_id: str | None
    browser_expected: bool
    browser_connected: bool | None
    active_operation: str | None
    last_operation: str | None
    last_event: str | None
    discovered_packet: str | None
    discovered_age_seconds: float | None
    discovery_stuck: bool
    approval_required: bool
    chatgpt_ui_error: bool = False
    chatgpt_ui_error_detail: str | None = None


@dataclass
class Decision:
    phase: str
    reason: str
    repair: str | None = None


def sample(now_epoch: float | None = None) -> Snapshot:
    now_epoch = time.time() if now_epoch is None else now_epoch
    settings = browser_manager.load_settings()
    browser_id = settings.get("browser_id") if isinstance(settings.get("browser_id"), str) else None
    pids = settings.get("browser_pids")
    browser_expected = bool(browser_id and isinstance(pids, dict) and isinstance(pids.get(browser_id), int))

    relay_online = False
    armed: bool | None = None
    pending: int | None = None
    browser_connected: bool | None = None
    try:
        status = _relay_get("/status")
        relay_online = bool(status.get("ok"))
        armed = bool(status.get("armed")) if relay_online else None
        value = status.get("pending_missions")
        pending = value if isinstance(value, int) else None
        if browser_id:
            bstatus = _relay_get(f"/browser-status?browser_id={browser_id}")
            browser_connected = bool(bstatus.get("connected"))
    except (OSError, ValueError, RuntimeError, urllib.error.URLError):
        relay_online = False

    relay_state = _read_json(RELAY_STATE_PATH)
    active = relay_state.get("active_action")
    last = relay_state.get("last_action")
    active_id = active.get("id") if isinstance(active, dict) and isinstance(active.get("id"), str) else None
    last_id = last.get("id") if isinstance(last, dict) and isinstance(last.get("id"), str) else None

    events = _recent_events()
    latest = _last_relevant_event(events, browser_id)
    last_event = latest.get("event") if isinstance(latest, dict) and isinstance(latest.get("event"), str) else None
    approval = last_event in APPROVAL_EVENTS
    ui_error = False
    ui_error_detail: str | None = None
    for event in reversed(events):
        detail = event.get("detail") if isinstance(event.get("detail"), dict) else {}
        if browser_id and detail.get("browser_id") not in (None, browser_id):
            continue
        name = event.get("event")
        if name == CHATGPT_UI_ERROR_CLEAR_EVENT:
            break
        if name == CHATGPT_UI_ERROR_EVENT:
            ui_error = True
            ui_error_detail = str(detail.get("text") or detail.get("kind") or "visible ChatGPT error")[:300]
            break
    stuck, packet, age = _discovery_stuck(events, now_epoch, browser_id)
    return Snapshot(
        sampled_at=utc_now(),
        relay_online=relay_online,
        armed=armed,
        pending_missions=pending,
        browser_id=browser_id,
        browser_expected=browser_expected,
        browser_connected=browser_connected,
        active_operation=active_id,
        last_operation=last_id,
        last_event=last_event,
        discovered_packet=packet,
        discovered_age_seconds=round(age, 3) if age is not None else None,
        discovery_stuck=stuck,
        approval_required=approval,
        chatgpt_ui_error=ui_error,
        chatgpt_ui_error_detail=ui_error_detail,
    )


def decide(s: Snapshot) -> Decision:
    if s.approval_required:
        return Decision("APPROVAL REQUIRED", "ChatGPT is waiting for a platform tool approval")
    if s.chatgpt_ui_error:
        detail = s.chatgpt_ui_error_detail or "visible ChatGPT failure surface"
        return Decision("RECOVERING", f"ChatGPT visible error: {detail}", "capture_diagnostic")
    if not s.relay_online:
        return Decision("RECOVERING", "local relay is offline", "restart_relay")
    if s.browser_expected and s.browser_connected is False:
        return Decision("RECOVERING", f"{s.browser_id} mission-capable integration is disconnected", "repair_browser")
    if s.discovery_stuck:
        label = s.discovered_packet or "unknown packet"
        return Decision("RECOVERING", f"{label} remained discovered without execution progress", "repair_browser")
    if s.active_operation:
        return Decision("RUNNING", f"{s.active_operation} is executing")
    if s.discovered_packet and s.discovered_age_seconds is not None and s.discovered_age_seconds < DISCOVERY_STALL_SECONDS:
        return Decision("DISCOVERED", f"{s.discovered_packet} is inside the bounded settlement window")
    return Decision("IDLE", "no expected work is stalled")


def _capture_screenshot(tag: str) -> str | None:
    helper = Path(__file__).resolve().parent / "runtime" / "screenshot_capture.ps1"
    if os.name != "nt" or not helper.is_file():
        return None
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe = "".join(ch for ch in tag if ch.isalnum() or ch in "-_.")[:80] or "recovery"
    target = SCREENSHOT_DIR / f"{stamp}-{safe}.png"
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(helper), "-Target", "screen", "-Output", str(target)],
            capture_output=True, text=True, timeout=20,
        )
        return str(target) if proc.returncode == 0 and target.is_file() else None
    except (OSError, subprocess.SubprocessError):
        return None


def _evidence(kind: str, snapshot: Snapshot, decision: Decision, **detail: Any) -> None:
    record = {
        "time": utc_now(),
        "kind": kind,
        "snapshot": asdict(snapshot),
        "decision": asdict(decision),
        **detail,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()


def _restart_relay() -> tuple[bool, str]:
    run = Path(__file__).resolve().parent / "runtime" / "run.ps1"
    if os.name != "nt" or not run.is_file():
        return False, "relay supervisor launcher unavailable"
    try:
        subprocess.Popen(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(run)],
            cwd=str(run.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        return False, f"relay restart launch failed: {exc}"
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        time.sleep(0.4)
        try:
            if _relay_get("/status").get("ok"):
                return True, "relay restarted"
        except Exception:
            pass
    return False, "relay did not return healthy after restart"


def _repair_browser(browser_id: str | None) -> tuple[bool, str]:
    if not browser_id:
        return False, "no selected browser"
    browser = next((item for item in browser_manager.detect_browsers() if item.get("id") == browser_id), None)
    if not browser:
        return False, f"{browser_id} is not installed"
    if not browser.get("supported"):
        return False, f"{browser_id} is not supported by this consumer build"
    try:
        result = browser_manager.open_extension_setup(browser_id)
    except Exception as exc:
        return False, f"browser repair failed: {type(exc).__name__}: {str(exc)[:300]}"
    return bool(result.get("connected")), f"{browser_id} browser integration rebuilt"


# GPT_CONSUMER_OUT_OF_BAND_GPT_RECOVERY_V1
def _recovery_classification(s: Snapshot, d: Decision) -> str:
    if s.chatgpt_ui_error:
        return "CHATGPT_UI_ERROR"
    if s.browser_expected and s.browser_connected is False:
        return "BROWSER_INTEGRATION_DISCONNECTED"
    if s.discovery_stuck:
        return "DISCOVERED_NOT_EXECUTED"
    if d.repair == "restart_relay":
        return "RELAY_OFFLINE"
    return "RECOVERY_UNCLASSIFIED"


# GPT_CONSUMER_RECOVERY_PROMPT_NON_SELF_PARSING_V1
def _build_gpt_recovery_prompt(s: Snapshot, d: Decision, incident_id: str) -> str:
    classification = _recovery_classification(s, d)
    packet_id = s.active_operation or s.discovered_packet or s.last_operation or "unknown"
    return (
        "GPT Windows Relay independent recovery request.\n"
        f"incident_id={incident_id}\n"
        f"classification={classification}\n"
        f"packet_id={packet_id}\n"
        f"browser={s.browser_id or 'unknown'}\n"
        f"relay_online={s.relay_online}; armed={s.armed}; browser_connected={s.browser_connected}\n"
        f"last_event={s.last_event or 'none'}; reason={d.reason}\n\n"
        "The ordinary browser-extension relay transport is unhealthy. Do NOT send a GPT_WINDOWS_ACTION "
        "through that broken transport. Read the consumer instructions and newest compatible timestamped "
        "audit/incident/recovery documents in GitHub for monag144/GPT-Windows-Relay, branch "
        "main. Diagnose the evidence. Do not generate shell commands. "
        "Return exactly one bounded recovery-advice envelope. The opening marker is the token "
        "GPT_RELAY_RECOVERY_ADVICE inside square brackets; the closing marker is the same token preceded "
        "by a slash inside square brackets. Between those markers return one JSON object with integer "
        "version 1, the exact incident_id and classification stated above, a non-empty recommended_repairs "
        "array containing only rebuild_browser_integration, audited_update, or restart_relay, and a brief "
        "evidence-based reason. Do not echo this request."
    )


def _extract_gpt_recovery_advice(text: str, incident_id: str) -> dict[str, Any] | None:
    matches = re.findall(
        r"\[GPT_RELAY_RECOVERY_ADVICE\]\s*(\{.*?\})\s*\[/GPT_RELAY_RECOVERY_ADVICE\]",
        text,
        flags=re.DOTALL,
    )
    for raw in reversed(matches):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(value, dict) or value.get("version") != 1 or value.get("incident_id") != incident_id:
            continue
        repairs = value.get("recommended_repairs")
        if not isinstance(repairs, list) or not repairs or not all(isinstance(item, str) for item in repairs):
            continue
        if any(item not in GPT_RECOVERY_ALLOWED_ACTIONS for item in repairs):
            continue
        return value
    return None


# GPT_CONSUMER_RECOVERY_ADVICE_COACHING_V1
# GPT_CONSUMER_RECOVERY_ADVICE_COMPLETE_BOUNDARY_V1
def _recovery_advice_mentions_incident(text: str, incident_id: str) -> bool:
    return (
        incident_id in text
        and "[GPT_RELAY_RECOVERY_ADVICE]" in text
        and "[/GPT_RELAY_RECOVERY_ADVICE]" in text
    )


def _build_recovery_advice_correction(incident_id: str) -> str:
    return (
        "Your previous relay-recovery response for incident_id=" + incident_id +
        " was visible but did not satisfy the bounded recovery-advice schema. "
        "Do not send GPT_WINDOWS_ACTION or shell commands. Retry exactly one "
        "[GPT_RELAY_RECOVERY_ADVICE] envelope with JSON version=1, this exact incident_id, "
        "a non-empty recommended_repairs array containing only rebuild_browser_integration, "
        "audited_update, or restart_relay, and a brief reason, then close the envelope."
    )


def _consult_gpt_out_of_band(s: Snapshot, d: Decision) -> tuple[bool, dict[str, Any] | None, str]:
    if not s.browser_id:
        return False, None, "no selected browser for independent GPT recovery"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seed = (s.active_operation or s.discovered_packet or s.last_operation or "relay")[-40:]
    incident_id = "RECOVERY-" + stamp + "-" + "".join(ch for ch in seed if ch.isalnum() or ch in "-_.")[:40]
    classification = _recovery_classification(s, d)
    prompt = _build_gpt_recovery_prompt(s, d, incident_id)
    deadline_epoch = time.time() + GPT_RECOVERY_TIMEOUT_SECONDS
    _set_recovery_state(
        incident_id, "OOB_PROMPT_SENDING", snapshot=s, classification=classification,
        deadline_epoch=deadline_epoch, detail="independent GPT recovery prompt pending",
    )
    try:
        sent = browser_manager.send_out_of_band_recovery_prompt(s.browser_id, prompt)
    except Exception as exc:
        detail = f"out-of-band GPT prompt failed: {type(exc).__name__}: {str(exc)[:300]}"
        _set_recovery_state(
            incident_id, "OOB_FAILED", snapshot=s, classification=classification,
            deadline_epoch=deadline_epoch, detail=detail,
        )
        return False, None, detail
    if not sent.get("ok"):
        detail = "out-of-band GPT prompt was not confirmed"
        _set_recovery_state(
            incident_id, "OOB_FAILED", snapshot=s, classification=classification,
            deadline_epoch=deadline_epoch, detail=detail,
        )
        return False, None, detail
    _set_recovery_state(
        incident_id, "OOB_WAITING_ADVICE", snapshot=s, classification=classification,
        deadline_epoch=deadline_epoch, detail="prompt sent; waiting for bounded GPT advice",
    )
    deadline = time.monotonic() + GPT_RECOVERY_TIMEOUT_SECONDS
    correction_sent = False
    read_failures = 0
    last_read_error = ""
    while time.monotonic() < deadline:
        time.sleep(2.0)
        try:
            body = browser_manager.read_out_of_band_chat(s.browser_id)
        except Exception as exc:
            read_failures += 1
            last_read_error = f"{type(exc).__name__}: {str(exc)[:240]}"
            if read_failures in {1, 3, 10}:
                _set_recovery_state(
                    incident_id, "OOB_READ_RETRYING", snapshot=s, classification=classification,
                    deadline_epoch=deadline_epoch,
                    detail=f"independent GPT read retry {read_failures}: {last_read_error}",
                )
            continue
        read_failures = 0
        advice = _extract_gpt_recovery_advice(body, incident_id)
        if advice is not None:
            detail = f"bounded GPT recovery advice received for {incident_id}"
            _set_recovery_state(
                incident_id, "OOB_ADVICE_RECEIVED", snapshot=s, classification=classification,
                deadline_epoch=deadline_epoch, detail=detail,
            )
            return True, advice, detail
        if not correction_sent and _recovery_advice_mentions_incident(body, incident_id):
            correction_sent = True
            detail = f"invalid GPT recovery advice observed for {incident_id}; requesting one bounded retry"
            _set_recovery_state(
                incident_id, "OOB_ADVICE_RETRYING", snapshot=s, classification=classification,
                deadline_epoch=deadline_epoch, detail=detail,
            )
            try:
                retried = browser_manager.send_out_of_band_recovery_prompt(
                    s.browser_id, _build_recovery_advice_correction(incident_id)
                )
            except Exception as exc:
                retried = {"ok": False, "error": str(exc)}
            if not retried.get("ok"):
                detail = f"out-of-band GPT correction prompt failed for {incident_id}"
                _set_recovery_state(
                    incident_id, "OOB_FAILED", snapshot=s, classification=classification,
                    deadline_epoch=deadline_epoch, detail=detail,
                )
                return False, None, detail
    detail = f"out-of-band GPT advice timeout for {incident_id}"
    if last_read_error:
        detail += f"; last independent read error: {last_read_error}"
    _set_recovery_state(
        incident_id, "OOB_FAILED", snapshot=s, classification=classification,
        deadline_epoch=deadline_epoch, detail=detail,
    )
    return False, None, detail


def _execute_gpt_recovery_advice(s: Snapshot, advice: dict[str, Any]) -> tuple[bool, str]:
    incident_id = str(advice.get("incident_id") or "RECOVERY-UNKNOWN")
    repairs = advice.get("recommended_repairs")
    if not isinstance(repairs, list) or not repairs or any(item not in GPT_RECOVERY_ALLOWED_ACTIONS for item in repairs):
        detail = "GPT advice failed recovery whitelist validation"
        _set_recovery_state(incident_id, "OOB_REPAIR_FAILED", snapshot=s, detail=detail)
        return False, detail
    details: list[str] = []
    for action in repairs:
        _set_recovery_state(
            incident_id, "OOB_REPAIR_EXECUTING", snapshot=s, action=action,
            detail=f"executing whitelisted recovery action {action}",
        )
        if action == "rebuild_browser_integration":
            ok, detail = _repair_browser(s.browser_id)
        elif action == "audited_update":
            ok, detail = _self_update()
        elif action == "restart_relay":
            ok, detail = _restart_relay()
        else:
            detail = f"rejected unknown GPT recovery action: {action}"
            _set_recovery_state(incident_id, "OOB_REPAIR_FAILED", snapshot=s, action=action, detail=detail)
            return False, detail
        details.append(f"{action}: {detail}")
        if not ok:
            joined = "; ".join(details)
            _set_recovery_state(incident_id, "OOB_REPAIR_FAILED", snapshot=s, action=action, detail=joined)
            return False, joined
    joined = "; ".join(details)
    _set_recovery_state(incident_id, "OOB_RECOVERED", snapshot=s, detail=joined)
    return True, joined


def _self_update() -> tuple[bool, str]:
    """Whitelisted update only: existing updater enforces configured branch and ff-only for linked Git."""
    updater_path = Path(__file__).resolve().parent / "updater.py"
    if not updater_path.is_file():
        return False, "consumer updater unavailable"
    try:
        proc = subprocess.run(
            [sys.executable, str(updater_path), "update"],
            cwd=str(updater_path.parent), capture_output=True, text=True, timeout=180,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"update launch failed: {exc}"
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "consumer update failed").strip()[-500:]
    return True, (proc.stdout or "consumer update completed").strip()[-500:]


def run_repair(s: Snapshot, d: Decision, attempt: int) -> tuple[bool, str]:
    shot = _capture_screenshot(s.active_operation or s.discovered_packet or d.phase)
    _evidence("repair_started", s, d, attempt=attempt, screenshot=shot)
    if d.repair == "restart_relay":
        ok, detail = _restart_relay()
    elif d.repair == "repair_browser":
        ok, detail = _repair_browser(s.browser_id)
    elif d.repair == "capture_diagnostic":
        ok, detail = False, "visible ChatGPT error captured; waiting for bounded recovery"
    else:
        return False, "no whitelisted repair for decision"
    _evidence("repair_finished", s, d, attempt=attempt, success=ok, detail=detail, screenshot=shot)
    return ok, detail


def supervise(*, once: bool = False) -> int:
    state = _read_json(SUPERVISOR_STATE_PATH)
    signature = state.get("signature")
    attempts = int(state.get("attempts", 0) or 0)
    last_attempt_epoch = float(state.get("last_attempt_epoch", 0) or 0)

    while True:
        s = sample()
        d = decide(s)
        current_signature = "|".join([
            d.repair or d.phase,
            s.browser_id or "",
            s.active_operation or s.discovered_packet or "",
        ])
        now_epoch = time.time()

        if d.repair is None:
            attempts = 0
            signature = current_signature
        elif current_signature != signature:
            attempts = 0
            signature = current_signature

        update_attempted = False
        detail = ""
        if d.repair and (now_epoch - last_attempt_epoch) >= REPAIR_COOLDOWN_SECONDS:
            attempts += 1
            last_attempt_epoch = now_epoch
            ok, detail = run_repair(s, d, attempts)
            if ok:
                attempts = 0
            elif attempts == 2:
                # After two deterministic repairs, stop repeating the broken transport.
                # Ask GPT through browser control that is independent of the WebExtension,
                # then execute only enumerated whitelist advice.
                consulted, advice, consult_detail = _consult_gpt_out_of_band(s, d)
                _evidence(
                    "out_of_band_gpt_recovery", s, d, attempt=attempts,
                    success=consulted, detail=consult_detail, advice=advice,
                )
                detail = detail + "; " + consult_detail
                if consulted and advice is not None:
                    recovered, advice_detail = _execute_gpt_recovery_advice(s, advice)
                    _evidence(
                        "out_of_band_gpt_repair", s, d, attempt=attempts,
                        success=recovered, detail=advice_detail, advice=advice,
                    )
                    detail = detail + "; " + advice_detail
                    if recovered:
                        attempts = 0
                else:
                    # Preserve the existing audited updater as a deterministic fallback
                    # when the independent GPT channel itself is unavailable.
                    update_attempted = True
                    updated, update_detail = _self_update()
                    _evidence("audited_update", s, d, attempt=attempts, success=updated, detail=update_detail)
                    detail = detail + "; " + update_detail
            elif attempts >= MAX_REPAIR_ATTEMPTS:
                d = Decision("STALLED", detail or "bounded recovery exhausted; user escalation required")

        recovery_state = _read_json(SUPERVISOR_STATE_PATH).get("recovery")
        if d.repair is None:
            recovery_state = None
        payload = {
            "version": 1,
            "updated_at": utc_now(),
            "phase": d.phase,
            "reason": d.reason,
            "signature": signature,
            "attempts": attempts,
            "last_attempt_epoch": last_attempt_epoch,
            "update_attempted": update_attempted,
            "snapshot": asdict(s),
            "detail": detail,
            "recovery": recovery_state,
        }
        _atomic_json(SUPERVISOR_STATE_PATH, payload)
        if once:
            print(json.dumps(payload, ensure_ascii=False))
            return 0
        time.sleep(POLL_SECONDS)


def _acquire_singleton():
    if os.name != "nt":
        return None
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.ReleaseMutex.argtypes = [ctypes.c_void_p]
    kernel32.ReleaseMutex.restype = ctypes.c_bool
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_bool
    ctypes.set_last_error(0)
    handle = kernel32.CreateMutexW(None, True, SINGLETON_NAME)
    if not handle or ctypes.get_last_error() == 183:
        if handle:
            kernel32.CloseHandle(handle)
        return False
    return (kernel32, handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    singleton = _acquire_singleton()
    if singleton is False:
        return 0
    try:
        return supervise(once=args.once)
    finally:
        if isinstance(singleton, tuple):
            kernel32, handle = singleton
            try:
                kernel32.ReleaseMutex(handle)
            finally:
                kernel32.CloseHandle(handle)


if __name__ == "__main__":
    raise SystemExit(main())
