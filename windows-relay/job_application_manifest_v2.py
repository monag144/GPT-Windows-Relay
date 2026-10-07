#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
import hashlib
import json
import re
from typing import Any

import resume_profile

SCHEMA_VERSION = 1

_FORBIDDEN_KEYS = {
    "allow_submit",
    "allow_legal_certification",
    "certify_truthfulness",
    "api_key",
    "api_token",
    "authorization",
}
_ALLOWED_TOP_LEVEL = {
    "schema_version",
    "application_id",
    "job",
    "browser_target",
    "context",
}
_ALLOWED_CONTEXT_KEYS = {
    "application_date",
    "attachments",
    "auto_bind_repeating_sections",
    "choice_answers",
    "entrypoint",
    "option_selections",
    "record_overrides",
    "repeating_section_goals",
    "repeating_sections",
    "review_expectations",
    "source_path",
}
_APP_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ManifestError(ValueError):
    pass


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be an object")
    return value


def _reject_forbidden(value: Any, path: str = "manifest") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in _FORBIDDEN_KEYS:
                raise ManifestError(f"{path}.{key} is forbidden persistent authorization/secret state")
            _reject_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden(child, f"{path}[{index}]")


def _validate_browser_target(value: Any) -> dict[str, str]:
    obj = _require_dict(value, "browser_target")
    extra = set(obj) - {"tab_name", "contains"}
    if extra:
        raise ManifestError("browser_target has unsupported fields")
    tab_name = obj.get("tab_name")
    contains = obj.get("contains")
    has_name = isinstance(tab_name, str) and bool(tab_name.strip())
    has_contains = isinstance(contains, str) and bool(contains.strip())
    if has_name == has_contains:
        raise ManifestError("browser_target requires exactly one of tab_name or contains")
    return {"tab_name": tab_name.strip()} if has_name else {"contains": contains.strip()}


def _validate_job(value: Any) -> dict[str, str]:
    obj = _require_dict(value, "job")
    allowed = {"title", "employer", "requisition_id"}
    extra = set(obj) - allowed
    if extra:
        raise ManifestError(f"job has unsupported fields: {sorted(extra)}")
    out: dict[str, str] = {}
    for key in allowed:
        raw = obj.get(key)
        if raw is None:
            continue
        if not isinstance(raw, str) or not raw.strip():
            raise ManifestError(f"job.{key} must be a nonempty string")
        out[key] = raw.strip()
    if not out.get("title"):
        raise ManifestError("job.title is required")
    return out


