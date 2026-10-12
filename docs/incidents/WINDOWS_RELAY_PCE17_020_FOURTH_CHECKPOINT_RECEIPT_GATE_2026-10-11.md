# Windows Relay — PCE17.020 fourth checkpoint receipt gate — 2026-10-11 PDT

## Observed native result
- `PCE17.020-cutover-staging-and-legacy-restart-source-inspection`, session pce17.1, `GOVERNANCE_BLOCKED`, `exit_code=null`, 2026-10-12 02:04:12 UTC.
- Native stderr: `GOVERNANCE_CHECKPOINT_BLOCKED: github_checkpoint_audit_missing; no action reserved or executed`.
- No .020 command or process query executed. No files, processes, state, task schedule, Firefox, or backups were intentionally modified by the blocked packet. `.020` ordinal permanently consumed.

## Checkpoint evidence already available before issuing .020
- Required five-operation audit `.015–.019` committed and read back from `main`: `docs/audits/AUDIT_2026-10-12T0158Z_PCE17_015_019_CHECKPOINT.md`, commit `d0ff2ab4b6345b2a415e2e1a8991f9830cbed3db`, blob `2748781d27a60999421610968b0d09872f440de3`.
- Separate 20-operation review committed/read back: `docs/reviews/WINDOWS_RELAY_PCE17_FIRST_TWENTY_OPERATIONS_REVIEW_2026-10-11.md`, commit `6d5ea927791b9be8362fd9b4d364919270e6b1ef`, blob `36b7e0091a1bf80bdd7c12046f2db95f8b51cb2c`.
- Canonical GitHub `consumer/control_harness.py` blob `ca2141c45726366abb889db0cb5a794ed8735075` contains `engineering_preflight`: at ordinals 005,010,015,020 and so on, `github_audit_receipt` is required; if absent, it returns the **same** `github_checkpoint_audit_missing` error. This makes a missing **receipt supplied to dispatcher** plausible, even when the GitHub audit file exists. Receipt transmission and the actual installed code path have not yet been independently inspected; do not claim conclusively why the legacy dispatcher rejected it.

## Pattern and current state
- All four PCE17 multiples of 5 (005,010,015,020) were blocked with the same error, with respective next ordinals 006,011,016 subsequently OK. Do not repeat an issued ordinal to try to bypass the gate.
- Last verified actual Windows state from PCE17.019: legacy nested backend PID 13344 on 127.0.0.1:8766; legacy watchdog PID 14476, HUD PID 1924->3340, zero pending missions, browser-owned outbound-result delivery. The unified canonical development build is staged but **not** proven deployed.
- Verified rollback backup PCE17.006 (2,628 files). Verified Windows Scheduler independent worker PCE17.012 by PCE17.014. Do not run old PCE8 cutover helper as-is.

## Corrective action
- Engineer should inspect **actual live nested source** and issuer for `engineering_preflight`, `github_audit_receipt`, and `GOVERNANCE_CHECKPOINT_BLOCKED`; distinguish missing transmitted receipt from missing GitHub audit. Do not forge a receipt or weaken authentication/STOP/ownership checks.
- Next unique operation **PCE17.021**, read-only, may inspect live local governance and scheduled legacy restart sources without invoking .020 again. 20-turn review already recorded; next five-turn audit before .025.
- Continue toward **one integrated development build** (backend + HUD + persistent browser integration + One-Click Go), with independent cutover and rollback. No re-release before acceptance.
