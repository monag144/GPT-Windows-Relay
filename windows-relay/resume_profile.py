#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

GPT_WINDOWS_RESUME_PROFILE_V1 = True
SCHEMA_VERSION = 1


def empty_profile() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "identity": {"first_name": "", "middle_name": "", "last_name": "", "preferred_name": ""},
        "contact": {"email": "", "phone": "", "city": "", "state": "", "postal_code": "", "country": ""},
        "links": {"linkedin": "", "portfolio": "", "github": ""},
        "work_authorization": {"authorized_to_work": None, "requires_sponsorship": None},
        "experience": [],
        "education": [],
        "certifications": [],
        "skills": [],
        "availability": {"start_date": "", "schedule": "", "travel_percent": None, "relocation": None},
        "custom": {},
    }


def normalize_field(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("field name must be str")
    return re.sub(r"[^a-z0-9]+", "", value.lower())


ALIASES = {
    "firstname": "identity.first_name", "givenname": "identity.first_name",
    "middlename": "identity.middle_name",
    "lastname": "identity.last_name", "surname": "identity.last_name", "familyname": "identity.last_name",
    "preferredname": "identity.preferred_name",
    "email": "contact.email", "emailaddress": "contact.email",
    "phone": "contact.phone", "phonenumber": "contact.phone", "mobilephone": "contact.phone",
    "city": "contact.city", "currentcity": "contact.city",
    "state": "contact.state", "province": "contact.state", "stateprovince": "contact.state",
    "zipcode": "contact.postal_code", "postalcode": "contact.postal_code",
    "country": "contact.country",
    "linkedin": "links.linkedin", "linkedinurl": "links.linkedin",
    "portfolio": "links.portfolio", "portfoliourl": "links.portfolio", "website": "links.portfolio",
    "github": "links.github", "githuburl": "links.github",
    "authorizedtowork": "work_authorization.authorized_to_work",
    "legallyauthorizedtowork": "work_authorization.authorized_to_work",
    "areyoulegallyauthorizedtowork": "work_authorization.authorized_to_work",
    "requiressponsorship": "work_authorization.requires_sponsorship",
    "needsponsorship": "work_authorization.requires_sponsorship",
    "willyourequiresponsorship": "work_authorization.requires_sponsorship",
    "availablestartdate": "availability.start_date", "startdate": "availability.start_date",
    "workschedule": "availability.schedule", "availability": "availability.schedule",
    "travelpercent": "availability.travel_percent",
    "willingtorelocate": "availability.relocation", "relocation": "availability.relocation",
}


def validate_profile(profile: dict[str, Any]) -> None:
    if not isinstance(profile, dict):
        raise ValueError("profile must be an object")
    if profile.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported schema_version")
    for key in ("identity", "contact", "links", "work_authorization", "availability", "custom"):
        if not isinstance(profile.get(key), dict):
            raise ValueError(f"{key} must be an object")
    for key in ("experience", "education", "certifications", "skills"):
        if not isinstance(profile.get(key), list):
            raise ValueError(f"{key} must be a list")


def load_profile(path: str | Path) -> dict[str, Any]:
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_profile(profile)
    return profile


def _get(profile: dict[str, Any], dotted: str) -> Any:
    value: Any = profile
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _present(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def reasoning_context(profile: dict[str, Any]) -> dict[str, Any]:
    validate_profile(profile)
    return {k: profile[k] for k in ("identity", "contact", "links", "work_authorization", "experience", "education", "certifications", "skills", "availability", "custom")}


def lookup_field(profile: dict[str, Any], field: str) -> dict[str, Any]:
    validate_profile(profile)
    normalized = normalize_field(field)
    dotted = ALIASES.get(normalized)
    if dotted:
        value = _get(profile, dotted)
        return {
            "status": "found" if _present(value) else "missing",
            "field": field,
            "normalized": normalized,
            "source": dotted,
            "value": value,
            "deterministic": True,
        }
    for key, value in profile["custom"].items():
        if normalize_field(str(key)) == normalized:
            return {
                "status": "found" if _present(value) else "missing",
                "field": field,
                "normalized": normalized,
                "source": f"custom.{key}",
                "value": value,
                "deterministic": True,
            }
    return {
        "status": "needs_reasoning",
        "field": field,
        "normalized": normalized,
        "deterministic": False,
        "reason": "no exact deterministic field mapping; do not guess",
        "context": reasoning_context(profile),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Local resume/application profile lookup")
    sub = ap.add_subparsers(dest="command", required=True)
    template = sub.add_parser("template")
    template.add_argument("--output")
    lookup = sub.add_parser("lookup")
    lookup.add_argument("--profile", required=True)
    lookup.add_argument("--field", required=True)
    context = sub.add_parser("context")
    context.add_argument("--profile", required=True)
    ns = ap.parse_args(argv)
    if ns.command == "template":
        data = empty_profile()
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if ns.output:
            Path(ns.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    profile = load_profile(ns.profile)
    result = lookup_field(profile, ns.field) if ns.command == "lookup" else reasoning_context(profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
