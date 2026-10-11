# Windows Relay twenty-operation review — PCE16.020–.039 — 2026-10-10 (Pacific)

**Canonical scope:** `monag144/GPT-Windows-Relay/main`, session `pce16.1`. Twenty issued ordinal slots `.020–.039`, analyzed using three already-committed five-operation audits and the separately documented `.035–.039` issuance window. **Review status: DOCUMENTATION COMPLETE WITH EXPLICIT UNKNOWNS; release/deployment NO-GO.** Authenticated GitHub readback for this new document is required; it is not an execution receipt.

## Complete issuance and outcome accounting

| Ordinal / exact issued ID | Native status | Material result / boundary |
| --- | --- | --- |
| `PCE16.020-create-offline-client-lifecycle-candidate-v2` | OK | Isolated eight-file HUD/lifecycle candidate, no deployment. |
| `PCE16.021-isolated-action-id-claim-race-reproduction` | OK | Synthetic old Client lookup/reserve allowed dual claim, no real double execution established. |
| `PCE16.022-isolated-atomic-action-claim-backend-candidate` | OK | Atomic offline candidate; 16 synthetic callers one claimant. |
| `PCE16.023-isolated-processed-id-eviction-replay-test` | COMMAND_FAILED | Test harness measured processed records after synthetic reclaim; incident logged. |
| `PCE16.024-verify-eviction-and-stage-durable-id-retention` | OK | Corrected fixture proved synthetic eviction/reclaim and protected pending; isolated candidate only. |
| `PCE16.025-isolated-sqlite-durable-action-identity-contracts` | OK | 21 SQLite-ledger contract checks, synthetic. |
| `PCE16.026-test-pinned-sqlite-ledger-and-stage-candidate-v5` | OK | 32 pinned ledger/source fixture checks; source not live. |
| `PCE16.027-integrate-durable-ledger-in-isolated-backend-v6` | OK | Offline cross-store claim and restart checks. |
| `PCE16.028-bound-recent-json-history-with-sqlite-tombstones` | OK | Offline JSON-cap/SQLite retention tests. |
| `PCE16.029-bound-submitted-outbound-journal-with-durable-ledger` | COMMAND_FAILED | Fixture tests passed but post-test V8 packaging hash-type error; incident logged. |
| `PCE16.030-recover-bounded-outbound-candidate-v8b` | OK | Corrected source-only V8B manifest and synthetic retention fixture. |
| `PCE16.031-fail-closed-ledger-startup-before-json-mutation` | OK | Offline missing-ledger-before-mutation failure gate. |
| `PCE16.032-isolated-full-backend-process-exact-once-tests` | OK | Complete offline `process()` with monkeypatched `execute`; no real OS command. |
| `PCE16.033-isolated-operator-stop-dispatch-and-restart-gap-proof` | OK | Reproduced offline STOP/spawn and automatic restart rearm weaknesses. |
| `PCE16.034-stage-stop-admission-and-persisted-disarm-candidate-v10` | OK | Synthetic STOP-preserving candidate; TOCTOU before process spawn remains. |
| `PCE16.035-isolated-atomic-stop-versus-process-spawn-v11` | UNKNOWN | Issued; no native receipt, no confirmed backend execution; consumed. |
| `PCE16.036-readonly-tasks-smoke-20261010` | UNKNOWN | Issued; no native receipt; consumed. |
| `PCE16.037-readonly-file-smoke-test` | UNKNOWN | Issued; packet visible in screenshot, no native receipt; consumed. |
| `PCE16.038-paired-relay-smoke-test` | GOVERNANCE_BLOCKED | Native response; missing canonical harness path; no reservation or execution. |
| `PCE16.039-post-migration-smoke-test` | GOVERNANCE_BLOCKED | Native response; same governance failure; no reservation or execution. |

**Counts:** 20 issued unique ordinals; **13 OK**, **2 COMMAND_FAILED** (`.023`, `.029`), **3 UNKNOWN** (`.035–.037`), **2 GOVERNANCE_BLOCKED** (`.038–.039`). Blocked, failed and unknown ordinals stay consumed. Synthetic test execution does not count as real Windows command/side-effect execution. This review reconciles issuance **as observed**, not a durable, independently attested runtime attempted-ID ledger.

## Four five-operation checkpoints and provenance

1. `.020–.024`: `docs/audits/AUDIT_2026-10-10T2324Z_PCE16_020_024_CHECKPOINT.md`, blob `9f3037f87d2f5fba61a36935cd5e5c40ed520d4b`.
2. `.025–.029`: `docs/audits/AUDIT_2026-10-10T2340Z_PCE16_025_029_CHECKPOINT.md`, blob `688047e49ca2f21e841369431c9efc7ec94fa8db`.
3. `.030–.034`: `docs/audits/AUDIT_2026-10-10T2353Z_PCE16_030_034_CHECKPOINT.md`, blob `de00e6c0a8cbe45c121382e2e4607622bc297947`.
4. `.035–.039`: `docs/audits/AUDIT_2026-10-11T0555Z_PCE16_035_039_CHECKPOINT.md`, prepared from main/WIP incidents and the user's two exact native governance-block receipts; `.035–.037` unresolved as UNKNOWN. The new file's commit/blob must be fetched *after* creation.

