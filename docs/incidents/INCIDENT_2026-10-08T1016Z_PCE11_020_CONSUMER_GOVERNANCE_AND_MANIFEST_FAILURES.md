# PCE11.020 consumer source acceptance blocked — 2026-10-08T1016Z

**OPEN. Source-only consumer test failures. Live v16/consumer promotion forbidden.**

Action `PCE11.020-audited-documentation-and-full-source-acceptance` returned `COMMAND_FAILED`, exit 2 after successful GOVSYNC for `.015–.019` audit and `.000–.019` review. Canonical source commit: `ba166ad70b86698bf2ce920c6050fde38cd964ed`. Evidence: `Client/Relay/bin/SOURCE_ACCEPTANCE_2026-10-08T101602Z/acceptance.json` (full suite logs stored in same folder).

- Protocol suite: **50 PASS**.
- Windows Relay suite: **476 PASS**. Prior `.019` documentation-hygiene failure is resolved by reducing canonical `TASKS.md` below 10,240 bytes and archiving historical task details.
- Consumer suite: **117 tests, FAIL**. The compact result names governance checkpoint tests `test_audit_due_before_025_and_not_after`, `test_missing_operation_slot_is_rejected`, `test_review_due_before_020_and_040`, `test_unsubstantiated_checkpoint_is_rejected`, and `test_manifest_is_exact_and_complete_for_declared_entries`. Output was truncated; additional failures and precise assertions must be collected before repair.
- JavaScript, Firefox mirror, original archive, historical v16 blob were **not reached** and may not be marked pass.
- No sidecar process was launched, no production listener/Firefox/HUD/STOP/mission mutation. Last observed production state (not necessarily current): 8766 listener PID 18632, ARMED, browser outbound, 2 pending missions.

## Initial hypothesis — not yet an accepted diagnosis
Current `consumer/control_harness.py` preflight defaults to series=11, while `consumer/tests/test_engineering_governance.py` creates synthetic PCE10 filename/slot fixtures and calls `due_engineering_checkpoints` and `engineering_preflight` without passing series=10. This would naturally make a correct PCE11 harness reject PCE10 fixtures; test must exercise the legacy series explicitly, retain a separate series=11 positive check, and not reduce checkpoint enforcement.

The migration evidence manifest `docs/migration/MIGRATION_2026-10-08T0110Z_TERMUX_WINDOWS_EVIDENCE_MANIFEST.json` lists 42 imported immutable Git blobs. Existing test compares `HEAD:<destination_path>` to manifest blobs. Determine *exact* mismatches and source history before changing either verifier or manifest. Do not rewrite migration provenance to match contemporary working files.

## Next safe action
PCE11.021: read complete stored `.020` consumer stderr and stdout, summarize exact failing IDs and bounded traceback lines, enumerate 42 Git object comparisons using the canonical tree and manifest, save local forensic report; no test replay or runtime interaction. Then GitHub-first targeted repair and exact full source retest with unique next ordinal. Audit `.020–.024` before `.025`.