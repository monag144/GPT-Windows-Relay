# PCE10.012 exact-conversation resolver failure — 2026-10-08T0123Z

## Observation

PCE10.012 successfully completed:

- canonical Windows repository preflight;
- all four mandatory control reads;
- runtime-source continuity proof;
- Harness v3 regression acceptance;
- full consumer suite;
- all 42 committed migration-blob checks;
- scoped `git diff --check` classification.

It then failed at the first managed-browser identity action:

`firefox_adapter.py resolve-conversation-tab --conversation-url <exact PCE10 URL>`

with non-zero return code.

The compact visible result did not preserve the exact nested Firefox-adapter failure text, so the browser sub-cause is not yet classified.

## Classification

**BROWSER-STATE / SEMANTIC RESOLVER FAILURE — EXACT SUB-CAUSE PENDING EXTRACTION**

Browser state changed enough to fail a named acceptance gate, so bounded Firefox state re-proof is authorized by the established lifecycle policy.

## Safety boundary

The failure occurred before the rollback-backed stale-settle canary stage.

- no live content files were copied;
- no add-on reload occurred;
- no ChatGPT refresh occurred;
- no rollback is required.

## Diagnostic rule for PCE10.013

1. Extract the exact PCE10.012 resolver stdout/stderr from the saved relay result.
2. Re-run the existing semantic `resolve-conversation-tab` action read-only.
3. Collect only bounded Firefox process-tree / visible-window telemetry needed to interpret that exact failure.
4. Do not mutate browser, add-on, source, or live relay state.
5. Only after the exact failure class is established may the harness or adapter be changed.
