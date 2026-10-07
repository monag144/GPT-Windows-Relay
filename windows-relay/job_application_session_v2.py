#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

SESSION_SCHEMA_VERSION = 1


class SessionStoreError(RuntimeError):
    pass


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug[:80] or "application"


def session_root() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise SessionStoreError("LOCALAPPDATA is not set")
    return Path(base) / "GPTWindowsRelay" / "job_application_sessions"


def session_path(application_id: str) -> Path:
    digest = hashlib.sha256(application_id.encode("utf-8")).hexdigest()[:12]
    return session_root() / f"{_safe_slug(application_id)}-{digest}.json"


def empty_session(application_id: str) -> dict[str, Any]:
    return {
        "schema_version": SESSION_SCHEMA_VERSION,
        "application_id": application_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_step_number": None,
        "highest_step_number": None,
        "downstream_revalidation_required_from": None,
        "reasoned_answers": {},
        "review_assertions": [],
        "browser_tab": None,
        "completion": None,
        "manifest_fingerprint": None,
        "notes": [],
    }


def validate_session(data: dict[str, Any], application_id: str | None = None) -> None:
    if not isinstance(data, dict):
        raise SessionStoreError("session must be an object")
    if data.get("schema_version") != SESSION_SCHEMA_VERSION:
        raise SessionStoreError("unsupported session schema")
    if not isinstance(data.get("application_id"), str) or not data["application_id"]:
        raise SessionStoreError("session missing application_id")
    if application_id is not None and data["application_id"] != application_id:
        raise SessionStoreError("session application_id mismatch")
    for key in ("last_step_number", "highest_step_number", "downstream_revalidation_required_from"):
        value = data.get(key)
        if value is not None and (not isinstance(value, int) or value < 1):
            raise SessionStoreError(f"invalid {key}")
    if not isinstance(data.get("reasoned_answers"), dict):
        raise SessionStoreError("reasoned_answers must be an object")
    assertions = data.get("review_assertions", [])
    if not isinstance(assertions, list):
        raise SessionStoreError("review_assertions must be a list")
    for item in assertions:
        if not isinstance(item, dict):
            raise SessionStoreError("review assertion must be an object")
        if item.get("kind") != "review_field_value":
            raise SessionStoreError("unsupported review assertion kind")
        if not isinstance(item.get("field"), str) or not item["field"]:
            raise SessionStoreError("review assertion missing field")
        if not isinstance(item.get("value"), str) or not item["value"]:
            raise SessionStoreError("review assertion missing value")
        group_name = item.get("group_name")
        if group_name is not None and (not isinstance(group_name, str) or not group_name):
            raise SessionStoreError("review assertion has invalid group_name")
        step_number = item.get("step_number")
        if step_number is not None and (not isinstance(step_number, int) or step_number < 1):
            raise SessionStoreError("review assertion has invalid step_number")
        if not isinstance(item.get("trusted", True), bool):
            raise SessionStoreError("review assertion trusted must be bool")
    _validate_browser_tab(data.get("browser_tab"))
    _validate_completion(data.get("completion"))
    _validate_manifest_fingerprint(data.get("manifest_fingerprint"))
    if "allow_submit" in data or "allow_legal_certification" in data or "certify_truthfulness" in data:
        raise SessionStoreError("authorization flags must not be persisted")


