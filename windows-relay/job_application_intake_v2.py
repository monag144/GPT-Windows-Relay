#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import job_application_manifest_v2 as manifests
import resume_profile

GPT_WINDOWS_JOB_APPLICATION_INTAKE_V2 = True


def _record_has_scalar(record: Any, key: str) -> bool:
    if not isinstance(record, dict):
        return False
    value = record.get(key)
    return value not in (None, "", [], {}) and not isinstance(value, (dict, list))


def _override_has(context: dict[str, Any], source: str, index: int, key: str) -> bool:
    root = context.get("record_overrides")
    if not isinstance(root, dict):
        return False
    source_map = root.get(source)
    if not isinstance(source_map, dict):
        return False
    item = source_map.get(str(index), source_map.get(index))
    return isinstance(item, dict) and item.get(key) not in (None, "", [], {})


def _goal_count(context: dict[str, Any], source: str) -> int:
    goals = context.get("repeating_section_goals")
    if not isinstance(goals, list):
        return 0
    for item in goals:
        if isinstance(item, dict) and item.get("source") == source:
            value = item.get("desired_count")
            return value if isinstance(value, int) and not isinstance(value, bool) else 0
    return 0


def compile_readiness(
    manifest: dict[str, Any],
    profile: dict[str, Any],
    *,
    check_files: bool = True,
) -> dict[str, Any]:
    normalized = manifests.validate_manifest(manifest, profile, check_files=check_files)
    context = normalized["context"]

    experience = profile.get("experience")
    education = profile.get("education")
    experience = experience if isinstance(experience, list) else []
    education = education if isinstance(education, list) else []

    exp_goal = _goal_count(context, "experience")
    edu_goal = _goal_count(context, "education")

    potential_record_requirements: list[dict[str, Any]] = []
    for index in range(exp_goal):
        record = experience[index] if index < len(experience) else {}
        missing: list[str] = []
        if not _record_has_scalar(record, "responsibilities"):
            missing.append("responsibilities")
        if not _record_has_scalar(record, "reason_for_leaving") and not _override_has(
            context, "experience", index, "reason_for_leaving"
        ):
            missing.append("reason_for_leaving")
        if missing:
            potential_record_requirements.append({
                "source": "experience",
                "record_index": index,
                "missing_if_requested_by_page": missing,
            })

    attachments = context.get("attachments")
    attachment_summary = []
    if isinstance(attachments, list):
        for item in attachments:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            attachment_summary.append({
                "expected_filename": item.get("expected_filename"),
                "exists": isinstance(path, str) and Path(path).is_file(),
                "target_named": bool((item.get("target") or {}).get("name"))
                if isinstance(item.get("target"), dict)
                else False,
            })

    explicit_sections = context.get("repeating_sections")
    explicit_sections = explicit_sections if isinstance(explicit_sections, list) else []
    option_selections = context.get("option_selections")
    option_selections = option_selections if isinstance(option_selections, list) else []
    review_expectations = context.get("review_expectations")
    review_expectations = review_expectations if isinstance(review_expectations, list) else []
    choice_answers = context.get("choice_answers")
    choice_answers = choice_answers if isinstance(choice_answers, dict) else {}

    live_dependencies = [
        "required-field discovery from the live application",
        "exact dropdown option discovery for selectors not explicitly configured",
        "date-format discovery from accessible field metadata",
        "final Review rendering and semantic verification",
    ]
    if context.get("entrypoint") is not None:
        live_dependencies.append("manifest-bound public-listing entrypoint transition")
    if context.get("auto_bind_repeating_sections") is True:
        live_dependencies.append("identity-anchored repeated-section discovery")
    if potential_record_requirements:
        live_dependencies.append(
            "record-local narrative facts may be required if the live page asks for them"
        )

    return {
        "schema_version": 1,
        "application_id": normalized["application_id"],
        "manifest_fingerprint": manifests.manifest_fingerprint(normalized),
        "job": dict(normalized["job"]),
        "browser_target": dict(normalized["browser_target"]),
        "preflight_ready": True,
        "browser_touched": False,
        "persistent_authorization_present": False,
        "runtime_authorization_required_for_submit": True,
        "runtime_authorization_required_for_legal_certification": True,
        "profile_inventory": {
            "experience_records": len(experience),
            "education_records": len(education),
        },
        "planned_record_counts": {
            "experience": exp_goal,
            "education": edu_goal,
        },
        "manifest_contracts": {
            "source_path_configured": bool(context.get("source_path")),
            "entrypoint_configured": isinstance(context.get("entrypoint"), dict),
            "auto_bind_repeating_sections": context.get("auto_bind_repeating_sections") is True,
            "explicit_repeating_sections": len(explicit_sections),
            "choice_answers": len(choice_answers),
            "option_selections": len(option_selections),
            "attachments": attachment_summary,
            "review_expectations": len(review_expectations),
        },
        "potential_record_requirements": potential_record_requirements,
        "live_discovery_required": True,
        "live_dependencies": live_dependencies,
    }


def compile_from_files(
    profile_path: str | Path,
    manifest_path: str | Path,
    *,
    check_files: bool = True,
) -> dict[str, Any]:
    profile = resume_profile.load_profile(profile_path)
    raw = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))
    return compile_readiness(raw, profile, check_files=check_files)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Offline application readiness compiler for job application engine v2"
    )
    ap.add_argument("--profile", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--skip-file-checks", action="store_true")
    ns = ap.parse_args(argv)
    report = compile_from_files(
        ns.profile,
        ns.manifest,
        check_files=not ns.skip_file_checks,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
