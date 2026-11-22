#!/usr/bin/env python3
"""Explicit-source, transport-neutral text forwarding for Command Courier.

No execution, screen scraping, ChatGPT UI Automation, or editor-clearing.
An operator-selected input directory contains UTF-8 .txt files; each new
file body is copied exactly to a selected directory or HTTPS/API endpoint.
The journal is independent of native command/result delivery holds.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error, parse
import hashlib
import json
import os
import re
import tempfile

import windows_relay as wr

MAX_TEXT_BYTES = 131_072
MAX_ROUTES = 12
MAX_FILES_PER_TICK = 32
ROUTE_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,79}$")


class ForwardingError(RuntimeError):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ForwardingError("FORWARDING_JOURNAL_OR_CONFIG_UNREADABLE") from exc


def _abs_directory(value, name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ForwardingError(name + "_PATH_REQUIRED")
    path = Path(os.path.expandvars(value)).expanduser()
    if not path.is_absolute():
        raise ForwardingError(name + "_PATH_MUST_BE_ABSOLUTE")
    return path.resolve()


def _url(value):
    if not isinstance(value, str):
        raise ForwardingError("HTTP_URL_REQUIRED")
    parsed = parse.urlsplit(value)
    if parsed.username or parsed.password or parsed.fragment or not parsed.hostname:
        raise ForwardingError("HTTP_URL_UNSAFE")
    # HTTPS for external services; plain HTTP allowed only for explicitly
    # configured loopback integrations on the same machine.
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname.lower()
        in {"localhost", "127.0.0.1", "::1"}
    ):
        raise ForwardingError("HTTP_HTTPS_REQUIRED_OUTSIDE_LOOPBACK")
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ForwardingError("HTTP_INVALID_PORT")
    return value


def load_routes(home: Path) -> list[dict]:
    return _validated_routes(_json(home / "courier-forwarding.json", None))


def _validated_routes(config) -> list[dict]:
    if config is None:
        return []
    if not isinstance(config, dict) or config.get("version") != 1 \
            or type(config.get("enabled")) is not bool \
            or not isinstance(config.get("routes"), list):
        raise ForwardingError("FORWARDING_CONFIG_INVALID")
    if not config["enabled"]:
        return []
    if len(config["routes"]) > MAX_ROUTES:
        raise ForwardingError("FORWARDING_TOO_MANY_ROUTES")

    routes = []
    ids = set()
    for obj in config["routes"]:
        if (not isinstance(obj, dict) or not isinstance(obj.get("id"), str)
                or not ROUTE_ID.fullmatch(obj["id"])):
            raise ForwardingError("FORWARDING_ROUTE_ID_INVALID")
        rid = obj["id"]
        if rid in ids:
            raise ForwardingError("FORWARDING_DUPLICATE_ROUTE_ID")
        ids.add(rid)
        if type(obj.get("enabled", True)) is not bool:
            raise ForwardingError("FORWARDING_ROUTE_ENABLED_INVALID")
        if not obj.get("enabled", True):
            continue
        source = obj.get("source")
        destination = obj.get("destination")
        if not isinstance(source, dict) or source.get("type") != "directory":
            raise ForwardingError("FORWARDING_SOURCE_DIRECTORY_REQUIRED")
        if not isinstance(destination, dict):
            raise ForwardingError("FORWARDING_DESTINATION_REQUIRED")
        src = _abs_directory(source.get("path"), "SOURCE")
        if destination.get("type") == "directory":
            dest = _abs_directory(destination.get("path"), "DESTINATION")
            target = {"type": "directory", "path": dest}
        elif destination.get("type") == "http":
            url = _url(destination.get("url"))
            token = destination.get("bearer_token_env")
            if token is not None and (
                not isinstance(token, str) or not ENV_NAME.fullmatch(token)
            ):
                raise ForwardingError("HTTP_TOKEN_ENV_INVALID")
            target = {"type": "http", "url": url, "bearer_token_env": token}
        else:
            raise ForwardingError("FORWARDING_DESTINATION_TYPE_INVALID")
        routes.append({"id": rid, "source": src, "destination": target})

    # A destination in any watched source tree risks recursive forwarding.
    # Reject that configuration before touching an input file.
    sources = [r["source"] for r in routes]
    for route in routes:
        target = route["destination"]
        if target["type"] == "directory":
            dest = target["path"]
            if any(dest == src or src in dest.parents for src in sources):
                raise ForwardingError("FORWARDING_OUTPUT_INSIDE_WATCHED_SOURCE")
    return routes


def _delivery_key(route: dict, filename: str, body: bytes) -> str:
    # A new source or target creates a different delivery identity. Reusing
    # a route name must not silently redirect already queued messages.
    dest = route["destination"]
    target = str(dest.get("path") if dest["type"] == "directory" else dest["url"])
    context = (route["id"] + "\0" + str(route["source"]) + "\0" +
               dest["type"] + "\0" + target + "\0" + filename + "\0")
    return hashlib.sha256(context.encode("utf-8") + body).hexdigest()


def _baseline_existing_inputs(home: Path, route: dict):
    """Never auto-forward historical input that predated route selection."""
    source = route["source"]
    if not source.is_dir():
        return
    ledger = _ledger(home)
    changed = False
    for entry in source.iterdir():
        if not entry.is_file() or entry.is_symlink() or entry.suffix.lower() != ".txt":
            continue
        st = entry.stat()
        if st.st_size > MAX_TEXT_BYTES:
            continue
        body = entry.read_bytes()
        if not body or len(body) > MAX_TEXT_BYTES:
            continue
        try:
            body.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            continue
        key = _delivery_key(route, entry.name, body)
        if key not in ledger["deliveries"]:
            ledger["deliveries"][key] = {
                "route": route["id"], "file": entry.name,
                "phase": "BASELINED", "created_utc": timestamp(),
            }
            changed = True
    if changed:
        _persist(home, ledger)


def configure_route(home: Path, route_id: str, source: str,
                    destination_type: str, value: str,
                    *, bearer_token_env: str | None = None):
    """Explicit operator action; replaces one named route atomically."""
    current = _json(home / "courier-forwarding.json", None)
    if current is None:
        current = {"version": 1, "enabled": True, "routes": []}
    if not isinstance(current, dict) or current.get("version") != 1 \
            or not isinstance(current.get("routes"), list):
        raise ForwardingError("FORWARDING_CONFIG_INVALID")
    dest = ({"type": "directory", "path": value}
            if destination_type == "directory" else
            {"type": "http", "url": value})
    if destination_type not in {"directory", "http"}:
        raise ForwardingError("FORWARDING_DESTINATION_TYPE_INVALID")
    if bearer_token_env is not None:
        if destination_type != "http":
            raise ForwardingError("HTTP_TOKEN_ONLY_FOR_HTTP")
        dest["bearer_token_env"] = bearer_token_env
    route = {"id": route_id,
             "source": {"type": "directory", "path": source},
             "destination": dest}
    current["routes"] = [
        existing for existing in current["routes"]
        if isinstance(existing, dict) and existing.get("id") != route_id
    ] + [route]
    current["enabled"] = True
    routes = _validated_routes(current)
    # Baseline existing files for the newly selected route BEFORE publishing
    # the config; the runner must never accidentally forward a historical
    # result when the operator enables a new destination.
    selected = next(route for route in routes if route["id"] == route_id)
    _baseline_existing_inputs(home, selected)
    home.mkdir(parents=True, exist_ok=True)
    wr.atomic_json(home / "courier-forwarding.json", current)


def set_enabled(home: Path, value: bool):
    current = _json(home / "courier-forwarding.json", None)
    if current is None:
        raise ForwardingError("FORWARDING_NOT_CONFIGURED")
    if not isinstance(current, dict):
        raise ForwardingError("FORWARDING_CONFIG_INVALID")
    if value:
        current["enabled"] = True
        _validated_routes(current)
    else:
        current["enabled"] = False
    wr.atomic_json(home / "courier-forwarding.json", current)


def _ledger(home: Path):
    state = _json(home / "courier-forwarding-state.json", None)
    if state is None:
        return {"version": 1, "deliveries": {}}
    if not isinstance(state, dict) or state.get("version") != 1 \
            or not isinstance(state.get("deliveries"), dict):
        raise ForwardingError("FORWARDING_LEDGER_INVALID")
    return state


def _persist(home: Path, state):
    home.mkdir(parents=True, exist_ok=True)
    wr.atomic_json(home / "courier-forwarding-state.json", state)


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _dispatch(route: dict, body: bytes, key: str):
    destination = route["destination"]
    if destination["type"] == "directory":
        folder = destination["path"]
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / (route["id"] + "-" + key + ".txt")
        if target.exists():
            if target.is_symlink() or target.read_bytes() != body:
                raise ForwardingError("FORWARDING_DESTINATION_COLLISION")
            return "FILE_ALREADY_MATCHES"
        fd, temporary = tempfile.mkstemp(prefix=".courier-", suffix=".tmp", dir=folder)
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(body)
                out.flush()
                os.fsync(out.fileno())
            if target.exists():
                if target.is_symlink() or target.read_bytes() != body:
                    raise ForwardingError("FORWARDING_DESTINATION_COLLISION")
            else:
                os.replace(temporary, target)
            return "FILE_WRITTEN"
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    token_env = destination.get("bearer_token_env")
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "X-Command-Courier-Idempotency-Key": key,
    }
    if token_env:
        token = os.environ.get(token_env, "")
        if not token:
            raise ForwardingError("HTTP_TOKEN_ENV_MISSING")
        headers["Authorization"] = "Bearer " + token
    outbound = request.Request(
        destination["url"], body, headers=headers, method="POST"
    )
    # Redirects are never followed: they might leak text or credentials to
    # an endpoint that the operator did not select.
    with request.build_opener(_NoRedirect()).open(outbound, timeout=8) as reply:
        status = int(reply.status)
        if not 200 <= status < 300:
            raise ForwardingError("HTTP_DESTINATION_NOT_ACKNOWLEDGED")
        return "HTTP_" + str(status)


def tick(home: Path, *, enabled: bool) -> dict:
    """Process a bounded batch; never depend on ChatGPT composer availability.

    Every body is forwarded once per route, filename and content hash. A
    failed/uncertain attempt remains HELD and cannot auto-retry blindly.
    """
    if not enabled:
        return {"active": False, "forwarded": 0, "held": 0}
    routes = load_routes(home)
    if not routes:
        return {"active": False, "forwarded": 0, "held": 0}
    state = _ledger(home)
    forwarded = 0
    held = 0
    remaining = MAX_FILES_PER_TICK
    for route in routes:
        source = route["source"]
        if not source.is_dir() or source.is_symlink():
            raise ForwardingError("FORWARDING_SOURCE_UNAVAILABLE")
        for entry in sorted(source.iterdir(), key=lambda p: p.name):
            if remaining <= 0:
                break
            if entry.suffix.lower() != ".txt" or not entry.is_file() or entry.is_symlink():
                continue
            # Never spend the per-tick *new delivery* budget on already
            # forwarded files; that would starve newer files as the folder grows.
            # Oversized and binary files are ignored rather than truncated.
            before = entry.stat()
            if before.st_size > MAX_TEXT_BYTES:
                continue
            body = entry.read_bytes()
            after = entry.stat()
            # Prefer atomic source-file drops. Skip concurrent writers rather
            # than forwarding a truncated/in-flight text body.
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                continue
            if not body or len(body) > MAX_TEXT_BYTES:
                continue
            try:
                body.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                continue
            key = _delivery_key(route, entry.name, body)
            record = state["deliveries"].get(key)
            if record is not None:
                if not isinstance(record, dict):
                    raise ForwardingError("FORWARDING_LEDGER_ENTRY_INVALID")
                continue  # DELIVERED, HELD, or interrupted attempt: no replay.
            remaining -= 1
            state["deliveries"][key] = {
                "route": route["id"], "file": entry.name,
                "phase": "SUBMITTING", "created_utc": timestamp(),
            }
            _persist(home, state)  # Admission journal precedes any side effect.
            try:
                receipt = _dispatch(route, body, key)
            except (OSError, error.URLError, error.HTTPError, ForwardingError) as exc:
                state["deliveries"][key].update(
                    phase="HELD", updated_utc=timestamp(),
                    error=type(exc).__name__
                )
                _persist(home, state)
                held += 1
            else:
                state["deliveries"][key].update(
                    phase="DELIVERED", updated_utc=timestamp(), receipt=receipt
                )
                _persist(home, state)
                forwarded += 1
    return {"active": True, "forwarded": forwarded, "held": held}


def status(home: Path) -> dict:
    config = _json(home / "courier-forwarding.json", None)
    routes = load_routes(home)
    state = _ledger(home)
    deliveries = state["deliveries"]
    return {
        "enabled": bool(config and config.get("enabled")),
        "routes": len(routes),
        "configured_routes": len(config.get("routes", [])) if isinstance(config, dict) else 0,
        "delivered": sum(1 for x in deliveries.values() if x.get("phase") == "DELIVERED"),
        "held": sum(1 for x in deliveries.values() if x.get("phase") in {"HELD", "SUBMITTING"}),
        "baselined": sum(1 for x in deliveries.values() if x.get("phase") == "BASELINED"),
    }
