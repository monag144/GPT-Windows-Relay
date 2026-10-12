# PCE17.015 — Repeated legacy checkpoint governance block — 2026-10-11 (Pacific)

## Native result
- PCE17.015-final-single-build-cutover-preflight, session pce17.1, 2026-10-12 01:50:30 UTC.
- status GOVERNANCE_BLOCKED; exit_code null; stderr `GOVERNANCE_CHECKPOINT_BLOCKED: github_checkpoint_audit_missing; no action reserved or executed`.
- Command was read-only; it **did not execute**. No Windows process/state/backup/Firefox modification occurred from .015. Its unique ordinal is consumed.

## Evidence invalidates the asserted missing-audit explanation
- The required PCE17.010–.014 five-operation audit was committed to GitHub `main` at commit `cd5430ad6f6ab48a9f3de52a04f3546cec225dcc` and independently fetched as blob `aa554c0c615a11b22c74cd822023227976b6dc89` before .015.
- The canonical GitHub `consumer/control_harness.py` is blob `ca2141c45726366abb889db0cb5a794ed8735075` and requires a receipt supplied by assistant-side engineering; the old live relay's enforcement is not receiving that receipt.
- Identical false-missing-audit blocks occurred at .005 and .010, immediately after legitimate five-operation checkpoints. The correlation with ordinals divisible by five is strong; the precise legacy gate implementation must be inspected before root-cause claims.

## System actually running (last successful evidence PCE17.014)
- Legacy nested `windows-relay/runtime/windows_relay.py` owns localhost 8766 as PID 13344; old watchdog PID 14476; legacy HUD process tree 1924->3340. Zero canonical HUD/watchdog processes. Do not claim successful new installation.
- Scheduler-independent worker probe .012 independently verified by .014: `INDEPENDENT_TASK_EXECUTED=True` and `TEMPORARY_TASK_REMOVED=True`, probe file valid and zero residual tasks; pending missions 0.
- Rollback backup PCE17.006 completed 2,628 verified allowlisted files; mission-cancellation snapshot PCE17.009 also exists. Single integrated development build policy remains in GitHub.

## Handling
- Consume .015; move to unique .016. No repeat of .015, no false bypass/forged GitHub receipt, no weakening STOP, owner, token authentication, or ordinary executor controls.
- GitHub-first audits remain mandatory and are documented externally. Keep legacy guard defect as P0 to repair in eventual canonical build.
- Proceed with short read-only .016 preflight and identity/latch verification ahead of an independently scheduled one-time cutover worker. Worker must persist verification and rollback, and must never replay an uncertain action.
- Manual interactive PowerShell clipboard paste is unreliable; user prefers relay or CMD and minimal operator action.
