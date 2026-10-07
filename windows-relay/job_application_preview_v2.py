#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import job_application_discovery_v2 as discovery
import job_application_engine_v2 as engine
import job_application_manifest_v2 as manifests
import resume_profile

GPT_WINDOWS_JOB_APPLICATION_PREVIEW_V2 = True


_REDACTED_VALUE_OPS = {
    "set_text",
    "set_toggle",
    "select_choice",
    "select_option",
    "select_hierarchy",
    "upload_file",
}


def _safe_target(action: dict[str, Any]) -> dict[str, Any]:
    target = action.get("target")
    if not isinstance(target, dict):
        return {}
    out: dict[str, Any] = {}
    control_type = target.get("control_type")
    if isinstance(control_type, str) and control_type:
        out["control_type"] = control_type
    group_name = target.get("group_name")
    if isinstance(group_name, str) and group_name:
        out["group_name"] = group_name

    name = target.get("name")
    if isinstance(name, str) and name:
        # For radio choices the control name is the selected answer itself.
        # Keep the question scope, but omit the chosen option from diagnostics.
        if action.get("op") == "select_choice":
            out["name"] = "[configured option omitted]"
        elif action.get("op") == "upload_file":
            out["name"] = name
        else:
            out["name"] = name
    return out


def _safe_action(action: dict[str, Any]) -> dict[str, Any]:
    op = str(action.get("op") or "")
    out: dict[str, Any] = {
        "op": op,
        "target": _safe_target(action),
    }
    source = action.get("source")
    if isinstance(source, str) and source:
        out["source"] = source
    verify = action.get("verify")
    if isinstance(verify, dict):
        kind = verify.get("kind")
        if isinstance(kind, str) and kind:
            out["verify_kind"] = kind
    if op in _REDACTED_VALUE_OPS:
        out["configured_value_omitted"] = True
    return out


def _safe_reasoning_request(request: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ("kind", "field", "key"):
        value = request.get(key)
        if isinstance(value, str) and value:
            out[key] = value
    options = request.get("options")
    if isinstance(options, list):
        out["option_count"] = len(options)
    reason = request.get("reason")
    if isinstance(reason, str) and reason:
        # The engine's reason strings describe page/config mismatch semantics,
        # not applicant values. Still avoid copying arbitrary nested context.
        out["reason"] = reason
    return out


def _safe_blockers(plan: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    safe_lists = {
        "repeating_freeform_blockers",
        "repeating_date_blockers",
        "repeating_section_blockers",
        "selector_blockers",
        "required_field_blockers",
        "entrypoint_blockers",
    }
    for key in safe_lists:
        value = plan.get(key)
        if isinstance(value, list):
            out[key] = [str(x) for x in value]
    mismatches = plan.get("review_mismatches")
    if isinstance(mismatches, list):
        # Review mismatch strings can contain expected applicant values.
        out["review_mismatch_count"] = len(mismatches)
    return out


def compile_preview(
    profile: dict[str, Any],
    state: engine.PageState,
    manifest: dict[str, Any],
    *,
    browser_restored: bool,
) -> dict[str, Any]:
    policy = engine.EnginePolicy()
    context = dict(manifest["context"])
    plan = engine.plan(profile, state, policy, context)

    safe_actions = [
        _safe_action(action)
        for action in plan.get("actions", [])
        if isinstance(action, dict)
    ]
    safe_reasoning = [
        _safe_reasoning_request(item)
        for item in plan.get("reasoning_requests", [])
        if isinstance(item, dict)
    ]

    entrypoint_buttons = sorted({
        control.name
        for control in state.controls
        if control.control_type == "ControlType.Button"
        and control.enabled
        and not control.offscreen
        and control.name in {"Apply", "Start Application"}
    })

    return {
        "schema_version": 1,
        "application_id": manifest["application_id"],
        "manifest_fingerprint": manifests.manifest_fingerprint(manifest),
        "browser_target": dict(manifest["browser_target"]),
        "browser_restored": browser_restored,
        "mutation_executed": False,
        "session_touched": False,
        "policy_preview": {
            "allow_submit": False,
            "allow_legal_certification": False,
        },
        "page": {
            "current_step": state.current_step,
            "completion_observed": state.contains_text("Application Submitted"),
            "error_count": len(state.errors),
            "entrypoint_buttons": entrypoint_buttons,
        },
        "plan": {
            "status": plan.get("status"),
            "reason": plan.get("reason"),
            "action_count": len(safe_actions),
            "actions": safe_actions,
            "first_action": safe_actions[0] if safe_actions else None,
            "reasoning_request_count": len(safe_reasoning),
            "reasoning_requests": safe_reasoning,
            "blockers": _safe_blockers(plan),
        },
    }


def preview_from_files(
    profile_path: str,
    manifest_path: str,
    *,
    runtime_id: str | None = None,
) -> dict[str, Any]:
    profile = resume_profile.load_profile(profile_path)
    manifest = manifests.load_manifest(manifest_path, profile, check_files=True)
    state = discovery.capture_live_state(manifest, runtime_id=runtime_id)
    result = compile_preview(
        profile,
        state,
        manifest,
        browser_restored=True,
    )
    if isinstance(runtime_id, str) and runtime_id.strip():
        result["live_run_binding"] = {
            "runtime_id": runtime_id.strip(),
            "expected_manifest_fingerprint": manifests.manifest_fingerprint(manifest),
        }
    return result
