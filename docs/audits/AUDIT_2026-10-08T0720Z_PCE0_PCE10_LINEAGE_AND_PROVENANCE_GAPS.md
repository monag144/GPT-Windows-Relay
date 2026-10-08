# PC Engineering 0–10 lineage and provenance gaps — 2026-10-08T0720Z

**Scope:** documentary ancestry and source-survival review, not eleven executable build artifacts and not proof of loaded Windows runtime. Evidence boundary: current Windows source branch, handoff/incident records, and predecessor-repository migration checkpoints. Dates and generation labels are not equivalent to release numbers.

## Critical correction to the first PCE10 build audit

The separate `monag144/GPT-Windows-Relay` repository was initialized on 2026-10-07. Its 312-commit ancestry at the prior documentation cleanup is **not** a complete commit-by-commit history of PC Engineering 0–10. Earlier Windows development was in `monag144/GPT-Termux-Relay`, particularly `development/runtime-control` and `consumer/r29-firefox-offline-tray`. The Windows repository was migrated from reconciled **snapshots**, including old r29 `d69666da` and runtime-control `d5254444`. Historical work must therefore be checked against the predecessor's history as well as surviving migrated files. Neither 312 commits nor the eleven PCE chat generations is an exact count of installable builds.

## Generation-by-generation provenance

| Generation | Recoverable evidence / known scope | Evidence and limitations |
| --- | --- | --- |
| **PCE0–PCE2** | The underlying Windows relay and its engineering/protocol work predate the Windows repository. Exact generation attribution **not established**. | Predecessor commit history and old chat handoffs required; no individually attributable PCE0/PCE1/PCE2 handoff in the active Windows branch. Do not infer absence or obsolescence. |
| **PCE3** | PCE4 inherited a predecessor checkpoint reported as `0ed472f`; engineering and Job Application Engine milestones precede PCE4. | An earlier PCE4 handoff exists outside this branch. Specific per-file PCE3 changes and the boundary SHA must still be reconciled against predecessor Git objects. |
| **PCE4** | Job Application Engine v2, Workday browser/provider targeting, deterministically validated applicant manifests and preflight; handoff reported 144/144 v2 tests at `231ca91`. | PCE5 handoff text preserves evidence. No assumption that all subsequent PCE5 tasks were implemented at this handoff. |
| **PCE5** | Continued Job Application Engine v2: passive live `discover` mode was next in the documented plan. Parallel consumer browser scanner evolution and One-Click work must be attributed by dated commits rather than assumed from chat number. | PCE5 handoff in predecessor history; `docs/windows-relay-engineering-log-2026-10-01.md` records scanner V3–V11 evolution and V7/V11 end-to-end proofs. |
| **PCE6** | r28 One-Click stable `d5b9db7`; r29 Firefox/consumer development; browser manager, zero-touch Firefox BiDi investigation, independent recovery supervisor, visible-error diagnosis, add-on reload/refresh, A6.399f replay evidence. A6.400 fresh-chat rotation **FAILED** before execution. | `docs/HANDOFF_2026-10-06T0246Z_PC_ENGINEERING_6_TO_7_FAILED_ROTATION.md`; original r28/r29 source branches in predecessor repository. |
| **PCE7** | Recovery/HUD control paths, STOP/ownership handling, PCE7.445/446/447 rollback-backed repair tools, exact-result and browser-control hardening; rotation to PCE8. | `docs/HANDOFF_2026-10-07T0336Z_PC_ENGINEERING_7_TO_8_AUTONOMY_PROOF.md`; `windows-relay/tools/pce7_445_apply.py`, `pce7_446_live_cutover.py`, `pce7_447_source_repair.py`. Some late local source was initially absent from the canonical snapshot; migration/reconciliation followed. |
| **PCE8** | Exact managed-URL-bound Windows result sender, durable submit-uncertainty states, ownership generation controls, dormant outbound worker, PCE9 rotation mechanism. Handoff states 321 Windows + 99 consumer source tests and records PCE8.199 patch as **not executed** at that time. | `docs/HANDOFF_2026-10-07T0336Z_PC_ENGINEERING_7_TO_8_AUTONOMY_PROOF.md`, `docs/HANDOFF_2026-10-07_PCE8_TO_PCE9.md`; eight historical PCE8 safety branches in Windows repo. |
| **PCE9** | Refined result-turn parsing, HUD controls, Firefox nested picker and temporary-manifest compatibility, integration regression tests. The 100-operation budget was exceeded and Windows source drifted to old Termux r29. | `docs/INCIDENT_2026-10-07_PCE9_OPERATION_BUDGET_REPO_DRIFT_AND_REPEAT_PROBES.md`, `docs/audits/AUDIT_2026-10-07T2034Z_TERMUX_WINDOWS_CONTAMINATION.md`. Post-split bounded drift: 35 commits / 63 changed paths; PCE10 reconciled valid paths. |
| **PCE10** | Canonical-repo reconciliation, 87/87 r29 Windows path-set migration, control harness and 5/20 governance, watchdog/replay repairs, rollback-preserving browser activation gates, tests and documentation index. | `docs/audits/AUDIT_2026-10-08T0650Z_BRANCH_BUILD_CONTAMINATION_AND_REDUNDANCY.md` and `docs/handoffs/HANDOFF_2026-10-08T0635Z_PCE10_037_TO_NEXT_AGENT_FIREFOX_IDENTITY.md`. Source suite reported GREEN in PCE10.035; loaded Firefox/runtime acceptance BLOCKED after PCE10.037 exact conversation zero-match. |

## Preserved technical inheritance — do not mark redundant solely by age

- Relay backend: authenticated localhost, assistant-only packet trust, command/native-Python transport, exact-once replay, collision refusal, result files and guarded process termination.
- Browser progression: event-driven V7, reduced-rescan V8+, persistent MV3 Port, V11 assistant selectors, scroll/reacquisition; live Firefox content-script injection is a distinct proof boundary.
- Consumer products: independent development and stable One-Click branches; r28 stable is a release checkpoint, not a claim that newer r29 was accepted.
- Job Application Engine v2: deterministic manifests/preflight/discovery, provider/runner tests, safety/legal gates.
- Autonomy: recovery supervisor, UIA Firefox controls, add-on reload, capture/evidence, watchdogs, chat rotation, owner leases, control HUD, operator STOP and rollback safety.
- Three synchronized `content.js` copies, temporary versus persistent extensions, named safety branches, frozen historical logs and rollback directories may be **intentional** redundancy.

## Unresolved audit debts

1. Establish attributable PCE0/PCE1/PCE2/PCE3 handoff/commit chains in the old private repository. Current Windows branch cannot alone certify that **every** early commit survived.
2. For PCE4/PCE5, map each legacy source/test path to its exact predecessor SHA and current Windows Git blob; prevent snapshot-only preservation from being misreported as history-complete.
3. Reconcile historical installable/local packages, r26/r27/r28/r29 consumer branches, and machine backup folders separately from the Windows repository commit count.
4. Confirm the Windows live tree/loaded Firefox extension and exact current conversation identity before claiming end-to-end acceptance.
5. Do not delete or rename historical handoffs, old scanner/source variants, or rollback evidence just because they are unreferenced in the latest documentation index. Use explicit reference and build/deployment reachability checks before any future removal.

**Disposition:** historical generations PCE0–PCE9 are **PRESERVE / TRACE**, not **OBSOLETE**. This is a lineage supplement to the prior GitHub-tree-only audit, and explicitly does **not** claim complete predecessor history or live release acceptance.
