#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

import firefox_adapter
import job_application_discovery_v2 as discovery
import job_application_engine_v2 as engine
import job_application_intake_v2 as intake
import job_application_manifest_v2 as manifests
import job_application_preview_v2 as preview
import job_application_rehearsal_v2 as rehearsal
import job_application_session_v2 as sessions
import reasoning_broker_v2 as reasoning_broker
import resume_profile
import workday_provider_v2 as provider

GPT_WINDOWS_JOB_APPLICATION_RUNNER_V2 = True


def _resolve_application_inputs(
    profile: dict[str, Any],
    *,
    manifest_path: str | None,
    context_path: str | None,
    application_id: str | None,
    tab_name: str | None,
    tab_contains: str | None,
) -> tuple[dict[str, Any], str | None, dict[str, str] | None, str | None]:
    if manifest_path:
        if context_path or application_id or tab_name or tab_contains:
            raise ValueError(
                "--manifest cannot be combined with --context, --application-id, "
                "--tab-name, or --tab-contains"
            )
        manifest = manifests.load_manifest(manifest_path, profile, check_files=True)
        return (
            dict(manifest["context"]),
            str(manifest["application_id"]),
            dict(manifest["browser_target"]),
            manifests.manifest_fingerprint(manifest),
        )

    context = _load(context_path, {})
    if not isinstance(context, dict):
        raise ValueError("context must be a JSON object")
    browser_target = (
        {"tab_name": tab_name}
        if tab_name
        else ({"contains": tab_contains} if tab_contains else None)
    )
    return context, application_id, browser_target, None


def _validate_browser_target(value: dict[str, Any] | None) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("browser_target must be an object")
    selectors = {
        key: raw
        for key in ("tab_name", "contains", "runtime_id")
        if isinstance((raw := value.get(key)), str) and raw
    }
    if len(selectors) != 1:
        raise ValueError(
            "browser_target requires exactly one of tab_name, contains, or runtime_id"
        )
    return selectors


def _ensure_browser_tab(browser_target: dict[str, str] | None) -> dict[str, Any] | None:
    if browser_target is None:
        return None
    if "tab_name" in browser_target:
        return firefox_adapter.select_tab(tab_name=browser_target["tab_name"])
    if "contains" in browser_target:
        return firefox_adapter.select_tab(contains=browser_target["contains"])
    return firefox_adapter.select_tab(runtime_id=browser_target["runtime_id"])


def _target_matches(state: engine.PageState, target: dict[str, Any]) -> list[engine.Control]:
    control_type = target.get("control_type")
    name = target.get("name") if isinstance(target.get("name"), str) else None
    automation_id = target.get("automation_id") if isinstance(target.get("automation_id"), str) else None
    group_name = target.get("group_name")

    def scoped(matches: list[engine.Control]) -> list[engine.Control]:
        if isinstance(group_name, str) and group_name:
            return [c for c in matches if group_name in c.group_path]
        return matches

    matches = scoped(
        state.find(
            control_type=control_type if isinstance(control_type, str) else None,
            name=name,
            automation_id=automation_id,
        )
    )
    if matches or not automation_id:
        return matches

    # Workday commonly rerenders controls after a successful mutation and
    # replaces generated AutomationIds. Verification is performed on a fresh
    # snapshot, so fall back to the stable semantic identity only when the old
    # id no longer exists. Callers still require exactly one match.
    return scoped(
        state.find(
            control_type=control_type if isinstance(control_type, str) else None,
            name=name,
            automation_id=None,
        )
    )


def _history_action(action: dict[str, Any]) -> dict[str, Any]:
    out = dict(action)
    if "path" in out:
        out["path"] = "[local file path omitted]"
    return out


