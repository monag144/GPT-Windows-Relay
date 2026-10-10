# Windows Relay PCE16 twenty-operation review — 2026-10-10

**Scope:** monag144/GPT-Windows-Relay/main; PCE16.000–.019, twenty issued attempts in session pce16.1. **Verdict: MATERIAL SOURCE/CLIENT DRIFT; MEASURABLE OFFLINE PROGRESS; LIVE PRODUCT NOT RELEASE READY.** This review was published before issuing PCE16.020.

## Native operation outcomes and coverage
Previous five-operation source audits: docs/audits/AUDIT_2026-10-10T0623Z_PCE16_000_004_CHECKPOINT.md; docs/audits/AUDIT_2026-10-10T0635Z_PCE16_005_009_CHECKPOINT.md; docs/audits/AUDIT_2026-10-10T2257Z_PCE16_010_014_CHECKPOINT.md; docs/audits/AUDIT_2026-10-10T2307Z_PCE16_015_019_CHECKPOINT.md.
Twenty unique ordinals: **16 OK**, **2 GOVERNANCE_BLOCKED** (.005,.010), **2 COMMAND_FAILED** (.007,.012). No ordinal was reused, and blocked/failed actions remain consumed. Separate authenticated audit-sync maintenance does not consume a PCE ordinal.

## Roadmap comparison
| Roadmap area | Net-new evidence | Remaining gap |
| --- | --- | --- |
| P0 exact-once backend safety | Source checks found Client non-atomic lookup/reserve and processed-ID retention of 500, 501 observed with one INFLIGHT. **No live duplicate proven.** | No isolated concurrency/uncertain-restart/eviction fixture passed, no atomic implementation or Client rollout. |
| P0 command → result | PID 11700 on 8766 proven launched from Client/Relay/windows_relay.py; scanner inspection traced. | No new end-to-end confirmed normal same-chat send→one Windows run→one visible reply. G26 0/60, G27 0/2. |
| P1 source/Client parity | Main, Client, PCE11, PCE8 and Termux inventoried. Offline stage 28/28 verified sources, manifest pinned. | Main and running Client differ. Firefox loaded extension, profile and code bytes UNKNOWN. |
| P1 HUD UX/control | Client 5 controls (START, STOP, RESTART, OFF, KILL), minimize and error states captured. Offline Client-based HUD candidate adds one **disabled/unbound** RETRY. Offline checks 18/18. | Candidate missing run-control.ps1, watchdog, launch/adapter dependencies; not runnable or deployable. FORCE, FOCUS CHAT, SELECT/CLAIM–CONNECT not built. |
| P1 archival safety | All six local checkouts had zero tracked dirty files; Main 4 untracked, PCE11 37 untracked Markdown, PCE8 2, Termux 0. | Unique content and local commit ancestry not completely classified; no folder safe to delete on present evidence. |
| P2 package/release | Existing signed-XPI scripts known; rollback staging plan created. | No signed, attested candidate addon, no tested live cutover, no multi-hour resilience acceptance. |

## Source divergence and engineering policy
- Current 127.0.0.1:8766 process runs installed Client/Relay/windows_relay.py, not Main checkout. GitHub Main and Client are **not interchangeable**, despite common extension version 1.1.0 on disk.
- Client HUD/controller contain process management and 5-button layout absent from Main; Main has RETRY only. PCE11 and Client source include retired auto chat/agent switching. Do not copy that functionality into merged build or reactivate it.
- The selected 129/129 offline unit/contract tests do not prove real installed release readiness. Last strict Grade F/BLOCKED, 11/28; no grade upgrade.
- Local PCE11 harness remains obsolete and expects compatibility-named local audit, while canonical GitHub control_harness.py expects GitHub connector audit readback. Continue authenticated pinned copies until audited migration; never bypass validator.