def _validate_manifest_fingerprint(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise SessionStoreError("manifest_fingerprint must be a lowercase SHA-256 hex digest or null")


def _has_operational_history(data: dict[str, Any]) -> bool:
    return any((
        data.get("last_step_number") is not None,
        data.get("highest_step_number") is not None,
        data.get("downstream_revalidation_required_from") is not None,
        bool(data.get("reasoned_answers")),
        bool(data.get("review_assertions")),
        data.get("browser_tab") is not None,
        data.get("completion") is not None,
    ))


def bind_manifest_fingerprint(data: dict[str, Any], fingerprint: str) -> None:
    _validate_manifest_fingerprint(fingerprint)
    current = data.get("manifest_fingerprint")
    if current is None:
        if _has_operational_history(data):
            raise SessionStoreError(
                "existing application session predates manifest binding and has operational history"
            )
        data["manifest_fingerprint"] = fingerprint
        return
    if current != fingerprint:
        raise SessionStoreError("application manifest fingerprint does not match existing session")


def _validate_browser_tab(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise SessionStoreError("browser_tab must be an object or null")
    tab_name = value.get("tab_name")
    contains = value.get("contains")
    has_name = isinstance(tab_name, str) and bool(tab_name)
    has_contains = isinstance(contains, str) and bool(contains)
    if has_name == has_contains:
        raise SessionStoreError("browser_tab requires exactly one of tab_name or contains")
    extra = set(value) - {"tab_name", "contains"}
    if extra:
        raise SessionStoreError("browser_tab has unsupported fields")


def set_browser_tab(data: dict[str, Any], value: dict[str, str] | None) -> None:
    _validate_browser_tab(value)
    data["browser_tab"] = None if value is None else dict(value)


def _validate_completion(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise SessionStoreError("completion must be an object or null")
    if value.get("status") != "submitted":
        raise SessionStoreError("unsupported completion status")
    if not isinstance(value.get("verified_at"), str) or not value["verified_at"]:
        raise SessionStoreError("completion missing verified_at")
    evidence = value.get("evidence")
    if evidence != "Application Submitted":
        raise SessionStoreError("unsupported completion evidence")


def mark_completed(data: dict[str, Any], *, evidence: str = "Application Submitted") -> None:
    if evidence != "Application Submitted":
        raise SessionStoreError("completion requires exact verified submission evidence")
    data["completion"] = {
        "status": "submitted",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "evidence": evidence,
    }


def is_completed(data: dict[str, Any]) -> bool:
    value = data.get("completion")
    return (
        isinstance(value, dict)
        and value.get("status") == "submitted"
        and value.get("evidence") == "Application Submitted"
    )


def load(application_id: str) -> dict[str, Any]:
    path = session_path(application_id)
    if not path.exists():
        return empty_session(application_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SessionStoreError("session could not be read") from exc
    validate_session(data, application_id)
    return data


def save(data: dict[str, Any]) -> Path:
    validate_session(data)
    data = dict(data)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = session_path(data["application_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    tmp.write_text(payload, encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    return path


def merge_reasoned_answers(data: dict[str, Any], answers: dict[str, str]) -> None:
    current = data.setdefault("reasoned_answers", {})
    if not isinstance(current, dict):
        raise SessionStoreError("reasoned_answers must be an object")
    for key, value in answers.items():
        if isinstance(key, str) and key and isinstance(value, str) and value:
            current[key] = value


def _review_assertion_from_action(action: dict[str, Any], step_number: int | None) -> dict[str, Any] | None:
    if not isinstance(action, dict):
        return None
    op = action.get("op")
    target = action.get("target")
    target = target if isinstance(target, dict) else {}
    field = target.get("name")
    value: Any = None
    if op == "set_text":
        value = action.get("value")
    elif op == "select_option":
        value = action.get("value")
    elif op == "select_choice":
        field = target.get("group_name")
        value = target.get("name")
    elif op == "select_hierarchy":
        verify = action.get("verify")
        if isinstance(verify, dict) and verify.get("kind") == "selected_pill_equals":
            value = verify.get("value")
    else:
        return None

    if not isinstance(field, str) or not field:
        return None
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    rendered = str(value).strip()
    if not rendered:
        return None
    # Review text checks are exact semantic text matches. Extremely long
    # freeform values are poor review assertions and may be split by UIA.
    if len(rendered) > 512:
        return None
    group_name = target.get("group_name")
    return {
        "kind": "review_field_value",
        "field": field,
        "value": rendered,
        "group_name": group_name if isinstance(group_name, str) and group_name else None,
        "step_number": step_number,
        "trusted": True,
    }


def record_verified_action(data: dict[str, Any], action: dict[str, Any], step_number: int | None) -> None:
    assertion = _review_assertion_from_action(action, step_number)
    if assertion is None:
        return
    items = data.setdefault("review_assertions", [])
    if not isinstance(items, list):
        raise SessionStoreError("review_assertions must be a list")
    key = (
        assertion["kind"],
        assertion["field"],
        assertion.get("group_name"),
        assertion.get("step_number"),
    )
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        item_key = (
            item.get("kind"),
            item.get("field"),
            item.get("group_name"),
            item.get("step_number"),
        )
        if item_key == key:
            items[index] = assertion
            return
    items.append(assertion)


def trusted_review_assertions(data: dict[str, Any]) -> list[dict[str, Any]]:
    items = data.get("review_assertions", [])
    if not isinstance(items, list):
        return []
    return [
        dict(item)
        for item in items
        if isinstance(item, dict) and item.get("trusted", True) is True
    ]


def _set_assertion_trust(data: dict[str, Any], predicate, trusted: bool) -> None:
    items = data.get("review_assertions", [])
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        if predicate(item):
            item["trusted"] = trusted


def observe_step(data: dict[str, Any], step_number: int | None) -> dict[str, Any]:
    if step_number is None:
        return data
    previous = data.get("last_step_number")
    highest = data.get("highest_step_number")
    if isinstance(previous, int) and step_number < previous:
        candidate = step_number + 1
        existing = data.get("downstream_revalidation_required_from")
        if existing is None or candidate < existing:
            data["downstream_revalidation_required_from"] = candidate
        _set_assertion_trust(
            data,
            lambda item: isinstance(item.get("step_number"), int) and item["step_number"] >= candidate,
            False,
        )
    data["last_step_number"] = step_number
    if not isinstance(highest, int) or step_number > highest:
        data["highest_step_number"] = step_number
    return data


def mark_revalidated_through(data: dict[str, Any], step_number: int | None) -> None:
    if step_number is None:
        return
    _set_assertion_trust(
        data,
        lambda item: item.get("step_number") == step_number,
        True,
    )
    required = data.get("downstream_revalidation_required_from")
    if isinstance(required, int) and step_number >= required:
        next_step = step_number + 1
        highest = data.get("highest_step_number")
        if isinstance(highest, int) and next_step <= highest:
            data["downstream_revalidation_required_from"] = next_step
        else:
            data["downstream_revalidation_required_from"] = None
