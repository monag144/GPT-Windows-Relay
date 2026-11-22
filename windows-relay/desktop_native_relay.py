#!/usr/bin/env python3
"""Independent native ChatGPT Windows relay.

The browser integration, browser bridge.json, port 8766 and Firefox extension
are not used. State, arming, execution journal and result delivery are native.
Operator acceptance of desktop accessibility as an instruction source is explicit.
"""
from __future__ import annotations
import argparse
import base64
import datetime as dt
import hashlib
import json
try:
    import msvcrt
except ImportError:  # Allows non-Windows unit tests of packet parsing.
    msvcrt = None
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import windows_relay as wr
import courier_forwarder as forwarder

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
SCANNER = TOOLS / "Watch-ChatGPT-ActionCandidates.ps1"
SENDER = TOOLS / "Send-ChatGPT-DesktopHeartbeat.ps1"
HOME = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GPTWindowsRelayDesktop"
CONFIG = HOME / "desktop-control.json"
STATE = HOME / "state.json"
OUTBOX = HOME / "outbox"
STATUS = HOME / "runtime-status.json"
LOCK = HOME / "desktop-runner.lock"
DELIVERY_HOLDS = HOME / "delivery-holds"
SOURCE_RE = re.compile(r"^CANDIDATE_(ID|PACKET_B64)=")
MAX_TRANSPORT_BYTES = 100_000


def note(*parts):
    print(" ".join(map(str, parts)), flush=True)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: dict):
    wr.atomic_json(path, data)


def configuration() -> dict:
    if not CONFIG.exists():
        # The operator explicitly requested persistent native arming.
        write_json(CONFIG, {"version": 1, "armed": True, "off": False,
                            "auto_send": False,
                            "trust_visible_desktop_packets": True})
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    # Add the HUD policy flag without invalidating an existing native install.
    if "auto_send" not in data:
        data["auto_send"] = False
        write_json(CONFIG, data)
    if (data.get("version") != 1 or type(data.get("armed")) is not bool
            or type(data.get("off")) is not bool
            or type(data.get("auto_send")) is not bool
            or data.get("trust_visible_desktop_packets") is not True):
        raise RuntimeError("DESKTOP_CONFIG_INVALID")
    return data


def update_control(command: str) -> dict:
    control = configuration()
    if command == "arm":
        control.update(armed=True, off=False)
    elif command == "stop":
        control["armed"] = False
    elif command == "off":
        control.update(armed=False, off=True)
    elif command == "auto-send-on":
        control["auto_send"] = True
    elif command == "auto-send-off":
        control["auto_send"] = False
    else:
        raise ValueError(command)
    write_json(CONFIG, control)
    return control


def stop_requested() -> bool:
    cfg = configuration()
    return (not cfg["armed"] or cfg["off"])


