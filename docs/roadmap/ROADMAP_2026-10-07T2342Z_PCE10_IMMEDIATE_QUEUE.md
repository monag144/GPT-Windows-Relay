# PCE10 immediate engineering queue — 2026-10-07T2342Z

Canonical repository: `monag144/GPT-Windows-Relay`.

This compact queue records the next authorized PCE10 operations so restart/recovery does not depend on another user message.

1. **PCE10.001 — FAILED before mutation.** Assumed the intended canonical clone target already existed; see the timestamped PCE10.001 workspace-path incident.\n2. **PCE10.002 — canonical reconciliation source acceptance retry.** Use the canonical Windows clone only. Check out `pce10/reconcile-control-and-rotation`, prove `PCE10.000` completed successfully, resolve the test-capable Python interpreter, run the targeted reconciliation tests plus the full Windows Relay and consumer suites, run JavaScript/PowerShell/Python parse gates and `git diff --check`, verify the three content-script mirrors, and emit the exact guarded live-deployment file set. No live STOP or self-termination is allowed in this operation.
3. **PCE10.003 — guarded live deployment and detached 8766 acceptance.** Only after PCE10.001 is green: preserve rollback, deploy the accepted files to `Client/Relay`, activate the browser-plane changes deliberately, then use a detached observer/harness for STOP→START so the relay does not kill its own acceptance proof. Require exact-generation browser quiescence and verified new-listener ancestry. Roll back on any failed gate.
4. **PCE10.004 — post-cutover evidence and branch disposition.** Record exact source/live hashes, acceptance evidence, queue behavior, and merge readiness; merge/promote only if all gates are green.
5. **PCE10.005+ — continue the canonical roadmap in recorded safe order.** Resume remaining R0/R1/browser-matrix/product gates after source/live convergence is resolved.

Hard budget: PCE10.000 through PCE10.100 inclusive. PCE10.101 is forbidden and requires rotation to PCE11.
