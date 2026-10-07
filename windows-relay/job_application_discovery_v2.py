#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from typing import Any

import firefox_adapter
import job_application_engine_v2 as engine
import job_application_manifest_v2 as manifests
import resume_profile
import workday_provider_v2 as provider

GPT_WINDOWS_JOB_APPLICATION_DISCOVERY_V2 = True

_INTERACTIVE_TYPES = {
    "ControlType.Edit",
    "ControlType.Spinner",
    "ControlType.Button",
    "ControlType.CheckBox",
    "ControlType.RadioButton",
    "ControlType.ComboBox",
}
_GENERIC_GROUPS = {
    "applicationquestions",
    "voluntarydisclosures",
    "myinformation",
    "myexperience",
    "selfidentify",
    "review",
}


class DiscoveryError(RuntimeError):
    pass


def _norm(value: str | None) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _semantic_group(control: engine.Control) -> str | None:
    own = _norm(control.name)
    for name in control.group_path:
        norm = _norm(name)
        if not norm or norm == own or norm in _GENERIC_GROUPS or norm in {"yes", "no"}:
            continue
        return name
    return None


def _observed_populated(control: engine.Control) -> bool:
    if control.value not in (None, ""):
        return True
    if control.toggle not in (None, "", "Off"):
        return True
    if control.selected is True:
        return True
    if control.selection:
        return True
    return False


def _selected_tab_identity(tab_state: dict[str, Any]) -> dict[str, str]:
    tabs = tab_state.get("tabs")
    if not isinstance(tabs, list):
        raise DiscoveryError("Firefox tab inventory missing tabs")
    selected = [
        item for item in tabs
        if isinstance(item, dict) and item.get("selected") is True
    ]
    if len(selected) != 1:
        raise DiscoveryError(f"expected exactly one selected Firefox tab, found {len(selected)}")
    item = selected[0]
    name = item.get("name")
    if not isinstance(name, str) or not name:
        raise DiscoveryError("selected Firefox tab has no usable name")
    runtime_id = item.get("runtime_id")
    out = {"name": name}
    if isinstance(runtime_id, str) and runtime_id:
        out["runtime_id"] = runtime_id
    return out


def _target_matches_name(target: dict[str, str], name: str) -> bool:
    if "tab_name" in target:
        return name == target["tab_name"]
    return target.get("contains", "") in name


def validate_runtime_target(
    browser_target: dict[str, str],
    runtime_id: str,
) -> dict[str, str]:
    if not isinstance(runtime_id, str) or not runtime_id.strip():
        raise DiscoveryError("runtime_id must be a non-empty string")
    runtime_id = runtime_id.strip()
    tabs_state = firefox_adapter.list_tabs()
    tabs = tabs_state.get("tabs")
    if not isinstance(tabs, list):
        raise DiscoveryError("Firefox tab inventory missing tabs")
    matches = [
        item for item in tabs
        if isinstance(item, dict) and item.get("runtime_id") == runtime_id
    ]
    if len(matches) != 1:
        raise DiscoveryError(f"Firefox runtime-id target match count {len(matches)}")
    name = matches[0].get("name")
    if not isinstance(name, str) or not _target_matches_name(browser_target, name):
        raise DiscoveryError(
            "Firefox runtime-id target does not satisfy manifest browser target"
        )
    return {"runtime_id": runtime_id, "name": name}