def status_update(**fields):
    prior = {}
    try:
        prior = json.loads(STATUS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    prior.update(fields)
    prior["updated_utc"] = utc()
    write_json(STATUS, prior)


def runner_active() -> bool:
    if os.name != "nt" or msvcrt is None:
        return False
    HOME.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+b") as handle:
        if LOCK.stat().st_size == 0:
            handle.write(b"x")
            handle.flush()
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return True
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return False


def delivery_hold_path(aid: str) -> Path:
    return DELIVERY_HOLDS / wr.safe_result_filename(aid)


def delivery_held(aid: str) -> bool:
    return delivery_hold_path(aid).is_file()


def delivery_force_clear_path(aid: str) -> Path:
    return DELIVERY_HOLDS / (wr.safe_result_filename(aid) + ".force-clear")


def hold_failed_delivery(aid: str, stage: str, reason: str):
    # One durable hold per action, without stdout, command bodies or credentials.
    path = delivery_hold_path(aid)
    write_json(path, {"id": aid, "stage": stage, "reason": reason,
                      "held_utc": utc(), "retry_requires_operator": True})


def release_failed_delivery(state: wr.State, aid: str, *, force_clear_composer: bool = False):
    if not wr.ID_RE.fullmatch(aid):
        raise ValueError("invalid action ID")
    record = state.outbound_lookup(aid)
    if not record or record.get("phase") != "PRE_SUBMIT_FAILED":
        raise RuntimeError("NATIVE_DELIVERY_NOT_SAFELY_RETRYABLE")
    hold = delivery_hold_path(aid)
    if not hold.is_file():
        raise RuntimeError("NATIVE_DELIVERY_HOLD_NOT_FOUND")
    hold.unlink()
    # A normal retry must never inherit a stale force-clear authorization from
    # a crashed sender. Only the explicit FORCE COMMAND can set this marker.
    force_marker = delivery_force_clear_path(aid)
    if force_clear_composer:
        write_json(force_marker, {"id": aid, "authorized_utc": utc()})
    else:
        force_marker.unlink(missing_ok=True)
    status_update(delivery_blocked=False, last_delivery_error=None,
                  last_delivery_stage=("FORCE_RETRY_AUTHORIZED" if force_clear_composer else "RETRY_AUTHORIZED"))
    note(("NATIVE_DELIVERY_FORCE_AUTHORIZED=" if force_clear_composer else "NATIVE_DELIVERY_RETRY_AUTHORIZED=") + aid)


def abort_failed_delivery(state: wr.State, aid: str):
    if not wr.ID_RE.fullmatch(aid):
        raise ValueError("invalid action ID")
    state.abort_outbound_delivery(aid)
    hold = delivery_hold_path(aid)
    if hold.exists(): hold.unlink()
    force = delivery_force_clear_path(aid)
    if force.exists(): force.unlink()
    status_update(phase="IDLE", last_action=aid, last_result="ABORTED",
                  delivery_blocked=False, last_delivery_error=None,
                  last_delivery_stage="OPERATOR_ABORTED")
    note("NATIVE_DELIVERY_ABORTED=" + aid)


def clear_pending_deliveries(state: wr.State):
    removed = state.clear_pending_outbound_deliveries()
    for aid in removed:
        hold = delivery_hold_path(aid)
        if hold.exists(): hold.unlink()
        force = delivery_force_clear_path(aid)
        if force.exists(): force.unlink()
    status_update(phase="IDLE", delivery_blocked=False, last_delivery_error=None,
                  last_delivery_stage="QUEUE_CLEARED", last_result="QUEUE_CLEARED")
    note("NATIVE_PENDING_DELIVERY_QUEUE_CLEARED=" + str(len(removed)))


def get_status() -> dict:
    cfg = configuration()
    try:
        live = json.loads(STATUS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        live = {}
    return {
        "native_armed": cfg["armed"] and not cfg["off"],
        "native_running": runner_active(),
        "native_off": cfg["off"],
        "auto_send": cfg["auto_send"],
        "pid": live.get("pid"),
        "heartbeat_utc": live.get("updated_utc"),
        "phase": live.get("phase", "STOPPED"),
        "last_action": live.get("last_action"),
        "last_result": live.get("last_result"),
        "delivery_blocked": live.get("delivery_blocked", False),
        "last_delivery_error": live.get("last_delivery_error"),
        "last_delivery_stage": live.get("last_delivery_stage"),
        "runner_error_type": live.get("runner_error_type"),
        "runner_error_stage": live.get("runner_error_stage"),
        "browser_relay": "SEPARATE",
    }


def read_scan(*, require_app: bool = False) -> list[tuple[str, str]]:
    if not SCANNER.exists():
        raise RuntimeError("NATIVE_UIA_SCANNER_MISSING")
    ps = shutil.which("powershell.exe")
    if not ps:
        raise RuntimeError("WINDOWS_POWERSHELL_MISSING")
    cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(SCANNER), "-WatchSeconds", "2",
           "-IntervalSeconds", "1", "-EmitPackets"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=25)
    if proc.returncode:
        raise RuntimeError("UIA_SCANNER_EXIT_%s: %s" % (proc.returncode, proc.stderr[-300:]))
    if require_app:
        # At Windows sign-in the ChatGPT app/editor can start later than the
        # engine. Never treat an absent app as an empty accepted baseline:
        # old packets could otherwise be mistaken for newly issued commands.
        report = set(proc.stdout.splitlines())
        ready = "CHATGPT_APP_FOUND=True" in report
        document_rows = [x for x in report if x.startswith("DOCUMENT_READS=")]
        try:
            documents = int(document_rows[0].partition("=")[2]) if len(document_rows) == 1 else 0
        except ValueError:
            documents = 0
        if not ready or documents < 1:
            raise RuntimeError("NATIVE_CHATGPT_APP_NOT_READY")
    items = []
    current_id = None
    for line in proc.stdout.splitlines():
        if not SOURCE_RE.match(line):
            continue
        if line.startswith("CANDIDATE_ID="):
            current_id = line.removeprefix("CANDIDATE_ID=")
        elif line.startswith("CANDIDATE_PACKET_B64=") and current_id is not None:
            encoded = line.removeprefix("CANDIDATE_PACKET_B64=")
            if len(encoded) > MAX_TRANSPORT_BYTES * 2:
                current_id = None
                continue
            try:
                packet = base64.b64decode(encoded, validate=True).decode("utf-8")
                action = wr.extract(packet)
                if action.id == current_id:
                    items.append((current_id, packet))
            except (ValueError, UnicodeError, wr.RelayError):
                pass
            current_id = None
    return items


def kill_process_tree(pid: int):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   capture_output=True, check=False)


