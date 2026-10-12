# PCE17.010–.014 checkpoint — 2026-10-11 (Pacific)

Canonical repo: `monag144/GPT-Windows-Relay`; GitHub `main`; assistant-side engineering audit. **Before** .015.

## Canonical reading evidence
- `consumer/control_harness.py`: blob ca2141c45726366abb889db0cb5a794ed8735075
- `windows-relay/TASKS.md`: d49999dc29466a04ba2c27cc39f341b9162779e9
- Dated docs index: 951611f6bc5e46efe9349e8cd101c1e9f5f5a420
- Dated mission/priorities: 86c3e0c3f2d1c44de9cccdc819597f120c8732be
- Dated backlog: ad1ea6f89ada030e54c220bc21dfac1a2d254708
- Safety: 693ad770964352de7de26886ba3b4e295ac0357a
- One integrated development build policy: 0981565145fd1dab9b31a7656705fde13e22f9b1
- PCE17 live handoff: fd900b6fb2dd4e6b57ac636260ea98580fccfd82
- Previous .005–.009 audit: 5a7d6a58481302c485e64406083bcdd795a8773c

## Issued operations and evidence
1. **PCE17.010-readonly-live-backend-and-hud-identity:** `GOVERNANCE_BLOCKED`, 2026-10-12 01:23:40 UTC, no action reserved or executed. Legacy returned `github_checkpoint_audit_missing` even though .005–.009 checkpoint was committed and verified. Incident at `docs/incidents/INCIDENT_2026-10-12T0123Z_PCE17_010_LEGACY_GOVERNANCE_GATE.md`. Ordinal consumed.
2. **PCE17.011-identify-active-backend-and-hud:** `OK`, 01:24:53–01:24:55 UTC, read-only. Port 8766 backend PID 7464 from nested **legacy** `windows-relay/runtime/windows_relay.py`. Legacy HUD tree PIDs 1924→3340. Canonical root process absent.
3. **PCE17.012-independent-cutover-worker-probe:** Original direct relay receipt **not seen in conversation**; verified from next two read-only actions: state `processed` entry status `OK`, saved result `status=OK`, `exit_code=0`, full stdout markers `INDEPENDENT_TASK_EXECUTED=True`, `TEMPORARY_TASK_REMOVED=True`, `NO_BACKEND_OR_HUD_TERMINATION=True`, `PCE17_012_END`. One probe directory marker contents verified; zero residual `PCE17-012` scheduled tasks. Independently scheduled task works. Uniqueness preserved.
4. **PCE17.013-independent-worker-probe-with-prior-status-check:** `OK`, 01:47:16–01:47:17 UTC. Found `PRIOR_PCE17_012_STATUS=OK`, `SECOND_PROBE_SKIPPED=True`, pending missions zero. Distinct ordinal, did not repeat scheduler side effects.
5. **PCE17.014-verify-scheduler-proof-and-live-legacy-processes:** `OK`, 01:48:44–01:48:48 UTC, read-only. Confirms all .012 stdout markers and actual marker file; zero residual scheduled tasks. **Legacy backend now PID 13344**, old watchdog PID 14476, old HUD PIDs 1924 and 3340. **Zero canonical HUD/watchdog**; no canonical release deployed. Pending missions zero. PID difference from .011 suggests restart/recovery but cause unknown; do not claim upgrade.

## Five-turn harness and evidence audit
- Ordinals .010 through .014 issued once and consumed. .010 blocked, no mutation. Subsequent .011/.013/.014 read-only. .012 created a single temporary scheduler task and confirmation file, then removed the task; no backend/HUD changes.
- Existing `PCE17.006` verified allowlisted 2,628-file backup and `PCE17.009` stale-queue cancellation snapshot remain rollback basis. No personal tokens exposed in GitHub.
- PCE17.012 demonstrates **isolated worker** capability only; live cutover not yet attempted and no canonical process evidence. Do not use historic PCE8 cutover script as-is: references old Client paths and wake/Firefox reload behavior.
- User rescue/drift: legacy HUD previously showed STALLED; operator hypothesizes reprinting relay action can wake it. Reprint is *not* a safe dedup/replay strategy. P0 work tracked in dated backlog and `docs/incidents/WINDOWS_RELAY_STALLED_COMMAND_REPRINT_OPERATOR_RESCUE_2026-10-11.md`. Manual PowerShell clipboard paste mangles ordering, so prefer relay or independent scheduled helper.
- User's latest single-build directive is committed to `docs/policy/WINDOWS_RELAY_SINGLE_DEVELOPMENT_BUILD_AND_RELEASE_2026-10-11.md`: exactly one integrated development build (backend + HUD + browser + One-Click Go), re-release after acceptance, preserve legacy for rollback only.
- No auto-rotation/new chat, no GitHub Actions, no claim of exact-once production safety or Firefox installed bytes attestation. User has authorized continued engineering, but **fail closed** on side effect uncertainty or unclear shutdown identities.
- Next ordinal **PCE17.015**; checkpoint requirement satisfied only after this file is committed to GitHub `main` and independently read back. Before risky scheduled cutover: independently verify old watchdog/HUD/relay exact process match, new Python runtime path, extension pairing, safety rollback and scheduler principal, and prepare bounded stateful helper with durable result/rollback logs and no duplicate backend. More than a staged build is required to call deployment successful.
- Next 20-operation drift review due before/at .020.

## Net-new progress
PCE17.012 successfully proved a real independent Windows Scheduler worker, .013 prevented duplicate execution, and .014 verified the original exact saved receipt and that legacy still owns runtime. User-side intervention reduced; architecture not yet activated.
