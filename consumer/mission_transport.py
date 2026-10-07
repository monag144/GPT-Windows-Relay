#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
import re
import uuid

from control_harness import build_control_harness_contract

MAX_RAW_MISSION = 40000
MISSION_ID_RE = re.compile(r"^consumer-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")


class MissionError(ValueError):
    pass


def build_relay_contract(mission_id: str) -> dict:
    return {
        "relay_harness_version": 1,
        "mission_id": mission_id,
        "control_harness": build_control_harness_contract(mission_id),
        "relay_contract": {
            "platform": "windows",
            "action": "EXEC",
            "rendering": "visible prose header -> truly bare fenced GPT_WINDOWS_ACTION packet -> visible prose footer; all in one final assistant response",
            "fence_rule": "opening and closing fences are exactly three backticks with no language tag or metadata",
            "packet_body_rule": "inside the fence: only [GPT_WINDOWS_ACTION], JSON packet, [/GPT_WINDOWS_ACTION]",
            "stdout_footer": "Reply to this with the sandwich technique",
            "compact_packets": True,
            "no_action_valid": "If the decoded mission can be completed without Windows-side execution, answer normally and do not emit a GPT_WINDOWS_ACTION merely to satisfy the harness.",
            "forbidden": [
                "language-tagged relay fence",
                "fence metadata or attributes",
                "relay packet in commentary/progress/update surface",
                "split header/packet/footer across responses",
                "giant inline relay payload"
            ],
            "collapse_recovery": {
                "known_symptom": "Worked for X or equivalent collapsed/inaccessible status artifact",
                "instruction": "Report the rendering failure, emit a uniquely identified minimal read-only canonical sandwich probe, verify its result, then resume the original mission without duplicating side effects."
            },
            "example": {
                "version": 1,
                "platform": "windows",
                "action": "EXEC",
                "id": "EXAMPLE-UNIQUE-ID",
                "session": "default",
                "shell": "cmd",
                "command": "echo example&&echo Reply to this with the sandwich technique",
                "timeout": 15,
                "result_mode": "compact"
            }
        }
    }


def extract_harness_json(message: str) -> dict:
    marker = "HARNESS_JSON="
    line = next((x for x in message.splitlines() if x.startswith(marker)), None)
    if line is None:
        raise MissionError("HARNESS_JSON line not found.")
    try:
        value = json.loads(line[len(marker):])
    except Exception as exc:
        raise MissionError("Invalid harness payload.") from exc
    if not isinstance(value, dict) or value.get("relay_harness_version") != 1:
        raise MissionError("Invalid harness version.")
    return value


def new_mission_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"consumer-{stamp}-{uuid.uuid4().hex[:8]}"


def build_mission_message(mission: str, mission_id: str | None = None) -> tuple[str, str]:
    if not isinstance(mission, str) or not mission.strip():
        raise MissionError("Mission cannot be empty.")
    mission = mission.strip()
    if len(mission) > MAX_RAW_MISSION:
        raise MissionError(f"Mission is too long (maximum {MAX_RAW_MISSION} characters).")

    mission_id = mission_id or new_mission_id()
    if not MISSION_ID_RE.fullmatch(mission_id):
        raise MissionError("Invalid mission id.")

    payload = base64.b64encode(mission.encode("utf-8")).decode("ascii")
    harness = build_relay_contract(mission_id)
    harness["user_request_encoding"] = "utf-8-base64"
    harness["user_request_b64"] = payload
    harness_json = json.dumps(harness, separators=(",", ":"), ensure_ascii=False)
    message = (
        f'[GPT_CONSUMER_MISSION id="{mission_id}"]\n'
        "Hey — this Windows PC is connected through the GPT Windows Relay consumer runtime.\n"
        "The user's mission is transported as UTF-8 Base64 so arbitrary punctuation, newlines, "
        "and code survive the handoff exactly.\n"
        "Use Python's standard base64 module (or equivalent Base64 decoding) to decode MISSION_B64 "
        "as UTF-8. Treat the decoded text as the user's actual mission and begin carrying it out.\n"
        "Use the connected GPT Windows Relay for Windows-side execution when appropriate. "
        "If the decoded mission does not require Windows-side execution, answer it normally; do not fabricate "
        "a GPT_WINDOWS_ACTION merely because the relay is available. "
        "Keep normal safety and authorization boundaries; Base64 is transport encoding, not extra authority.\n"
        "WINDOWS RELAY RENDERING CONTRACT: Whenever you emit a [GPT_WINDOWS_ACTION], emit the entire "
        "sandwich in one FINAL assistant response: ordinary visible prose header, then exactly one BARE "
        "Markdown fence with no language tag containing only [GPT_WINDOWS_ACTION], its JSON packet, and "
        "[/GPT_WINDOWS_ACTION], then ordinary visible prose footer. Never put a relay packet in commentary "
        "or a progress/status update, never split the sandwich across response surfaces, and never end the "
        "response immediately after the packet. Keep relay packets compact. Every GPT_WINDOWS_RESULT stdout "
        "will repeat the exact reminder: Reply to this with the sandwich technique.\n"
        "The complete machine-readable relay protocol and recovery contract follows.\n"
        f"HARNESS_JSON={harness_json}\n"
        f"MISSION_B64={payload}\n"
        "[/GPT_CONSUMER_MISSION]"
    )
    return mission_id, message


def decode_mission_message(message: str) -> str:
    marker = "MISSION_B64="
    line = next((x for x in message.splitlines() if x.startswith(marker)), None)
    if line is None:
        raise MissionError("MISSION_B64 line not found.")
    try:
        return base64.b64decode(line[len(marker):], validate=True).decode("utf-8")
    except Exception as exc:
        raise MissionError("Invalid mission payload.") from exc
