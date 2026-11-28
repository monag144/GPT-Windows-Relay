#!/usr/bin/env python3
"""Universal Command Courier: operator-supplied output, foreground-field delivery.

No third-party conversation scanning, inferred instructions or application
allowlist is permitted in the active native runner. The original execution
journal is retained for historical results and exact-once delivery.
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
import threading
import time
import uuid
from pathlib import Path

import windows_relay as wr
import courier_forwarder as forwarder

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
FOREGROUND_SENDER = TOOLS / "Send-Foreground-TextResult.ps1"
HOME = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GPTWindowsRelayDesktop"
CONFIG = HOME / "desktop-control.json"
STATE = HOME / "state.json"
OUTBOX = HOME / "outbox"
STATUS = HOME / "runtime-status.json"
LOCK = HOME / "desktop-runner.lock"
DELIVERY_HOLDS = HOME / "delivery-holds"
RECEIPT_REQUESTS = HOME / "receipt-reconciliations"
FORCE_CLEAR_REQUESTS = HOME / "force-clear-requests"
FORCE_CLEAR_RECEIPTS = HOME / "force-clear-receipts"
FORCE_SEND_REQUESTS = HOME / "force-send-requests"
FORCE_SEND_RECEIPTS = HOME / "force-send-receipts"
OUTPUT_REQUESTS = HOME / "explicit-output-requests"
OUTPUT_RECEIPTS = HOME / "explicit-output-receipts"
MAX_EXPLICIT_OUTPUT_BYTES = 16000


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
                            "trust_visible_desktop_packets": False})
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    # Add the HUD policy flag without invalidating an existing native install.
    if "auto_send" not in data:
        data["auto_send"] = False
        write_json(CONFIG, data)
    if (data.get("version") != 1 or type(data.get("armed")) is not bool
            or type(data.get("off")) is not bool
            or type(data.get("auto_send")) is not bool
            or type(data.get("trust_visible_desktop_packets")) is not bool):
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


def queue_explicit_output(text: str, *, source: str = "explicit-file", aid: str | None = None) -> str:
    """Local file/clipboard/API result intake; only the running owner journals.

    No command execution, transcript reading, UI automation, or direct
    State() mutation occurs in this client-side function.
    """
    if source not in {"explicit-file","explicit-clipboard","authorized-api"}:
        raise ValueError("OUTPUT_SOURCE_INVALID")
    if (not isinstance(text,str) or not text.strip()
            or "\x00" in text or len(text.encode("utf-8")) > MAX_EXPLICIT_OUTPUT_BYTES):
        raise ValueError("OUTPUT_TEXT_INVALID")
    if aid is None:
        aid = "COURIER-" + uuid.uuid4().hex
    if not isinstance(aid,str) or not wr.ID_RE.fullmatch(aid):
        raise ValueError("OUTPUT_ACTION_ID_INVALID")
    request_path = OUTPUT_REQUESTS / (wr.safe_result_filename(aid))
    if request_path.exists() or (OUTPUT_RECEIPTS / request_path.name).exists():
        raise ValueError("OUTPUT_ID_ALREADY_QUEUED")
    OUTPUT_REQUESTS.mkdir(parents=True,exist_ok=True)
    write_json(request_path, {
        "version":1,"kind":"EXPLICIT_OUTPUT","id":aid,
        "source":source,"text":text,
        "text_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "queued_utc":utc(),
    })
    note("COURIER_EXPLICIT_OUTPUT_QUEUED="+aid, "BYTES="+str(len(text.encode("utf-8"))))
    return aid


def queue_output_file(file_path: str, *, aid: str | None = None) -> str:
    """Read ONLY a deliberately named local UTF-8 .txt source file."""
    path = Path(file_path)
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".txt":
        raise ValueError("OUTPUT_SOURCE_MUST_BE_LOCAL_TXT_FILE")
    if path.stat().st_size > MAX_EXPLICIT_OUTPUT_BYTES:
        raise ValueError("OUTPUT_SOURCE_TOO_LARGE")
    return queue_explicit_output(path.read_text(encoding="utf-8"),
                                 source="explicit-file",aid=aid)


def reconcile_explicit_output_requests(state: wr.State) -> int:
    """Single native journal owner consumes explicitly queued local text."""
    if not OUTPUT_REQUESTS.is_dir():
        return 0
    processed=0
    for path in sorted(OUTPUT_REQUESTS.glob("*.json"))[:24]:
        if path.is_symlink():
            continue
        claimed=path.with_suffix(".claimed")
        aid=path.stem
        outcome="REJECTED"
        try:
            # Remove the pending entry atomically before any journal write.
            path.replace(claimed)
            request=json.loads(claimed.read_text(encoding="utf-8"))
            if not isinstance(request,dict):
                raise ValueError("OUTPUT_INVALID_REQUEST")
            aid=request.get("id")
            if (not isinstance(aid,str) or not wr.ID_RE.fullmatch(aid)
                    or path.name!=wr.safe_result_filename(aid)):
                raise ValueError("OUTPUT_INVALID_REQUEST_ID")
            raw_text=request.get("text")
            if (request.get("version")!=1 or
                    request.get("kind")!="EXPLICIT_OUTPUT" or request.get("id")!=aid or
                    request.get("source") not in
                    {"explicit-file","explicit-clipboard","authorized-api"} or
                    not isinstance(raw_text,str) or not raw_text.strip() or
                    len(raw_text.encode("utf-8")) > MAX_EXPLICIT_OUTPUT_BYTES or
                    request.get("text_sha256")!=hashlib.sha256(raw_text.encode("utf-8")).hexdigest()):
                raise ValueError("OUTPUT_INVALID_REQUEST")
            created=state.enqueue_text_output(aid, raw_text, source=request["source"])
            outcome="READY" if created else "ALREADY_QUEUED"
            processed+=1
            note("COURIER_EXPLICIT_OUTPUT="+outcome, "ID="+aid)
        except (OSError,ValueError,wr.RelayError) as exc:
            note("COURIER_EXPLICIT_OUTPUT=REJECTED","ID="+aid,
                 "ERROR="+type(exc).__name__)
        finally:
            if claimed.is_file():
                OUTPUT_RECEIPTS.mkdir(parents=True,exist_ok=True)
                write_json(OUTPUT_RECEIPTS / path.name, {
                    "id":aid,"result":outcome,"finished_utc":utc(),
                })
                claimed.unlink(missing_ok=True)
    return processed


def outbox_result(state: wr.State, aid: str) -> tuple[Path, str]:
    delivery=state.outbound_lookup(aid)
    source=wr.read_outbound_wire_result(state, aid)
    if delivery and delivery.get("wire_format") == "plain_text":
        # Plain text remains byte-for-byte identical to the supplied source.
        # Receipt is bound in a sidecar, never injected into the destination.
        digest=hashlib.sha256(source.encode("utf-8")).hexdigest()
        if digest != delivery.get("text_sha256"):
            raise RuntimeError("COURIER_PLAINTEXT_HASH_MISMATCH")
        OUTBOX.mkdir(parents=True,exist_ok=True)
        path=OUTBOX / (wr.safe_result_filename(aid).removesuffix(".json")+".txt")
        meta=path.with_suffix(".receipt.json")
        if meta.is_file():
            saved=json.loads(meta.read_text(encoding="utf-8"))
            if (saved.get("id")!=aid or saved.get("text_sha256")!=digest or
                    not re.fullmatch(r"NATIVE-RECEIPT-[0-9a-f]{32}",
                                     str(saved.get("receipt") or ""))):
                raise RuntimeError("COURIER_PLAINTEXT_RECEIPT_MISMATCH")
        elif path.is_file():
            raise RuntimeError("COURIER_ORPHANED_OUTBOX_DO_NOT_RESEND")
        else:
            saved={"id":aid,"text_sha256":digest,
                   "receipt":"NATIVE-RECEIPT-"+uuid.uuid4().hex}
            write_json(meta,saved)
        if path.is_file():
            if path.read_text(encoding="utf-8") != source:
                raise RuntimeError("COURIER_EXISTING_OUTBOX_MISMATCH")
        else:
            path.write_text(source,encoding="utf-8")
        return path,saved["receipt"]
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


def _verify_saved_receipt_binding(aid: str, receipt: str):
    """Exact saved-result binding; never infer delivery from a bare action ID."""
    if not wr.ID_RE.fullmatch(aid):
        raise RuntimeError("NATIVE_RECEIPT_ACK_ACTION_INVALID")
    if not re.fullmatch(r"NATIVE-RECEIPT-[0-9a-f]{32}", receipt):
        raise RuntimeError("NATIVE_RECEIPT_ACK_MARKER_INVALID")
    path = OUTBOX / (wr.safe_result_filename(aid).removesuffix(".json") + ".txt")
    if not path.is_file():
        raise RuntimeError("NATIVE_RECEIPT_ACK_OUTBOX_MISSING")
    sidecar = path.with_suffix(".receipt.json")
    if sidecar.is_file():
        try:
            row=json.loads(sidecar.read_text(encoding="utf-8"))
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
        except (OSError, ValueError) as exc:
            raise RuntimeError("NATIVE_RECEIPT_ACK_PLAINTEXT_INVALID") from exc
        if (row.get("id")!=aid or row.get("receipt")!=receipt
                or row.get("text_sha256")!=digest):
            raise RuntimeError("NATIVE_RECEIPT_ACK_PLAINTEXT_MISMATCH")
        return
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


def request_force_send(aid: str, foreground_hwnd: int) -> str:
    """Request ONE manual dispatch of a saved, still-eligible result.

    This does not open a second journal writer or execute an instruction.
    The running singleton verifies the saved phase and the exact previously
    focused foreground window before invoking the existing delivery owner.
    """
    if not isinstance(aid, str) or not wr.ID_RE.fullmatch(aid):
        raise ValueError("FORCE_SEND_ACTION_ID_INVALID")
    if type(foreground_hwnd) is not int or not (0 < foreground_hwnd <= 0xFFFFFFFFFFFFFFFF):
        raise ValueError("FORCE_SEND_WINDOW_INVALID")
    if not runner_active():
        raise RuntimeError("FORCE_SEND_REQUIRES_RUNNING_SINGLETON")
    cfg = configuration()
    if not cfg["armed"] or cfg["off"]:
        raise RuntimeError("FORCE_SEND_REQUIRES_ARMED_RUNNER")
    request_id = uuid.uuid4().hex
    FORCE_SEND_REQUESTS.mkdir(parents=True, exist_ok=True)
    write_json(FORCE_SEND_REQUESTS / (request_id + ".json"), {
        "id": request_id, "kind": "FORCE_SEND", "action_id": aid,
        "foreground_hwnd": foreground_hwnd, "expires_epoch": time.time() + 45.0,
    })
    note("NATIVE_FORCE_SEND=QUEUED", "REQUEST=" + request_id, "ACTION=" + aid)
    return request_id


def current_foreground_hwnd() -> int:
    """Read-only foreground identity, patchable for synthetic offline tests."""
    if os.name != "nt":
        return 0
    import ctypes
    ctypes.windll.user32.GetForegroundWindow.restype = ctypes.c_void_p
    return int(ctypes.windll.user32.GetForegroundWindow() or 0)


def reconcile_force_send_requests(state: wr.State) -> int:
    """The singleton consumes manual sends before normal automatic delivery.

    A request is claimed on disk before calling the sender, so a crash does
    not resurrect the mouse click. The durable outbound journal is the
    final authority on whether any message may be inserted or submitted.
    """
    if not FORCE_SEND_REQUESTS.is_dir():
        return 0
    processed = 0
    for path in sorted(FORCE_SEND_REQUESTS.glob("*.json")):
        claimed = path.with_suffix(".claimed")
        request_id = path.stem
        aid = ""
        outcome = "REJECTED"
        try:
            if path.is_symlink() or not re.fullmatch(r"[0-9a-f]{32}", request_id):
                raise ValueError("FORCE_SEND_REQUEST_INVALID_PATH")
            req = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(req, dict) or req.get("id") != request_id or req.get("kind") != "FORCE_SEND":
                raise ValueError("FORCE_SEND_REQUEST_INVALID")
            aid = req.get("action_id")
            hwnd = req.get("foreground_hwnd")
            deadline = req.get("expires_epoch")
            if not isinstance(aid, str) or not wr.ID_RE.fullmatch(aid):
                raise ValueError("FORCE_SEND_ACTION_ID_INVALID")
            if type(hwnd) is not int or hwnd <= 0 or type(deadline) not in (int, float):
                raise ValueError("FORCE_SEND_REQUEST_FIELDS_INVALID")
            # Atomic claim must precede all side effects; never replay a
            # claimed request after a process crash.
            path.replace(claimed)
            if time.time() > deadline:
                outcome = "EXPIRED_NO_SEND"
            elif stop_requested():
                outcome = "DISARMED_NO_SEND"
            else:
                foreground = current_foreground_hwnd()
                if foreground != hwnd:
                    outcome = "WINDOW_CHANGED_NO_SEND"
                else:
                    record = state.outbound_lookup(aid)
                    phase = record.get("phase") if isinstance(record, dict) else None
                    if not isinstance(record, dict) or record.get("has_attachments") is not False:
                        outcome = "NO_ELIGIBLE_RESULT"
                    elif phase == "READY" and not delivery_held(aid):
                        deliver(state, aid, manual=True)
                        outcome = str((state.outbound_lookup(aid) or {}).get("phase") or "UNKNOWN")
                        if outcome == "READY": outcome = "NO_TEXT_FIELD"
                        elif outcome == "SEND_PENDING": outcome = "SEND_NOT_AVAILABLE"
                    elif (phase == "SEND_PENDING"
                          and int(record.get("submit_only_attempt_count", 0) or 0) == 0):
                        recover_submit_only(state, aid, manual=True)
                        outcome = str((state.outbound_lookup(aid) or {}).get("phase") or "UNKNOWN")
                        if outcome == "READY": outcome = "NO_TEXT_FIELD"
                        elif outcome == "SEND_PENDING": outcome = "SEND_NOT_AVAILABLE"
                    else:
                        # ABORTED, SUBMITTED, TEXT_INSERTED, uncertain or held
                        # are NOT authorized by a Force Send click.
                        outcome = "NO_ELIGIBLE_RESULT"
            note("NATIVE_FORCE_SEND=" + outcome, "ACTION=" + aid, "REQUEST=" + request_id)
            processed += 1
        except (OSError, ValueError, RuntimeError, wr.RelayError) as exc:
            note("NATIVE_FORCE_SEND=REJECTED", "ERROR=" + type(exc).__name__,
                 "REQUEST=" + request_id)
        finally:
            if claimed.is_file():
                FORCE_SEND_RECEIPTS.mkdir(parents=True, exist_ok=True)
                write_json(FORCE_SEND_RECEIPTS / (request_id + ".json"), {
                    "id": request_id, "action_id": aid, "result": outcome,
                    "finished_utc": utc(),
                })
                claimed.unlink(missing_ok=True)
            elif path.is_file() and not path.is_symlink():
                # Invalid requests must not be retried every loop.
                path.rename(path.with_suffix(".rejected"))
    return processed


def request_force_clear_pending() -> str:
    """Queue an operator-confirmed reset for the running journal owner.

    This function writes only an inbox request, never a second State instance
    while the singleton is live. No result is executed or resent.
    """
    if not runner_active():
        raise RuntimeError("NATIVE_FORCE_CLEAR_RUNNER_NOT_ACTIVE")
    request_id = uuid.uuid4().hex
    FORCE_CLEAR_REQUESTS.mkdir(parents=True, exist_ok=True)
    request = FORCE_CLEAR_REQUESTS / (request_id + ".json")
    write_json(request, {"id": request_id, "kind": "FORCE_CLEAR_PENDING",
                         "created_utc": utc()})
    note("NATIVE_FORCE_CLEAR=QUEUED", "REQUEST=" + request_id)
    return request_id


def wait_force_clear_receipt(request_id: str, timeout: float = 12.0) -> dict:
    if not re.fullmatch(r"[0-9a-f]{32}", request_id):
        raise ValueError("invalid force-clear request ID")
    target = FORCE_CLEAR_RECEIPTS / (request_id + ".json")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if target.is_file():
            data = json.loads(target.read_text(encoding="utf-8"))
            if (data.get("id") != request_id or
                    data.get("result") != "FORCE_CLEAR_COMPLETE"):
                raise RuntimeError("NATIVE_FORCE_CLEAR_RECEIPT_INVALID")
            return data
        time.sleep(0.15)
    raise RuntimeError("NATIVE_FORCE_CLEAR_REQUEST_PENDING_UNCONFIRMED_" + request_id)


def reconcile_force_clear_requests(state: wr.State) -> int:
    """Single native runner owns all persisted delivery transitions."""
    if not FORCE_CLEAR_REQUESTS.is_dir():
        return 0
    completed = 0
    for path in sorted(FORCE_CLEAR_REQUESTS.glob("*.json")):
        try:
            if path.is_symlink():
                raise RuntimeError("NATIVE_FORCE_CLEAR_REQUEST_SYMLINK_REFUSED")
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise RuntimeError("NATIVE_FORCE_CLEAR_REQUEST_INVALID")
            request_id = data.get("id")
            if (not isinstance(request_id, str)
                    or not re.fullmatch(r"[0-9a-f]{32}", request_id)
                    or path.name != request_id + ".json"
                    or data.get("kind") != "FORCE_CLEAR_PENDING"):
                raise RuntimeError("NATIVE_FORCE_CLEAR_REQUEST_INVALID")
            receipt_path = FORCE_CLEAR_RECEIPTS / (request_id + ".json")
            if receipt_path.is_file():
                prior = json.loads(receipt_path.read_text(encoding="utf-8"))
                if prior.get("id") != request_id or prior.get("result") != "FORCE_CLEAR_COMPLETE":
                    raise RuntimeError("NATIVE_FORCE_CLEAR_RECEIPT_CONFLICT")
                path.unlink()
                continue
            holds = {}
            for aid,delivery in state.data.get("outbound_deliveries",{}).items():
                if not isinstance(delivery,dict):
                    continue
                if delivery.get("phase") not in {"READY","PRE_SUBMIT_FAILED","SUBMIT_UNCERTAIN","SEND_PENDING"}:
                    continue
                hold = delivery_hold_path(aid)
                if hold.is_file():
                    try:
                        record = json.loads(hold.read_text(encoding="utf-8"))
                        if isinstance(record,dict) and record.get("id") == aid:
                            holds[aid] = record
                    except (OSError,ValueError):
                        pass  # Preserve an unreadable hold on disk.
            affected = state.force_clear_unresolved_deliveries(request_id, holds)
            for aid in affected:
                # Executed results and journal entries remain untouched.
                # Hold evidence was copied into the terminal delivery record.
                hold = delivery_hold_path(aid)
                if aid in holds:
                    hold.unlink(missing_ok=True)
                delivery_force_clear_path(aid).unlink(missing_ok=True)
            remaining = sum(
                isinstance(d, dict) and d.get("phase") in
                {"READY","PRE_SUBMIT_FAILED","SUBMIT_UNCERTAIN","SEND_PENDING"}
                for d in state.data.get("outbound_deliveries",{}).values())
            receipt = {"id":request_id, "result":"FORCE_CLEAR_COMPLETE",
                       "aborted_ids":affected, "aborted_count":len(affected),
                       "unresolved_remaining":remaining,"finished_utc":utc()}
            write_json(receipt_path,receipt)
            path.unlink()
            status_update(phase="IDLE", last_result="FORCE_CLEAR_COMPLETE",
                          last_delivery_stage="OPERATOR_FORCE_CLEAR_PENDING",
                          delivery_blocked=False, last_delivery_error=None)
            note("NATIVE_FORCE_CLEAR=COMPLETE","REQUEST="+request_id,
                 "ABORTED="+str(len(affected)),"UNRESOLVED="+str(remaining))
            completed += 1
        except (RuntimeError, ValueError, OSError, wr.RelayError) as exc:
            note("NATIVE_FORCE_CLEAR=HELD",type(exc).__name__)
    return completed


def request_confirmed_receipt(aid: str, receipt: str):
    """Queue a known received result for the ACTIVE runner to reconcile.

    The CLI never opens its own writable State while the runner is active,
    never resends the result, and never clears the operator's composer.
    """
    _verify_saved_receipt_binding(aid, receipt)
    RECEIPT_REQUESTS.mkdir(parents=True, exist_ok=True)
    target = RECEIPT_REQUESTS / wr.safe_result_filename(aid)
    if target.is_file():
        current = json.loads(target.read_text(encoding="utf-8"))
        if current.get("id") != aid or current.get("receipt") != receipt:
            raise RuntimeError("NATIVE_RECEIPT_ACK_CONFLICTING_REQUEST")
        return "ALREADY_QUEUED"
    write_json(target, {"id": aid, "receipt": receipt, "queued_utc": utc()})
    note("NATIVE_RECEIPT_ACK=QUEUED", "ID=" + aid)
    return "QUEUED"


def reconcile_receipt_requests(state: wr.State):
    """Apply explicit operator-confirmed receipts using the runner's State."""
    if not RECEIPT_REQUESTS.is_dir():
        return 0
    completed = 0
    for path in sorted(RECEIPT_REQUESTS.glob("*.json")):
        try:
            if path.is_symlink():
                raise RuntimeError("NATIVE_RECEIPT_ACK_SYMLINK_REFUSED")
            request = json.loads(path.read_text(encoding="utf-8"))
            aid = request.get("id")
            receipt = request.get("receipt")
            if not isinstance(aid, str) or not isinstance(receipt, str):
                raise RuntimeError("NATIVE_RECEIPT_ACK_REQUEST_INVALID")
            if path.name != wr.safe_result_filename(aid):
                raise RuntimeError("NATIVE_RECEIPT_ACK_FILENAME_MISMATCH")
            _verify_saved_receipt_binding(aid, receipt)
            before = state.outbound_lookup(aid)
            if not before:
                raise RuntimeError("NATIVE_RECEIPT_ACK_DELIVERY_NOT_FOUND")
            if before.get("phase") == "SUBMITTED":
                prior = before.get("reconciled_receipt")
                if prior is not None and prior != receipt:
                    raise RuntimeError("NATIVE_RECEIPT_ACK_ALREADY_SUBMITTED_DIFFERENTLY")
                # Already submitted natively: receipt was accepted without an
                # operator reconciliation field. This request is idempotent.
            else:
                state.reconcile_outbound_receipt(aid, receipt)
            status_update(phase="IDLE", last_action=aid, last_result="SUBMITTED",
                          delivery_blocked=False, last_delivery_error=None,
                          last_delivery_stage="OPERATOR_RECEIPT_RECONCILED")
            path.unlink()
            note("NATIVE_RECEIPT_ACK=RECONCILED", "ID=" + aid)
            completed += 1
        except (OSError, ValueError, RuntimeError, wr.RelayError) as exc:
            # Preserve the request and saved evidence for investigation. The
            # problem must not prevent the runner from processing other work.
            note("NATIVE_RECEIPT_ACK_HELD=" + type(exc).__name__)
    return completed


