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

## Scheduler probe status through PCE17.013
- `PCE17.012-independent-cutover-worker-probe` was issued. Its original full native receipt remains unavailable in this conversation, but **PCE17.013 inspected the persisted state** on 2026-10-12 01:47:16–01:47:17 UTC and reported `PRIOR_PCE17_012_STATUS=OK`. The unique `.012` identity was executed and is **not eligible for replay**. An `OK` status alone does not establish the scheduler-specific stdout markers.
- `PCE17.013-independent-worker-probe-with-prior-status-check` returned `OK`, `PENDING_MISSIONS=0`, and `SECOND_PROBE_SKIPPED=True`. This is correct de-duplication and a successful relay receipt, not confirmation that an independent worker started. No new scheduler task was created in `.013`.
- Next unique ordinal **PCE17.014** should read the saved `.012` result and explicitly verify `INDEPENDENT_TASK_EXECUTED=True` and `TEMPORARY_TASK_REMOVED=True`, plus current process identities, before staging any independently scheduled cutover. Do not confuse source hashes with loaded runtime.
- User also reports that reprinting a stuck action might wake the scanner; repair is a P0 item in the dated task backlog, not an approved duplicate execution workaround.

## PCE17.015–.018 updated live evidence — 2026-10-11 (PDT)
- `PCE17.015` was consumed as a third `GOVERNANCE_BLOCKED` at the legacy checkpoint guard (GitHub .010–.014 audit independently verified). See incident `docs/incidents/WINDOWS_RELAY_PCE17_015_REPEATED_LEGACY_CHECKPOINT_GATE_2026-10-11.md`. No execution.
- `PCE17.016` OK: root `windows_relay.py`, `hud.py`, control, watchdog, launcher have the expected SHA256 values; legacy PID 13344 owns port 8766; old HUD PIDs 1924/3340, old watchdog PID 14476; zero root HUD/watchdog. Backup exists. System Python and Pythonw available, no canonical venv. Zero pending missions. Count of 518 READY outbound delivery entries read while .016 was inflight; no delivery mutation.
- `PCE17.017` COMMAND_FAILED only on badly quoted inline Python test, after read-only measurements: 519 READY outbound records, processed 520, outbound owner `browser`, no Windows sender attempts observed. This command did **not** establish a Python failure; use argument-quoting-safe inspection instead.
- `PCE17.018` OK: system Python 3.13.15, Tkinter imported, canonical backend and HUD syntax parsed successfully. Legacy nested backend source SHA256 `540F2589EEB4B6980C6947D26381E653F17C0886043514E39721268E998CAB93` matches browser-owner delivery semantics: `outbound_owner=browser` suppresses Windows outbound worker, `READY` entries accumulate for completed commands. **520 READY entries do NOT imply 520 unsent messages; never bulk-send or clear based on READY counts.** No Windows outbound attempts, no pending missions, legacy backend PID 13344 still running.
- Next unique ordinal PCE17.019. The five-operation .015–.019 GitHub audit and 20-operation drift review are due **before .020**. .018 is evidence of Python import/syntax only, **not proof of the new backend/hud live operation or loaded Firefox compatibility**.

## PCE17.019 and 20-operation checkpoint — 2026-10-11 PDT
- `PCE17.019` **OK**, read-only (2026-10-12 01:57:10–01:57:13 UTC): legacy controller SHA256 `79264E06AE53F54BFE5F43CAC6664F967C32244FFC1201F46F280A4D6E9850FC`, legacy watchdog SHA256 `38B5FE08D8230658C9153925FB7D4F8CC3AF846CB2AA447CF6837B850B748DDE`. Actual `OFF` uses backend disarm/quiescence and kills old backend + watchdog; watchdog `taskkill /T` might terminate child HUD and must be verified, never assumed. Root `windows_relay.py --help` imported successfully; persistent extension manifest version 0.3.17, ID `gpt-windows-relay@local`, loaded Firefox bytes **unknown**. Legacy port 8766 PID 13344; watcher 14476; HUD 1924→3340; pending missions 0; browser owns outbound delivery.
- Four audit windows through .019 reconciled; fourth `docs/audits/AUDIT_2026-10-12T0158Z_PCE17_015_019_CHECKPOINT.md` was committed/read back on `main`, Git blob `2748781d27a60999421610968b0d09872f440de3`. Twenty-operation drift review `docs/reviews/WINDOWS_RELAY_PCE17_FIRST_TWENTY_OPERATIONS_REVIEW_2026-10-11.md` was committed/read back: 15 OK, 3 legacy governance blocks, 2 command failures, no live canonical cutover. Next unique ordinal PCE17.020, not previously issued.
- New priority: prepare the one-time independently scheduled cutover helper **within the single development build's controlled source path**, not another running build. First identify whether the local canonical folder is a Git checkout or staged files, and identify all old process ancestors and scheduled restart sources before stopping the watcher. Do not run PCE8 `safe_live_cutover.py` as-is, and never claim active source matches staged source without a new process-ID readback.

## PCE17.020 receipt-gate block — 2026-10-11 PDT
- `PCE17.020-cutover-staging-and-legacy-restart-source-inspection` returned `GOVERNANCE_BLOCKED` 2026-10-12 02:04:12 UTC, no reservation/execution. The audit for `.015–.019` and 20-turn review **were committed and independently read back** before it was issued. All four PCE17 multiples of five (`.005`, `.010`, `.015`, `.020`) have failed with `github_checkpoint_audit_missing` while subsequent ordinals worked.
- Canonical `engineering_preflight` requires an explicit `github_audit_receipt`; GitHub file existence alone is not a receipt supplied to the executor. The legacy transport for this receipt remains unproven; do not claim source cause or forge a receipt. Detailed incident: `docs/incidents/WINDOWS_RELAY_PCE17_020_FOURTH_CHECKPOINT_RECEIPT_GATE_2026-10-11.md`.
- Next **unique** ordinal PCE17.021. PCE17.020's git checkout / process ancestry / scheduled-restart inspection never ran. Keep this preflight read-only before staging an independent cutover. The cutover has not occurred.

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
