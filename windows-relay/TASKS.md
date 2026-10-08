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
- [x] PCE11.016 **FAILED before tests/pull/launch**: canonical Windows source remained at verified .015 commit `7f894e2e90e5f35156558957ed3b148d49be50e6`, but new preflight's BASE_SHA was stale intermediate commit `2b02b506d8850882d806f8461c25b0a7f03140fd`; exit 2, `unexpected source base before .016`. Incident `docs/incidents/INCIDENT_2026-10-08T0959Z_PCE11_016_STALE_CHECKPOINT_BASE.md`. No process launch or live mutation.
- [x] PCE11.017 STATIC ACCEPTANCE BLOCKED: first full `windows-relay` unittest discovery failed after correcting SHA gate. Original runner returned only last 700 characters of suite stderr, obscuring the failing test name and trace; incident `docs/incidents/INCIDENT_2026-10-08T1003Z_PCE11_017_FULL_WINDOWS_TEST_SUITE_FAILED.md`. No sidecar launched or live runtime mutated.
- [x] PCE11.018 forensic test run: 476 Windows Relay unittests, 1 failure only. `test_protocol.Tests.test_every_serialized_result_stdout_enforces_turn_discipline_and_sandwich` expects `monag144/GPT-Windows-Relay` in serialized stdout; canonical `OPERATION_DISCIPLINE_REMINDER` omitted the repository identifier. Full evidence `Client/Relay/bin/SOURCE_SUITE_FORENSICS_2026-10-08T100608Z/summary.json`; stderr SHA256 `db34a10dfe0cb1afe29b0cc4abde343e6820a63a6ced9a69271b45f810049928`. No sidecar launch.
- [x] PCE11.019: protocol 50/50 PASS; full Windows 476 tests with 1 documentation hygiene failure; consumer/JS and archive tests unrun. Canonical TASKS over 10KB was archived verbatim and compacted.
- [x] GitHub published `.015–.019` audit at `docs/audits/AUDIT_2026-10-08T1012Z_PCE11_OPERATIONS_015_019.md` and 20-operation review at `docs/reviews/REVIEW_2026-10-08T1013Z_PCE11_OPERATIONS_000_019.md`.
- [ ] Before PCE11.020, independent restricted GOVSYNC must install BOTH documents locally. Verify Harness due audit and review; then source-only tests. No live cutover.
- [x] PCE11.020 source-only: audited GOVSYNC passed; protocol 50/50 and Windows full 476/476 PASS; consumer 117 tests FAIL (PCE10 fixture defaults and migration Git blob mismatch suspected). JS/archive/v16 gates not reached. Incident `docs/incidents/INCIDENT_2026-10-08T1016Z_PCE11_020_CONSUMER_GOVERNANCE_AND_MANIFEST_FAILURES.md`. Evidence `Client/Relay/bin/SOURCE_ACCEPTANCE_2026-10-08T101602Z/acceptance.json`; no canary.
- [ ] PCE11.021: inspect persisted .020 consumer test output, exact failed assertions and full 42-entry manifest-to-Git comparison, report masked paths/IDs and complete durable log. GitHub-first sync and governance preflight before reading; no suite replay or live mutation.
- [x] PCE11.021 persisted consumer forensics: 117 tests, 4 FAIL + 1 ERROR; PCE10 fixtures invoked PCE11 default; all 42 original Termux migration Git blobs validated at pinned source commit, 15 current Windows destination blobs differ. No tests replayed. Evidence `Client/Relay/bin/CONSUMER_FORENSICS_2026-10-08T101845Z.json`.
- [ ] PCE11.022: GitHub-first source repairs only to legacy governance tests (`series=10`) and immutable migration provenance assertions; run targeted, full Windows/consumer, JS, original ZIP and staged v16 source gates. No runtime or browser mutation.
- [ ] After verified inventory, design independently supervised, rollback-backed v16 canary before any consumer promotion.

## Full original queue preserved
[Complete 2026-10-08T1011Z snapshot](TASKS_2026-10-08T1011Z_PCE11_PRE020_FULL_SNAPSHOT.md).

## CHECKPOINTS
- Five-operation audit every .005/.010/... covering preceding five attempted IDs, including 0 baseline slot, failures and missing results. **Historical audit PCE10.015-.019 already recorded:** `docs/audits/AUDIT_2026-10-08T0316Z_PCE10_OPERATIONS_015_019.md`.
- Twenty-operation review every .020/.040/.060/.080/.100.
- Soft reporting/email checkpoint .050; mandatory safe rotation .100.
- Human STOP, uncertain side effects, ambiguous tab identity, failed rollback or dirty checkout always prohibit unsafe unattended mutation; reporting and read-only diagnosis may continue.

## HISTORICAL TASK DETAIL
Earlier full backlog was preserved at Git blob `9dd9080ed2e9b1a489c3f9258f3a5c829dce3763` and verbatim archives:
- [Part 1](TASKS_2026-10-08T0752Z_WINDOWS_RELAY_PART_01.md)
- [Part 2](TASKS_2026-10-08T0752Z_WINDOWS_RELAY_PART_02.md)

Do not confuse a user-reported running Relay with current source SHA or an accepted browser runtime.