def acknowledge_confirmed_receipt(aid: str, receipt: str):
    """Reconcile an already received native result; never send or execute.

    Require the operator to stop the singleton first.  This prevents a second
    State instance racing against the live runner's in-memory journal.
    Historical hold markers and saved result/outbox evidence are retained.
    """
    if runner_active() or not stop_requested():
        raise RuntimeError("NATIVE_RECEIPT_ACK_REQUIRES_STOPPED_DISARMED_RUNNER")
    _verify_saved_receipt_binding(aid, receipt)
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


def deliver(state: wr.State, aid: str, *, manual: bool = False):
    if stop_requested() or delivery_held(aid):
        return
    delivery = state.outbound_lookup(aid)
    if not delivery or delivery.get("phase") not in {"READY", "PRE_SUBMIT_FAILED"}:
        return
    if delivery.get("has_attachments") is not False:
        note("NATIVE_ATTACHMENT_RESULT_FILE_ONLY=" + aid)
        return
    if delivery_force_clear_path(aid).is_file():
        raise RuntimeError("LEGACY_CHATGPT_FORCE_DELIVERY_DISABLED")
    path, marker = outbox_result(state, aid)
    state.claim_outbound_delivery(aid)  # SUBMITTING persisted before click.
    note("NATIVE_DELIVERY_ATTEMPT=" + aid)
    status_update(phase="DELIVERING", last_action=aid)
    ps = shutil.which("powershell.exe")
    sender_script = FOREGROUND_SENDER
    cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-STA",
           "-File", str(sender_script), "-NativeResultPath", str(path),
           "-NativeActionId", aid, "-NativeReceiptMarker", marker]
    if delivery.get("wire_format") == "plain_text":
        cmd.append("-PlainText")
    if manual:
        cmd.append("-ManualForceSend")
    phase = "SUBMIT_UNCERTAIN"
    error_code = "SENDER_NO_RECEIPT"
    stage = "STARTING"
    try:
        response = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=70,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
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
        if (sender_script == FOREGROUND_SENDER
                and response.returncode == 0
                and "RESULT=FOREGROUND_NO_TARGET" in output):
            # No editor was touched; return the saved result to READY without
            # counting a delivery attempt or creating a hold.
            state.defer_outbound_delivery(aid)
            status_update(phase="AWAITING_TEXT_FIELD", last_action=aid,
                          last_result="READY", last_delivery_stage="NO_TARGET",
                          last_delivery_error=None)
            note("NATIVE_DELIVERY_WAITING_FOR_TEXT_FIELD=" + aid)
            return
        if response.returncode == 0 and "RESULT=HEARTBEAT_SUBMITTED" in output:
            phase = "SUBMITTED"
        elif (sender_script == FOREGROUND_SENDER
              and response.returncode == 0
              and "RESULT=TEXT_INSERTED_VERIFIED" in output):
            phase = "TEXT_INSERTED"
        elif (sender_script == FOREGROUND_SENDER
              and response.returncode == 0
              and "RESULT=CHAT_SEND_PENDING" in output):
            phase = "SEND_PENDING"
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
        pass
    # Persist the durable outbound phase before any native-only hold update.
    state.finish_outbound_delivery(aid, phase)
    state.record_outbound_sender_diagnostic(
        aid, stage, "" if phase in {"SUBMITTED", "TEXT_INSERTED"} else error_code)
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
        completed=phase in {"SUBMITTED", "TEXT_INSERTED"}
        # SEND_PENDING has a saved draft eligible for bounded send-only
        # recovery; it is not a blocked engine or a completed delivery.
        recoverable=phase == "SEND_PENDING"
        status_update(phase=("IDLE" if completed else "DELIVERY_UNCERTAIN"),
                      last_action=aid, last_result=phase,
                      delivery_blocked=not (completed or recoverable),
                      last_delivery_stage=stage,
                      last_delivery_error=(None if completed or recoverable else error_code))
    note("NATIVE_DELIVERY_PHASE=" + phase, "ID=" + aid)


