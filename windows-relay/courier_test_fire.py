#!/usr/bin/env python3
"""Temporary Command Courier TEST FIRE against a configured file destination.

This test injects a unique text body into the selected input directory and
requires the independently running forwarder to deliver it. This module
NEVER calls forwarder.tick(), executes code, invokes ChatGPT UIA or posts to
an external endpoint. A PASS requires a real, matching destination file AND
a durable DELIVERED journal receipt.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time
import uuid

import courier_forwarder as forwarding


class TestFireError(RuntimeError):
    pass


def _select_route(home: Path, route_id: str | None):
    routes = forwarding.load_routes(home)
    files = [route for route in routes if route["destination"]["type"] == "directory"]
    if route_id:
        matching = [route for route in files if route["id"] == route_id]
        if len(matching) != 1:
            raise TestFireError("TEST_FIRE_ROUTE_NOT_ENABLED_DIRECTORY")
        return matching[0]
    preferred = [route for route in files if route["id"] == "local-test"]
    if preferred:
        return preferred[0]
    if len(files) == 1:
        return files[0]
    if not files:
        raise TestFireError("TEST_FIRE_NO_DIRECTORY_ROUTE_CONFIGURED")
    raise TestFireError("TEST_FIRE_ROUTE_SELECTION_REQUIRED")


def fire(home: Path, native: dict, *, route_id: str | None = None,
         timeout: float = 12.0, sleep=time.sleep) -> dict:
    """Send a unique synthetic file packet through the real running relay."""
    nonce = uuid.uuid4().hex
    route = _select_route(home, route_id)
    body = ("COURIER_TEST_FIRE_V1\nroute=" + route["id"] +
            "\nnonce=" + nonce + "\n").encode("utf-8")
    return _submit_and_verify(home, native, route, body, nonce=nonce,
                              filename_prefix="courier-test-fire",
                              timeout=timeout, sleep=sleep)


def send_copied_text(home: Path, native: dict, text: str, *,
                     route_id: str | None = None,
                     timeout: float = 12.0, sleep=time.sleep) -> dict:
    """Forward only text explicitly copied by the operator; never execute it."""
    if not isinstance(text, str) or not text:
        raise TestFireError("COPY_TEXT_EMPTY_CLIPBOARD")
    try:
        body = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise TestFireError("COPY_TEXT_ENCODING_INVALID") from exc
    if len(body) > forwarding.MAX_TEXT_BYTES:
        raise TestFireError("COPY_TEXT_EXCEEDS_ROUTE_LIMIT")
    route = _select_route(home, route_id)
    return _submit_and_verify(home, native, route, body,
                              nonce=uuid.uuid4().hex,
                              filename_prefix="courier-copied-text",
                              timeout=timeout, sleep=sleep)


def _submit_and_verify(home: Path, native: dict, route: dict,
                       body: bytes, *, nonce: str, filename_prefix: str,
                       timeout: float, sleep) -> dict:
    """Drop a complete UTF-8 file and verify the real worker's receipt.

    This method does NOT call forwarder.tick and cannot dispatch a packet
    itself. The native singleton must be running with Auto Send enabled.
    """
    if not (native.get("native_running") and native.get("native_armed")
            and native.get("auto_send") and not native.get("native_off")):
        raise TestFireError("TEST_FIRE_REQUIRES_RUNNING_ARMED_AUTO_SEND")
    source = route["source"]
    target_folder = route["destination"]["path"]
    if not source.is_dir() or source.is_symlink():
        raise TestFireError("TEST_FIRE_SOURCE_UNAVAILABLE")

    name = filename_prefix + "-" + nonce + ".txt"
    source_file = source / name
    key = forwarding._delivery_key(route, name, body)
    target_file = target_folder / (route["id"] + "-" + key + ".txt")
    # Atomic file drop: no partial body can be observed by the native worker.
    fd, temporary = tempfile.mkstemp(
        prefix="." + filename_prefix + "-", suffix=".tmp", dir=source
    )
    try:
        with os.fdopen(fd, "wb") as writer:
            writer.write(body)
            writer.flush()
            os.fsync(writer.fileno())
        if source_file.exists():
            raise TestFireError("TEST_FIRE_FILENAME_COLLISION")
        os.replace(temporary, source_file)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    end = time.monotonic() + timeout
    while time.monotonic() < end:
        ledger = forwarding._ledger(home)["deliveries"]
        record = ledger.get(key)
        phase = record.get("phase") if isinstance(record, dict) else None
        if phase == "DELIVERED":
            if record.get("route") != route["id"] or record.get("file") != name:
                raise TestFireError("TEST_FIRE_RECEIPT_IDENTITY_MISMATCH")
            if record.get("receipt") not in {"FILE_WRITTEN", "FILE_ALREADY_MATCHES"}:
                raise TestFireError("TEST_FIRE_RECEIPT_NOT_VERIFIED")
            if not target_file.is_file() or target_file.is_symlink():
                raise TestFireError("TEST_FIRE_RECEIPT_WITHOUT_DESTINATION_FILE")
            if target_file.read_bytes() != body:
                raise TestFireError("TEST_FIRE_DESTINATION_BODY_MISMATCH")
            return {"result": "PASS", "route": route["id"],
                    "receipt": record.get("receipt"), "nonce": nonce,
                    "bytes": len(body), "destination_file": str(target_file),
                    "source_file": str(source_file)}
        if phase == "HELD":
            raise TestFireError("TEST_FIRE_ROUTE_HELD")
        if phase not in (None, "SUBMITTING"):
            raise TestFireError("TEST_FIRE_UNEXPECTED_JOURNAL_PHASE")
        sleep(0.2)
    raise TestFireError("TEST_FIRE_TIMEOUT_NO_VERIFIED_DELIVERY")