def verify_action(state: engine.PageState, action: dict[str, Any]) -> tuple[bool, str]:
    verify = action.get("verify")
    if not isinstance(verify, dict):
        return False, "action has no verifier"
    kind = verify.get("kind")
    if kind == "value_equals":
        matches = _target_matches(state, action.get("target") or {})
        if len(matches) != 1:
            return False, f"value target match count {len(matches)}"
        return (matches[0].value or "") == str(verify.get("value") or ""), "value readback"
    if kind == "toggle_equals":
        matches = _target_matches(state, action.get("target") or {})
        if len(matches) != 1:
            return False, f"toggle target match count {len(matches)}"
        return (matches[0].toggle or "") == str(verify.get("value") or ""), "toggle readback"
    if kind == "selected_pill_equals":
        value = str(verify.get("value") or "")
        return value in state.selected_pills, "selected pill"
    if kind == "option_selected":
        matches = _target_matches(state, action.get("target") or {})
        if len(matches) != 1:
            return False, f"option target match count {len(matches)}"
        wanted = str(verify.get("value") or "")
        return (matches[0].value or "") == wanted or wanted in matches[0].selection, "option selected"
    if kind == "choice_selected":
        group_name = str(verify.get("group_name") or "")
        option = str(verify.get("option") or "")
        matches = [
            c for c in state.controls
            if c.control_type == "ControlType.RadioButton"
            and c.name == option
            and group_name in c.group_path
        ]
        if len(matches) != 1:
            return False, f"choice target match count {len(matches)}"
        return matches[0].selected is True, "choice selected"
    if kind == "section_count_increases":
        family = str(verify.get("family") or "")
        before = verify.get("before_count")
        if not family or not isinstance(before, int):
            return False, "section-count verifier is incomplete"
        now = engine.section_inventory(state)
        count = sum(1 for item in now["sections"] if item.get("family") == family)
        return count > before, f"section family count {count} > {before}"
    if kind == "step_changes":
        before = verify.get("from")
        before_number = before.get("number") if isinstance(before, dict) else None
        now = state.current_step
        if before_number is None:
            return now != before, "step changed"
        return not now or now.get("number") != before_number, "step number changed"
    if kind == "upload_verified":
        expected = str(verify.get("expected_filename") or "")
        success = str(verify.get("success_text") or "")
        if not expected or not success:
            return False, "upload verifier is incomplete"
        return state.contains_text(expected) and state.contains_text(success), "upload confirmed"
    if kind == "control_absent":
        name = verify.get("name")
        if not isinstance(name, str) or not name:
            return False, "control_absent verifier missing name"
        return not any(c.name == name and c.enabled and not c.offscreen for c in state.controls), "control absent"
    return False, f"unsupported verifier {kind}"


def wait_for_verification(
    action: dict[str, Any],
    *,
    attempts: int = 15,
    delay: float = 0.35,
    browser_target: dict[str, str] | None = None,
) -> tuple[engine.PageState, dict[str, Any]]:
    last_reason = "not checked"
    last_state: engine.PageState | None = None
    for attempt in range(1, attempts + 1):
        if attempt > 1:
            time.sleep(delay)
        _ensure_browser_tab(browser_target)
        last_state = provider.snapshot()
        ok, reason = verify_action(last_state, action)
        last_reason = reason
        if ok:
            return last_state, {"ok": True, "attempt": attempt, "reason": reason}
    assert last_state is not None
    return last_state, {"ok": False, "attempt": attempts, "reason": last_reason}


