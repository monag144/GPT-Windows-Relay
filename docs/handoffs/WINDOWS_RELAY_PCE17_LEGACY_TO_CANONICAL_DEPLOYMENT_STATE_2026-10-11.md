# Windows Relay PCE17 — Legacy-to-canonical deployment state — 2026-10-11

**Canonical repository:** monag144/GPT-Windows-Relay. **Primary rule:** the verified staged source tree is NOT the installed/live application. Current live identities from PCE17.011 take precedence over GitHub build existence.

## Last authoritative live observation
- PCE17.011-identify-active-backend-and-hud: native status OK at 2026-10-12 01:24:53–01:24:55 UTC.
- Port 127.0.0.1:8766 listener PID 7464: **LEGACY_RUNTIME**, executing nested `C:\Users\Craig Morgan\Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay\runtime\windows_relay.py`.
- HUD processes: PID 1924 (parent 14476) and PID 3340 (parent 1924), both **LEGACY_RUNTIME** with nested `windows-relay\runtime\hud.py`; related python launcher chain does not prove two separate visible windows.
- New canonical staged source is `windows-relay\windows_relay.py`, `windows-relay\hud.py`, `windows-relay\extension-persistent`, `windows-relay\START-GPT-WINDOWS-RELAY.bat`. WIP SHA as last independently verified: a35d325ce9a666a372e2a88bc7b60704bdf785f9. No successful canonical live cutover proven.
- Firefox temporary loaded extension was observed in UI but loaded-byte identity and permanence remain **unverified**.

## Completed and safely preserved
- PCE17.006: verified 2,628-file rollback under `%LOCALAPPDATA%\GPTWindowsRelayDeployBackups\PCE17-006-20261011-174328-5118e464`, excluding historical backups and virtual environments.
- PCE17.009: user-approved removal of two Oct 4 Chrome-only queued consumer missions. Post-cleanup pending count 0; pre-cleanup state backup in `%LOCALAPPDATA%\GPTWindowsRelayDeployBackups\PCE17-009-Mission-Cancellation-20261011-175213-c4e44cc5`.
- PCE17.010: stale legacy runtime blocked a read-only identity operation with `github_checkpoint_audit_missing` despite committed main audit. No execution, ordinal consumed; incident is filed. PCE17.011 succeeded and identified actual legacy processes.
- Required five-operation audits through .009 committed and read back on GitHub main. Next five-op audit due **before .015**. Do not repeat blocked .010.

## Outstanding operation: PCE17.012
- `PCE17.012-independent-cutover-worker-probe` was issued as a scheduled task probe. **Its native result is not yet in the conversation**. Do not claim success, do not reissue its unique ID, and do not perform an irreversible cutover before reviewing its exact result.
- Probe design is independent of the running relay, but the currently issued operation itself uses legacy relay transport to schedule and verify a harmless temporary task. No backend shutdown is authorized as part of .012.

## Operator experience and deployment restrictions
- User's interactive PowerShell paste can reverse/mangle code. **Prefer the authenticated relay tool; for self-terminating operations use an independently executed .cmd/.bat or proven task-scheduler worker**, not paste into PowerShell console.
- User prefers as little manual work as possible; do not repeatedly ask them for PowerShell or to uninstall/re-add Firefox. The user will forward the .012 result when available.
- A relay execution action cannot safely kill its own backend while still requiring that backend to return the outcome. Use an independent, bounded local cutover helper with persistent local logs and rollback, scheduled **only after .012 proves the worker works**.
- Keep legacy processes untouched until cutover is separately staged. Treat any `FOREIGN_LISTENER` output from the canonical controller as expected while legacy PID 7464 owns 8766, not proof of canonical startup.
- Respect the shared HUD singleton mutex and proactively ensure old watchdog/supervisor do not revive the legacy process. Do not execute queued missions, erase state, or bypass STOP/ownership/authentication. Verify exact full script paths, not root-prefix matches.
- Historical `windows-relay/safe_live_cutover.py` on current WIP is **NOT** a drop-in helper for this deployment: it references old `Client\Relay` and PCE8/Firefox auto-reload, mutates live trees and may wake/send prompts. Do not run it without a separate safety redesign/review. Likewise README/older setup instructions are not loaded-install evidence.
- Once independent handoff passes, check backend PID/full path, correct five-button HUD (START STOP RESTART OFF KILL), authenticated status/owner, extension loaded identity and safe single command receipt. Live exact-once/endurance/release acceptance remains open.

## Governance
Read canonical `consumer/control_harness.py`, dated documentation index, mission/priorities, backlog, established operating facts, relevant incident/audit and this dated state note before future PCE operation. Governance belongs to assistant engineering, not the old live relay. Every ordinal is consumed once. Automatic chat/agent rotation is permanently retired.
