# Windows Relay PCE16.038 paired round-trip, governance path drift — 2026-10-10

**PCE16.038 result:** `GOVERNANCE_BLOCKED`, exit_code `null`, finished `2026-10-11T05:04:25+00:00` (2026-10-10 22:04:25 Pacific). Operator pasted a native `[GPT_WINDOWS_RESULT]` in ChatGPT for issued ID `PCE16.038-paired-relay-smoke-test`, session `pce16.1`. The intended read-only Powershell `Get-Content -TotalCount 3` action **was not reserved or executed**, per backend stderr `GOVERNANCE_CANONICAL_HARNESS_UNAVAILABLE; no action reserved or executed`. The code path is a fail-closed gate, not an execution failure. **Never reuse/replay PCE16.038.**

## New, positive live acceptance

- User manually paired the single normal-Firefox temporary `GPT Windows Relay v0.3.17` / `gpt-windows-relay@local` add-on to the installed Client backend. Before pairing, the extension popup explicitly showed `NOT PAIRED`. Pairing token was not exposed in this record.
- After pairing, a fresh assistant packet `PCE16.038` was discovered and a native result appeared in this same ChatGPT conversation. This positively supports the browser packet-detection → extension/background → authenticated Client/backend response → visible result pathway for the **governance-rejection branch**. It does **not** prove actual Windows shell execution, successful result-file delivery, delivery acknowledgment or exactly-once side effects.
- Earlier `PCE16.035`, `.036`, `.037` had no native receipts; do not reuse, resend or assume no possible activity without ledger evidence.
- Five-button HUD and installed Client are retained. WIP source snapshot at commit `909415c8cd8de05fd74fac56f4b43f2d74043aab`; Codex reported controller restart recovered one port-8766 listener and 403 offline tests, with repair report on WIP branch commit `80a8b61e2765aa617659d2ff6f89fefa2d9af772`.

## Exact source-level root cause discovered in reviewed WIP snapshot

Inspected `Prototype/WIP-Windows-Relay-Rebuilt-Resynced-2047-101026/client/windows_relay.py` (Git blob `9e3cd20a47a7f9ae72c85abcc06f91290fcb2955`), the preserved installed Client source:

```python
root=Path(repo_root) if repo_root else Path.home()/"Downloads"/"Dev"/"GPT"/"GPT-Windows-Relay"
root=root.resolve()
harness=root/"consumer"/"control_harness.py"
if not harness.is_file():
    raise RelayError("GOVERNANCE_CANONICAL_HARNESS_UNAVAILABLE")
```

This **hardcodes the historical** `Downloads/Dev/GPT/GPT-Windows-Relay` source clone rather than the presently designated `Downloads/Dev/GPT-Windows-Relay-Main-Build` checkout. That is sufficient to explain `GOVERNANCE_CANONICAL_HARNESS_UNAVAILABLE` **if** that historical path no longer contains a readable `consumer/control_harness.py`. The actual filesystem existence at the time of PCE16.038 has not yet been freshly probed; the error confirms the selected harness path was absent from the backend's view.

**A simple path substitution is not sufficient.** The same preserved Client source invokes `module.engineering_preflight(root, ordinal, series)` and requires `len(evidence.get("reads",{})) == 5`. Canonical GitHub `main` `consumer/control_harness.py` blob `ca2141c45726366abb889db0cb5a794ed8735075` instead has signature `engineering_preflight(series: str, next_ordinal: int, *, github_audit_receipt: dict|None = None, attempted_action_ids: list[str]|None = None, max_ordinal: int = 100)`, returns checkpoint fields but not a `reads` map. Blindly pointing the old Client gate to the newer harness could fail with incompatible arguments, or an absent expected five-read proof. The runtime output also contains obsolete PCE10 roadmap/review/agent-rotation instructions hardcoded in that Client source; these are not valid reason to revive automatic agent switching.

## Required repair (offline first)

1. Preserve live STOP/START/HUD behavior, the authentication token, all persisted execution/attempted-ID state, PCE16.035–.038 receipts, and rollback snapshots. Do **not** unset the governance gate, route around it with a non-PCE ID, falsify read receipts, automatically replay or clear historical records.
2. Codex: inspect actual `Main-Build/consumer/control_harness.py`, the installed Client hardcoded gate, and the selected paths. Identify what original local governance API exists, what current canonical API requires, and how to supply genuine authenticated GitHub audit receipt + complete attempted-ID ledger + date-stamped source-read evidence. The oldest legacy clone might still be needed as an explicit compatibility source; do not remove it before migration.
3. Develop a **tested compatibility adapter** for the installed Client governance check with explicit primary Main-Build root, exact function signature/API validation, fail-closed missing/mismatched audit/ordinal/read evidence, and backward-compatible controls. Avoid path-only hotfixes, restoring obsolete PCE10 governance or bypass.
4. Isolated negative/positive tests: missing harness, import failure, wrong signature, missing required reads, missing checkpoint, invalid GitHub receipt, unknown prior IDs, genuine approved read-only PCE ordinal acceptance, positive server block on disarm, replay/collision, STOP and owner. Do not invoke real shell during fixtures. Preserve five-button HUD and lifecycle.
5. Stage code/tests in existing Prototype (and backups in Backup), test, document hashes/rollback; commit to WIP branch only. Require explicit review/approval before modifying installed Client or restarting service. Then issue **a new unique PCE16 ordinal** only after original gate accepts the full governance preflight; PCE16.038 remains burned.
6. No source/output title should claim stable release; WIP label remains **Windows Relay — Rebuilt and Resynced — 2047 101026**.

**Status:** Browser-to-native governance-response loop PASSED; guarded execution and file-content round trip NOT YET PROVEN; governance compatibility ROOT/ABI defect targeted for repair. No live Client/Firefox/backend mutation performed by this logging action.