def compile_discovery(
    state: engine.PageState,
    manifest: dict[str, Any],
    *,
    browser_restored: bool,
) -> dict[str, Any]:
    counts = Counter(c.control_type for c in state.controls)
    visible_interactive = [
        c for c in state.controls
        if c.control_type in _INTERACTIVE_TYPES and c.enabled and not c.offscreen
    ]
    required = [c for c in visible_interactive if c.required]

    required_controls = []
    for c in required:
        required_controls.append({
            "type": c.control_type,
            "name": c.name,
            "group_name": _semantic_group(c),
            "observed_populated": _observed_populated(c),
        })

    selectors = []
    for c in visible_interactive:
        if c.control_type != "ControlType.ComboBox":
            continue
        selectors.append({
            "name": c.name,
            "group_name": _semantic_group(c),
            "required": c.required,
            "observed_populated": _observed_populated(c),
            "expand_collapse": c.expand_collapse,
        })

    radio_groups: dict[str, list[engine.Control]] = {}
    for c in visible_interactive:
        if c.control_type != "ControlType.RadioButton":
            continue
        question = _semantic_group(c)
        if question:
            radio_groups.setdefault(question, []).append(c)
    choices = []
    for question, controls in sorted(radio_groups.items()):
        option_names = sorted({c.name for c in controls if c.name})
        choices.append({
            "question": question,
            "option_names": option_names,
            "required": any(c.required for c in controls),
            "has_selection": any(c.selected is True for c in controls),
        })

    inventory = engine.section_inventory(state)
    repeated_sections = []
    for item in inventory.get("sections", []):
        controls = item.get("controls")
        labels = []
        if isinstance(controls, list):
            labels = sorted({
                str(control.get("name"))
                for control in controls
                if isinstance(control, dict) and control.get("name")
            })
        repeated_sections.append({
            "group_name": item.get("group_name"),
            "family": item.get("family"),
            "control_count": item.get("control_count"),
            "ambiguous_within_scope": bool(item.get("ambiguous_within_scope")),
            "likely_repeating": bool(item.get("likely_repeating")),
            "labels": labels,
        })

    important_buttons = []
    for c in visible_interactive:
        if c.control_type != "ControlType.Button" or not c.name:
            continue
        norm = _norm(c.name)
        if any(term in norm for term in (
            "apply", "saveandcontinue", "submit", "addanother",
            "selectfiles", "upload", "back", "next", "continue",
        )):
            important_buttons.append(c.name)

    return {
        "schema_version": 1,
        "application_id": manifest["application_id"],
        "manifest_fingerprint": manifests.manifest_fingerprint(manifest),
        "browser_target": dict(manifest["browser_target"]),
        "browser_restored": browser_restored,
        "mutation_executed": False,
        "session_touched": False,
        "page": {
            "current_step": state.current_step,
            "error_count": len(state.errors),
            "completion_observed": state.contains_text("Application Submitted"),
            "selected_pill_count": len(state.selected_pills),
            "control_counts": dict(sorted(counts.items())),
            "visible_interactive_count": len(visible_interactive),
            "required_control_count": len(required),
            "required_unpopulated_count": sum(
                1 for c in required if not _observed_populated(c)
            ),
        },
        "required_controls": required_controls,
        "selectors": selectors,
        "choice_groups": choices,
        "sections": repeated_sections,
        "important_buttons": sorted(set(important_buttons)),
    }


def capture_live_state(
    manifest: dict[str, Any],
    *,
    runtime_id: str | None = None,
) -> engine.PageState:
    target = dict(manifest["browser_target"])
    if runtime_id is not None and (not isinstance(runtime_id, str) or not runtime_id.strip()):
        raise DiscoveryError("runtime_id override must be a non-empty string")
    runtime_id = runtime_id.strip() if isinstance(runtime_id, str) else None

    tab_state = firefox_adapter.list_tabs()
    original = _selected_tab_identity(tab_state)
    original_name = original["name"]
    original_runtime_id = original.get("runtime_id")
    tabs = tab_state.get("tabs") or []

    if runtime_id:
        runtime_matches = [
            item for item in tabs
            if isinstance(item, dict) and item.get("runtime_id") == runtime_id
        ]
        if len(runtime_matches) != 1:
            raise DiscoveryError(
                f"Firefox runtime-id target match count {len(runtime_matches)}"
            )
        candidate = runtime_matches[0]
        candidate_name = candidate.get("name")
        if not isinstance(candidate_name, str) or not _target_matches_name(target, candidate_name):
            raise DiscoveryError(
                "Firefox runtime-id target does not satisfy manifest browser target"
            )
        target_matches = runtime_matches
    else:
        target_matches = [
            item for item in tabs
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and _target_matches_name(target, item["name"])
        ]
        if len(target_matches) != 1:
            raise DiscoveryError(
                f"Firefox browser target match count {len(target_matches)}"
            )
    target_is_original = target_matches[0].get("selected") is True
    if not target_is_original and not original_runtime_id:
        same_name_count = sum(
            1 for item in tabs
            if isinstance(item, dict) and item.get("name") == original_name
        )
        if same_name_count != 1:
            raise DiscoveryError(
                "original Firefox tab has no runtime id and cannot be restored uniquely by exact name"
            )

    switched = False
    snapshot_error: BaseException | None = None
    state: engine.PageState | None = None
    try:
        if not target_is_original:
            if runtime_id:
                firefox_adapter.select_tab(runtime_id=runtime_id)
            elif "tab_name" in target:
                firefox_adapter.select_tab(tab_name=target["tab_name"])
            else:
                firefox_adapter.select_tab(contains=target["contains"])
            switched = True
        state = provider.snapshot()
    except BaseException as exc:
        snapshot_error = exc
    finally:
        if switched:
            try:
                if original_runtime_id:
                    firefox_adapter.select_tab(runtime_id=original_runtime_id)
                else:
                    firefox_adapter.select_tab(tab_name=original_name)
            except BaseException as restore_exc:
                raise DiscoveryError(
                    f"live discovery could not restore original Firefox tab: {restore_exc}"
                ) from restore_exc

    if snapshot_error is not None:
        raise snapshot_error
    assert state is not None
    return state


def discover_from_files(
    profile_path: str,
    manifest_path: str,
    *,
    runtime_id: str | None = None,
) -> dict[str, Any]:
    profile = resume_profile.load_profile(profile_path)
    manifest = manifests.load_manifest(manifest_path, profile, check_files=True)
    state = capture_live_state(manifest, runtime_id=runtime_id)
    return compile_discovery(state, manifest, browser_restored=True)