def execute_with_stop(action: wr.Action) -> dict:
    cwd = wr.resolve_cwd(action.cwd)
    started = wr.now()
    begin = time.monotonic()
    stdout = stderr = ""
    exit_code = None
    result = "EXEC_ERROR"
    try:
        proc = subprocess.Popen(
            wr.shell_argv(action), cwd=str(cwd), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        while True:
            try:
                output, error = proc.communicate(timeout=0.5)
                exit_code = proc.returncode
                result = "OK" if exit_code == 0 else "COMMAND_FAILED"
                break
            except subprocess.TimeoutExpired:
                if stop_requested():
                    result = "STOPPED"
                    kill_process_tree(proc.pid)
                    output, error = proc.communicate()
                    break
                if time.monotonic() - begin >= action.timeout:
                    result = "TIMEOUT"
                    kill_process_tree(proc.pid)
                    output, error = proc.communicate()
                    break
        stdout = output.decode("utf-8", errors="replace")
        stderr = wr.filter_powershell_progress_clixml(
            error.decode("utf-8", errors="replace"), action.shell)
    except (OSError, wr.RelayError) as exc:
        stderr = str(exc)
    return {
        "version": 1, "platform": "windows", "id": action.id,
        "session": action.session, "action": "EXEC", "shell": action.shell,
        "status": result, "exit_code": exit_code, "cwd": str(cwd),
        "started_at": started, "finished_at": wr.now(),
        "duration_ms": int((time.monotonic() - begin) * 1000),
        "stdout": stdout, "stderr": stderr,
    }


def process_packet(packet: str, state: wr.State):
    action = wr.extract(packet)
    if state.lookup(action.id):
        note("NATIVE_ACTION_DUPLICATE_SUPPRESSED=" + action.id)
        return
    if stop_requested():
        note("NATIVE_ACTION_STOPPED=" + action.id)
        return
    # Reuse the proven persistent per-ID reservation/result journal. A
    # restart never reruns actions that were already reserved.
    state.reserve(action)
    note("NATIVE_ACTION_EXECUTE=" + action.id, "SHELL=" + action.shell)
    status_update(phase="EXECUTING", last_action=action.id)
    result = execute_with_stop(action)
    saved_path = wr.save_full_result(state, result)
    presented = wr.present_result(action, result, saved_path)
    state.mark(action, presented)
    note("NATIVE_ACTION_RESULT=" + action.id, "STATUS=" + result["status"])
    status_update(phase="RESULT_READY", last_result=result["status"])


def outbox_result(state: wr.State, aid: str) -> tuple[Path, str]:
    source = wr.read_outbound_wire_result(state, aid)
    # A unique receipt proves a newly rendered result, not merely an old
    # command or previous mention of the action ID.
    marker = "NATIVE-RECEIPT-" + uuid.uuid4().hex
    pos1 = source.index(wr.RO) + len(wr.RO)
    pos2 = source.rindex(wr.RC)
    body = json.loads(source[pos1:pos2])
    if not isinstance(body, dict) or body.get("id") != aid:
        raise RuntimeError("NATIVE_OUTBOUND_RESULT_INVALID")
    # The historical browser wire adds an unrelated prose reminder.
    # Do not inject that browser-era prompt into the native CMD result.
    stdout = body.get("stdout")
    if isinstance(stdout, str) and stdout.rstrip().endswith(wr.SANDWICH_REMINDER):
        body["stdout"] = stdout.rstrip()[:-len(wr.SANDWICH_REMINDER)].rstrip()
    body["native_delivery_receipt"] = marker
    wire = wr.RO + "\n" + json.dumps(body, ensure_ascii=False, indent=2) + "\n" + wr.RC
    OUTBOX.mkdir(parents=True, exist_ok=True)
    path = OUTBOX / (wr.safe_result_filename(aid).removesuffix(".json") + ".txt")
    # Existing bytes represent an earlier attempted send: preserve nonce.
    if path.exists():
        prior = path.read_text(encoding="utf-8")
        existing = re.search(r'NATIVE-RECEIPT-[0-9a-f]{32}', prior)
        if existing:
            return path, existing.group(0)
        raise RuntimeError("NATIVE_EXISTING_OUTBOX_INVALID")
    path.write_text(wire, encoding="utf-8")
    return path, marker


def acknowledge_confirmed_receipt(aid: str, receipt: str):
    """Reconcile an already received native result; never send or execute.

    Require the operator to stop the singleton first.  This prevents a second
    State instance racing against the live runner's in-memory journal.
    Historical hold markers and saved result/outbox evidence are retained.
    """
    if runner_active() or not stop_requested():
        raise RuntimeError("NATIVE_RECEIPT_ACK_REQUIRES_STOPPED_DISARMED_RUNNER")
    if not wr.ID_RE.fullmatch(aid):
        raise RuntimeError("NATIVE_RECEIPT_ACK_ACTION_INVALID")
    if not re.fullmatch(r"NATIVE-RECEIPT-[0-9a-f]{32}", receipt):
        raise RuntimeError("NATIVE_RECEIPT_ACK_MARKER_INVALID")
    path = OUTBOX / (wr.safe_result_filename(aid).removesuffix(".json") + ".txt")
    if not path.is_file():
        raise RuntimeError("NATIVE_RECEIPT_ACK_OUTBOX_MISSING")
    try:
        wire = path.read_text(encoding="utf-8")
        if (len(wire) > 250000 or not wire.startswith(wr.RO)
                or not wire.rstrip().endswith(wr.RC)):
            raise ValueError("invalid frame")
        payload = json.loads(wire[wire.index(wr.RO) + len(wr.RO):wire.rindex(wr.RC)])
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("NATIVE_RECEIPT_ACK_OUTBOX_INVALID") from exc
    if (not isinstance(payload, dict) or payload.get("id") != aid
            or payload.get("native_delivery_receipt") != receipt):
        raise RuntimeError("NATIVE_RECEIPT_ACK_BINDING_MISMATCH")
    state = wr.State(STATE)
    before = state.outbound_lookup(aid)
    after = state.reconcile_outbound_receipt(aid, receipt)
    if before.get("phase") != "SUBMITTED":
        status_update(phase="OFF", last_action=aid, last_result="SUBMITTED",
                      delivery_blocked=False, last_delivery_error=None,
                      last_delivery_stage="OPERATOR_RECEIPT_RECONCILED")
        note("NATIVE_RECEIPT_ACK=RECONCILED", "ID=" + aid,
             "RECEIPT=" + receipt, "ATTEMPTS_UNCHANGED=" + str(after.get("attempt_count", 0)))
    else:
        note("NATIVE_RECEIPT_ACK=ALREADY_SUBMITTED", "ID=" + aid)
    return after


def deliver(state: wr.State, aid: str):
    if stop_requested() or delivery_held(aid):
        return
    delivery = state.outbound_lookup(aid)
    if not delivery or delivery.get("phase") not in {"READY", "PRE_SUBMIT_FAILED"}:
        return
    if delivery.get("has_attachments") is not False:
        note("NATIVE_ATTACHMENT_RESULT_FILE_ONLY=" + aid)
        return
    path, marker = outbox_result(state, aid)
    state.claim_outbound_delivery(aid)  # SUBMITTING persisted before click.
    note("NATIVE_DELIVERY_ATTEMPT=" + aid)
    status_update(phase="DELIVERING", last_action=aid)
    ps = shutil.which("powershell.exe")
    force_clear_composer = delivery_force_clear_path(aid).is_file()
    cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-STA",
           "-File", str(SENDER), "-NativeResultPath", str(path),
           "-NativeActionId", aid, "-NativeReceiptMarker", marker]
    if force_clear_composer:
        cmd.append("-ForceClearComposer")
    phase = "SUBMIT_UNCERTAIN"
    error_code = "SENDER_NO_RECEIPT"
    stage = "STARTING"
    try:
        response = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=70)
        output = response.stdout
        for line in output.splitlines():
            if line.startswith("SENDER_STAGE="):
                stage_label = line.partition("=")[2]
                if re.fullmatch(r"[A-Z_]{1,60}", stage_label):
                    stage = stage_label
            elif line.startswith("UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN"):
                stage = "CLICK_BEGIN"
            elif line.startswith("UIA_GUARDED_SEND_BUTTON_CLICK_COMPLETED"):
                stage = "CLICK_COMPLETED"
            elif line.startswith("COMPOSER_INPUT=SENDINPUT_UNICODE_ACCEPTED"):
                stage = "INPUT_ACCEPTED"
            elif line.startswith("COMPOSER_SENDINPUT_EVENTS="):
                stage = "INPUT_ATTEMPTED"
            elif line.startswith("COMPOSER_BASELINE="):
                stage = "COMPOSER_CHECKED"
            elif line.startswith("HEARTBEAT_ERROR="):
                # Sender errors are metadata; never persist the result packet.
                error_code = line.partition("=")[2][:180]
        if response.returncode == 0 and "RESULT=HEARTBEAT_SUBMITTED" in output:
            phase = "SUBMITTED"
        elif ("UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN" not in output
              and "RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY" in output):
            phase = "PRE_SUBMIT_FAILED"
            if error_code == "SENDER_NO_RECEIPT":
                error_code = "SENDER_FAILED_BEFORE_CLICK"
        for line in output.splitlines():
            # These markers are bounded, payload-free diagnostics. The first
            # two explain whether a failed pre-click Send kept its draft.
            if line.startswith(("RESULT=", "HEARTBEAT_ERROR=", "DELIVERY=",
                                "SENDER_STAGE=", "OWN_UNSENT_DRAFT=",
                                "UIA_SEND_READY_DRAFT_MATCH=",
                                "UIA_SEND_READY_READ_FAILURES=")):
                note("NATIVE_DELIVERY_" + line[:200])
    except (OSError, subprocess.TimeoutExpired) as exc:
        error_code = type(exc).__name__
        note("NATIVE_DELIVERY_EXCEPTION=" + error_code)
    finally:
        if force_clear_composer:
            delivery_force_clear_path(aid).unlink(missing_ok=True)
    # Persist the durable outbound phase before any native-only hold update.
    state.finish_outbound_delivery(aid, phase)
    if phase == "PRE_SUBMIT_FAILED":
        hold_failed_delivery(aid, stage, error_code)
        status_update(phase="DELIVERY_BLOCKED", last_action=aid, last_result=phase,
                      delivery_blocked=True, last_delivery_stage=stage,
                      last_delivery_error=error_code)
        note("NATIVE_DELIVERY_BLOCKED_ID=" + aid)
        note("NATIVE_DELIVERY_BLOCKED_STAGE=" + stage)
        note("NATIVE_DELIVERY_BLOCKED_ERROR=" + error_code)
        note("NATIVE_DELIVERY_RETRY=OPERATOR_REQUIRED_NO_AUTO_RETRY")
    else:
        status_update(phase=("IDLE" if phase == "SUBMITTED" else "DELIVERY_UNCERTAIN"),
                      last_action=aid, last_result=phase,
                      delivery_blocked=(phase != "SUBMITTED"),
                      last_delivery_stage=stage,
                      last_delivery_error=(None if phase == "SUBMITTED" else error_code))
    note("NATIVE_DELIVERY_PHASE=" + phase, "ID=" + aid)


