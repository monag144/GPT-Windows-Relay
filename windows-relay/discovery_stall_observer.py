#!/usr/bin/env python3
"""Independent Windows watchdog observer for a stuck Firefox action discovery.

Read-only: never replays packets, refreshes Firefox, changes operator state,
or touches the relay state.json. State for deduplicating alerts is separate.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys


ACTION_ID = re.compile(r"^PCE\d+\.\d{3}$", re.IGNORECASE)
EXECUTION_EVENTS = frozenset({
    "relay_action_execution_requested",
    "action_received",
    "action_result",
    "relay_result_delivery_complete",
})
DISCOVERY_EVENT = "relay_packet_discovered"
STALL_SECONDS = 45


def date(value: str) -> datetime | None:
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result if result.tzinfo else None
    except (ValueError, TypeError):
        return None


def latest_unexecuted_discovery(events: list[dict], state: dict, now: datetime,
                                timeout: int = STALL_SECONDS) -> dict | None:
    """Return a stale packet only if backend/transport have no execution proof."""
    latest = None
    for event in events:
        if not isinstance(event, dict):
            continue
        details = event.get("detail")
        details = details if isinstance(details, dict) else {}
        ident = details.get("packet_id")
        stamp = date(event.get("time"))
        if (event.get("event") == DISCOVERY_EVENT and isinstance(ident, str)
                and ACTION_ID.fullmatch(ident) and stamp):
            if latest is None or stamp >= latest["at"]:
                latest = {"id": ident, "at": stamp}
    if latest is None:
        return None
    elapsed = (now - latest["at"]).total_seconds()
    if elapsed < timeout:
        return None
    ident = latest["id"]
    active = state.get("active_action")
    if isinstance(active, dict) and active.get("id") == ident:
        return None
    processed = state.get("processed") or {}
    if isinstance(processed, dict) and isinstance(processed.get(ident), dict):
        return None
    for event in events:
        if not isinstance(event, dict):
            continue
        details = event.get("detail")
        details = details if isinstance(details, dict) else {}
        if details.get("packet_id") != ident:
            continue
        stamp = date(event.get("time"))
        if stamp and stamp >= latest["at"] and event.get("event") in EXECUTION_EVENTS:
            return None
    return {
        "id": ident,
        "age_seconds": int(max(0, elapsed)),
        "at": latest["at"].isoformat(),
        "classification": "DISCOVERY_STALLED_BEFORE_BACKEND_EXECUTION",
        "replay_allowed": False,
    }


def load_recent_events(path: Path, limit: int = 2500) -> list[dict]:
    if not path.is_file():
        return []
    # Bounded to 5MB. The operational event journal may be large.
    with path.open("rb") as fh:
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        fh.seek(max(0, size - 5_000_000))
        text = fh.read().decode("utf-8", errors="replace")
    rows = []
    for line in text.splitlines()[-limit:]:
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


def poll(base: Path, now: datetime | None = None) -> dict:
    state_path = base / "state.json"
    events_path = base / "browser-events.jsonl"
    if not state_path.is_file():
        return {"state": "UNKNOWN", "reason": "backend_state_missing"}
    try:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError):
        return {"state": "UNKNOWN", "reason": "backend_state_unreadable"}
    if state.get("armed") is not True:
        return {"state": "PAUSED", "reason": "operator_not_armed"}
    stale = latest_unexecuted_discovery(load_recent_events(events_path),
                                        state, now or datetime.now(timezone.utc))
    if stale is None:
        return {"state": "HEALTHY_OR_UNPROVEN"}
    return {"state": "DISCOVERY_STALLED", **stale}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--latch", type=Path, required=True)
    args = parser.parse_args(argv)
    observed = poll(args.base)
    if observed["state"] != "DISCOVERY_STALLED":
        # A non-stalled observation never auto-clears a prior alert: its root
        # failure is still pending until a newer completed action is proven.
        return 0
    latch = args.latch
    signature = observed["id"] + "|" + observed["at"]
    if latch.is_file():
        try:
            prior = json.loads(latch.read_text(encoding="utf-8-sig"))
            if prior.get("signature") == signature:
                return 0
        except (ValueError, OSError):
            pass
    latch.parent.mkdir(parents=True, exist_ok=True)
    tmp = latch.with_suffix(".tmp")
    tmp.write_text(json.dumps({"signature": signature, **observed}, indent=2),
                   encoding="utf-8")
    os.replace(tmp, latch)
    print("DISCOVERY_STALLED packet_id=" + observed["id"] +
          " age_seconds=" + str(observed["age_seconds"]) +
          " replay_allowed=False", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