def recover_submit_only(state: wr.State, aid: str, *, manual: bool = False):
    """At most one saved-draft Send click; never retry ambiguous submissions or EXEC."""
    if stop_requested():
        return
    record = state.outbound_lookup(aid)
    if (not record or record.get("phase") != "SEND_PENDING"
            or int(record.get("submit_only_attempt_count", 0) or 0) >= 1
            or record.get("has_attachments") is not False):
        return
    path, marker = outbox_result(state, aid)
    previous = state.claim_submit_only_retry(aid)
    status_update(phase="DELIVERING", last_action=aid,
                  last_delivery_stage="SUBMIT_ONLY_VERIFICATION")
    stage = "SUBMIT_ONLY_STARTING"
    output = ""
    code = -1
    try:
        ps = shutil.which("powershell.exe")
        if not ps:
            raise RuntimeError("SUBMIT_ONLY_POWERSHELL_UNAVAILABLE")
        cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-STA",
               "-File", str(FOREGROUND_SENDER), "-NativeResultPath", str(path),
               "-NativeActionId", aid, "-NativeReceiptMarker", marker,
               "-SubmitExistingOnly"]
        if record.get("wire_format") == "plain_text":
            cmd.append("-PlainText")
        if manual:
            cmd.append("-ManualForceSend")
        response = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=70,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        output = response.stdout
        code = response.returncode
        for line in output.splitlines():
            if line.startswith("SENDER_STAGE="):
                part = line.partition("=")[2]
                if re.fullmatch(r"[A-Z0-9_]{1,60}", part):
                    stage = part
        note("NATIVE_SUBMIT_ONLY_SENDER_STAGE=" + stage, "ID=" + aid)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        stage = "SUBMIT_ONLY_" + type(exc).__name__.upper()
        note("NATIVE_SUBMIT_ONLY_EXCEPTION=" + type(exc).__name__)
    submitted = code == 0 and "RESULT=HEARTBEAT_SUBMITTED" in output
    no_target = code == 0 and "RESULT=FOREGROUND_NO_TARGET" in output
    phase = "SUBMITTED" if submitted else "SUBMIT_UNCERTAIN"
    state.finish_submit_only_retry(aid, phase, no_target=no_target, stage=stage)
    if not no_target:
        state.record_outbound_sender_diagnostic(
            aid, stage, "" if submitted else "SUBMIT_ONLY_UNCONFIRMED")
    if no_target:
        status_update(phase="AWAITING_TEXT_FIELD", last_action=aid,
                      last_result=previous, delivery_blocked=False,
                      last_delivery_stage="SUBMIT_ONLY_NO_VERIFIED_DRAFT",
                      last_delivery_error=None)
        note("NATIVE_SUBMIT_ONLY_WAITING_FOR_OWN_DRAFT=" + aid)
        return
    if submitted:
        if "SENDER_STAGE=SUBMIT_ONLY_ALREADY_IN_TRANSCRIPT" in output:
            state.record_submit_only_evidence(
                aid, "UIA_EXISTING_TRANSCRIPT_RECEIPT")
        status_update(phase="IDLE", last_action=aid, last_result="SUBMITTED",
                      delivery_blocked=False, last_delivery_stage=stage,
                      last_delivery_error=None)
        note("NATIVE_SUBMIT_ONLY_SUBMITTED=" + aid)
    else:
        status_update(phase="DELIVERY_UNCERTAIN", last_action=aid,
                      last_result="SUBMIT_UNCERTAIN", delivery_blocked=True,
                      last_delivery_stage=stage,
                      last_delivery_error="SUBMIT_ONLY_UNCONFIRMED")
        note("NATIVE_SUBMIT_ONLY_UNCONFIRMED=" + aid,
             "ORIGIN=" + previous, "NO_EXECUTION_RETRY")


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
        note("NATIVE_UNIVERSAL_COMMAND_COURIER_V2")
        note("MODE=EXPLICIT_OUTPUT_GENERIC_FOREGROUND_NO_TRANSCRIPT_SCANNER")
        note("CMD_PYTHON_POWERSHELL_BASE64=SUPPORTED")
        note("PERSISTENT_ARM=" + str(configuration()["armed"]).upper())
        status_update(pid=os.getpid(), phase="IDLE")
        # Explicit local request files, not third-party UI transcripts,
        # are the only automatic source of new output.
        next_foreground_probe = 0.0
        next_submit_only_probe = 0.0
        # This worker has its own journal lock and does not use ChatGPT UIA.
        # Slow API responses cannot delay the scanner or other native actions.
        forward_activity = {"active": False}
        def forward_worker():
            while True:
                try:
                    policy = configuration()
                    if policy["off"]:
                        return
                    if policy["armed"] and policy["auto_send"]:
                        report = forwarder.tick(HOME, enabled=True)
                        forward_activity["active"] = report["active"]
                        if (report["forwarded"] or report["held"]
                                or report.get("route_errors")):
                            note("NATIVE_TEXT_ROUTED=" + str(report["forwarded"]),
                                 "TEXT_HELD=" + str(report["held"]),
                                 "SOURCE_ERRORS=" + str(report.get("route_errors", 0)))
                    else:
                        forward_activity["active"] = False
                except (forwarder.ForwardingError, OSError, ValueError) as exc:
                    forward_activity["active"] = False
                    note("NATIVE_TEXT_ROUTE_ERROR=" + type(exc).__name__,
                         str(exc)[:120])
                time.sleep(1)
        threading.Thread(target=forward_worker, name="command-courier-text-forwarder",
                         daemon=True).start()
        while not configuration()["off"]:
            # One journal owner reconciles confirmed receipts regardless of
            # whether ChatGPT is open. This never sends or reexecutes packets.
            reconcile_receipt_requests(state)
            # Manual FORCE CLEAR is applied by the same journal owner before
            # scanning new instructions or claiming any outbound delivery.
            reconcile_force_clear_requests(state)
            # Manual FORCE SEND consumes one receipt-bound queued result and
            # works independently of Auto Send, without any EXEC replay.
            reconcile_force_send_requests(state)
            # Send-only retry of a saved chat draft, never a command replay.
            policy = configuration()
            if (policy["armed"] and policy["auto_send"] and not stop_requested()
                    and time.monotonic() >= next_submit_only_probe):
                next_submit_only_probe = time.monotonic() + 5.0
                try:
                    candidates = state.list_claimable_submit_retries()
                    if candidates:
                        recover_submit_only(state, candidates[0])
                except (RuntimeError, ValueError, wr.RelayError, OSError) as exc:
                    note("NATIVE_SUBMIT_ONLY_LOOP_ERROR=" + type(exc).__name__,
                         str(exc)[:120])
            # Deliver the saved output into the verified foreground app.
            policy = configuration()
            if (policy["armed"] and policy["auto_send"] and not stop_requested()
                    and time.monotonic() >= next_foreground_probe):
                next_foreground_probe = time.monotonic() + 2.0
                try:
                    for aid in state.list_claimable_outbound_ids():
                        if delivery_held(aid):
                            continue
                        deliver(state, aid)
                        break  # one foreground result per polling interval
                except (RuntimeError, ValueError, wr.RelayError, OSError) as exc:
                    note("NATIVE_FOREGROUND_DELIVERY_ERROR=" + type(exc).__name__,
                         str(exc)[:120])
            runner_stage = "QUEUING_EXPLICIT_OUTPUT"
            try:
                cfg=configuration()
                if state.armed != cfg["armed"]:
                    state.set_armed(cfg["armed"])
                if cfg["armed"] and not stop_requested():
                    reconcile_explicit_output_requests(state)
                if not cfg["armed"]:
                    display_phase="DISARMED"
                else:
                    prior=json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
                    display_phase=("AWAITING_TEXT_FIELD"
                                   if prior.get("phase")=="AWAITING_TEXT_FIELD"
                                   else "DELIVERY_BLOCKED" if prior.get("delivery_blocked")
                                   and prior.get("last_result")=="PRE_SUBMIT_FAILED"
                                   else "DELIVERY_UNCERTAIN" if prior.get("delivery_blocked")
                                   else "IDLE")
                status_update(pid=os.getpid(),phase=display_phase,
                              runner_error_type=None,runner_error_stage=None)
            except (OSError,ValueError,RuntimeError,wr.RelayError) as exc:
                note("COURIER_OUTPUT_INTAKE_ERROR="+type(exc).__name__)
                status_update(pid=os.getpid(),phase="ERROR",
                              runner_error_type=type(exc).__name__,
                              runner_error_stage=runner_stage)
            time.sleep(1)
        status_update(pid=None, phase="OFF")
        note("NATIVE_RELAY_OFF")
    return 0


