# PCE11.017 full Windows Relay test suite acceptance failure — 2026-10-08T1003Z

**Status: OPEN** until exact failing tests and causes are recovered. Safety guard worked: no canary launch, source acceptance blocked.

## Exact result
Action `PCE11.017-corrected-full-source-and-v16-static-preflight` returned `COMMAND_FAILED`, exit 2, at 10:03:26–10:03:54 UTC. The source successfully advanced past stale base gate. Targeted static tests had apparently completed before the full `windows-relay` discovery suite failed; do not claim full test success. Runner raised `RuntimeError: full windows-relay source suite failed`, and its error handler printed only the **last 700 characters** of the full suite stderr. The provided fragment concluded with governance messages including `After exact result and safe checkpoint proof, progress to next operation only when an ACTIVE controller exists.` That fragment is insufficient to identify a failing test or root cause. Do not infer governance failure from an excerpt of unrelated output.

The full raw test stderr and stdout were **not persisted by the .017 implementation**, so we cannot reconstruct failing test IDs from the compact result. This is an evidence-handling defect in the test runner, not necessarily in Windows Relay runtime code. The source remained on clean canonical branch; original backup, production 8766 process, browser and HUD were not replaced or controlled by this test.

## Narrow, non-repeating recovery
A new unique PCE11.018 diagnostic shall read all five canonical controls, fast-forward only clean pinned GitHub checkout, validate engineering_preflight(repo,18,series=11), then run the **Windows Relay unittest discovery once, explicitly for detailed failure capture**. Persist complete raw test stdout/stderr in a new uniquely named evidence folder and emit a bounded machine-readable count, failing test identifiers, trace excerpts and exact exit code, without exposing secrets. This is the first instrumented re-run; it must not replay .017 packet, claim acceptance, or proceed to canary. Diagnose and patch at the source, test narrowly, then full suite.

## Blockers
Sidecar live canary PCE11.018 is CANCELLED and moved to later unique operation only after full source suite passes, isolation/containment accepted, and no impending checkpoint. No STOP/kill/reload. Include the failed .016 and .017 slots and further operations in audit .015–.019 before PCE11.020.