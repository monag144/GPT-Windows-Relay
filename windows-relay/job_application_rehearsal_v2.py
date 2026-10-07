#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from typing import Any

import job_application_discovery_v2 as discovery
import job_application_engine_v2 as engine
import job_application_manifest_v2 as manifests
import job_application_preview_v2 as preview
import resume_profile

GPT_WINDOWS_JOB_APPLICATION_REHEARSAL_V2 = True

_MUTATING_OPS = {
    "set_text",
    "set_toggle",
    "select_choice",
    "select_hierarchy",
    "select_option",
    "upload_file",
    "invoke",
}
_READ_ONLY_OPS = {"inspect_options"}


def is_mutating_action(action: dict[str, Any]) -> bool:
    return isinstance(action,dict) and action.get("op") in _MUTATING_OPS


def is_read_only_action(action: dict[str, Any]) -> bool:
    return isinstance(action,dict) and action.get("op") in _READ_ONLY_OPS


def action_fingerprint(action: dict[str, Any]) -> str:
    if not isinstance(action, dict) or not isinstance(action.get("op"), str):
        raise TypeError("action must be a planner action object")
    raw=json.dumps(
        action,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",",":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _target_match_count(state: engine.PageState, action: dict[str, Any]) -> int:
    target=action.get("target")
    if not isinstance(target,dict) or not target:
        return 0
    control_type=target.get("control_type")
    name=target.get("name")
    automation_id=target.get("automation_id")
    group_name=target.get("group_name")
    matches=[]
    for control in state.controls:
        if isinstance(control_type,str) and control_type and control.control_type != control_type:
            continue
        if isinstance(name,str) and name and control.name != name:
            continue
        if isinstance(automation_id,str) and automation_id and control.automation_id != automation_id:
            continue
        if isinstance(group_name,str) and group_name and group_name not in control.group_path:
            continue
        if not control.enabled:
            continue
        matches.append(control)
    return len(matches)


def compile_rehearsal(
    profile: dict[str, Any],
    state: engine.PageState,
    manifest: dict[str, Any],
    *,
    browser_restored: bool,
) -> dict[str, Any]:
    context=dict(manifest["context"])
    policy=engine.EnginePolicy()
    plan=engine.plan(profile,state,policy,context)
    safe_preview=preview.compile_preview(
        profile,
        state,
        manifest,
        browser_restored=browser_restored,
    )
    actions=[
        item for item in plan.get("actions",[])
        if isinstance(item,dict)
    ]
    first=actions[0] if actions else None
    first_safe=safe_preview["plan"].get("first_action")

    base={
        "schema_version":1,
        "application_id":manifest["application_id"],
        "manifest_fingerprint":manifests.manifest_fingerprint(manifest),
        "browser_target":dict(manifest["browser_target"]),
        "browser_restored":browser_restored,
        "mutation_executed":False,
        "session_touched":False,
        "plan_status":plan.get("status"),
        "plan_reason":plan.get("reason"),
        "ready_for_first_mutation":False,
        "first_mutation":None,
    }

    if plan.get("status") != "act" or first is None:
        base["rehearsal_status"]="not_ready"
        return base

    op=str(first.get("op") or "")
    if is_read_only_action(first):
        base["rehearsal_status"]="read_only_probe_required"
        base["read_only_action"]=first_safe
        return base
    if not is_mutating_action(first):
        base["rehearsal_status"]="unsupported_first_action"
        return base

    target_match_count=_target_match_count(state,first)
    verifier=first.get("verify")
    verifier_present=isinstance(verifier,dict) and isinstance(verifier.get("kind"),str)
    fingerprint=action_fingerprint(first)
    ready=target_match_count == 1 and verifier_present
    base["rehearsal_status"]="ready" if ready else "target_not_unique"
    base["ready_for_first_mutation"]=ready
    base["first_mutation"]={
        "action":first_safe,
        "fingerprint":fingerprint,
        "target_match_count":target_match_count,
        "verifier_present":verifier_present,
    }
    return base


def rehearse_from_files(
    profile_path: str,
    manifest_path: str,
    *,
    runtime_id: str,
) -> dict[str, Any]:
    if not isinstance(runtime_id,str) or not runtime_id.strip():
        raise discovery.DiscoveryError("rehearsal requires a non-empty runtime_id")
    runtime_id=runtime_id.strip()
    profile=resume_profile.load_profile(profile_path)
    manifest=manifests.load_manifest(manifest_path,profile,check_files=True)
    discovery.validate_runtime_target(dict(manifest["browser_target"]),runtime_id)
    state=discovery.capture_live_state(manifest,runtime_id=runtime_id)
    result=compile_rehearsal(
        profile,
        state,
        manifest,
        browser_restored=True,
    )
    binding={
        "runtime_id":runtime_id,
        "expected_manifest_fingerprint":manifests.manifest_fingerprint(manifest),
    }
    first=result.get("first_mutation")
    if result.get("ready_for_first_mutation") is True and isinstance(first,dict):
        fingerprint=first.get("fingerprint")
        if isinstance(fingerprint,str) and fingerprint:
            binding["expected_first_mutation_fingerprint"]=fingerprint
    result["live_run_binding"]=binding
    return result
