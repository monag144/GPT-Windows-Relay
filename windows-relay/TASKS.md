# PCE011 Relay & One-Click GO — Mandatory Daily Task Queue — 2026-10-08T0852Z

## Read THIS ENTIRE FILE and the ENTIRE control harness before EVERY operation
Read `consumer/control_harness.py` completely, this queue completely, `docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md`, established facts and relay sandwich procedure. Run `engineering_preflight(root, ordinal, series=11)` and log SHA256s. The full source is authoritative; a previous model summary is not a replacement.

## ACTIVE ORDER (no speculative detours)
- [x] GitHub verified legacy source references: historic full-tree One-Click GO r28 `d5b9db7ad785b5cae8dc3b64219303b9fcfa634a`; PCE8 v16 source `694d47ab89596d5c3801f749caa352b951a2be52`. Both original Git objects exist in Termux history; Termux branch tips have no `windows-relay/` folder.
- [x] A–Z Relay and consumer benchmark criteria committed; no overnight pass is yet claimed.
- [x] Corrected PCE011 harness scheduled reads/audit-reviews and created dated PCE011 queue on canonical Windows GitHub branch.
- [x] PCE11.004 source acceptance: backup integrity and staged SHA checks, **19/19 jobs PASS, 697 tests counted**, report `Client/Relay/bin/SOURCE_GATES_2026-10-08T091457Z/source-gates.json`; live activation and overnight qualification remain untested.
- [x] PCE11.001: exact PCE011 SHA pulled by fast-forward on clean canonical checkout; 5-control governance receipt returned. Preserve Codex-mapped paths and do not overwrite dirty future changes.
- [x] PCE11.001: 2532-file current Relay ZIP and SHA256 manifest saved non-destructively at `Client/Relay/bin/BROKEN_2026-10-08T090413Z.zip`; running listener left untouched.
- [x] PCE11.001: immutable historical v16 `694d47ab` and r28 `d5b9db7` staged in separate `Client/Relay/builds/` checkout trees; exact source HEAD verified. Live deployment NOT performed.
- [ ] Test both independently using pinned benchmark catalog: offline syntax/unit tests -> read-only identity -> STOP+rollback acceptance -> exactly-once canary -> 12h night -> 24h release gate.
- [ ] Recover exact PCE7 legacy rollback as independent standalone Relay challenger, not guessed from PCE7.447 branch.
- [ ] Qualify One-Click GO r28 Chrome and Edge consumer flows. Temporary Firefox development add-on is NOT signed persistent consumer Firefox support.
- [ ] Reintroduce newer HUD UI cautiously with **RETRY**; make STOP fully quiescent. Do not remove emergency KILL unless safety behavior of STOP is proven equivalent and recoverability retained.
- [ ] After five distinct repeated failures, optional Codex CLI scoped repair, preferred 5.6 or 6 Luna **if installed**, with GitHub-first commit and rollback.
- [ ] At PCE011.050 compile finding and send via connected mail only when an actual sender action is available; report send receipt, don't fake delivery.
- [ ] At PCE011.100 hand off/rotate to verified `💻PC Engineering 12🔧`, not OP101.

## Completed diagnostics .005–.014
Historical evidence and complete verbatim details: [dated task snapshot](TASKS_2026-10-08T1011Z_PCE11_PRE020_FULL_SNAPSHOT.md). Existing audits: `docs/audits/AUDIT_2026-10-08T0933Z_PCE11_OPERATIONS_005_009.md` and `docs/audits/AUDIT_2026-10-08T0951Z_PCE11_OPERATIONS_010_014.md`.

