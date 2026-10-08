# PCE10.009 historical-evidence diff-check block — 2026-10-08T0108Z

## Observation

PCE10.009 successfully completed:

- required Harness v3 / TODO / roadmap / mission reads;
- exact previously failing result-wrapper test;
- complete Windows Relay unittest suite;
- complete consumer unittest suite;
- JavaScript syntax checks for all content-script and worker mirrors.

It then failed at:

`git diff --check origin/main...HEAD`

The visible failure was trailing whitespace in migrated historical evidence, including:

`docs/ACCEPTANCE_2026-10-05T2333Z_A6_399F_FIREFOX_OUT_OF_BAND_CUTOVER_REPLAY.md`

Those historical records were intentionally copied from the contaminated Termux repository as migration evidence.

## Classification

**ACCEPTANCE-GATE SCOPE DEFECT / HISTORICAL-EVIDENCE PRESERVATION CONFLICT**

The source/test acceptance gate and the byte-preservation goal for migrated historical records were conflated into one repository-wide whitespace gate.

## Impact

- all source suites were green;
- JS parse gates were green;
- live browser staging did not begin;
- no live mutation occurred;
- no rollback is required.

## Corrective rule

1. Preserve migrated historical evidence bytes; do not silently rewrite provenance records solely to satisfy a source-style gate.
2. Maintain an explicit migration-evidence manifest/hash set.
3. Run `git diff --check` across active source/tests/current docs while excluding byte-preserved migration evidence.
4. Verify the excluded historical files separately against the migration manifest hashes.
5. New/current documentation remains subject to normal whitespace hygiene.

## Promotion

Blocked until the scoped diff gate and historical-evidence verification both pass.