def run(
    profile: dict[str, Any],
    policy: engine.EnginePolicy,
    context: dict[str, Any],
    *,
    max_iterations: int = 256,
    reasoning_config: dict[str, Any] | None = None,
    application_id: str | None = None,
    browser_target: dict[str, Any] | None = None,
    manifest_fingerprint: str | None = None,
    browser_runtime_id: str | None = None,
    expected_manifest_fingerprint: str | None = None,
    expected_first_mutation_fingerprint: str | None = None,
    force_live: bool = False,
) -> dict[str, Any]:
    if max_iterations < 1 or max_iterations > 1000:
        raise ValueError("max_iterations must be 1..1000")
    history: list[dict[str, Any]] = []
    context = dict(context)
    existing_answers = context.get("reasoned_answers")
    context["reasoned_answers"] = dict(existing_answers) if isinstance(existing_answers, dict) else {}

    existing_options = context.get("selector_options")
    context["selector_options"] = dict(existing_options) if isinstance(existing_options, dict) else {}

    existing_trusted_groups = context.get("trusted_empty_repeating_groups")
    context["trusted_empty_repeating_groups"] = list(dict.fromkeys(
        value
        for value in (existing_trusted_groups if isinstance(existing_trusted_groups, list) else [])
        if isinstance(value, str) and value
    ))

    browser_target = _validate_browser_target(browser_target)

    has_runtime_binding = isinstance(browser_runtime_id, str) and bool(browser_runtime_id.strip())
    has_expected_fingerprint = (
        isinstance(expected_manifest_fingerprint, str)
        and bool(expected_manifest_fingerprint.strip())
    )
    if has_runtime_binding != has_expected_fingerprint:
        return {
            "ok": False,
            "status": "live_binding_failed",
            "iterations": 0,
            "history": [],
            "binding_error": {
                "type": "ValueError",
                "message": "runtime-id live binding requires expected manifest fingerprint",
            },
        }
    has_rehearsal_binding = (
        isinstance(expected_first_mutation_fingerprint, str)
        and bool(expected_first_mutation_fingerprint.strip())
    )
    if has_rehearsal_binding:
        expected_first_mutation_fingerprint = expected_first_mutation_fingerprint.strip()
        if not has_runtime_binding:
            return {
                "ok": False,
                "status": "rehearsal_binding_failed",
                "iterations": 0,
                "history": [],
                "binding_error": {
                    "type": "ValueError",
                    "message": "first-mutation rehearsal binding requires runtime-id live binding",
                },
            }
        if (
            len(expected_first_mutation_fingerprint) != 64
            or any(ch not in "0123456789abcdef" for ch in expected_first_mutation_fingerprint.lower())
        ):
            return {
                "ok": False,
                "status": "rehearsal_binding_failed",
                "iterations": 0,
                "history": [],
                "binding_error": {
                    "type": "ValueError",
                    "message": "first-mutation rehearsal fingerprint must be a SHA-256 hex digest",
                },
            }

    if has_runtime_binding:
        runtime_id = browser_runtime_id.strip()
        expected = expected_manifest_fingerprint.strip()
        if manifest_fingerprint is None:
            return {
                "ok": False,
                "status": "live_binding_failed",
                "iterations": 0,
                "history": [],
                "binding_error": {
                    "type": "ValueError",
                    "message": "runtime-id live binding requires manifest mode",
                },
            }
        if expected != manifest_fingerprint:
            return {
                "ok": False,
                "status": "live_binding_failed",
                "iterations": 0,
                "history": [],
                "binding_error": {
                    "type": "ValueError",
                    "message": "expected manifest fingerprint does not match current manifest",
                },
            }
        if browser_target is None or "runtime_id" in browser_target:
            return {
                "ok": False,
                "status": "live_binding_failed",
                "iterations": 0,
                "history": [],
                "binding_error": {
                    "type": "ValueError",
                    "message": "runtime-id live binding requires manifest browser target",
                },
            }
        try:
            discovery.validate_runtime_target(browser_target, runtime_id)
        except Exception as exc:
            return {
                "ok": False,
                "status": "live_binding_failed",
                "iterations": 0,
                "history": [],
                "binding_error": {"type": type(exc).__name__, "message": str(exc)},
            }

    session: dict[str, Any] | None = None
    if application_id:
        session = sessions.load(application_id)
        if manifest_fingerprint is not None:
            try:
                sessions.bind_manifest_fingerprint(session, manifest_fingerprint)
                sessions.save(session)
            except sessions.SessionStoreError as exc:
                return {
                    "ok": False,
                    "status": "manifest_session_mismatch",
                    "iterations": 0,
                    "history": [],
                    "manifest_error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                }
        persisted_browser = session.get("browser_tab")
        if browser_target is None and isinstance(persisted_browser, dict):
            browser_target = _validate_browser_target(persisted_browser)
        elif browser_target is not None and "runtime_id" not in browser_target:
            sessions.set_browser_tab(session, browser_target)
            sessions.save(session)
        if sessions.is_completed(session) and not force_live:
            return {
                "ok": True,
                "status": "done",
                "iterations": 0,
                "history": [],
                "decision": {
                    "engine_version": engine.ENGINE_VERSION,
                    "current_step": None,
                    "errors": [],
                    "actions": [],
                    "reasoning_requests": [],
                    "status": "done",
                    "reason": "local session records verified application submission",
                },
                "completion": dict(session["completion"]),
            }
        active_browser_target = (
            {"runtime_id": browser_runtime_id.strip()}
            if has_runtime_binding
            else browser_target
        )
        persisted_answers = session.get("reasoned_answers")
        if isinstance(persisted_answers, dict):
            merged = dict(persisted_answers)
            merged.update(context["reasoned_answers"])
            context["reasoned_answers"] = merged

    if session is None:
        active_browser_target = (
            {"runtime_id": browser_runtime_id.strip()}
            if has_runtime_binding
            else browser_target
        )

    downstream_untrusted_from: int | None = (
        session.get("downstream_revalidation_required_from")
        if session is not None
        else None
    )
    previous_step: int | None = (
        session.get("last_step_number")
        if session is not None and isinstance(session.get("last_step_number"), int)
        else None
    )
    rehearsal_gate_consumed = False

    for iteration in range(1, max_iterations + 1):
        try:
            selected_tab = _ensure_browser_tab(active_browser_target)
            if isinstance(selected_tab, dict):
                runtime_id = selected_tab.get("runtime_id")
                if isinstance(runtime_id, str) and runtime_id:
                    active_browser_target = {"runtime_id": runtime_id}
        except Exception as exc:
            return {
                "ok": False,
                "status": "browser_target_failed",
                "iterations": iteration,
                "history": history,
                "browser_error": {"type": type(exc).__name__, "message": str(exc)},
            }
        state = provider.snapshot()
        step = state.current_step
        step_number = step.get("number") if step else None
        if previous_step is not None and step_number is not None and step_number < previous_step:
            downstream_untrusted_from = step_number + 1
        previous_step = step_number
        if session is not None:
            sessions.observe_step(session, step_number)
            downstream_untrusted_from = session.get("downstream_revalidation_required_from")
            sessions.save(session)

        if session is not None:
            context["verified_review_expectations"] = sessions.trusted_review_assertions(session)
        decision = engine.plan(profile, state, policy, context)
        item: dict[str, Any] = {
            "iteration": iteration,
            "step": step,
            "status": decision.get("status"),
            "reason": decision.get("reason"),
            "errors": decision.get("errors", []),
        }
        if downstream_untrusted_from is not None:
            item["downstream_revalidation_required_from"] = downstream_untrusted_from

        status = decision.get("status")
        if (
            status == "done"
            and session is not None
            and state.contains_text("Application Submitted")
        ):
            sessions.mark_completed(session, evidence="Application Submitted")
            sessions.save(session)
        if status == "needs_reasoning" and reasoning_config is not None:
            requests = decision.get("reasoning_requests", [])
            try:
                answers = reasoning_broker.resolve(reasoning_config, requests)
            except Exception as exc:
                item["reasoning_requests"] = requests
                item["reasoning_error"] = {"type": type(exc).__name__, "message": str(exc)}
                history.append(item)
                return {
                    "ok": False,
                    "status": "reasoning_failed",
                    "iterations": iteration,
                    "history": history,
                }
            context["reasoned_answers"].update(answers)
            if session is not None:
                sessions.merge_reasoned_answers(session, answers)
                sessions.save(session)
            item["reasoning_requests"] = requests
            item["reasoning_resolved"] = [
                {"key": key, "answer_chars": len(value)}
                for key, value in sorted(answers.items())
            ]
            history.append(item)
            continue
        if status != "act":
            item["reasoning_requests"] = decision.get("reasoning_requests", [])
            item["review_mismatches"] = decision.get("review_mismatches", [])
            history.append(item)
            return {
                "ok": status in {"done", "ready_to_submit", "needs_reasoning"},
                "status": status,
                "iterations": iteration,
                "history": history,
                "decision": decision,
            }

        actions = decision.get("actions")
        if not isinstance(actions, list) or not actions:
            item["status"] = "blocked"
            item["reason"] = "planner returned act without actions"
            history.append(item)
            return {"ok": False, "status": "blocked", "iterations": iteration, "history": history}

        # Execute exactly one mutation from each plan. Workday frequently rerenders
        # after a field change, which can invalidate AutomationIds and even nearby
        # control structure. Fresh perception + replanning after every verified
        # mutation prevents later actions from using stale page state.
        action = actions[0]
        item["planned_action_count"] = len(actions)

        if has_rehearsal_binding and not rehearsal_gate_consumed:
            if rehearsal.is_read_only_action(action):
                item["rehearsal_gate"] = {
                    "status": "deferred_for_read_only_action",
                    "op": action.get("op"),
                }
            elif rehearsal.is_mutating_action(action):
                actual_fingerprint = rehearsal.action_fingerprint(action)
                if actual_fingerprint != expected_first_mutation_fingerprint:
                    item["rehearsal_gate"] = {
                        "status": "mismatch",
                        "expected_fingerprint": expected_first_mutation_fingerprint,
                        "actual_fingerprint": actual_fingerprint,
                    }
                    history.append(item)
                    return {
                        "ok": False,
                        "status": "rehearsal_mismatch",
                        "iterations": iteration,
                        "history": history,
                    }
                rehearsal_gate_consumed = True
                item["rehearsal_gate"] = {
                    "status": "matched",
                    "fingerprint": actual_fingerprint,
                }
            else:
                item["rehearsal_gate"] = {
                    "status": "unsupported_action",
                    "op": action.get("op"),
                }
                history.append(item)
                return {
                    "ok": False,
                    "status": "rehearsal_mismatch",
                    "iterations": iteration,
                    "history": history,
                }

        pre_action_state = state
        before = state.current_step
        try:
            provider_result = provider.execute(action)
        except Exception as exc:
            item["actions"] = [{"action": _history_action(action), "ok": False, "error": type(exc).__name__, "message": str(exc)}]
            history.append(item)
            return {"ok": False, "status": "provider_failed", "iterations": iteration, "history": history}

        if action.get("op") == "inspect_options":
            probe_key = action.get("probe_key")
            options = provider_result.get("options")
            unchanged = provider_result.get("selection_unchanged")
            if (
                not isinstance(probe_key, str)
                or not probe_key
                or not isinstance(options, list)
                or not options
                or not all(isinstance(value, str) and value for value in options)
                or unchanged is not True
            ):
                item["actions"] = [{
                    "action": _history_action(action),
                    "ok": False,
                    "error": "INVALID_OPTION_PROBE_RESULT",
                }]
                history.append(item)
                return {"ok": False, "status": "provider_failed", "iterations": iteration, "history": history}
            context["selector_options"][probe_key] = list(dict.fromkeys(options))
            item["actions"] = [{
                "action": action,
                "provider": {
                    "ok": True,
                    "op": "inspect_options",
                    "probe_key": probe_key,
                    "option_count": len(context["selector_options"][probe_key]),
                    "selection_unchanged": True,
                },
            }]
            history.append(item)
            continue

        state, verification = wait_for_verification(action, browser_target=active_browser_target)
        item["actions"] = [{"action": _history_action(action), "provider": provider_result, "verification": verification}]
        if not verification["ok"]:
            history.append(item)
            return {"ok": False, "status": "verification_failed", "iterations": iteration, "history": history}

        verify_spec = action.get("verify")
        if isinstance(verify_spec, dict) and verify_spec.get("kind") == "section_count_increases":
            family = str(verify_spec.get("family") or "")
            before_groups = {
                str(section.get("group_name") or "")
                for section in engine.section_inventory(pre_action_state)["sections"]
                if section.get("family") == family and section.get("group_name")
            }
            after_groups = {
                str(section.get("group_name") or "")
                for section in engine.section_inventory(state)["sections"]
                if section.get("family") == family and section.get("group_name")
            }
            new_groups = sorted(after_groups - before_groups)
            if len(new_groups) == 1:
                if new_groups[0] not in context["trusted_empty_repeating_groups"]:
                    context["trusted_empty_repeating_groups"].append(new_groups[0])
                item["trusted_new_repeating_group"] = new_groups[0]
            else:
                item["repeating_group_trust_warning"] = (
                    f"expected one newly created {family} scope, observed {len(new_groups)}"
                )

        after = state.current_step
        before_number = before.get("number") if before else None
        after_number = after.get("number") if after else None
        if session is not None:
            sessions.record_verified_action(session, action, before_number)
            sessions.save(session)
        if before_number is not None and after_number is not None and after_number < before_number:
            downstream_untrusted_from = after_number + 1
        if (
            session is not None
            and action.get("op") == "invoke"
            and (action.get("target") or {}).get("name") == "Save and Continue"
            and verification["ok"]
        ):
            sessions.mark_revalidated_through(session, before_number)
            sessions.observe_step(session, after_number)
            downstream_untrusted_from = session.get("downstream_revalidation_required_from")
            sessions.save(session)

        history.append(item)

    return {
        "ok": False,
        "status": "iteration_limit",
        "iterations": max_iterations,
        "history": history,
    }


def _load(path: str | None, default: Any) -> Any:
    if not path:
        return default
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Closed-loop Workday job application runner v2")
    sub = ap.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot")
    snap.add_argument("--compact", action="store_true")

    preflight = sub.add_parser("preflight")
    preflight.add_argument("--profile", required=True)
    preflight.add_argument("--manifest", required=True)
    preflight.add_argument("--skip-file-checks", action="store_true")

    discover = sub.add_parser("discover")
    discover.add_argument("--profile", required=True)
    discover.add_argument("--manifest", required=True)
    discover.add_argument("--runtime-id")

    previewp = sub.add_parser("preview")
    previewp.add_argument("--profile", required=True)
    previewp.add_argument("--manifest", required=True)
    previewp.add_argument("--runtime-id")

    rehearsep = sub.add_parser("rehearse")
    rehearsep.add_argument("--profile", required=True)
    rehearsep.add_argument("--manifest", required=True)
    rehearsep.add_argument("--runtime-id", required=True)

    runp = sub.add_parser("run")
    runp.add_argument("--profile", required=True)
    runp.add_argument("--manifest")
    runp.add_argument("--policy")
    runp.add_argument("--context")
    runp.add_argument("--reasoning-config")
    runp.add_argument("--application-id")
    runp.add_argument("--runtime-id")
    runp.add_argument("--expected-manifest-fingerprint")
    runp.add_argument("--expected-first-mutation-fingerprint")
    tab = runp.add_mutually_exclusive_group()
    tab.add_argument("--tab-name")
    tab.add_argument("--tab-contains")
    runp.add_argument("--max-iterations", type=int, default=256)
    runp.add_argument("--force-live", action="store_true")

    ns = ap.parse_args(argv)
    if ns.command == "snapshot":
        raw = provider.snapshot_raw()
        result = engine.compact_snapshot(engine.PageState.from_obj(raw)) if ns.compact else raw
    elif ns.command == "preflight":
        result = intake.compile_from_files(
            ns.profile,
            ns.manifest,
            check_files=not ns.skip_file_checks,
        )
    elif ns.command == "discover":
        result = discovery.discover_from_files(
            ns.profile,
            ns.manifest,
            runtime_id=ns.runtime_id,
        )
    elif ns.command == "preview":
        result = preview.preview_from_files(
            ns.profile,
            ns.manifest,
            runtime_id=ns.runtime_id,
        )
    elif ns.command == "rehearse":
        result = rehearsal.rehearse_from_files(
            ns.profile,
            ns.manifest,
            runtime_id=ns.runtime_id,
        )
    else:
        profile = resume_profile.load_profile(ns.profile)
        policy = engine.EnginePolicy.from_obj(_load(ns.policy, None))
        if ns.runtime_id or ns.expected_manifest_fingerprint:
            if not ns.manifest:
                raise ValueError(
                    "--runtime-id/--expected-manifest-fingerprint require --manifest"
                )
            if not ns.runtime_id or not ns.expected_manifest_fingerprint:
                raise ValueError(
                    "--runtime-id and --expected-manifest-fingerprint must be supplied together"
                )
        if ns.expected_first_mutation_fingerprint and not ns.runtime_id:
            raise ValueError(
                "--expected-first-mutation-fingerprint requires --runtime-id live binding"
            )
        context, application_id, browser_target, manifest_fingerprint = _resolve_application_inputs(
            profile,
            manifest_path=ns.manifest,
            context_path=ns.context,
            application_id=ns.application_id,
            tab_name=ns.tab_name,
            tab_contains=ns.tab_contains,
        )
        reasoning_config = _load(ns.reasoning_config, None)
        result = run(
            profile,
            policy,
            context,
            max_iterations=ns.max_iterations,
            reasoning_config=reasoning_config,
            application_id=application_id,
            browser_target=browser_target,
            manifest_fingerprint=manifest_fingerprint,
            browser_runtime_id=ns.runtime_id,
            expected_manifest_fingerprint=ns.expected_manifest_fingerprint,
            expected_first_mutation_fingerprint=ns.expected_first_mutation_fingerprint,
            force_live=ns.force_live,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
