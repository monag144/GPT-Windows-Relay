#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
import urllib.error
import urllib.request


class ReasoningBrokerError(RuntimeError):
    pass


def _load_config(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ReasoningBrokerError("reasoning config must be an object")
    return data


def _request_key(item: dict[str, Any]) -> str:
    explicit_key = item.get("key")
    if isinstance(explicit_key, str) and explicit_key:
        return explicit_key
    automation_id = item.get("automation_id")
    if isinstance(automation_id, str) and automation_id:
        return automation_id
    field = item.get("field")
    if isinstance(field, str) and field:
        return field
    raise ReasoningBrokerError("reasoning request has no stable key")


def _validate_requests(requests: list[dict[str, Any]]) -> None:
    if not isinstance(requests, list) or not requests:
        raise ReasoningBrokerError("reasoning requests must be a non-empty list")
    for item in requests:
        if not isinstance(item, dict) or item.get("kind") not in {"field_answer", "choice_answer"}:
            raise ReasoningBrokerError("unsupported reasoning request kind")
        if not isinstance(item.get("field"), str) or not item["field"].strip():
            raise ReasoningBrokerError("field_answer request missing field")


def _static_answers(config: dict[str, Any], requests: list[dict[str, Any]]) -> dict[str, str]:
    configured = config.get("answers")
    if not isinstance(configured, dict):
        raise ReasoningBrokerError("static provider requires answers object")
    out: dict[str, str] = {}
    for item in requests:
        key = _request_key(item)
        candidates = [key, item["field"]]
        answer = next((configured.get(k) for k in candidates if isinstance(configured.get(k), str)), None)
        if not answer:
            raise ReasoningBrokerError(f"static provider missing answer for {item['field']}")
        if item.get("kind") == "choice_answer":
            options = item.get("options")
            if not isinstance(options, list) or answer not in options:
                raise ReasoningBrokerError(f"static choice answer is not an allowed option for {item['field']}")
        out[key] = answer
    return out


def _openai_compatible_answers(config: dict[str, Any], requests: list[dict[str, Any]]) -> dict[str, str]:
    base_url = str(config.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    model = config.get("model")
    key_env = str(config.get("api_key_env") or "JOB_APP_AI_API_KEY")
    if not isinstance(model, str) or not model:
        raise ReasoningBrokerError("openai_compatible provider requires model")
    api_key = os.environ.get(key_env)
    if not api_key:
        raise ReasoningBrokerError(f"API key environment variable is not set: {key_env}")

    minimal_requests = []
    for item in requests:
        minimal_requests.append({
            "key": _request_key(item),
            "field": item["field"],
            "kind": item.get("kind"),
            "options": item.get("options"),
            "page_context": item.get("page_context"),
            "profile_context": item.get("profile_context"),
            "constraints": item.get("constraints") or [],
        })

    system = (
        "You resolve job-application text fields. Return JSON only. "
        "Use only the supplied applicant/profile/page facts. Never invent credentials, dates, employers, "
        "education, legal status, health facts, references, compensation history, or other factual claims. "
        "If the supplied facts do not support a truthful answer, return an empty answer for that key. "
        "Schema: {\"answers\":[{\"key\":\"...\",\"answer\":\"...\"}]}."
    )
    body = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps({"requests": minimal_requests}, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
    }
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base_url + "/chat/completions",
        data=raw,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    timeout = float(config.get("timeout_seconds", 45))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ReasoningBrokerError(f"reasoning API HTTP error: {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ReasoningBrokerError("reasoning API connection failed") from exc

    try:
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        rows = parsed["answers"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ReasoningBrokerError("reasoning API returned an invalid response schema") from exc

    allowed = {_request_key(item) for item in requests}
    out: dict[str, str] = {}
    if not isinstance(rows, list):
        raise ReasoningBrokerError("reasoning answers must be a list")
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = row.get("key")
        answer = row.get("answer")
        if key not in allowed or not isinstance(answer, str):
            continue
        answer = answer.strip()
        if not answer:
            continue
        if len(answer) > int(config.get("max_answer_chars", 4000)):
            raise ReasoningBrokerError(f"reasoning answer too long for {key}")
        request = next((item for item in requests if _request_key(item) == key), None)
        if request and request.get("kind") == "choice_answer":
            options = request.get("options")
            if not isinstance(options, list) or answer not in options:
                raise ReasoningBrokerError(f"reasoning choice is not an allowed option for {key}")
        out[key] = answer

    missing = sorted(allowed - set(out))
    if missing:
        raise ReasoningBrokerError("reasoning provider could not ground answers for: " + ", ".join(missing))
    return out


def resolve(config: dict[str, Any], requests: list[dict[str, Any]]) -> dict[str, str]:
    _validate_requests(requests)
    provider = config.get("provider")
    if provider == "static":
        return _static_answers(config, requests)
    if provider == "openai_compatible":
        return _openai_compatible_answers(config, requests)
    raise ReasoningBrokerError("unsupported reasoning provider")


def resolve_from_file(config_path: str | Path, requests: list[dict[str, Any]]) -> dict[str, str]:
    return resolve(_load_config(config_path), requests)
