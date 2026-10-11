"""Candidate-only bridge from runtime dispatch to authenticated governance."""
import importlib.util, json, os
from pathlib import Path
from governance_evidence import authenticated_github_fetch, EvidenceError
from governance_dispatch_adapter import DispatchAdapter

def _harness(root):
    path=Path(root)/'consumer'/'control_harness.py'
    if not path.is_file(): raise EvidenceError('canonical_harness_unavailable')
    spec=importlib.util.spec_from_file_location('_candidate_control_harness',path)
    if spec is None or spec.loader is None: raise EvidenceError('canonical_harness_import_unavailable')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def preflight(next_ordinal=41):
    token=os.environ.get('GPT_WINDOWS_RELAY_GITHUB_TOKEN','').strip()
    if not token: raise EvidenceError('github_authentication_missing')
    root=os.environ.get('GPT_WINDOWS_RELAY_REPO_ROOT','').strip()
    if not root: raise EvidenceError('repository_root_missing')
    receipt_path=os.environ.get('GPT_WINDOWS_RELAY_AUDIT_RECEIPT','').strip()
    ledger_path=os.environ.get('GPT_WINDOWS_RELAY_ISSUANCE_LEDGER','').strip()
    review_path=os.environ.get('GPT_WINDOWS_RELAY_REVIEW_RECEIPT','').strip()
    if not receipt_path or not ledger_path or not review_path: raise EvidenceError('governance_evidence_paths_missing')
    audit=json.loads(Path(receipt_path).read_text(encoding='utf-8'))
    review=json.loads(Path(review_path).read_text(encoding='utf-8'))
    records=json.loads(Path(ledger_path).read_text(encoding='utf-8'))
    if not isinstance(records,list): raise EvidenceError('issuance_ledger_invalid')
    adapter=DispatchAdapter(_harness(root),authenticated_github_fetch(token),audit,review,records)
    verdict=adapter.preflight(next_ordinal)
    if not verdict.allowed: raise EvidenceError(verdict.reason)
    return verdict.preflight
