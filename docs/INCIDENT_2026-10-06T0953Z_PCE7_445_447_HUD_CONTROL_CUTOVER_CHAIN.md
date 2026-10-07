# Incident — 2026-10-06T0953Z — PCE7.445–PCE7.447 HUD/control cutover failure chain

**Class:** INCIDENT / WINDOWS RELAY / HUD CONTROL PLANE / CUTOVER SAFETY  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Live install protected:** `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay`  
**Status:** OPEN — source repair and live re-acceptance remain pending.

## Boundary truth

The legacy live relay/HUD is the current usable fallback. The new HUD/control-plane source exists and has repeatedly passed its pre-cutover source suite, but the new control plane is **not accepted live**. The most important live PCE7.446 attempt deployed the new HUD, proved STOP and OFF, failed START with `DISCONNECTED`, then automatically restored the previous live files and relaunched the legacy HUD.

Do not infer live acceptance from the presence of the new source, helper scripts, or a briefly visible new HUD. The acceptance boundary remains a real runtime sequence with rollback protection.

## Intended operator state model

The Director's accepted state semantics are:

- `STOPPED`: intentional operator stop; the entire product must quiesce, not merely the backend listener.
- `STARTING`: explicit startup in progress.
- normal runtime phase: relay should be running and recoverable.
- `OFF`: intentional shutdown.
- `DISCONNECTED`: relay is intended to run but a required dependency/listener is unavailable; show the reason.
- `KILLING RELAY` → `KILLING HUD` → no HUD: emergency teardown sequence.
- `KILL FAILED`: teardown verification failed; HUD must remain visible with the reason.
- MINIMIZE affects only the HUD window and must not alter relay state.
- RESTART is an explicit operator action.

Successful KILL must persist its latch before teardown so watchdog/recovery components cannot resurrect the product. The next deliberate START clears kill/off state.

## PCE7.445 — source implementation

PCE7.445 introduced the expanded HUD/control state machine in:

- `windows-relay/hud.py`
- `windows-relay/relay-control.ps1`
- `windows-relay/relay-watchdog-loop.ps1`
- `windows-relay/sync-live.py`
- `windows-relay/tests/test_hud.py`

The implementation reached a 273-test source pass before live cutover. Commit `68e3487` recorded the principal HUD/control-plane source change. Earlier helper-generation failures were rolled back rather than stacked.

## PCE7.446 — live cutover grief

The cutover exposed several tooling and runtime defects in sequence:

1. The first live-cutover helper failed before deployment because its rollback snapshot code attempted to copy state markers into a `markers` directory that had not been created.
2. A temporary `_v2` wrapper was introduced to work around that defect. The Director rejected the resulting untidy wrapper pattern. The approach was replaced by one canonical cutover helper and the wrapper was deleted.
3. An early broad `sync-live.py` approach copied an unnecessarily wide runtime/test surface into live. This was abandoned in favor of a narrow control-plane deployment boundary.
4. The clean narrow cutover ran all 273 source tests successfully, created a live rollback, staged exact source bytes, deployed the new HUD/control plane, and showed the new HUD on screen.
5. Live STOP succeeded and status reported `STATE=STOPPED`.
6. Live OFF succeeded and status reported `STATE=OFF`.
7. The next START returned `DISCONNECTED` and the cutover failed closed.
8. Automatic rollback restored the previous live files and the legacy HUD. The Director visually confirmed the new HUD disappeared and the legacy `PAUSED` HUD returned.

This is the desired rollback behavior: a failed acceptance step must return the machine to the pre-cutover usable relay rather than leave a partially upgraded control plane.

## PCE7.447 — source-repair grief

The START failure investigation identified process-launch construction as the immediate source-repair target. PCE7.447 then accumulated its own validation failures, all contained to source work:

1. A temporary repair helper invoked `unittest -s tests` from the repository root even though the suite is under `windows-relay/tests`, producing `ImportError: Start directory is not importable: 'tests'`.
2. That helper caught `Exception` rather than `BaseException`, so a `SystemExit` path could bypass its intended rollback handler.
3. The first tracked replacement helper contained a Python syntax error (`'(' was never closed`) and therefore never began mutation.
4. The next helper passed syntax preflight but generated a launch string containing a literal backslash before the quote; the new regression test caught it and source rollback completed.
5. The next iteration strengthened validation with a real PowerShell `Start-Process` test, but the static test assumed three launch sites when there are actually four, and the candidate runtime launch primitive did not create its expected output file. Source rollback again completed.

The four relevant launch sites are:

- `relay-control.ps1` → start `run.ps1` supervisor;
- `relay-control.ps1` → start `relay-watchdog-loop.ps1`;
- `relay-watchdog-loop.ps1` → start `hud.py` through `pythonw.exe`;
- `relay-watchdog-loop.ps1` → start `run.ps1` when listener and supervisor are absent.

The repair must cover all four sites and must be proven on Windows with real paths containing spaces before live deployment.

## Separate open STOP defect

This incident does not close `INCIDENT_2026-10-06T0701Z_HUD_STOP_PAUSED_BUT_BROWSER_RESULT_SPAM_CONTINUED.md`.

That earlier incident proved a backend pause can coexist with browser-side saved-result delivery/recovery. Therefore whole-product STOP acceptance still requires browser timers, retry/recovery machinery, packet discovery, result delivery, watchdog resurrection, and any other autonomy plane to become dormant until explicit START.

Backend exact-once protection prevented evidence of repeated Windows side effects during that incident, but browser quiescence still failed.

## Root-cause direction

The immediate PCE7.447 defect is not the HUD state vocabulary. It is safe detached process creation when script/file paths contain spaces. Previous code used backslash-quote constructions inside PowerShell `Start-Process -ArgumentList`; PowerShell does not treat backslash as its native string-escape mechanism, and repeated attempts to repair this through generated nested escaping produced misleading source strings.

The next source gate must first prove the proposed detached-launch primitive independently on `windows-latest`. Only after that proof passes should the four production launch sites be changed.

## Reliability rules learned tonight

1. Never use live as the first place a Windows process-launch primitive is proven.
2. Generated helpers must be syntax/parse checked before execution.
3. Test working directory is part of the test contract; use the canonical `windows-relay` root for relay suite discovery.
4. Rollback handlers must cover `BaseException` when the helper itself can raise `SystemExit`.
5. Count the actual launch topology before writing static assertions.
6. Prefer a dedicated regression file over repeatedly injecting tests into an unrelated large test module.
7. Source green is not live green.
8. Live mutation requires an exact rollback snapshot and automatic restore on the first failed semantic acceptance.
9. Never force-push recovery work.
10. One-shot repair wrappers are temporary debt and must be removed after closure.

## Current safe state

- Legacy live relay/HUD: restored and usable fallback.
- New HUD/control plane: source exists; live acceptance not complete.
- PCE7.447 source mutations from failed attempts: rolled back.
- Safety branch before overnight source hardening: `safety/PCE7.447-pre-overnight-source-hardening-4b4f454`.
- Stable consumer branch remains outside this work and must not be promoted from incomplete acceptance evidence.

## Required closure

PCE7.447 closes only when a Windows runtime test proves the launch primitive and the production source uses that proven primitive at all four launch sites with full source tests green.

PCE7.448 then performs a narrow, backed-up live acceptance sequence:

`STOP → OFF → START → RESTART → KILL → START → STOP`

The final state must be intentional `STOPPED`, the new HUD must be the running HUD, and any failure must restore the legacy fallback automatically.