## Failure trends, rescues and rollback
- .005 and .010 failed closed before execution because the local legacy audit checkpoint had not been synced. An authenticated pinned-GitHub blob compatibility copy (exclusive create, readback and real local validator) restored preflight for .005 and .015. User was not asked to run manual commands.
- .007 was an error in our audit synchronization script: checked a future ordinal instead of the correct gate; correctly removed the newly created file, then corrected at a NEW unique .008. Do not repeat such false-gate test.
- .012 Codex CLI 0.161.0 broad seven-checkout task timed out (105s) with no completed analysis; do not attribute the observed Codex process instances or kill them without evidence. Deterministic bounded source diff succeeded at .013.
- Source snapshots and candidate are isolated and original Client/Main/legacy folders preserved; no browser/HUD control launched. A stage file or offline test is **not a rollback of the installed Client**, which remains untouched.
- Permanent no-autonomous-chat/agent-switching: only user-authorized existing one-shot handoff script, no current handoff demanded.

## Next priorities
1. Authenticate the verified GitHub .015–.019 audit via existing pinned-download compatibility mechanism; ensure local engineering_preflight(repo,20,series=16) returns ok. Do not issue .020 blindly.
2. Establish the offline candidate's dependency closure by allowlisted source copies and exact hashes; do not launch, deploy, copy config, or change live Client. Test STOP/OFF/KILL semantics with isolated mocks.
3. Resolve backend atomic action-ID claim, crash/replay retention and owner negative cases in isolated fixtures before any release.
4. Implement separate RETRY, FOCUS CHAT, SELECT/CLAIM–CONNECT and visible FORCE button under STOP, legitimate conversation ownership and dedup rules. No force takeover or automatic ChatGPT new chat.
5. Attest loaded Firefox code, sign/privately package reviewed extension, rehearse rollback, then request explicit operator approval before deployment.
6. Preserve/classify unique untracked documentation and commits before proposing archive/removal of old checkouts.

**Bottom line:** Progress moved from uncontrolled build ambiguity to a verified 28-source comparison stage and a syntactically valid, offline HUD candidate. Live build consolidation and product-grade reliability still require implementation and independent acceptance.

## Full native audit ledger — exact ordinal coverage

**Checkpoint status: COMPLETE AS A 20-ATTEMPT REVIEW; NOT A PRODUCT RELEASE.** Every row is cross-checked against one of the four committed five-operation audits named above. These are issued operation identifiers and native result classifications, including every failure; the individual audits contain detailed timestamps and evidence. The one-row-per-ordinal ledger is added for auditability and for the installed legacy validator's required proof of each .000–.019 operation.

| Issued Windows action | Native result |
| --- | --- |
| `PCE16.000-read-only-live-hud-and-backend-inventory` | OK |
| `PCE16.001-read-only-hud-controller-behavior-audit` | OK |
| `PCE16.002-runtime-identity-and-hud-bindings` | OK |
| `PCE16.003-scanner-recovery-and-queue-read-only-audit` | OK |
| `PCE16.004-force-scanner-safety-and-ledger-audit` | OK |
| `PCE16.005-force-path-and-adapter-contract-inspection` | GOVERNANCE_BLOCKED |
| `PCE16.006-local-checkpoint-validator-source-audit` | OK |
| `PCE16.007-verified-audit-ingestion-and-legacy-preflight` | COMMAND_FAILED |
| `PCE16.008-corrected-legacy-audit-compatibility` | OK |
| `PCE16.009-force-scanner-dispatch-and-safety-review` | OK |
| `PCE16.010-windows-relay-workspace-and-runtime-inventory` | GOVERNANCE_BLOCKED |
| `PCE16.011-read-only-workspace-build-and-codex-inventory` | OK |
| `PCE16.012-codex-readonly-relay-build-lineage-review` | COMMAND_FAILED |
| `PCE16.013-deterministic-source-capability-comparison` | OK |
| `PCE16.014-readonly-git-preservation-and-runtime-identity` | OK |
| `PCE16.015-live-source-and-untracked-work-preservation-review` | OK |
| `PCE16.016-create-verified-isolated-consolidation-source-stage` | OK |
| `PCE16.017-verified-stage-hud-controller-diff` | OK |
| `PCE16.018-build-isolated-five-control-hud-candidate` | OK |
| `PCE16.019-offline-hud-control-contract-and-dependency-test` | OK |

**Native accounting checked:** 16 OK, 2 GOVERNANCE_BLOCKED (.005 and .010), 2 COMMAND_FAILED (.007 and .012), 20 unique issued identifiers, no missing/reused ordinal. This review continues to report material source and Client drift. Authenticated GitHub evidence is not proof that the local compatibility file has been installed; the actual old local validator must still accept PCE16.020 before issuance.
