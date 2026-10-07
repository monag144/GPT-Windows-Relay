#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import resume_profile
import windows_tools

GPT_WINDOWS_JOB_APPLICATION_HELPER_V1 = True


def render_value(value: Any) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def prepare(profile: dict[str, Any], field: str, copied_context: str) -> dict[str, Any]:
    if not isinstance(copied_context, str):
        raise TypeError("copied_context must be str")
    lookup = resume_profile.lookup_field(profile, field)
    base = {
        "kind": "job_application_answer_plan",
        "field": field,
        "copied_context": copied_context,
        "deterministic": bool(lookup.get("deterministic")),
    }
    if lookup["status"] == "found":
        return {
            **base,
            "status": "ready",
            "answer": render_value(lookup.get("value")),
            "source": lookup.get("source"),
            "reasoning_required": False,
        }
    if lookup["status"] == "missing":
        return {
            **base,
            "status": "missing_profile_data",
            "source": lookup.get("source"),
            "reasoning_required": False,
            "reason": "mapped factual field is empty; do not invent a value",
        }
    return {
        **base,
        "status": "needs_reasoning",
        "reasoning_required": True,
        "reason": lookup.get("reason"),
        "reasoning_request": {
            "question": field,
            "copied_context": copied_context,
            "profile_context": lookup.get("context"),
            "constraints": [
                "Use only supplied profile/context facts.",
                "Do not invent credentials, dates, employers, education, authorization, or other factual claims.",
                "Return only the proposed field answer unless explanation is explicitly requested.",
            ],
        },
    }


def prepare_from_clipboard(profile: dict[str, Any], field: str) -> dict[str, Any]:
    copied = windows_tools.clipboard_read_text()
    if copied is None:
        return {"kind":"job_application_answer_plan","field":field,"status":"clipboard_has_no_text","reasoning_required":False,"deterministic":False}
    return prepare(profile, field, copied)


def apply_answer(answer: str, *, window_title: str, field_name: str | None = None, automation_id: str | None = None, process_id: int | None = None) -> dict[str, Any]:
    if not isinstance(answer, str) or answer == "":
        raise ValueError("non-empty answer is required")
    result = windows_tools.field_set_text(window_title, answer, field_name=field_name, automation_id=automation_id, process_id=process_id)
    return {"kind":"job_application_apply_result","ok":True,"answer_chars":len(answer),"field_result":result}


def main(argv: list[str] | None = None) -> int:
    ap=argparse.ArgumentParser(description="Simple ChatGPT-mediated job application helper")
    sub=ap.add_subparsers(dest="command",required=True)
    prep=sub.add_parser("prepare")
    prep.add_argument("--profile",required=True); prep.add_argument("--field",required=True)
    cg=prep.add_mutually_exclusive_group(required=True); cg.add_argument("--clipboard",action="store_true"); cg.add_argument("--context")
    apply=sub.add_parser("apply")
    apply.add_argument("--answer",required=True); apply.add_argument("--window-title",required=True); apply.add_argument("--field-name"); apply.add_argument("--automation-id"); apply.add_argument("--process-id",type=int)
    ns=ap.parse_args(argv)
    if ns.command=="prepare":
        profile=resume_profile.load_profile(ns.profile)
        result=prepare_from_clipboard(profile,ns.field) if ns.clipboard else prepare(profile,ns.field,ns.context)
    else:
        result=apply_answer(ns.answer,window_title=ns.window_title,field_name=ns.field_name,automation_id=ns.automation_id,process_id=ns.process_id)
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0


if __name__=="__main__": raise SystemExit(main())
