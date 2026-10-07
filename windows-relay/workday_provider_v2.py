#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
from pathlib import Path
import subprocess
from typing import Any

import job_application_engine_v2 as engine

GPT_WINDOWS_WORKDAY_PROVIDER_V2 = True


class WorkdayProviderError(RuntimeError):
    pass


def _script() -> Path:
    path = Path(__file__).with_name("workday_uia_provider.ps1")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _run_ps(action: str, intent: dict[str, Any] | None = None) -> dict[str, Any]:
    args = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(_script()), "-Action", action,
    ]
    if intent is not None:
        raw = json.dumps(intent, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        args += ["-ActionJsonBase64", base64.b64encode(raw).decode("ascii")]
    cp = subprocess.run(args, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if cp.returncode:
        raise WorkdayProviderError((cp.stderr or cp.stdout or "provider command failed").strip())
    lines = [x for x in cp.stdout.splitlines() if x.strip()]
    if not lines:
        raise WorkdayProviderError("provider returned no JSON")
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise WorkdayProviderError("provider returned invalid JSON") from exc


def snapshot_raw() -> dict[str, Any]:
    result = _run_ps("snapshot")
    if not isinstance(result.get("controls"), list):
        raise WorkdayProviderError("snapshot missing controls")
    return result


def snapshot() -> engine.PageState:
    return engine.PageState.from_obj(snapshot_raw())


def execute(intent: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(intent, dict) or not isinstance(intent.get("op"), str):
        raise TypeError("intent must be an action object")
    result = _run_ps("execute", intent)
    if result.get("ok") is not True:
        raise WorkdayProviderError("provider action was not verified")
    return result
