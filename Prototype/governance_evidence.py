"""Read-only GitHub audit evidence and issued-operation ledger helpers.

Network access is injected for tests. No runtime state is written.
"""
from __future__ import annotations
import json, re
from urllib.request import Request, urlopen
from dataclasses import dataclass
from typing import Callable

REPO = "monag144/GPT-Windows-Relay"
BRANCH = "main"

class EvidenceError(ValueError): pass

def authenticated_github_fetch(token: str, opener=urlopen):
    """Return an authenticated JSON fetcher; never accepts caller-supplied provenance."""
    if not isinstance(token, str) or not token.strip():
        raise EvidenceError("github_authentication_missing")
    def fetch(url: str, extra_headers: dict | None = None) -> dict:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "GPT-Windows-Relay-governance"}
        headers.update(extra_headers or {})
        headers["Authorization"] = f"Bearer {token.strip()}"
        with opener(Request(url, headers=headers), timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    return fetch

@dataclass(frozen=True)
class AuditReceipt:
    repository: str
    branch: str
    path: str
    start: int
    end: int
    commit_sha: str
    file_sha: str
    url: str
    readback_verified: bool = True

def verify_github_audit(receipt: dict, fetch: Callable[[str, dict], dict]) -> dict:
    """Verify receipt against authenticated GitHub API responses.

    `fetch` must perform authenticated HTTPS requests and return decoded JSON.
    The caller's readback flag is never trusted as provenance.
    """
    required = ("repository","branch","path","start","end","commit_sha","file_sha","url")
    if not isinstance(receipt, dict) or any(k not in receipt for k in required):
        raise EvidenceError("receipt_fields_missing")
    if receipt["repository"] != REPO or receipt["branch"] != BRANCH:
        raise EvidenceError("receipt_repository_or_branch_mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", str(receipt["commit_sha"])):
        raise EvidenceError("receipt_commit_invalid")
    if not re.fullmatch(r"[0-9a-f]{40}", str(receipt["file_sha"])):
        raise EvidenceError("receipt_blob_invalid")
    commit = fetch(f"https://api.github.com/repos/{REPO}/git/ref/heads/{BRANCH}", {"accept":"application/vnd.github+json"})
    actual_commit = (((commit.get("object") or {}).get("sha")) if isinstance(commit, dict) else None)
    if actual_commit != receipt["commit_sha"]:
        raise EvidenceError("github_branch_commit_mismatch")
    blob = fetch(f"https://api.github.com/repos/{REPO}/contents/{receipt['path']}?ref={actual_commit}", {"accept":"application/vnd.github+json"})
    actual_blob = blob.get("sha") if isinstance(blob, dict) else None
    if actual_blob != receipt["file_sha"]:
        raise EvidenceError("github_audit_blob_mismatch")
    expected_url = f"https://github.com/{REPO}/blob/{actual_commit}/{receipt['path']}"
    if receipt["url"] != expected_url:
        raise EvidenceError("receipt_url_mismatch")
    return {**receipt, "readback_verified": True, "verified_commit": actual_commit, "verified_blob": actual_blob}

def reconstruct_issued_ids(records: list[dict]) -> list[str]:
    """Normalize documented records without changing any operational state."""
    ids=[]; seen=set()
    for row in records:
        ident=row.get("id") if isinstance(row,dict) else None
        if not isinstance(ident,str) or not re.fullmatch(r"PCE16\.\d{3}.*", ident):
            continue
        if ident in seen:
            raise EvidenceError("duplicate_issued_id:"+ident)
        seen.add(ident); ids.append(ident)
    return ids

def validate_pce16_ledger(records: list[dict], first: int = 0, last: int = 39) -> list[str]:
    """Require one source-backed record for every issued ordinal."""
    ids = reconstruct_issued_ids(records)
    by_ord = {}
    for ident in ids:
        ordinal = int(re.match(r"PCE16\.(\d{3})", ident).group(1))
        if ordinal in by_ord:
            raise EvidenceError(f"duplicate_ordinal:{ordinal:03d}")
        by_ord[ordinal] = ident
    missing = [f"{n:03d}" for n in range(first, last + 1) if n not in by_ord]
    if missing:
        raise EvidenceError("missing_ordinals:" + ",".join(missing))
    return [by_ord[n] for n in range(first, last + 1)]

def verify_audit_and_review(receipt: dict, review: dict, fetch: Callable[[str, dict], dict]) -> dict:
    audit = verify_github_audit(receipt, fetch)
    if review.get("repository") != REPO or review.get("branch") != BRANCH:
        raise EvidenceError("review_repository_or_branch_mismatch")
    commit = fetch(f"https://api.github.com/repos/{REPO}/git/ref/heads/{BRANCH}", {"accept":"application/vnd.github+json"})
    actual = ((commit.get("object") or {}).get("sha"))
    if actual != audit["verified_commit"] or review.get("commit_sha") != actual:
        raise EvidenceError("review_commit_mismatch")
    blob = fetch(f"https://api.github.com/repos/{REPO}/contents/{review['path']}?ref={actual}", {"accept":"application/vnd.github+json"})
    if blob.get("sha") != review.get("file_sha"):
        raise EvidenceError("review_blob_mismatch")
    return {"audit": audit, "review": {**review, "verified_commit": actual, "verified_blob": blob.get("sha")}}

def canonical_preflight(harness, series: str, next_ordinal: int, receipt: dict,
                        records: list[dict]) -> dict:
    """Validate provenance/continuity, then call only the canonical API."""
    if (not isinstance(receipt, dict) or receipt.get("readback_verified") is not True
            or receipt.get("verified_commit") != receipt.get("commit_sha")
            or receipt.get("verified_blob") != receipt.get("file_sha")):
        raise EvidenceError("unverified_audit_receipt")
    ids = validate_pce16_ledger(records, 0, 39)
    if next_ordinal != 40:
        raise EvidenceError("unexpected_next_ordinal")
    result = harness.engineering_preflight(
        series, next_ordinal, github_audit_receipt=receipt,
        attempted_action_ids=ids)
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise EvidenceError("canonical_preflight_blocked:" + ",".join(result.get("blockers", [])))
    return result