Previous review `.000–.019`: `docs/reviews/WINDOWS_RELAY_PCE16_TWENTY_OPERATION_REVIEW_000_019_2026-10-10.md`, blob `7dcccd3886365aeb3d55e9014425589b89bac346`.

Read canonical controls: `consumer/control_harness.py` blob `ca2141c45726366abb889db0cb5a794ed8735075`, `windows-relay/TASKS.md` `d49999dc29466a04ba2c27cc39f341b9162779e9`, task backlog `9a59e77967dc384962a777869c1964f9bda60e29`, dated mission `86c3e0c3f2d1c44de9cccdc819597f120c8732be`, documentation index `c10b5ef2e1b33d87f77cc689f041110ffab127f9`. This records GitHub source reads, not an on-device runtime read ledger.

## Twenty-operation drift and material progress

| Workstream | Verified or expressly operator-reported progress | Blocking gap / lesson |
| --- | --- | --- |
| P0 exactly-once and STOP | .021–.034 synthetic tests reproduced non-atomic claim, 500-record eviction/replay and STOP/rearm defects; staged SQLite ledger/V10 admission mitigations in isolation. | Production atomic dispatch, full STOP-to-Popen interlock, durable migration and rollback **not proven**; no blanket guarantee of one OS execution. |
| P0 normal command/result | Following operator pairing, .038 and .039 returned native `[GPT_WINDOWS_RESULT]` to this same conversation. | Both commands were **GOVERNANCE_BLOCKED**, no shell/file read; earlier .035–.037 no receipts. Positive browser-to-backend **rejection pathway** is not executable round-trip acceptance. |
| Governance and audits | Source audits .020–.034 on `main`. Codex reports staged Main-Build loader/API compatibility fix and 5/5 isolated receipt-verifier tests using injected network access. | Staged/live runtime does not acquire authentic GitHub receipt or persisted attempted-ID ledger and pass them to canonical preflight. Missing `.035–.039` audit/readback until this documentation-only commit. Actual `main` receipt + continuous ID history must be independently supplied, with fail-closed tests. |
| Workspace/installed runtime | Operator reports relocating the sole Client backend/HUD into `Main-Build/windows-relay/runtime`, preserving five HUD controls, one localhost listener and startup watchdog. SHA/rollback copy reported. | Local migrated source/runtime not yet pushed as an accepted release; no independent inspection of current machine performed in this GitHub review; 12 relocated Client/extension regression failures remain unresolved. |
| Firefox/addon and HUD UX | Operator observed one `GPT Windows Relay v0.3.17` Firefox addon; addon popup revealed **NOT PAIRED**. Pairing enabled native governance-response delivery. User requested FOCUS CHAT, SELECT/CLAIM-CONNECT, FORCE and RETRY alongside START/STOP/RESTART/OFF/KILL. | READY/ONLINE failed to distinguish DISARMED/NOT PAIRED and stale scanner; visible error and authorization display is a defect. Buttons documented on WIP only, not shipped. Loaded-code and full delivery-confirmation acceptance incomplete. |
| Product confidence, endurance | 403 canonical offline tests reported passed; 5/5 governance provider isolated checks reported; meaningful diagnosis of browser pairing and governance blocker. | 12 Client tests affecting result selectors, scanner telemetry, STOP generation, worker bridge and ownership remain release blockers. No measured 12/24-hour soak; no stable release. |

## Failures, rescue, repetition, rollback and user controls

- **Two real failed test fixtures:** `.023` count-after-reclaim assertion and `.029` V8 hash-type packaging error; both logged and corrected at *new* ordinals (.024/.030), not replayed.
- **Three unknown receipts:** `.035–.037` were issued while result-turn scanner/extension pairing was unreliable; no unsupported conclusion about backend execution. Earlier sampled state lacked .035/.036 processed/delivery records. Never rerun.
- **Two failed-closed backend actions:** `.038` and `.039` displayed the obsolete `GOVERNANCE_CANONICAL_HARNESS_UNAVAILABLE` and explicitly no reservation/execution. Neither is an acceptable file-read result.
- **Operator correction:** extension popup showed `NOT PAIRED` even though HUD READY/ONLINE did not; operator paired manually. Record as HUD visibility defect, not operator fault. Avoid cycling another smoke attempt into unchanged governance gate.
- **Backup and no unapproved mutation:** operator reports hash-backed WIP/Client snapshots and a preserved old Client rollback copy. Audit publication performs **GitHub documentation writes only**; no Windows process, state, Firefox, restart, migration or shell dispatch.
- **Retired agent handoff:** automatic new-chat/agent-switching is not part of repair. Only expressly requested existing one-shot script may hand off.

## Release/governance readiness verdict

**NO-GO for PCE16.040 live dispatch, runtime deployment, restart, feature promotion or a stable WIP release.** Before next command: fetch and verify the actual GitHub `main` commit+blob of the `.035–.039` checkpoint and this review, connect a verified read-only evidence provider plus complete persisted issued-ID history to the canonical preflight, enforce STOP/owner/duplicate gates, resolve material Client/extension regressions, and obtain separate operator approval for any running-code change. The canonical `engineering_preflight("PCE16", 40, github_audit_receipt=..., attempted_action_ids=...)` can validate provided metadata but cannot itself authenticate GitHub or invent missing attempted history. Do not forge a receipt or default absent IDs to success.

**Purpose of this commit:** close the documentation gap accurately; it is **not** a claim that the deployed backend can now authorize or execute PCE16.040.