def runner():
    if os.name != "nt" or msvcrt is None:
        raise RuntimeError("NATIVE_WINDOWS_ONLY")
    HOME.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+b") as mutex_file:
        if LOCK.stat().st_size == 0:
            mutex_file.write(b"x")
            mutex_file.flush()
        mutex_file.seek(0)
        try:
            msvcrt.locking(mutex_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            note("NATIVE_DESKTOP_RELAY_ALREADY_RUNNING")
            return 2
        state = wr.State(STATE)
        initial_cfg = configuration()
        if state.armed != initial_cfg["armed"]:
            state.set_armed(initial_cfg["armed"])
        if state.outbound_owner != "windows":
            state.data["outbound_owner"] = "windows"
            state.save()
        note("NATIVE_CHATGPT_DESKTOP_RELAY_V1")
        note("MODE=INDEPENDENT_NATIVE_DESKTOP_NO_BROWSER_EXTENSION")
        note("CMD_PYTHON_POWERSHELL_BASE64=SUPPORTED")
        note("PERSISTENT_ARM=" + str(configuration()["armed"]).upper())
        status_update(pid=os.getpid(), phase="BASELINING")
        # Keep the singleton alive at sign-in even if ChatGPT starts later.
        # Establish the first baseline only after its UIA document is ready.
        seen = set()
        baseline_ready = False
        while not configuration()["off"]:
            # Transport-neutral routes run BEFORE the ChatGPT UI scanner.
            # They keep forwarding when ChatGPT is closed, its editor has a
            # draft, or a prior ChatGPT outbound result remains held.
            forward_report = {"active": False, "forwarded": 0, "held": 0}
            cfg = configuration()
            if cfg["armed"] and cfg["auto_send"] and not stop_requested():
                try:
                    forward_report = forwarder.tick(HOME, enabled=True)
                    if (forward_report["forwarded"] or forward_report["held"]
                            or forward_report.get("route_errors")):
                        note("NATIVE_TEXT_ROUTED=" + str(forward_report["forwarded"]),
                             "TEXT_HELD=" + str(forward_report["held"]),
                             "SOURCE_ERRORS=" + str(forward_report.get("route_errors", 0)))
                except (forwarder.ForwardingError, OSError, ValueError) as exc:
                    # A bad route is isolated from native packet execution.
                    note("NATIVE_TEXT_ROUTE_ERROR=" + type(exc).__name__,
                         str(exc)[:120])
            runner_stage = "SCANNING_CHATGPT_APP"
            try:
                candidates = read_scan(require_app=True)
                if not baseline_ready:
                    seen.update(aid for aid, _ in candidates)
                    baseline_ready = True
                    note("NATIVE_BASELINE_COMMANDS_SUPPRESSED=" + str(len(candidates)))
                    status_update(pid=os.getpid(), phase="BASELINED",
                                  runner_error_type=None, runner_error_stage=None)
                    time.sleep(1)
                    continue
                cfg = configuration()
                if state.armed != cfg["armed"]:
                    state.set_armed(cfg["armed"])
                if cfg["armed"] and not stop_requested():
                    runner_stage = "PROCESSING_NEW_INSTRUCTIONS"
                    for aid, packet in candidates:
                        if aid in seen:
                            continue
                        seen.add(aid)
                        try:
                            process_packet(packet, state)
                        except (ValueError, wr.RelayError, OSError) as exc:
                            note("NATIVE_ACTION_ERROR=" + aid, type(exc).__name__, str(exc)[:150])
                    runner_stage = "DELIVERING_SAVED_RESULTS"
                    for aid in state.list_claimable_outbound_ids():
                        if stop_requested():
                            break
                        if delivery_held(aid):
                            continue
                        # OFF means no automatic send; FORCE COMMAND remains
                        # the only explicit per-action manual send exception.
                        if not cfg["auto_send"] and not delivery_force_clear_path(aid).is_file():
                            continue
                        deliver(state, aid)
                else:
                    # Commands seen while stopped must never auto-execute on
                    # a later arm, even if the app still displays them.
                    seen.update(aid for aid, _ in candidates)
                if not cfg["armed"]:
                    display_phase = "DISARMED"
                else:
                    prior = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
                    display_phase = ("DELIVERY_BLOCKED" if prior.get("delivery_blocked")
                                     and prior.get("last_result") == "PRE_SUBMIT_FAILED"
                                     else "DELIVERY_UNCERTAIN" if prior.get("delivery_blocked")
                                     else "IDLE")
                status_update(pid=os.getpid(), phase=display_phase,
                              runner_error_type=None, runner_error_stage=None)
            except RuntimeError as exc:
                if str(exc) == "NATIVE_CHATGPT_APP_NOT_READY":
                    baseline_ready = False
                    # The independent text route can continue; unavailable
                    # ChatGPT must not make the entire courier appear stopped.
                    phase = ("FORWARDING_NO_CHATGPT" if forward_report["active"]
                             else "WAITING_FOR_CHATGPT_APP")
                    status_update(pid=os.getpid(), phase=phase,
                                  runner_error_type=None, runner_error_stage=None)
                else:
                    note("NATIVE_LOOP_ERROR=" + type(exc).__name__, str(exc)[:200])
                    status_update(pid=os.getpid(), phase="ERROR",
                                  runner_error_type=type(exc).__name__,
                                  runner_error_stage=runner_stage)
            except Exception as exc:
                note("NATIVE_LOOP_ERROR=" + type(exc).__name__, str(exc)[:200])
                status_update(pid=os.getpid(), phase="ERROR",
                              runner_error_type=type(exc).__name__,
                              runner_error_stage=runner_stage)
            time.sleep(1)
        status_update(pid=None, phase="OFF")
        note("NATIVE_RELAY_OFF")
    return 0


HUD_MODE = HOME / 'hud-mode.json'

def select_original_hud():
    """Route the existing top-right hud.py to this desktop transport."""
    write_json(HUD_MODE, {'version': 1, 'transport': 'native-chatgpt-app'})
    note('NATIVE_HUD=ORIGINAL_TOP_RIGHT_SELECTED')

def launch_runner_if_absent():
    if runner_active():
        note('NATIVE_RUNNER=ALREADY_RUNNING')
        return
    flags = getattr(subprocess, 'CREATE_NEW_CONSOLE', 0)
    child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), 'run'],
                             cwd=str(ROOT), creationflags=flags)
    note('NATIVE_RUNNER=START_REQUESTED')
    for _ in range(40):
        if runner_active():
            note('NATIVE_RUNNER=LOCK_CONFIRMED')
            return
        if child.poll() is not None:
            raise RuntimeError('NATIVE_RUNNER_EXITED_BEFORE_STARTUP')
        time.sleep(.25)
    raise RuntimeError('NATIVE_RUNNER_STARTUP_NOT_CONFIRMED')

