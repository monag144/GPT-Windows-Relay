#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import date
import json
from pathlib import Path
import re
from typing import Any, Iterable

import resume_profile

GPT_WINDOWS_JOB_APPLICATION_ENGINE_V2 = True
ENGINE_VERSION = 2

_STEP_RE = re.compile(r"^current step\s+(\d+)\s+of\s+(\d+)\s+(.+)$", re.I)
_ERROR_RE = re.compile(r"(^Errors Found$|^Error(?:[^a-z]|$)|required and must have a value)", re.I)
_SELECTED_PILL_RE = re.compile(r"^(.*?), press delete to clear value\.$", re.I)

_IGNORED_EDIT_NAMES = {
    "",
    "search",
}
_IGNORED_EDIT_AUTOMATION_IDS = {
    "source--source",
}

_SENSITIVE_DECLINE_LABELS = {
    "i do not want to answer",
    "i do not wish to answer",
}
_COMPLETION_TEXTS = {
    "Application Submitted",
}


def _norm(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


@dataclass(frozen=True)
class Control:
    control_type: str
    name: str = ""
    automation_id: str = ""
    value: str | None = None
    toggle: str | None = None
    selected: bool | None = None
    enabled: bool = True
    offscreen: bool = False
    top: float | None = None
    left: float | None = None
    group_path: tuple[str, ...] = ()
    expand_collapse: str | None = None
    selection: tuple[str, ...] = ()
    help_text: str = ""
    required: bool = False

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> "Control":
        if not isinstance(obj, dict):
            raise TypeError("control must be an object")
        return cls(
            control_type=str(obj.get("type") or obj.get("control_type") or ""),
            name=str(obj.get("name") or ""),
            automation_id=str(obj.get("id") or obj.get("automation_id") or ""),
            value=None if obj.get("value") is None else str(obj.get("value")),
            toggle=None if obj.get("toggle") is None else str(obj.get("toggle")),
            selected=obj.get("selected") if isinstance(obj.get("selected"), bool) else None,
            enabled=bool(obj.get("enabled", True)),
            offscreen=bool(obj.get("offscreen", False)),
            top=float(obj["top"]) if isinstance(obj.get("top"), (int, float)) else None,
            left=float(obj["left"]) if isinstance(obj.get("left"), (int, float)) else None,
            group_path=tuple(str(x) for x in obj.get("group_path", []) if isinstance(x, str) and x),
            expand_collapse=None if obj.get("expand_collapse") is None else str(obj.get("expand_collapse")),
            selection=tuple(str(x) for x in obj.get("selection", []) if isinstance(x, str) and x),
            help_text=str(obj.get("help_text") or ""),
            required=bool(obj.get("required", False)),
        )

    def to_obj(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "type": self.control_type,
            "id": self.automation_id,
            "name": self.name,
            "enabled": self.enabled,
            "offscreen": self.offscreen,
        }
        if self.value is not None:
            out["value"] = self.value
        if self.toggle is not None:
            out["toggle"] = self.toggle
        if self.selected is not None:
            out["selected"] = self.selected
        if self.top is not None:
            out["top"] = self.top
        if self.left is not None:
            out["left"] = self.left
        if self.group_path:
            out["group_path"] = list(self.group_path)
        if self.expand_collapse is not None:
            out["expand_collapse"] = self.expand_collapse
        if self.selection:
            out["selection"] = list(self.selection)
        if self.help_text:
            out["help_text"] = self.help_text
        if self.required:
            out["required"] = True
        return out


@dataclass
class PageState:
    controls: list[Control]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_obj(cls, obj: Any) -> "PageState":
        if isinstance(obj, list):
            raw_controls = obj
            metadata: dict[str, Any] = {}
        elif isinstance(obj, dict):
            raw_controls = obj.get("controls", [])
            metadata = {k: v for k, v in obj.items() if k != "controls"}
        else:
            raise TypeError("snapshot must be a list or object")
        if not isinstance(raw_controls, list):
            raise TypeError("snapshot controls must be a list")
        return cls([Control.from_obj(x) for x in raw_controls], metadata)

    @property
    def current_step(self) -> dict[str, Any] | None:
        for c in self.controls:
            m = _STEP_RE.match(c.name)
            if m:
                return {"number": int(m.group(1)), "total": int(m.group(2)), "label": m.group(3)}
        return None

    @property
    def errors(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for c in self.controls:
            if c.name and _ERROR_RE.search(c.name) and c.name not in seen:
                seen.add(c.name)
                out.append(c.name)
        return out

    @property
    def selected_pills(self) -> list[str]:
        out: list[str] = []
        for c in self.controls:
            m = _SELECTED_PILL_RE.match(c.name)
            if m:
                out.append(m.group(1))
        return out

    def find(
        self,
        *,
        control_type: str | None = None,
        name: str | None = None,
        automation_id: str | None = None,
        visible_only: bool = False,
        enabled_only: bool = False,
    ) -> list[Control]:
        out: list[Control] = []
        for c in self.controls:
            if control_type is not None and c.control_type != control_type:
                continue
            if name is not None and c.name != name:
                continue
            if automation_id is not None and c.automation_id != automation_id:
                continue
            if visible_only and c.offscreen:
                continue
            if enabled_only and not c.enabled:
                continue
            out.append(c)
        return out

    def contains_text(self, text: str) -> bool:
        needle = _norm(text)
        return any(needle and needle == _norm(c.name) for c in self.controls)


@dataclass(frozen=True)
class EnginePolicy:
    allow_submit: bool = False
    allow_legal_certification: bool = False
    prefer_decline_sensitive: bool = True
    fail_on_review_mismatch: bool = True

    @classmethod
    def from_obj(cls, obj: dict[str, Any] | None) -> "EnginePolicy":
        obj = obj or {}
        return cls(
            allow_submit=bool(obj.get("allow_submit", False)),
            allow_legal_certification=bool(obj.get("allow_legal_certification", False)),
            prefer_decline_sensitive=bool(obj.get("prefer_decline_sensitive", True)),
            fail_on_review_mismatch=bool(obj.get("fail_on_review_mismatch", True)),
        )


def _action(op: str, *, verify: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    out = {"op": op, **kwargs}
    if verify is not None:
        out["verify"] = verify
    return out


def compact_snapshot(snapshot: PageState) -> dict[str, Any]:
    keep_types = {
        "ControlType.Edit",
        "ControlType.Spinner",
        "ControlType.Button",
        "ControlType.CheckBox",
        "ControlType.RadioButton",
        "ControlType.ComboBox",
        "ControlType.ListItem",
        "ControlType.Group",
        "ControlType.Text",
    }
    seen: set[tuple[Any, ...]] = set()
    compact: list[dict[str, Any]] = []
    for c in snapshot.controls:
        if c.control_type not in keep_types:
            continue
        meaningful = (
            bool(c.automation_id)
            or bool(c.value)
            or bool(c.toggle)
            or bool(c.selected)
            or _STEP_RE.match(c.name)
            or _ERROR_RE.search(c.name or "")
            or c.control_type in {
                "ControlType.Edit",
                "ControlType.Spinner",
                "ControlType.Button",
                "ControlType.CheckBox",
                "ControlType.RadioButton",
                "ControlType.ComboBox",
                "ControlType.ListItem",
            }
        )
        if not meaningful:
            continue
        key = (c.control_type, c.automation_id, c.name, c.value, c.toggle, c.selected, c.offscreen)
        if key in seen:
            continue
        seen.add(key)
        compact.append(c.to_obj())
    return {
        "engine_version": ENGINE_VERSION,
        "current_step": snapshot.current_step,
        "errors": snapshot.errors,
        "selected_pills": snapshot.selected_pills,
        "controls": compact,
    }


def _section_family(name: str) -> str:
    value = re.sub(r"(?:\s*[-_#]?\s*\d+|\s*\(\d+\))$", "", name.strip())
    return value or name.strip()


def section_inventory(state: PageState) -> dict[str, Any]:
    input_types = {
        "ControlType.Edit",
        "ControlType.Spinner",
        "ControlType.CheckBox",
        "ControlType.RadioButton",
        "ControlType.ComboBox",
    }
    grouped: dict[str, list[Control]] = {}
    for control in state.controls:
        if control.control_type not in input_types:
            continue
        scope = _field_scope_name(control)
        if scope:
            grouped.setdefault(scope, []).append(control)

    sections: list[dict[str, Any]] = []
    for group_name, controls in grouped.items():
        label_counts: dict[tuple[str, str], int] = {}
        for control in controls:
            key = (control.control_type, control.name)
            label_counts[key] = label_counts.get(key, 0) + 1
        duplicate_labels = sorted(
            name
            for (control_type, name), count in label_counts.items()
            if count > 1 and name
        )
        ordered = sorted(
            controls,
            key=lambda c: (
                float("inf") if c.top is None else c.top,
                float("inf") if c.left is None else c.left,
                c.control_type,
                c.name,
            ),
        )
        tops = [c.top for c in controls if c.top is not None]
        sections.append({
            "group_name": group_name,
            "family": _section_family(group_name),
            "top": min(tops) if tops else None,
            "control_count": len(controls),
            "ambiguous_within_scope": bool(duplicate_labels),
            "duplicate_labels": duplicate_labels,
            "controls": [
                {
                    "type": c.control_type,
                    "name": c.name,
                    "automation_id": c.automation_id,
                    "has_value": c.value not in (None, ""),
                    "value": c.value,
                    "toggle": c.toggle,
                    "selected": c.selected,
                    "selection": list(c.selection),
                    "help_text": c.help_text,
                    "required": c.required,
                }
                for c in ordered
            ],
        })

    sections.sort(key=lambda item: (
        float("inf") if item["top"] is None else item["top"],
        item["group_name"],
    ))
    family_counts: dict[str, int] = {}
    for item in sections:
        family = str(item["family"])
        family_counts[family] = family_counts.get(family, 0) + 1
    for item in sections:
        item["family_occurrences"] = family_counts[str(item["family"])]
        item["likely_repeating"] = (
            item["family_occurrences"] > 1 or item["ambiguous_within_scope"]
        )
        item["safe_named_scope"] = not item["ambiguous_within_scope"]

    return {
        "engine_version": ENGINE_VERSION,
        "current_step": state.current_step,
        "section_count": len(sections),
        "sections": sections,
    }


def _field_scope_name(control: Control) -> str | None:
    field_norm = _norm(control.name)
    for name in control.group_path:
        norm = _norm(name)
        if not norm or norm == field_norm or norm in _GENERIC_GROUP_NAMES:
            continue
        return name
    return None


def _scoped_target(control: Control) -> dict[str, Any]:
    target: dict[str, Any] = {
        "automation_id": control.automation_id,
        "name": control.name,
    }
    scope = _field_scope_name(control)
    if scope:
        target["group_name"] = scope
    return target


def _field_answer(profile: dict[str, Any], label: str) -> dict[str, Any]:
    normalized = _norm(label)
    if normalized in {"name", "legalname", "fullname"}:
        first = str(profile["identity"].get("first_name") or "").strip()
        middle = str(profile["identity"].get("middle_name") or "").strip()
        last = str(profile["identity"].get("last_name") or "").strip()
        value = " ".join(x for x in (first, middle, last) if x)
        return {
            "status": "found" if value else "missing",
            "value": value,
            "source": "identity.*",
            "deterministic": True,
        }
    return resume_profile.lookup_field(profile, label)


def _plan_text_fields(state: PageState, profile: dict[str, Any], context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    actions: list[dict[str, Any]] = []
    reasoning: list[dict[str, Any]] = []
    repeating = context.get("repeating_sections")
    repeating = list(repeating) if isinstance(repeating, list) else []
    if context.get("auto_bind_repeating_sections") is True:
        inferred = infer_repeating_sections(
            state,
            profile,
            trusted_empty_group_names=context.get("trusted_empty_repeating_groups"),
        ).get("bindings", [])
        explicit_groups = {
            item.get("group_name")
            for item in repeating
            if isinstance(item, dict) and isinstance(item.get("group_name"), str)
        }
        repeating += [
            item for item in inferred
            if isinstance(item, dict) and item.get("group_name") not in explicit_groups
        ]
    repeating_group_names = {
        item.get("group_name")
        for item in repeating
        if isinstance(item, dict) and isinstance(item.get("group_name"), str) and item.get("group_name")
    }
    repeating_field_names = {
        _norm(label)
        for item in repeating
        if isinstance(item, dict) and isinstance(item.get("fields"), dict)
        for label in item["fields"]
        if isinstance(label, str) and label
    }
    reasoned_answers = context.get("reasoned_answers")
    if not isinstance(reasoned_answers, dict):
        reasoned_answers = {}
    for c in state.controls:
        if c.control_type != "ControlType.Edit" or not c.enabled:
            continue
        if repeating_group_names and any(group in repeating_group_names for group in c.group_path):
            continue
        if _norm(c.name) in repeating_field_names:
            continue
        if c.automation_id in _IGNORED_EDIT_AUTOMATION_IDS:
            continue
        if _norm(c.name) in _IGNORED_EDIT_NAMES:
            continue
        if c.value not in (None, ""):
            continue
        reasoning_key = c.automation_id or c.name
        reasoned = reasoned_answers.get(reasoning_key)
        if isinstance(reasoned, str) and reasoned.strip():
            answer = reasoned.strip()
            actions.append(
                _action(
                    "set_text",
                    target=_scoped_target(c),
                    value=answer,
                    source="reasoning_broker",
                    verify={"kind": "value_equals", "value": answer},
                )
            )
            continue
        lookup = _field_answer(profile, c.name)
        if lookup.get("status") == "found":
            answer = str(lookup.get("value") or "")
            if answer:
                actions.append(
                    _action(
                        "set_text",
                        target=_scoped_target(c),
                        value=answer,
                        source=lookup.get("source"),
                        verify={"kind": "value_equals", "value": answer},
                    )
                )
        elif lookup.get("status") == "needs_reasoning":
            reasoning.append(
                {
                    "kind": "field_answer",
                    "field": c.name,
                    "automation_id": c.automation_id,
                    "profile_context": lookup.get("context"),
                    "page_context": {
                        "current_step": state.current_step,
                        "errors": state.errors,
                    },
                    "constraints": [
                        "Use only supplied applicant facts and page context.",
                        "Do not invent credentials, dates, employers, education, legal status, or health information.",
                        "Prefer concise truthful answers.",
                    ],
                }
            )
    return actions, reasoning


_GENERIC_GROUP_NAMES = {
    "applicationquestions",
    "voluntarydisclosures",
    "myinformation",
    "myexperience",
    "selfidentify",
    "review",
}
_SENSITIVE_CHOICE_TERMS = (
    "gender", "race", "ethnicity", "hispanic", "latino", "veteran",
    "disability", "medical", "religion", "sexual", "age", "dateofbirth",
    "agree", "termsandconditions",
)


def _question_group(control: Control) -> str | None:
    option_norm = _norm(control.name)
    for name in control.group_path:
        norm = _norm(name)
        if not norm or norm == option_norm or norm in {"yes", "no"} or norm in _GENERIC_GROUP_NAMES:
            continue
        return name
    return None


def _choice_is_sensitive(question: str) -> bool:
    norm = _norm(question)
    return any(term in norm for term in _SENSITIVE_CHOICE_TERMS)


def _plan_choice_fields(
    state: PageState,
    profile: dict[str, Any],
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[Control]] = {}
    for c in state.controls:
        if c.control_type != "ControlType.RadioButton" or not c.enabled:
            continue
        question = _question_group(c)
        if question:
            groups.setdefault(question, []).append(c)

    explicit = context.get("choice_answers")
    if not isinstance(explicit, dict):
        explicit = {}
    reasoned = context.get("reasoned_answers")
    if not isinstance(reasoned, dict):
        reasoned = {}

    actions: list[dict[str, Any]] = []
    reasoning: list[dict[str, Any]] = []
    for question, controls in groups.items():
        options = sorted({c.name for c in controls if c.name})
        if len(options) < 2:
            continue
        answer = explicit.get(question)
        source = "context.choice_answers"
        if not isinstance(answer, str) or not answer:
            answer = reasoned.get(question)
            source = "reasoning_broker"
        if not isinstance(answer, str) or not answer:
            selected = [control for control in controls if control.selected is True]
            if len(selected) == 1:
                continue
        if isinstance(answer, str) and answer:
            if answer not in options:
                reasoning.append({
                    "kind": "choice_answer",
                    "field": question,
                    "key": question,
                    "options": options,
                    "profile_context": resume_profile.reasoning_context(profile),
                    "page_context": {"current_step": state.current_step, "errors": state.errors},
                    "constraints": [
                        "Choose exactly one supplied option.",
                        "Use only supplied applicant facts and page context.",
                        "Do not invent legal, credential, health, demographic, or employment facts.",
                    ],
                    "reason": f"configured answer {answer!r} is not an available option",
                })
                continue
            desired = next(c for c in controls if c.name == answer)
            if desired.selected is True:
                continue
            actions.append(
                _action(
                    "select_choice",
                    target={
                        "control_type": "ControlType.RadioButton",
                        "group_name": question,
                        "name": answer,
                    },
                    source=source,
                    verify={"kind": "choice_selected", "group_name": question, "option": answer},
                )
            )
            continue
        if _choice_is_sensitive(question):
            continue
        reasoning.append({
            "kind": "choice_answer",
            "field": question,
            "key": question,
            "options": options,
            "profile_context": resume_profile.reasoning_context(profile),
            "page_context": {"current_step": state.current_step, "errors": state.errors},
            "constraints": [
                "Choose exactly one supplied option.",
                "Use only supplied applicant facts and page context.",
                "Do not invent legal, credential, health, demographic, or employment facts.",
            ],
        })
    return actions, reasoning


def _plan_source(state: PageState, context: dict[str, Any]) -> list[dict[str, Any]]:
    path = context.get("source_path")
    if not isinstance(path, list) or not path or not all(isinstance(x, str) and x for x in path):
        return []
    terminal = path[-1]
    if terminal in state.selected_pills:
        return []
    field = state.find(control_type="ControlType.Edit", automation_id="source--source")
    if not field:
        return []
    return [
        _action(
            "select_hierarchy",
            target={"automation_id": "source--source", "name": "How Did You Hear About Us?"},
            path=path,
            verify={"kind": "selected_pill_equals", "value": terminal},
        )
    ]


_EXPERIENCE_FIELD_ALIASES = {
    "company": "employer",
    "companyname": "employer",
    "employer": "employer",
    "employername": "employer",
    "jobtitle": "title",
    "positiontitle": "title",
    "position": "title",
    "title": "title",
    "startdate": "start",
    "employmentstartdate": "start",
    "enddate": "end",
    "employmentenddate": "end",
    "employerphone": "phone",
    "companyphone": "phone",
    "supervisor": "supervisor",
    "supervisorname": "supervisor",
    "salary": "salary",
}
_EXPERIENCE_TOGGLE_ALIASES = {
    "icurrentlyworkhere": "current",
    "currentjob": "current",
    "currentlyemployed": "current",
    "maywecontactthisemployer": "may_contact",
    "maycontactthisemployer": "may_contact",
    "maycontact": "may_contact",
}
_EDUCATION_OPTION_ALIASES = {
    "degree": "credential",
    "degreeorcredential": "credential",
}
_EDUCATION_FIELD_ALIASES = {
    "school": "school",
    "schooloruniversity": "school",
    "university": "school",
    "institution": "school",
    "schoolname": "school",
    "graduationyear": "end_year",
    "endyear": "end_year",
    "yearcompleted": "end_year",
}
_EXPERIENCE_FAMILY_TERMS = ("workexperience", "employmenthistory", "employmentexperience")
_EDUCATION_FAMILY_TERMS = ("education", "educationhistory")


def _source_for_section_family(family: str) -> str | None:
    normalized = _norm(family)
    if any(term in normalized for term in _EXPERIENCE_FAMILY_TERMS):
        return "experience"
    if any(term in normalized for term in _EDUCATION_FAMILY_TERMS):
        return "education"
    return None


def _identity_keys_for_source(source: str) -> tuple[str, ...]:
    if source == "experience":
        return ("employer", "title")
    if source == "education":
        return ("school",)
    return ()


def _record_identity_matches(record: dict[str, Any], anchors: dict[str, str]) -> bool:
    for key, observed in anchors.items():
        expected = _record_value(record, key)
        if expected is None or _norm(str(expected)) != _norm(observed):
            return False
    return True


def infer_repeating_sections(
    state: PageState,
    profile: dict[str, Any],
    *,
    trusted_empty_group_names: Iterable[str] | None = None,
) -> dict[str, Any]:
    resume_profile.validate_profile(profile)
    inventory = section_inventory(state)
    trusted_empty = {
        str(name)
        for name in (trusted_empty_group_names or ())
        if isinstance(name, str) and name
    }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for section in inventory["sections"]:
        source = _source_for_section_family(str(section["family"]))
        if source is None:
            continue
        grouped.setdefault(source, []).append(section)

    bindings: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for source, sections in grouped.items():
        records = profile.get(source)
        if not isinstance(records, list):
            continue
        sections = sorted(
            sections,
            key=lambda item: (
                float("inf") if item["top"] is None else item["top"],
                item["group_name"],
            ),
        )
        used_indexes: set[int] = set()
        prepared: list[dict[str, Any]] = []

        for section in sections:
            if not section.get("safe_named_scope"):
                skipped.append({
                    "group_name": section["group_name"],
                    "source": source,
                    "reason": "section scope is structurally ambiguous",
                })
                continue

            aliases = _EXPERIENCE_FIELD_ALIASES if source == "experience" else _EDUCATION_FIELD_ALIASES
            toggle_aliases = _EXPERIENCE_TOGGLE_ALIASES if source == "experience" else {}
            identity_keys = set(_identity_keys_for_source(source))
            fields: dict[str, str] = {}
            toggles: dict[str, str] = {}
            options: dict[str, str] = {}
            anchors: dict[str, str] = {}
            recognized = 0
            any_recognized_value = False
            unknown_inputs: list[str] = []

            for control in section["controls"]:
                label = str(control.get("name") or "")
                normalized = _norm(label)
                ctype = control.get("type")
                if ctype in {"ControlType.Edit", "ControlType.Spinner"}:
                    key = aliases.get(normalized)
                    if key:
                        fields[label] = key
                        recognized += 1
                        raw = control.get("value")
                        if raw is not None and str(raw).strip():
                            any_recognized_value = True
                            if key in identity_keys:
                                anchors[key] = str(raw).strip()
                    elif label:
                        unknown_inputs.append(label)
                elif ctype == "ControlType.CheckBox":
                    key = toggle_aliases.get(normalized)
                    if key:
                        toggles[label] = key
                        recognized += 1
                    elif label:
                        unknown_inputs.append(label)
                elif ctype == "ControlType.ComboBox" and source == "education":
                    key = _EDUCATION_OPTION_ALIASES.get(normalized)
                    if key:
                        options[label] = key
                        recognized += 1
                        raw_selection = control.get("selection")
                        raw_value = control.get("value")
                        if (
                            isinstance(raw_selection, list)
                            and any(isinstance(x, str) and x.strip() for x in raw_selection)
                        ) or (raw_value is not None and str(raw_value).strip()):
                            any_recognized_value = True
                    elif label:
                        unknown_inputs.append(label)

            if recognized < 2:
                skipped.append({
                    "group_name": section["group_name"],
                    "source": source,
                    "reason": "insufficient recognized field structure",
                    "recognized_fields": recognized,
                    "unknown_inputs": sorted(set(unknown_inputs)),
                })
                continue

            prepared.append({
                "section": section,
                "fields": fields,
                "toggles": toggles,
                "options": options,
                "anchors": anchors,
                "any_recognized_value": any_recognized_value,
                "unknown_inputs": sorted(set(unknown_inputs)),
            })

        # Resolve populated identity anchors first, independent of screen order.
        unresolved: list[dict[str, Any]] = []
        for item in prepared:
            anchors = item["anchors"]
            section = item["section"]
            if not anchors:
                unresolved.append(item)
                continue
            candidates = [
                index
                for index, record in enumerate(records)
                if index not in used_indexes
                and isinstance(record, dict)
                and _record_identity_matches(record, anchors)
            ]
            if len(candidates) != 1:
                skipped.append({
                    "group_name": section["group_name"],
                    "source": source,
                    "reason": (
                        "prefilled identity does not match canonical profile"
                        if len(candidates) == 0
                        else "prefilled identity is ambiguous"
                    ),
                    "anchors": dict(anchors),
                    "candidate_count": len(candidates),
                })
                continue
            index = candidates[0]
            used_indexes.add(index)
            bindings.append({
                "source": source,
                "record_index": index,
                "group_name": section["group_name"],
                "fields": item["fields"],
                "toggles": item["toggles"],
                "options": item["options"],
                "binding_confidence": "identity_anchor",
                "identity_anchors": dict(anchors),
                "unknown_inputs": item["unknown_inputs"],
            })

        # Empty sections are only position-bound when there is one blank starter
        # section, or when the runner just verified creation of that exact scope.
        for item in unresolved:
            section = item["section"]
            if item["any_recognized_value"]:
                skipped.append({
                    "group_name": section["group_name"],
                    "source": source,
                    "reason": "prefilled section lacks a canonical identity anchor",
                })
                continue

            group_name = str(section["group_name"])
            singleton_blank = len(prepared) == 1
            runner_trusted = group_name in trusted_empty
            if not singleton_blank and not runner_trusted:
                skipped.append({
                    "group_name": group_name,
                    "source": source,
                    "reason": "empty section requires trusted creation order",
                })
                continue

            remaining = [index for index in range(len(records)) if index not in used_indexes]
            if not remaining:
                skipped.append({
                    "group_name": group_name,
                    "source": source,
                    "reason": "no remaining canonical profile record",
                })
                continue
            index = remaining[0]
            used_indexes.add(index)
            bindings.append({
                "source": source,
                "record_index": index,
                "group_name": group_name,
                "fields": item["fields"],
                "toggles": item["toggles"],
                "options": item["options"],
                "binding_confidence": (
                    "trusted_created_empty"
                    if runner_trusted
                    else "single_blank_starter"
                ),
                "identity_anchors": {},
                "unknown_inputs": item["unknown_inputs"],
            })

    bindings.sort(
        key=lambda item: (
            item["source"],
            next(
                (
                    float("inf") if section["top"] is None else section["top"]
                    for section in inventory["sections"]
                    if section["group_name"] == item["group_name"]
                ),
                float("inf"),
            ),
            item["group_name"],
        )
    )
    return {
        "engine_version": ENGINE_VERSION,
        "current_step": state.current_step,
        "bindings": bindings,
        "skipped": skipped,
    }

def _default_family_for_source(source: str) -> str | None:
    if source == "experience":
        return "Work Experience"
    if source == "education":
        return "Education"
    return None


def _family_section_count(state: PageState, family: str) -> int:
    inventory = section_inventory(state)
    return sum(1 for item in inventory["sections"] if item.get("family") == family)


def _plan_repeating_section_growth(
    state: PageState,
    profile: dict[str, Any],
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    goals = context.get("repeating_section_goals")
    if not isinstance(goals, list):
        return [], []
    actions: list[dict[str, Any]] = []
    blockers: list[str] = []
    for goal in goals:
        if not isinstance(goal, dict):
            continue
        source = goal.get("source")
        if source not in {"experience", "education"}:
            blockers.append("repeating section goal has unsupported source")
            continue
        desired = goal.get("desired_count")
        if not isinstance(desired, int) or desired < 0:
            blockers.append(f"{source} repeating section goal has invalid desired_count")
            continue
        records = profile.get(source)
        if not isinstance(records, list):
            blockers.append(f"profile source {source} is unavailable")
            continue
        if desired > len(records):
            blockers.append(
                f"{source} desired_count {desired} exceeds canonical profile record count {len(records)}"
            )
            continue
        family = goal.get("family")
        if not isinstance(family, str) or not family:
            family = _default_family_for_source(source)
        if not family:
            blockers.append(f"{source} repeating section goal has no family")
            continue

        current = _family_section_count(state, family)
        if current >= desired:
            continue

        button_name = goal.get("add_button_name")
        if not isinstance(button_name, str) or not button_name:
            button_name = "Add Another"
        button_group = goal.get("add_button_group")
        if not isinstance(button_group, str) or not button_group:
            button_group = family

        candidates = [
            c for c in state.controls
            if c.control_type == "ControlType.Button"
            and c.name == button_name
            and c.enabled
            and not c.offscreen
            and button_group in c.group_path
        ]
        if len(candidates) != 1:
            blockers.append(
                f"{family} needs {desired} sections but exact add button match count is {len(candidates)}"
            )
            continue

        button = candidates[0]
        actions.append(
            _action(
                "invoke",
                target={
                    "control_type": "ControlType.Button",
                    "automation_id": button.automation_id,
                    "name": button.name,
                    "group_name": button_group,
                },
                source="context.repeating_section_goals",
                verify={
                    "kind": "section_count_increases",
                    "family": family,
                    "before_count": current,
                },
            )
        )
    return actions, blockers


def _record_value(record: dict[str, Any], key: str) -> Any:
    value: Any = record
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _selector_probe_key(control: Control) -> str:
    scope = _field_scope_name(control)
    return f"{scope}::{control.name}" if scope else control.name


def _selector_is_sensitive(control: Control) -> bool:
    text = " ".join([control.name, *control.group_path])
    return _choice_is_sensitive(text)


def _plan_selector_fields(
    state: PageState,
    profile: dict[str, Any],
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    option_cache = context.get("selector_options")
    if not isinstance(option_cache, dict):
        option_cache = {}
    reasoned = context.get("reasoned_answers")
    if not isinstance(reasoned, dict):
        reasoned = {}

    explicit_targets: set[tuple[str, str]] = set()
    configured = context.get("option_selections")
    if isinstance(configured, list):
        for item in configured:
            if not isinstance(item, dict) or not isinstance(item.get("target"), dict):
                continue
            target = item["target"]
            explicit_targets.add((str(target.get("group_name") or ""), str(target.get("name") or "")))

    actions: list[dict[str, Any]] = []
    reasoning: list[dict[str, Any]] = []
    blockers: list[str] = []
    for control in state.controls:
        if control.control_type != "ControlType.ComboBox" or not control.enabled:
            continue
        if control.value not in (None, "") or control.selection:
            continue
        scope = _field_scope_name(control) or ""
        if (scope, control.name) in explicit_targets:
            continue

        key = _selector_probe_key(control)
        options = option_cache.get(key)
        if not isinstance(options, list) or not options or not all(isinstance(x, str) and x for x in options):
            actions.append(
                _action(
                    "inspect_options",
                    target={
                        "control_type": "ControlType.ComboBox",
                        "automation_id": control.automation_id,
                        "name": control.name,
                        **({"group_name": scope} if scope else {}),
                    },
                    probe_key=key,
                    source="page_semantics",
                )
            )
            continue

        answer = reasoned.get(key)
        if isinstance(answer, str) and answer:
            if answer not in options:
                blockers.append(f"reasoned selector answer for {key} is not an observed option")
                continue
            actions.append(
                _action(
                    "select_option",
                    target={
                        "control_type": "ControlType.ComboBox",
                        "automation_id": control.automation_id,
                        "name": control.name,
                        **({"group_name": scope} if scope else {}),
                    },
                    value=answer,
                    source="reasoning_broker",
                    verify={"kind": "option_selected", "value": answer},
                )
            )
            continue

        if _selector_is_sensitive(control):
            blockers.append(f"sensitive selector requires explicit answer: {key}")
            continue

        reasoning.append({
            "kind": "choice_answer",
            "field": control.name,
            "key": key,
            "options": options,
            "profile_context": resume_profile.reasoning_context(profile),
            "page_context": {
                "current_step": state.current_step,
                "errors": state.errors,
                "group_name": scope or None,
            },
            "constraints": [
                "Choose exactly one supplied option.",
                "Use only supplied applicant facts and page context.",
                "Do not invent legal, credential, health, demographic, or employment facts.",
            ],
        })
    return actions, reasoning, blockers


def _option_is_selected(control: Control, value: str) -> bool:
    return (control.value or "") == value or value in control.selection


def _plan_option_selections(state: PageState, context: dict[str, Any]) -> list[dict[str, Any]]:
    configured = context.get("option_selections")
    if not isinstance(configured, list):
        return []
    actions: list[dict[str, Any]] = []
    for item in configured:
        if not isinstance(item, dict):
            continue
        target = item.get("target")
        value = item.get("value")
        if not isinstance(target, dict) or not target:
            continue
        if not isinstance(value, str) or not value:
            continue
        matches = [
            c for c in state.controls
            if (not target.get("control_type") or c.control_type == target.get("control_type"))
            and (not target.get("name") or c.name == target.get("name"))
            and (not target.get("automation_id") or c.automation_id == target.get("automation_id"))
            and (not target.get("group_name") or target.get("group_name") in c.group_path)
            and c.enabled
        ]
        if len(matches) != 1:
            continue
        control = matches[0]
        if _option_is_selected(control, value):
            continue
        actions.append(
            _action(
                "select_option",
                target=target,
                value=value,
                source=item.get("source") or "context.option_selections",
                verify={"kind": "option_selected", "value": value},
            )
        )
    return actions


def _record_override_value(
    context: dict[str, Any],
    source: str,
    index: int,
    key: str,
) -> Any:
    root = context.get("record_overrides")
    if not isinstance(root, dict):
        return None
    source_overrides = root.get(source)
    if not isinstance(source_overrides, dict):
        return None
    record_overrides = source_overrides.get(str(index), source_overrides.get(index))
    if not isinstance(record_overrides, dict):
        return None
    return _record_value(record_overrides, key)


def _grounded_record_value(
    record: dict[str, Any],
    context: dict[str, Any],
    source: str,
    index: int,
    key: str,
) -> Any:
    override = _record_override_value(context, source, index, key)
    if override not in (None, ""):
        return override
    return _record_value(record, key)


def _repeating_freeform_semantic(control: Control) -> str | None:
    text = " ".join(x for x in (control.name, control.help_text) if x)
    norm = _norm(text)
    has_reason = any(term in norm for term in (
        "reasonforleaving", "reasonyouleft", "whydidyouleave", "whyyouleft"
    ))
    has_duties = any(term in norm for term in (
        "duties", "responsibilities", "jobdescription", "roledescription",
        "descriptionofwork", "workperformed"
    ))
    if has_reason and has_duties:
        return "duties_and_reason"
    if has_reason:
        return "reason_for_leaving"
    label = _norm(control.name)
    if has_duties or label in {
        "duties", "responsibilities", "jobduties", "jobdescription",
        "roledescription", "description", "descriptionofwork",
    }:
        return "responsibilities"
    return None


def _bound_repeating_specs(
    state: PageState,
    profile: dict[str, Any],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    configured = context.get("repeating_sections")
    if not isinstance(configured, list):
        configured = []
    if context.get("auto_bind_repeating_sections") is True:
        inferred = infer_repeating_sections(
            state,
            profile,
            trusted_empty_group_names=context.get("trusted_empty_repeating_groups"),
        ).get("bindings", [])
        explicit_groups = {
            item.get("group_name")
            for item in configured
            if isinstance(item, dict) and isinstance(item.get("group_name"), str)
        }
        configured = list(configured) + [
            item for item in inferred
            if isinstance(item, dict) and item.get("group_name") not in explicit_groups
        ]
    return [item for item in configured if isinstance(item, dict)]


def _plan_repeating_freeform_fields(
    state: PageState,
    profile: dict[str, Any],
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    actions: list[dict[str, Any]] = []
    blockers: list[str] = []
    for spec in _bound_repeating_specs(state, profile, context):
        source = spec.get("source")
        index = spec.get("record_index")
        group_name = spec.get("group_name")
        if source != "experience" or not isinstance(index, int) or index < 0:
            continue
        if not isinstance(group_name, str) or not group_name:
            continue
        records = profile.get(source)
        if not isinstance(records, list) or index >= len(records):
            continue
        record = records[index]
        if not isinstance(record, dict):
            continue

        mapped_labels = set()
        for key in ("fields", "toggles", "options"):
            mapping = spec.get(key)
            if isinstance(mapping, dict):
                mapped_labels.update(str(x) for x in mapping if isinstance(x, str))

        candidates = [
            control for control in state.controls
            if control.control_type == "ControlType.Edit"
            and control.enabled
            and control.name not in mapped_labels
            and group_name in control.group_path
            and control.value in (None, "")
        ]
        for control in candidates:
            semantic = _repeating_freeform_semantic(control)
            if semantic is None:
                continue
            responsibilities = _grounded_record_value(
                record, context, source, index, "responsibilities"
            )
            reason = _grounded_record_value(
                record, context, source, index, "reason_for_leaving"
            )

            rendered: str | None = None
            source_desc: str | None = None
            if semantic == "responsibilities":
                if responsibilities not in (None, ""):
                    rendered = str(responsibilities).strip()
                    source_desc = f"profile.{source}[{index}].responsibilities"
                else:
                    blockers.append(
                        f"{group_name} {control.name}: missing responsibilities for bound experience record {index}"
                    )
            elif semantic == "reason_for_leaving":
                if reason not in (None, ""):
                    rendered = str(reason).strip()
                    source_desc = (
                        f"context.record_overrides.{source}[{index}].reason_for_leaving"
                        if _record_override_value(context, source, index, "reason_for_leaving") not in (None, "")
                        else f"profile.{source}[{index}].reason_for_leaving"
                    )
                else:
                    blockers.append(
                        f"{group_name} {control.name}: missing reason_for_leaving for bound experience record {index}"
                    )
            elif semantic == "duties_and_reason":
                missing: list[str] = []
                if responsibilities in (None, ""):
                    missing.append("responsibilities")
                if reason in (None, ""):
                    missing.append("reason_for_leaving")
                if missing:
                    blockers.append(
                        f"{group_name} {control.name}: missing {', '.join(missing)} for bound experience record {index}"
                    )
                else:
                    rendered = (
                        f"Duties: {str(responsibilities).strip()}\n"
                        f"Reason for Leaving: {str(reason).strip()}"
                    )
                    source_desc = f"grounded composite profile.{source}[{index}]"

            if rendered:
                actions.append(
                    _action(
                        "set_text",
                        target={
                            "automation_id": control.automation_id,
                            "name": control.name,
                            "group_name": group_name,
                        },
                        value=rendered,
                        source=source_desc,
                        verify={"kind": "value_equals", "value": rendered},
                    )
                )
    return actions, blockers


def _parse_profile_date(value: Any) -> tuple[int, int | None, int | None] | None:
    text = str(value or "").strip()
    m = re.fullmatch(r"(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?", text)
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2)) if m.group(2) else None
    day = int(m.group(3)) if m.group(3) else None
    if month is not None and not 1 <= month <= 12:
        return None
    if day is not None:
        try:
            date(year, month or 1, day)
        except ValueError:
            return None
    return year, month, day


def _date_format_hint(control: Control) -> str | None:
    hay = " ".join(x for x in (control.name, control.help_text, control.value or "") if x)
    compact = hay.upper().replace(" ", "")
    if "MM/DD/YYYY" in compact or "M/D/YYYY" in compact:
        return "mdy"
    if "MM/YYYY" in compact or "M/YYYY" in compact:
        return "my"
    if "YYYY-MM-DD" in compact:
        return "ymd"
    if "YYYY-MM" in compact:
        return "ym"
    normalized = _norm(control.name)
    if normalized in {"graduationyear", "endyear", "yearcompleted"}:
        return "year"
    return None


def _render_profile_date_for_control(value: Any, control: Control) -> tuple[str | None, str | None]:
    parsed = _parse_profile_date(value)
    if parsed is None:
        return None, "profile date is not canonical YYYY, YYYY-MM, or YYYY-MM-DD"
    year, month, day = parsed
    hint = _date_format_hint(control)
    if hint == "year":
        return str(year), None
    if hint == "my":
        if month is None:
            return None, "field requires month/year but profile has only year"
        return f"{month:02d}/{year:04d}", None
    if hint == "mdy":
        if month is None or day is None:
            return None, "field requires full date but profile does not contain a day"
        return f"{month:02d}/{day:02d}/{year:04d}", None
    if hint == "ym":
        if month is None:
            return None, "field requires year-month but profile has only year"
        return f"{year:04d}-{month:02d}", None
    if hint == "ymd":
        if month is None or day is None:
            return None, "field requires full ISO date but profile does not contain a day"
        return f"{year:04d}-{month:02d}-{day:02d}", None
    return None, "date field has no deterministic format hint"


def _is_repeating_date_key(source: str, profile_key: str) -> bool:
    return (
        (source == "experience" and profile_key in {"start", "end"})
        or (source == "education" and profile_key in {"end_year"})
    )


def _repeating_date_blockers(
    state: PageState,
    profile: dict[str, Any],
    context: dict[str, Any],
) -> list[str]:
    configured = _bound_repeating_specs(state, profile, context)

    blockers: list[str] = []
    for spec in configured:
        if not isinstance(spec, dict):
            continue
        source = spec.get("source")
        group_name = spec.get("group_name")
        index = spec.get("record_index", 0)
        fields = spec.get("fields")
        if source not in {"experience", "education"} or not isinstance(group_name, str):
            continue
        records = profile.get(source)
        if not isinstance(index, int) or not isinstance(records, list) or index >= len(records):
            continue
        record = records[index]
        if not isinstance(record, dict) or not isinstance(fields, dict):
            continue
        for page_label, profile_key in fields.items():
            if not isinstance(page_label, str) or not isinstance(profile_key, str):
                continue
            if not _is_repeating_date_key(source, profile_key):
                continue
            value = _record_value(record, profile_key)
            if value in (None, ""):
                continue
            matches = [
                control for control in state.controls
                if control.control_type in {"ControlType.Edit", "ControlType.Spinner"}
                and control.name == page_label
                and group_name in control.group_path
                and control.enabled
            ]
            if len(matches) != 1:
                continue
            control = matches[0]
            if control.value not in (None, ""):
                continue
            rendered, reason = _render_profile_date_for_control(value, control)
            if rendered is None:
                blockers.append(f"{group_name} {page_label}: {reason}")
    return blockers


def _plan_repeating_sections(
    state: PageState,
    profile: dict[str, Any],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    configured = context.get("repeating_sections")
    if not isinstance(configured, list):
        configured = []
    if context.get("auto_bind_repeating_sections") is True:
        inferred = infer_repeating_sections(
            state,
            profile,
            trusted_empty_group_names=context.get("trusted_empty_repeating_groups"),
        ).get("bindings", [])
        explicit_groups = {
            item.get("group_name")
            for item in configured
            if isinstance(item, dict) and isinstance(item.get("group_name"), str)
        }
        configured = list(configured) + [
            item for item in inferred
            if isinstance(item, dict) and item.get("group_name") not in explicit_groups
        ]
    if not configured:
        return []
    actions: list[dict[str, Any]] = []
    for spec in configured:
        if not isinstance(spec, dict):
            continue
        source = spec.get("source")
        group_name = spec.get("group_name")
        index = spec.get("record_index", 0)
        fields = spec.get("fields")
        toggles = spec.get("toggles")
        options = spec.get("options")
        if source not in {"experience", "education"}:
            continue
        if not isinstance(group_name, str) or not group_name:
            continue
        if not isinstance(index, int) or index < 0:
            continue
        records = profile.get(source)
        if not isinstance(records, list) or index >= len(records):
            continue
        record = records[index]
        if not isinstance(record, dict) or not isinstance(fields, dict):
            continue
        for page_label, profile_key in fields.items():
            if not isinstance(page_label, str) or not page_label:
                continue
            if not isinstance(profile_key, str) or not profile_key:
                continue
            value = _record_value(record, profile_key)
            if value is None or value == "":
                continue
            if isinstance(value, bool):
                continue
            matches = [
                c for c in state.controls
                if c.control_type in {"ControlType.Edit", "ControlType.Spinner"}
                and c.name == page_label
                and group_name in c.group_path
                and c.enabled
            ]
            if len(matches) != 1:
                continue
            control = matches[0]
            if _is_repeating_date_key(source, profile_key):
                rendered, _date_reason = _render_profile_date_for_control(value, control)
                if rendered is None:
                    continue
            else:
                rendered = str(value)
            if (control.value or "") == rendered:
                continue
            actions.append(
                _action(
                    "set_text",
                    target={
                        "automation_id": control.automation_id,
                        "name": control.name,
                        "group_name": group_name,
                    },
                    value=rendered,
                    source=f"profile.{source}[{index}].{profile_key}",
                    verify={"kind": "value_equals", "value": rendered},
                )
            )
        if isinstance(toggles, dict):
            for page_label, profile_key in toggles.items():
                if not isinstance(page_label, str) or not page_label:
                    continue
                if not isinstance(profile_key, str) or not profile_key:
                    continue
                value = _record_value(record, profile_key)
                if not isinstance(value, bool):
                    continue
                matches = [
                    c for c in state.controls
                    if c.control_type == "ControlType.CheckBox"
                    and c.name == page_label
                    and group_name in c.group_path
                    and c.enabled
                ]
                if len(matches) != 1:
                    continue
                control = matches[0]
                want = "On" if value else "Off"
                if (control.toggle or "") == want:
                    continue
                actions.append(
                    _action(
                        "set_toggle",
                        target={
                            "automation_id": control.automation_id,
                            "name": control.name,
                            "group_name": group_name,
                        },
                        checked=value,
                        source=f"profile.{source}[{index}].{profile_key}",
                        verify={"kind": "toggle_equals", "value": want},
                    )
                )
        if isinstance(options, dict):
            for page_label, profile_key in options.items():
                if not isinstance(page_label, str) or not page_label:
                    continue
                if not isinstance(profile_key, str) or not profile_key:
                    continue
                value = _record_value(record, profile_key)
                if value is None or value == "" or isinstance(value, (bool, dict, list)):
                    continue
                matches = [
                    c for c in state.controls
                    if c.control_type == "ControlType.ComboBox"
                    and c.name == page_label
                    and group_name in c.group_path
                    and c.enabled
                ]
                if len(matches) != 1:
                    continue
                control = matches[0]
                rendered = str(value)
                if _option_is_selected(control, rendered):
                    continue
                actions.append(
                    _action(
                        "select_option",
                        target={
                            "control_type": "ControlType.ComboBox",
                            "automation_id": control.automation_id,
                            "name": control.name,
                            "group_name": group_name,
                        },
                        value=rendered,
                        source=f"profile.{source}[{index}].{profile_key}",
                        verify={"kind": "option_selected", "value": rendered},
                    )
                )
    return actions


def _plan_attachments(state: PageState, context: dict[str, Any]) -> list[dict[str, Any]]:
    configured = context.get("attachments")
    if not isinstance(configured, list):
        return []
    actions: list[dict[str, Any]] = []
    for item in configured:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        expected_filename = item.get("expected_filename")
        target = item.get("target")
        success_text = item.get("success_text") or "Successfully Uploaded!"
        if not isinstance(path, str) or not path:
            continue
        if not isinstance(expected_filename, str) or not expected_filename:
            continue
        if not isinstance(target, dict) or not target:
            continue
        if state.contains_text(expected_filename) and state.contains_text(str(success_text)):
            continue
        matches = state.find(
            control_type=target.get("control_type") if isinstance(target.get("control_type"), str) else None,
            name=target.get("name") if isinstance(target.get("name"), str) else None,
            automation_id=target.get("automation_id") if isinstance(target.get("automation_id"), str) else None,
        )
        if len(matches) != 1:
            continue
        actions.append(
            _action(
                "upload_file",
                target=target,
                path=path,
                expected_filename=expected_filename,
                success_text=str(success_text),
                source="context.attachments",
                verify={
                    "kind": "upload_verified",
                    "expected_filename": expected_filename,
                    "success_text": str(success_text),
                },
            )
        )
    return actions


def _control_semantically_filled(control: Control, state: PageState) -> bool:
    if control.control_type in {"ControlType.Edit", "ControlType.Spinner"}:
        value = (control.value or "").strip()
        if value and _norm(value) not in {"mm", "dd", "yyyy", "mmddyyyy", "mmyyyy"}:
            return True
        if control.automation_id in _IGNORED_EDIT_AUTOMATION_IDS and state.selected_pills:
            return True
        return False
    if control.control_type == "ControlType.ComboBox":
        if any(str(x).strip() for x in control.selection):
            return True
        return bool((control.value or "").strip())
    if control.control_type == "ControlType.CheckBox":
        return (control.toggle or "").lower() == "on"
    if control.control_type == "ControlType.RadioButton":
        return control.selected is True
    return True


def _required_field_blockers(state: PageState) -> list[str]:
    blockers: list[str] = []
    required_controls = [
        c for c in state.controls
        if c.required and c.enabled and not c.offscreen
        and c.control_type in {
            "ControlType.Edit",
            "ControlType.Spinner",
            "ControlType.ComboBox",
            "ControlType.CheckBox",
            "ControlType.RadioButton",
        }
    ]

    # Radio requiredness is group-level: one selected option satisfies the group.
    radio_groups: dict[str, list[Control]] = {}
    for control in required_controls:
        if control.control_type != "ControlType.RadioButton":
            continue
        group = _field_scope_name(control) or " / ".join(control.group_path) or control.name
        radio_groups.setdefault(group, []).append(control)

    handled_radio_groups: set[str] = set()
    for control in required_controls:
        label = control.name or control.automation_id or control.control_type
        scope = _field_scope_name(control)
        prefix = f"{scope} " if scope else ""
        if control.control_type == "ControlType.RadioButton":
            group = scope or " / ".join(control.group_path) or control.name
            if group in handled_radio_groups:
                continue
            handled_radio_groups.add(group)
            peers = radio_groups.get(group, [])
            if peers and any(peer.selected is True for peer in peers):
                continue
            blockers.append(f"{group}: required choice has no selected option")
            continue
        if not _control_semantically_filled(control, state):
            blockers.append(f"{prefix}{label}: required field is unresolved")
    return blockers


def _plan_step4(state: PageState, policy: EnginePolicy, context: dict[str, Any]) -> dict[str, Any] | None:
    agree = state.find(control_type="ControlType.CheckBox", name="I agree")
    if not agree:
        return None
    current = (agree[0].toggle or "").lower()
    if current == "on":
        return None
    if not policy.allow_legal_certification or context.get("certify_truthfulness") is not True:
        return {
            "status": "blocked",
            "reason": "legal certification requires explicit policy authorization and certify_truthfulness=true",
            "actions": [],
            "reasoning_requests": [],
        }
    return {
        "status": "act",
        "reason": "required legal certification is off",
        "actions": [
            _action(
                "set_toggle",
                target={"automation_id": agree[0].automation_id, "name": "I agree"},
                checked=True,
                verify={"kind": "toggle_equals", "value": "On"},
            )
        ],
        "reasoning_requests": [],
    }


def _date_parts(application_date: str | None) -> tuple[str, str, str] | None:
    if not application_date:
        return None
    try:
        parsed = date.fromisoformat(application_date)
    except ValueError as exc:
        raise ValueError("application_date must be YYYY-MM-DD") from exc
    return str(parsed.month), str(parsed.day), str(parsed.year)


def _plan_step5(state: PageState, profile: dict[str, Any], policy: EnginePolicy, context: dict[str, Any]) -> dict[str, Any] | None:
    actions: list[dict[str, Any]] = []
    name = state.find(control_type="ControlType.Edit", name="Name")
    if name and name[0].value in (None, ""):
        lookup = _field_answer(profile, "Name")
        if lookup.get("status") == "found":
            value = str(lookup["value"])
            actions.append(_action("set_text", target={"name": "Name", "automation_id": name[0].automation_id}, value=value, source=lookup.get("source"), verify={"kind": "value_equals", "value": value}))

    parts = _date_parts(context.get("application_date"))
    if parts:
        for label, value in zip(("Month", "Day", "Year"), parts):
            controls = state.find(control_type="ControlType.Spinner", name=label)
            if controls and (controls[0].value or "") != value:
                actions.append(_action("set_text", target={"name": label, "automation_id": controls[0].automation_id}, value=value, source="context.application_date", verify={"kind": "value_equals", "value": value}))

    if policy.prefer_decline_sensitive:
        for label in _SENSITIVE_DECLINE_LABELS:
            matches = [c for c in state.controls if c.control_type == "ControlType.CheckBox" and _norm(c.name) == _norm(label)]
            if matches and (matches[0].toggle or "").lower() != "on":
                actions.append(_action("set_toggle", target={"name": matches[0].name, "automation_id": matches[0].automation_id}, checked=True, source="privacy_policy", verify={"kind": "toggle_equals", "value": "On"}))
                break

    if actions:
        return {
            "status": "act",
            "reason": "restore or complete required self-identification metadata without inferring sensitive facts",
            "actions": actions,
            "reasoning_requests": [],
        }
    return None


def _review_controls_named(state: PageState, text: str) -> list[Control]:
    needle = _norm(text)
    if not needle:
        return []
    return [control for control in state.controls if _norm(control.name) == needle]


def _review_controls_in_scope(state: PageState, group_name: str) -> list[Control]:
    return [
        control
        for control in state.controls
        if group_name in control.group_path or control.name == group_name
    ]


def _review_field_value_mismatch(
    state: PageState,
    *,
    field: str,
    value: str,
    group_name: str | None = None,
) -> str | None:
    field_controls = _review_controls_named(state, field)
    if not field_controls:
        # Workday does not necessarily render every field on final Review.
        return None

    if group_name:
        scoped = _review_controls_in_scope(state, group_name)
        if scoped:
            scoped_field = any(_norm(control.name) == _norm(field) for control in scoped)
            if not scoped_field:
                # The requested field is not rendered in this scope; preserve
                # the existing skip semantics rather than guessing.
                return None
            scoped_value = any(_norm(control.name) == _norm(value) for control in scoped)
            if not scoped_value:
                return (
                    f"review field {field!r} in {group_name!r} "
                    f"missing verified value: {value}"
                )
            return None

        # If the Review surface dropped group ancestry, a unique field label is
        # still unambiguous and can use the historical global check. Repeated
        # labels are not safely attributable to any one record.
        if len(field_controls) > 1:
            return (
                f"review field {field!r} is repeated but scope {group_name!r} "
                "is unavailable; verified value cannot be attributed safely"
            )

    if not state.contains_text(value):
        return f"review field {field!r} missing verified value: {value}"
    return None


def _review_mismatches(state: PageState, context: dict[str, Any]) -> list[str]:
    expected: list[Any] = []
    manual = context.get("review_expectations")
    if isinstance(manual, list):
        expected.extend(manual)
    verified = context.get("verified_review_expectations")
    if isinstance(verified, list):
        expected.extend(verified)
    mismatches: list[str] = []
    for item in expected:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        value = str(item.get("value") or "")
        if kind == "contains_text" and value and not state.contains_text(value):
            mismatches.append(f"missing review text: {value}")
        elif kind == "not_contains_text" and value and state.contains_text(value):
            mismatches.append(f"unexpected review text: {value}")
        elif kind == "review_field_value":
            field = str(item.get("field") or "")
            group_name = item.get("group_name")
            group_name = group_name if isinstance(group_name, str) and group_name else None
            if field and value:
                mismatch = _review_field_value_mismatch(
                    state,
                    field=field,
                    value=value,
                    group_name=group_name,
                )
                if mismatch:
                    mismatches.append(mismatch)
    return mismatches


def _plan_entrypoint(state: PageState, context: dict[str, Any]) -> dict[str, Any]:
    spec = context.get("entrypoint")
    if not isinstance(spec, dict):
        return {
            "status": "blocked",
            "reason": "configured entrypoint contract is invalid",
            "entrypoint_blockers": ["entrypoint contract is not an object"],
        }
    target = spec.get("target")
    verify = spec.get("verify")
    if not isinstance(target, dict) or not isinstance(verify, dict):
        return {
            "status": "blocked",
            "reason": "configured entrypoint contract is invalid",
            "entrypoint_blockers": ["entrypoint target or verifier is missing"],
        }

    name = target.get("name")
    control_type = target.get("control_type")
    automation_id = target.get("automation_id")
    group_name = target.get("group_name")
    matches: list[Control] = []
    for control in state.controls:
        if control.offscreen or not control.enabled:
            continue
        if isinstance(control_type, str) and control_type and control.control_type != control_type:
            continue
        if isinstance(name, str) and name and control.name != name:
            continue
        if isinstance(automation_id, str) and automation_id and control.automation_id != automation_id:
            continue
        if isinstance(group_name, str) and group_name and group_name not in control.group_path:
            continue
        matches.append(control)

    if len(matches) != 1:
        return {
            "status": "blocked",
            "reason": "configured application entrypoint is not uniquely available",
            "entrypoint_blockers": [f"entrypoint target match count {len(matches)}"],
        }

    action_target = {
        key: value
        for key, value in target.items()
        if key in {"control_type", "name", "automation_id", "group_name"}
        and isinstance(value, str)
        and value
    }
    return {
        "status": "act",
        "reason": "manifest-authorized application entrypoint is available",
        "actions": [
            _action(
                "invoke",
                target=action_target,
                verify=dict(verify),
            )
        ],
    }


def plan(
    profile: dict[str, Any],
    snapshot: PageState,
    policy: EnginePolicy,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resume_profile.validate_profile(profile)
    context = context or {}
    step = snapshot.current_step

    base: dict[str, Any] = {
        "engine_version": ENGINE_VERSION,
        "current_step": step,
        "errors": snapshot.errors,
        "actions": [],
        "reasoning_requests": [],
    }

    if any(snapshot.contains_text(text) for text in _COMPLETION_TEXTS):
        return {**base, "status": "done", "reason": "provider page indicates application completion"}

    if step is None and context.get("entrypoint") is not None:
        return {**base, **_plan_entrypoint(snapshot, context)}

    if step and step["number"] == 6:
        mismatches = _review_mismatches(snapshot, context)
        if snapshot.errors:
            return {**base, "status": "blocked", "reason": "review contains validation errors", "review_mismatches": mismatches}
        if mismatches and policy.fail_on_review_mismatch:
            return {**base, "status": "blocked", "reason": "final review semantic assertions failed", "review_mismatches": mismatches}
        submit = snapshot.find(control_type="ControlType.Button", name="Submit", visible_only=True, enabled_only=True)
        if not submit:
            return {**base, "status": "done", "reason": "no enabled Submit control on review", "review_mismatches": mismatches}
        if not policy.allow_submit:
            return {**base, "status": "ready_to_submit", "reason": "review passed but submit policy is disabled", "review_mismatches": mismatches}
        return {
            **base,
            "status": "act",
            "reason": "review passed and submit is authorized",
            "review_mismatches": mismatches,
            "actions": [_action("invoke", target={"name": "Submit", "control_type": "ControlType.Button"}, verify={"kind": "control_absent", "name": "Submit"})],
        }

    if step and step["number"] == 4:
        step4 = _plan_step4(snapshot, policy, context)
        if step4:
            return {**base, **step4}

    if step and step["number"] == 5:
        step5 = _plan_step5(snapshot, profile, policy, context)
        if step5:
            return {**base, **step5}

    actions, reasoning = _plan_text_fields(snapshot, profile, context)
    choice_actions, choice_reasoning = _plan_choice_fields(snapshot, profile, context)
    option_actions = _plan_option_selections(snapshot, context)
    selector_actions, selector_reasoning, selector_blockers = _plan_selector_fields(snapshot, profile, context)
    repeating_actions = _plan_repeating_sections(snapshot, profile, context)
    repeating_freeform_actions, repeating_freeform_blockers = _plan_repeating_freeform_fields(
        snapshot, profile, context
    )
    repeating_date_blockers = _repeating_date_blockers(snapshot, profile, context)
    growth_actions, growth_blockers = _plan_repeating_section_growth(snapshot, profile, context)
    attachment_actions = _plan_attachments(snapshot, context)
    required_field_blockers = _required_field_blockers(snapshot)
    actions = attachment_actions + repeating_actions + repeating_freeform_actions + option_actions + choice_actions + growth_actions + selector_actions + actions
    reasoning = choice_reasoning + selector_reasoning + reasoning
    if step and step["number"] == 1:
        actions = _plan_source(snapshot, context) + actions

    if actions:
        return {**base, "status": "act", "reason": "deterministic page actions available", "actions": actions, "reasoning_requests": reasoning}

    if reasoning:
        return {**base, "status": "needs_reasoning", "reason": "one or more fields require grounded reasoning", "reasoning_requests": reasoning}

    if repeating_freeform_blockers:
        return {
            **base,
            "status": "blocked",
            "reason": "repeating freeform field lacks grounded record facts",
            "repeating_freeform_blockers": repeating_freeform_blockers,
        }

    if repeating_date_blockers:
        return {
            **base,
            "status": "blocked",
            "reason": "repeating date field cannot be formatted deterministically",
            "repeating_date_blockers": repeating_date_blockers,
        }

    if growth_blockers:
        return {
            **base,
            "status": "blocked",
            "reason": "repeating section goal is not safely satisfiable",
            "repeating_section_blockers": growth_blockers,
        }

    if selector_blockers:
        return {
            **base,
            "status": "blocked",
            "reason": "selector requires explicit or grounded resolution",
            "selector_blockers": selector_blockers,
        }

    if required_field_blockers:
        return {
            **base,
            "status": "blocked",
            "reason": "required field coverage is incomplete",
            "required_field_blockers": required_field_blockers,
        }

    save = snapshot.find(control_type="ControlType.Button", name="Save and Continue", visible_only=True, enabled_only=True)
    if save:
        return {
            **base,
            "status": "act",
            "reason": "no unresolved deterministic work on current step",
            "actions": [_action("invoke", target={"name": "Save and Continue", "control_type": "ControlType.Button"}, verify={"kind": "step_changes", "from": step})],
        }

    return {**base, "status": "blocked", "reason": "no safe action identified"}


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Closed-loop job application planner v2")
    sub = ap.add_subparsers(dest="command", required=True)

    compact = sub.add_parser("compact", help="reduce a raw page snapshot to reasoning-relevant state")
    compact.add_argument("--snapshot", required=True)

    inventory = sub.add_parser("inventory", help="inventory named form scopes and repeated-section candidates")
    inventory.add_argument("--snapshot", required=True)

    bindings = sub.add_parser("bindings", help="infer conservative profile-record bindings for repeated sections")
    bindings.add_argument("--profile", required=True)
    bindings.add_argument("--snapshot", required=True)

    planner = sub.add_parser("plan", help="produce verified action intents for one page state")
    planner.add_argument("--profile", required=True)
    planner.add_argument("--snapshot", required=True)
    planner.add_argument("--policy")
    planner.add_argument("--context")

    ns = ap.parse_args(argv)
    state = PageState.from_obj(_load_json(ns.snapshot))

    if ns.command == "compact":
        result = compact_snapshot(state)
    elif ns.command == "inventory":
        result = section_inventory(state)
    elif ns.command == "bindings":
        profile = resume_profile.load_profile(ns.profile)
        result = infer_repeating_sections(state, profile)
    else:
        profile = resume_profile.load_profile(ns.profile)
        policy = EnginePolicy.from_obj(_load_json(ns.policy) if ns.policy else None)
        context = _load_json(ns.context) if ns.context else {}
        result = plan(profile, state, policy, context)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