- [x] PCE11.015 audited source acceptance PASSED: separate GOVSYNC accepted .010–.014 audit; source commit `7f894e2e90e5f35156558957ed3b148d49be50e6`; nine historic supervisor and nine suspended-start containment tests passed (18 total). Held old canary remains disabled, no process launched. Evidence `Client/Relay/bin/CONTAINMENT_GATE_2026-10-08T095526Z.json`.
- [x] PCE11.016 blocked stale base SHA; incident `docs/incidents/INCIDENT_2026-10-08T0959Z_PCE11_016_STALE_CHECKPOINT_BASE.md`. No launch.
- [x] PCE11.017 STATIC ACCEPTANCE BLOCKED: first full `windows-relay` unittest discovery failed after correcting SHA gate. Original runner returned only last 700 characters of suite stderr, obscuring the failing test name and trace; incident `docs/incidents/INCIDENT_2026-10-08T1003Z_PCE11_017_FULL_WINDOWS_TEST_SUITE_FAILED.md`. No sidecar launched or live runtime mutated.
- [x] PCE11.018 forensic test run: 476 Windows Relay unittests, 1 failure only. `test_protocol.Tests.test_every_serialized_result_stdout_enforces_turn_discipline_and_sandwich` expects `monag144/GPT-Windows-Relay` in serialized stdout; canonical `OPERATION_DISCIPLINE_REMINDER` omitted the repository identifier. Full evidence `Client/Relay/bin/SOURCE_SUITE_FORENSICS_2026-10-08T100608Z/summary.json`; stderr SHA256 `db34a10dfe0cb1afe29b0cc4abde343e6820a63a6ced9a69271b45f810049928`. No sidecar launch.
- [x] PCE11.019: protocol 50/50 PASS; full Windows 476 tests with 1 documentation hygiene failure; consumer/JS and archive tests unrun. Canonical TASKS over 10KB was archived verbatim and compacted.
- [x] GitHub published `.015–.019` audit at `docs/audits/AUDIT_2026-10-08T1012Z_PCE11_OPERATIONS_015_019.md` and 20-operation review at `docs/reviews/REVIEW_2026-10-08T1013Z_PCE11_OPERATIONS_000_019.md`.
- [x] PCE11.020 source-only: audited GOVSYNC passed; protocol 50/50 and Windows full 476/476 PASS; consumer 117 tests FAIL (PCE10 fixture defaults and migration Git blob mismatch suspected). JS/archive/v16 gates not reached. Incident `docs/incidents/INCIDENT_2026-10-08T1016Z_PCE11_020_CONSUMER_GOVERNANCE_AND_MANIFEST_FAILURES.md`. Evidence `Client/Relay/bin/SOURCE_ACCEPTANCE_2026-10-08T101602Z/acceptance.json`; no canary.
- [x] PCE11.021 persisted consumer forensics: 117 tests, 4 FAIL + 1 ERROR; PCE10 fixtures invoked PCE11 default; all 42 original Termux migration Git blobs validated at pinned source commit, 15 current Windows destination blobs differ. No tests replayed. Evidence `Client/Relay/bin/CONSUMER_FORENSICS_2026-10-08T101845Z.json`.
- [x] PCE11.022 full source acceptance PASS: protocol 50, Windows 476, governance 8, migration 2, consumer 119, JS 4; ZIP/source verified. `Client/Relay/bin/SOURCE_ACCEPTANCE_2026-10-08T102230Z/acceptance.json`.
- [x] PCE11.023 inert private Job smoke PASS: child 1052 cleaned, 12+479+119 suites pass; main preserved. `Client/Relay/bin/PRIVATE_JOB_SMOKE_2026-10-08T102641Z.json`.
- [x] PCE11.024 canary FAILED; .025 later proved child cleanup. `docs/incidents/INCIDENT_2026-10-08T1029Z_PCE11_024_V16_CANARY_RUNTIME_FAILURE.md`.
- [x] Audit .020–.024 published at `docs/audits/AUDIT_2026-10-08T1031Z_PCE11_OPERATIONS_020_024.md`, documenting full source acceptance and failed runtime canary. Requires independent GOVSYNC before .025.
- [x] PCE11.025 PASS: sidecar 4480 cleaned, port 8768 free; main PID 18632 ARMED, two missions unchanged. `Client/Relay/bin/PCE11_025_V16_FAILURE_FORENSICS_2026-10-08T103325Z.json`.
- [x] PCE11.026: private state 0 missions/actions, no auth config; historical `/status` source 5/5. `Client/Relay/bin/PCE11_026_PRIVATE_STATE_DIAG_2026-10-08T103556Z.json`.
- [x] PCE11.027 source PASS: 9 v16, 12 containment, 481 Windows, 119 consumer, 4 JS and archive/source. `Client/Relay/bin/SOURCE_TELEMETRY_ACCEPTANCE_2026-10-08T103943Z/acceptance.json`.
- [x] PCE11.028 runtime FAILED: launch PID 1640, HTTP PID 11180, missions 0; private Job cleanup OK. `docs/incidents/INCIDENT_2026-10-08T1043Z_PCE11_028_V16_PID_IDENTITY_MISMATCH.md`.
- [x] PCE11.029 PASS read-only: venv launcher python.exe 255,200 bytes vs base Python313 python.exe 105,696; historic 1640->11180 ancestry UNPROVEN. Main 18632 ARMED, 2 missions; 8768 free. `Client/Relay/bin/PCE11_029_PID_IDENTITY_DIAG_2026-10-08T104655Z.json`.
- [x] Audit .025–.029 published `docs/audits/AUDIT_2026-10-08T1049Z_PCE11_OPERATIONS_025_029.md`. Independent GOVSYNC required before .030.
- [x] PCE11.030 real venv host ancestry PASS: launcher 1360 → host 12844 direct child, both in exact Job, host exited on Job close, main 18632 preserved. `ops/PCE11_030_LINEAGE_20261008T105116Z/lineage-report.json`.
- [x] PCE11.031 source FAIL: 1 outdated malformed-PID assertion; no canary. `docs/incidents/INCIDENT_2026-10-08T1057Z_PCE11_031_MALFORMED_PID_TEST_EXPECTATION.md`.
- [x] PCE11.032 pre-suite BLOCKED: wrong .030 evidence source SHA. `docs/incidents/INCIDENT_2026-10-08T1100Z_PCE11_032_WRONG_NATIVE_PROOF_SOURCE_SHA.md`.
- [x] PCE11.033 full HOST source acceptance PASS at `e4e89c4075ddc49e6bb6bae8db8bed2e48cad280`: 12 v16, 9 host, 12 Job, 493 Windows, 119 consumer; JS4, ZIP/source guards. `Client/Relay/bin/SOURCE_HOST_IDENTITY_ACCEPTANCE_033_2026-10-08T110349Z/acceptance.json`. No runtime launch.
- [ ] PCE11.034: one NEW bounded v16 on private 8768; require .033 acceptance, .030 real host-in-Job proof, .023/.025 cleanup, fresh tests, archival backup, exact listener PID+parent+Job+host exit, main 18632 identity. No production cutover; diagnostic fail-closed.
- [ ] USER INCIDENT (investigation pending): ChatGPT `Connection interrupted. Waiting for the complete answer` during partial PCE11.033 reply; issue #1, `docs/incidents/INCIDENT_2026-10-08T1928Z_PCE11_USER_REPORTED_CONNECTION_INTERRUPTED_WAITING_COMPLETE_ANSWER.md`. Design guarded same-chat refresh/New Chat continuity; no automatic replay or live mutation.

## Full original queue preserved
[Complete 2026-10-08T1011Z snapshot](TASKS_2026-10-08T1011Z_PCE11_PRE020_FULL_SNAPSHOT.md).

## CHECKPOINTS
- Five-operation audit every .005/.010/... covering preceding five attempted IDs, including 0 baseline slot, failures and missing results. **Historical audit PCE10.015-.019 already recorded:** `docs/audits/AUDIT_2026-10-08T0316Z_PCE10_OPERATIONS_015_019.md`.
- Twenty-operation review every .020/.040/.060/.080/.100.
- Soft reporting/email checkpoint .050; mandatory safe rotation .100.
- Human STOP, uncertain side effects, ambiguous tab identity, failed rollback or dirty checkout always prohibit unsafe unattended mutation; reporting and read-only diagnosis may continue.

## Historical task archives
Full prior task details in [pre020 snapshot](TASKS_2026-10-08T1011Z_PCE11_PRE020_FULL_SNAPSHOT.md). Prior series evidence preserved in GitHub audits and incidents.
