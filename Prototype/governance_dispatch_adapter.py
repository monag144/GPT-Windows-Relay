"""Staged, fail-closed governance dispatch adapter.

This module is deliberately outside the installed runtime.  Callers provide
authenticated GitHub fetching, persisted records, and the canonical harness;
the adapter never writes runtime state or executes commands.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from governance_evidence import EvidenceError, verify_audit_and_review, validate_pce16_ledger

@dataclass(frozen=True)
class DispatchVerdict:
    allowed: bool
    reason: str
    preflight: dict | None = None
    attempted_ids: tuple[str, ...] = ()

class DispatchAdapter:
    def __init__(self, harness: Any, github_fetch: Callable, audit: dict, review: dict,
                 records: list[dict]):
        self.harness, self.fetch = harness, github_fetch
        self.audit, self.review, self.records = audit, review, records

    def preflight(self, next_ordinal: int = 41) -> DispatchVerdict:
        try:
            verified = verify_audit_and_review(self.audit, self.review, self.fetch)
            ids = validate_pce16_ledger(self.records, 0, 40)
            receipt = verified["audit"]
            result = self.harness.engineering_preflight(
                "PCE16", next_ordinal,
                github_audit_receipt=receipt,
                attempted_action_ids=ids)
            if not isinstance(result, dict) or result.get("ok") is not True:
                blockers = result.get("blockers", []) if isinstance(result, dict) else []
                detail = ",".join(str(x) for x in blockers) or "canonical_preflight_not_ok"
                return DispatchVerdict(False, "canonical_blocked:" + detail, result, tuple(ids))
            return DispatchVerdict(True, "authorized_by_canonical_preflight", result, tuple(ids))
        except (EvidenceError, OSError, ValueError) as exc:
            return DispatchVerdict(False, str(exc))
        except Exception:
            # Do not disclose tokens, private records, or provider internals.
            return DispatchVerdict(False, "governance_evidence_unavailable")

    def dispatch(self, action_id: str, *, stopped: bool, owner_ok: bool,
                 reserve: Callable[[str], bool], execute: Callable[[str], Any]) -> DispatchVerdict:
        if stopped:
            return DispatchVerdict(False, "stop_active")
        if not owner_ok:
            return DispatchVerdict(False, "conversation_owner_mismatch")
        verdict = self.preflight()
        if not verdict.allowed:
            return verdict
        # Reservation is deliberately after every governance check.
        if not reserve(action_id):
            return DispatchVerdict(False, "action_already_claimed", verdict.preflight, verdict.attempted_ids)
        execute(action_id)
        return verdict
