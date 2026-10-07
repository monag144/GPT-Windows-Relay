# PCE10 immediate engineering queue — 2026-10-07T2342Z

Canonical repository: `monag144/GPT-Windows-Relay`.

This compact queue records the next authorized PCE10 operations so restart/recovery does not depend on another user message.

1. **PCE10.001 — reconciliation acceptance and live cutover gate.** Use the canonical Windows clone only. Check out `pce10/reconcile-control-and-rotation`, resolve the test-capable Python interpreter, run targeted + full source suites and parse/diff gates, then perform the guarded live deployment and detached 8766 STOP→START ancestry acceptance. Preserve rollback before live mutation. Do not rediscover unchanged Firefox lifecycle facts.
2. **PCE10.002 — post-cutover evidence and branch disposition.** If PCE10.001 is green, record exact source/live hashes, acceptance evidence, queue behavior, and merge readiness. If red, rollback first and log the failure before any further mutation.
3. **PCE10.003+ — continue the canonical roadmap in recorded safe order.** Resume remaining R0/R1/browser-matrix/product gates only after the reconciliation/live convergence gate is resolved.

Hard budget: PCE10.000 through PCE10.100 inclusive. PCE10.101 is forbidden and requires rotation to PCE11.