def _validate_source_path(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ManifestError("context.source_path must be a nonempty list")
    if not all(isinstance(x, str) and x.strip() for x in value):
        raise ManifestError("context.source_path entries must be nonempty strings")
    return [x.strip() for x in value]


def _validate_attachments(value: Any, *, check_files: bool) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ManifestError("context.attachments must be a list")
    out: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        obj = _require_dict(item, f"context.attachments[{index}]")
        allowed = {"path", "expected_filename", "target", "success_text"}
        extra = set(obj) - allowed
        if extra:
            raise ManifestError(f"context.attachments[{index}] has unsupported fields")
        path = obj.get("path")
        expected = obj.get("expected_filename")
        target = obj.get("target")
        success = obj.get("success_text", "Successfully Uploaded!")
        if not isinstance(path, str) or not path:
            raise ManifestError(f"context.attachments[{index}].path must be a nonempty string")
        p = Path(path)
        if not p.is_absolute():
            raise ManifestError(f"context.attachments[{index}].path must be absolute")
        if not isinstance(expected, str) or not expected:
            raise ManifestError(f"context.attachments[{index}].expected_filename is required")
        if p.name != expected:
            raise ManifestError(f"context.attachments[{index}] expected_filename must equal path basename")
        if check_files and (not p.exists() or not p.is_file()):
            raise ManifestError(f"context.attachments[{index}].path does not exist as a file")
        target_obj = _require_dict(target, f"context.attachments[{index}].target")
        if not any(isinstance(target_obj.get(k), str) and target_obj.get(k) for k in ("name", "automation_id")):
            raise ManifestError(f"context.attachments[{index}].target requires name or automation_id")
        if not isinstance(success, str) or not success:
            raise ManifestError(f"context.attachments[{index}].success_text must be a nonempty string")
        out.append({
            "path": path,
            "expected_filename": expected,
            "target": dict(target_obj),
            "success_text": success,
        })
    return out


def _validate_repeating_goals(value: Any, profile: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ManifestError("context.repeating_section_goals must be a list")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        obj = _require_dict(item, f"context.repeating_section_goals[{index}]")
        extra = set(obj) - {"source", "desired_count", "family", "group_name"}
        if extra:
            raise ManifestError(f"context.repeating_section_goals[{index}] has unsupported fields")
        source = obj.get("source")
        count = obj.get("desired_count")
        if source not in {"experience", "education"}:
            raise ManifestError(f"context.repeating_section_goals[{index}].source is unsupported")
        if source in seen:
            raise ManifestError(f"context.repeating_section_goals has duplicate source {source}")
        seen.add(source)
        records = profile.get(source)
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ManifestError(f"context.repeating_section_goals[{index}].desired_count must be positive integer")
        if not isinstance(records, list) or count > len(records):
            raise ManifestError(f"context.repeating_section_goals[{index}].desired_count exceeds profile records")
        normalized = {"source": source, "desired_count": count}
        for key in ("family", "group_name"):
            raw = obj.get(key)
            if raw is not None:
                if not isinstance(raw, str) or not raw.strip():
                    raise ManifestError(f"context.repeating_section_goals[{index}].{key} must be nonempty string")
                normalized[key] = raw.strip()
        out.append(normalized)
    return out


def _validate_record_overrides(value: Any, profile: dict[str, Any]) -> dict[str, dict[str, dict[str, str]]]:
    root = _require_dict(value, "context.record_overrides")
    extra_sources = set(root) - {"experience", "education"}
    if extra_sources:
        raise ManifestError("context.record_overrides has unsupported source")
    out: dict[str, dict[str, dict[str, str]]] = {}
    allowed_keys = {
        "experience": {"reason_for_leaving"},
        "education": set(),
    }
    for source, records_raw in root.items():
        records = profile.get(source)
        if not isinstance(records_raw, dict):
            raise ManifestError(f"context.record_overrides.{source} must be an object")
        source_out: dict[str, dict[str, str]] = {}
        for raw_index, facts_raw in records_raw.items():
            try:
                index = int(raw_index)
            except (TypeError, ValueError) as exc:
                raise ManifestError(f"context.record_overrides.{source} index must be integer-like") from exc
            if index < 0 or not isinstance(records, list) or index >= len(records):
                raise ManifestError(f"context.record_overrides.{source}.{raw_index} is outside profile records")
            facts = _require_dict(facts_raw, f"context.record_overrides.{source}.{raw_index}")
            extra = set(facts) - allowed_keys[source]
            if extra:
                raise ManifestError(f"context.record_overrides.{source}.{raw_index} has unsupported facts")
            clean: dict[str, str] = {}
            for key, raw in facts.items():
                if not isinstance(raw, str) or not raw.strip():
                    raise ManifestError(f"context.record_overrides.{source}.{raw_index}.{key} must be nonempty string")
                clean[key] = raw.strip()
            source_out[str(index)] = clean
        out[source] = source_out
    return out


def _validate_target(value: Any, label: str, *, combo_only: bool = False) -> dict[str, str]:
    obj = _require_dict(value, label)
    allowed = {"control_type", "name", "automation_id", "group_name"}
    extra = set(obj) - allowed
    if extra:
        raise ManifestError(f"{label} has unsupported fields: {sorted(extra)}")
    out: dict[str, str] = {}
    for key in allowed:
        raw = obj.get(key)
        if raw is None:
            continue
        if not isinstance(raw, str) or not raw.strip():
            raise ManifestError(f"{label}.{key} must be a nonempty string")
        out[key] = raw.strip()
    if not out.get("name") and not out.get("automation_id"):
        raise ManifestError(f"{label} requires name or automation_id")
    if combo_only and out.get("control_type") not in (None, "ControlType.ComboBox"):
        raise ManifestError(f"{label}.control_type must be ControlType.ComboBox")
    return out


def _validate_entrypoint(value: Any) -> dict[str, Any]:
    obj = _require_dict(value, "context.entrypoint")
    extra = set(obj) - {"target", "verify"}
    if extra:
        raise ManifestError("context.entrypoint has unsupported fields")

    target = _validate_target(obj.get("target"), "context.entrypoint.target")
    if target.get("control_type") not in (None, "ControlType.Button"):
        raise ManifestError("context.entrypoint.target.control_type must be ControlType.Button")
    name = target.get("name")
    if not isinstance(name, str) or not name:
        raise ManifestError("context.entrypoint.target.name is required")
    target["control_type"] = "ControlType.Button"

    verify = _require_dict(obj.get("verify"), "context.entrypoint.verify")
    if set(verify) - {"kind", "name"}:
        raise ManifestError("context.entrypoint.verify has unsupported fields")
    if verify.get("kind") != "control_absent":
        raise ManifestError("context.entrypoint.verify.kind must be control_absent")
    verify_name = verify.get("name")
    if not isinstance(verify_name, str) or not verify_name.strip():
        raise ManifestError("context.entrypoint.verify.name is required")
    verify_name = verify_name.strip()
    if verify_name != name:
        raise ManifestError("context.entrypoint verifier must require the invoked button to disappear")

    return {
        "target": target,
        "verify": {"kind": "control_absent", "name": verify_name},
    }


def _validate_option_selections(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ManifestError("context.option_selections must be a list")
    out: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        obj = _require_dict(item, f"context.option_selections[{index}]")
        extra = set(obj) - {"target", "value", "source"}
        if extra:
            raise ManifestError(f"context.option_selections[{index}] has unsupported fields")
        target = _validate_target(
            obj.get("target"),
            f"context.option_selections[{index}].target",
            combo_only=True,
        )
        selected = obj.get("value")
        if not isinstance(selected, str) or not selected.strip():
            raise ManifestError(f"context.option_selections[{index}].value must be a nonempty string")
        normalized: dict[str, Any] = {"target": target, "value": selected.strip()}
        source = obj.get("source")
        if source is not None:
            if not isinstance(source, str) or not source.strip():
                raise ManifestError(f"context.option_selections[{index}].source must be a nonempty string")
            normalized["source"] = source.strip()
        out.append(normalized)
    return out


def _validate_mapping(
    value: Any,
    label: str,
    record: dict[str, Any],
    *,
    expected: str,
) -> dict[str, str]:
    if value is None:
        return {}
    obj = _require_dict(value, label)
    out: dict[str, str] = {}
    for page_label, profile_key in obj.items():
        if not isinstance(page_label, str) or not page_label.strip():
            raise ManifestError(f"{label} page labels must be nonempty strings")
        if not isinstance(profile_key, str) or not profile_key.strip():
            raise ManifestError(f"{label} profile keys must be nonempty strings")
        key = profile_key.strip()
        if key not in record:
            raise ManifestError(f"{label}.{page_label} references missing profile key {key}")
        fact = record.get(key)
        if fact in (None, "", [], {}):
            raise ManifestError(f"{label}.{page_label} references an empty profile fact {key}")
        if expected == "toggle" and not isinstance(fact, bool):
            raise ManifestError(f"{label}.{page_label} requires boolean profile fact {key}")
        if expected != "toggle" and isinstance(fact, (bool, dict, list)):
            raise ManifestError(f"{label}.{page_label} requires scalar profile fact {key}")
        out[page_label.strip()] = key
    return out


def _validate_repeating_sections(value: Any, profile: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ManifestError("context.repeating_sections must be a list")
    out: list[dict[str, Any]] = []
    seen_groups: set[str] = set()
    for index, item in enumerate(value):
        obj = _require_dict(item, f"context.repeating_sections[{index}]")
        extra = set(obj) - {"source", "record_index", "group_name", "fields", "toggles", "options"}
        if extra:
            raise ManifestError(f"context.repeating_sections[{index}] has unsupported fields")
        source = obj.get("source")
        if source not in {"experience", "education"}:
            raise ManifestError(f"context.repeating_sections[{index}].source is unsupported")
        record_index = obj.get("record_index", 0)
        records = profile.get(source)
        if (
            not isinstance(record_index, int)
            or isinstance(record_index, bool)
            or record_index < 0
            or not isinstance(records, list)
            or record_index >= len(records)
        ):
            raise ManifestError(f"context.repeating_sections[{index}].record_index is outside profile records")
        group_name = obj.get("group_name")
        if not isinstance(group_name, str) or not group_name.strip():
            raise ManifestError(f"context.repeating_sections[{index}].group_name is required")
        group_name = group_name.strip()
        if group_name in seen_groups:
            raise ManifestError(f"context.repeating_sections has duplicate group_name {group_name}")
        seen_groups.add(group_name)
        record = records[record_index]
        if not isinstance(record, dict):
            raise ManifestError(f"context.repeating_sections[{index}] profile record is not an object")
        fields = _validate_mapping(
            obj.get("fields"), f"context.repeating_sections[{index}].fields", record, expected="field"
        )
        toggles = _validate_mapping(
            obj.get("toggles"), f"context.repeating_sections[{index}].toggles", record, expected="toggle"
        )
        options = _validate_mapping(
            obj.get("options"), f"context.repeating_sections[{index}].options", record, expected="option"
        )
        if not fields and not toggles and not options:
            raise ManifestError(f"context.repeating_sections[{index}] must configure at least one mapping")
        out.append({
            "source": source,
            "record_index": record_index,
            "group_name": group_name,
            "fields": fields,
            "toggles": toggles,
            "options": options,
        })
    return out


def _validate_review_expectations(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ManifestError("context.review_expectations must be a list")
    out: list[dict[str, str]] = []
    for index, item in enumerate(value):
        obj = _require_dict(item, f"context.review_expectations[{index}]")
        kind = obj.get("kind")
        if kind not in {"contains_text", "not_contains_text", "review_field_value"}:
            raise ManifestError(f"context.review_expectations[{index}].kind is unsupported")
        allowed = {"kind", "value"} if kind != "review_field_value" else {"kind", "field", "value", "group_name"}
        extra = set(obj) - allowed
        if extra:
            raise ManifestError(f"context.review_expectations[{index}] has unsupported fields")
        raw_value = obj.get("value")
        if not isinstance(raw_value, str) or not raw_value.strip():
            raise ManifestError(f"context.review_expectations[{index}].value must be a nonempty string")
        normalized = {"kind": kind, "value": raw_value.strip()}
        if kind == "review_field_value":
            field = obj.get("field")
            if not isinstance(field, str) or not field.strip():
                raise ManifestError(f"context.review_expectations[{index}].field is required")
            normalized["field"] = field.strip()
            group_name = obj.get("group_name")
            if group_name is not None:
                if not isinstance(group_name, str) or not group_name.strip():
                    raise ManifestError(
                        f"context.review_expectations[{index}].group_name must be a nonempty string"
                    )
                normalized["group_name"] = group_name.strip()
        out.append(normalized)
    return out


def _validate_string_map(value: Any, label: str) -> dict[str, str]:
    obj = _require_dict(value, label)
    out: dict[str, str] = {}
    for key, raw in obj.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(raw, str) or not raw.strip():
            raise ManifestError(f"{label} must map nonempty strings to nonempty strings")
        out[key.strip()] = raw.strip()
    return out


def validate_manifest(
    manifest: Any,
    profile: dict[str, Any],
    *,
    check_files: bool = False,
) -> dict[str, Any]:
    resume_profile.validate_profile(profile)
    root = _require_dict(manifest, "manifest")
    _reject_forbidden(root)

    extra = set(root) - _ALLOWED_TOP_LEVEL
    if extra:
        raise ManifestError(f"manifest has unsupported fields: {sorted(extra)}")
    if root.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError(f"schema_version must be {SCHEMA_VERSION}")
    application_id = root.get("application_id")
    if not isinstance(application_id, str) or not _APP_ID_RE.fullmatch(application_id):
        raise ManifestError("application_id must be a stable 1-128 character identifier")

    job = _validate_job(root.get("job"))
    browser_target = _validate_browser_target(root.get("browser_target"))
    context_raw = _require_dict(root.get("context", {}), "context")
    extra_context = set(context_raw) - _ALLOWED_CONTEXT_KEYS
    if extra_context:
        raise ManifestError(f"context has unsupported fields: {sorted(extra_context)}")

    context: dict[str, Any] = {}
    if "application_date" in context_raw:
        raw = context_raw["application_date"]
        if not isinstance(raw, str):
            raise ManifestError("context.application_date must be YYYY-MM-DD")
        try:
            date.fromisoformat(raw)
        except ValueError as exc:
            raise ManifestError("context.application_date must be YYYY-MM-DD") from exc
        context["application_date"] = raw
    if "source_path" in context_raw:
        context["source_path"] = _validate_source_path(context_raw["source_path"])
    if "attachments" in context_raw:
        context["attachments"] = _validate_attachments(context_raw["attachments"], check_files=check_files)
    if "auto_bind_repeating_sections" in context_raw:
        raw = context_raw["auto_bind_repeating_sections"]
        if not isinstance(raw, bool):
            raise ManifestError("context.auto_bind_repeating_sections must be boolean")
        context["auto_bind_repeating_sections"] = raw
    if "repeating_section_goals" in context_raw:
        context["repeating_section_goals"] = _validate_repeating_goals(
            context_raw["repeating_section_goals"], profile
        )
    if "record_overrides" in context_raw:
        context["record_overrides"] = _validate_record_overrides(
            context_raw["record_overrides"], profile
        )
    if "choice_answers" in context_raw:
        context["choice_answers"] = _validate_string_map(context_raw["choice_answers"], "context.choice_answers")
    if "entrypoint" in context_raw:
        context["entrypoint"] = _validate_entrypoint(context_raw["entrypoint"])

    if "option_selections" in context_raw:
        context["option_selections"] = _validate_option_selections(context_raw["option_selections"])
    if "repeating_sections" in context_raw:
        context["repeating_sections"] = _validate_repeating_sections(
            context_raw["repeating_sections"], profile
        )
    if "review_expectations" in context_raw:
        context["review_expectations"] = _validate_review_expectations(
            context_raw["review_expectations"]
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "application_id": application_id,
        "job": job,
        "browser_target": browser_target,
        "context": context,
    }


def manifest_fingerprint(manifest: dict[str, Any]) -> str:
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def load_manifest(path: str | Path, profile: dict[str, Any], *, check_files: bool = False) -> dict[str, Any]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    return validate_manifest(data, profile, check_files=check_files)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Validate a job-application manifest v2")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--check-files", action="store_true")
    ns = ap.parse_args(argv)
    profile = resume_profile.load_profile(ns.profile)
    out = load_manifest(ns.manifest, profile, check_files=ns.check_files)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