HUD_MODE = HOME / 'hud-mode.json'

def select_original_hud():
    """Route the existing top-right hud.py to this desktop transport."""
    write_json(HUD_MODE, {'version': 1, 'transport': 'native-foreground'})
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
                                 "acknowledge-receipt", "queue-confirmed-receipt",
                                 "queue-force-clear-pending",
                                 "queue-output-file","queue-output-clipboard"))
    parser.add_argument("action_id", nargs="?")
    parser.add_argument("receipt", nargs="?")
    parser.add_argument("--file", dest="output_file", default=None)
    parser.add_argument("--id", dest="output_id", default=None)

    args = parser.parse_args()
    if args.command == "run":
        return runner()
    if args.command == "queue-output-file":
        if not args.output_file:
            raise SystemExit("queue-output-file requires --file PATH")
        queue_output_file(args.output_file,aid=args.output_id)
        return 0
    if args.command == "queue-output-clipboard":
        import tkinter as tk
        root=tk.Tk()
        root.withdraw()
        try:
            copied=root.clipboard_get()
        finally:
            root.destroy()
        queue_explicit_output(copied,source="explicit-clipboard",
                              aid=args.output_id)
        return 0
    if args.command == "acknowledge-receipt":
        if not args.action_id or not args.receipt:
            raise SystemExit("acknowledge-receipt requires action ID and confirmed receipt")
        acknowledge_confirmed_receipt(args.action_id, args.receipt)
        return 0
    if args.command == "queue-confirmed-receipt":
        if not args.action_id or not args.receipt:
            raise SystemExit("queue-confirmed-receipt requires action ID and received result nonce")
        request_confirmed_receipt(args.action_id, args.receipt)
        return 0
    if args.command == "queue-force-clear-pending":
        request_force_clear_pending()
        return 0
    if args.command == "retry-delivery":
        if not args.action_id:
            raise SystemExit("retry-delivery requires an action ID")
        release_failed_delivery(wr.State(STATE), args.action_id)
        return 0
    if args.command == "force-delivery":
        raise SystemExit("LEGACY_CHATGPT_FORCE_RESEND_DISABLED_USE_HUD_FORCE_SEND")
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