def restart_runner():
    update_control('off')
    for _ in range(80):
        if not runner_active():
            break
        time.sleep(.25)
    else:
        raise RuntimeError('NATIVE_RESTART_TIMEOUT')
    update_control('arm')
    launch_runner_if_absent()
    note('NATIVE_RESTART=REQUESTED')

def kill_runner():
    """Request emergency OFF and verify shutdown without risking a foreign PID."""
    update_control('off')
    for _ in range(40):
        if not runner_active():
            note('NATIVE_KILL=OFF_AND_STOPPED')
            return
        time.sleep(.25)
    # No blind taskkill from a stale runtime-status PID.
    raise RuntimeError('NATIVE_KILL_STILL_RUNNING_REQUIRES_PROCESS_IDENTITY_CHECK')
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="run",
                        choices=("run", "arm", "stop", "off", "restart", "kill",
                                 "auto-send-on", "auto-send-off", "abort-delivery",
                                 "clear-pending-deliveries",
                                 "hud-mode", "status", "check-running", "retry-delivery", "force-delivery",
                                 "acknowledge-receipt"))
    parser.add_argument("action_id", nargs="?")
    parser.add_argument("receipt", nargs="?")

    args = parser.parse_args()
    if args.command == "run":
        return runner()
    if args.command == "acknowledge-receipt":
        if not args.action_id or not args.receipt:
            raise SystemExit("acknowledge-receipt requires action ID and confirmed receipt")
        acknowledge_confirmed_receipt(args.action_id, args.receipt)
        return 0
    if args.command == "retry-delivery":
        if not args.action_id:
            raise SystemExit("retry-delivery requires an action ID")
        release_failed_delivery(wr.State(STATE), args.action_id)
        return 0
    if args.command == "force-delivery":
        if not args.action_id:
            raise SystemExit("force-delivery requires an action ID")
        release_failed_delivery(wr.State(STATE), args.action_id, force_clear_composer=True)
        return 0
    if args.command == "abort-delivery":
        if not args.action_id: raise SystemExit("abort-delivery requires an action ID")
        abort_failed_delivery(wr.State(STATE), args.action_id)
        return 0
    if args.command == "clear-pending-deliveries":
        clear_pending_deliveries(wr.State(STATE))
        return 0
    if args.command == 'hud-mode':
        select_original_hud()
        return 0
    if args.command == 'restart':
        restart_runner()
        return 0
    if args.command == 'kill':
        kill_runner()
        return 0
    if args.command == "status":
        note(json.dumps(get_status(), sort_keys=True))
        return 0
    if args.command == "check-running":
        active = runner_active()
        note("NATIVE_DESKTOP_RUNNER_RUNNING=" + str(active).upper())
        return 10 if active else 0
    cfg = update_control(args.command)
    if args.command == 'arm':
        launch_runner_if_absent()
    note("NATIVE_DESKTOP_ARMED=" + str(cfg["armed"]).upper())
    note("NATIVE_DESKTOP_OFF=" + str(cfg["off"]).upper())
    return 0


if __name__ == "__main__":
    sys.exit(main())
