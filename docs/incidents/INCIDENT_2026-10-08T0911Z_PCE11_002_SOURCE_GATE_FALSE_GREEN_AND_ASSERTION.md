# PCE011.002 source-gate run returned transport OK with test FAIL — 2026-10-08T0911Z

## Observed
Relay result packet `PCE11.002-v16-r28-source-acceptance` was delivered once with process exit 0, but reported `all_source_checks_pass=false`. Detailed evidence is local at `Client/Relay/bin/SOURCE_GATES_2026-10-08T090937Z/source-gates.json`. Assistant-visible compact stdout was truncated, so do not guess the other job verdicts.

One proved failure: `consumer/tests/test_control_harness.py::test_pce011_queue_and_50_100_checkpoints` expected a bare roadmap basename, whereas `MANDATORY_ENGINEERING_READS` correctly stores the canonical repo-relative path `docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md`. Source harness itself is not disproven by this assertion.

## Corrective GitHub edits
- `c9c37a82507519c174d14916032ed074852b425c`: repair the test assertion to check exact complete relative path.
- `2a9dd268a2f18eb7ddf59050145af6df9545e544`: change source-gate helper to return nonzero when any suite is FAIL/BLOCKED/TIMEOUT, even when it successfully wrote a report.

## Governance classification
Status: **OPEN until rerun with original report inventory and targeted/full tests**. A successful relay packet proves successful orchestration, NOT build acceptance. Neither Relay v16 nor One-Click GO r28 is approved for live replacement; current 2532-file archive and both staged commits must remain immutable. No replay of `PCE11.002` action ID.

## Next permitted operation
`PCE11.003`: read the entire earlier `source-gates.json` summary and log SHA, fast-forward-only to GitHub-approved PCE011 HEAD, run exact PCE011.003 preflight and source suites, preserve logs in a new timestamped evidence folder. No loaded-extension/browser changes. If any tests fail, continue GitHub-first repairs and track each distinct attempt toward Codex threshold.
