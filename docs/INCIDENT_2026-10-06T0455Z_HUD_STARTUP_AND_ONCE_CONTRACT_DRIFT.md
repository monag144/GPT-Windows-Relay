# Incident — HUD startup coupling and `--once` contract drift

Timestamp: 2026-10-06T04:55Z  
Branch: `consumer/r29-firefox-offline-tray`  
Status: **OPEN — source contract repaired; live startup topology and coupling still require proof**

## Operator observation

During recovery from the PCE7.408 relay failure, the operator reported that the relay PowerShell was running but the Windows HUD was gone. The intended product behavior is that relay supervision and the HUD come up together; recovering the backend alone must not silently leave observability behind.

## Evidence from PCE7.410–PCE7.415

- PCE7.410 proved the relay transport was executing again, but its diagnostic call to `hud.py --once` timed out after 15 seconds.
- Direct r29 source inspection showed the current `hud.py` had no argparse/`--once` handling and always entered `run_ui()` / Tk mainloop.
- This contradicts the engineering-log P1 proof, which explicitly records `hud.py --once` returning a valid live snapshot. This is source/documented-contract drift.
- `START-HUD.bat` launches `pythonw.exe hud.py` separately. A manually started `windows_relay.py server` therefore does not, by itself, prove the HUD has been launched.
- PCE7.415 attempted one real HUD launch and then observed two Windows processes matching `hud.py`. The action failed only because its assertion required raw process count == 1.
- The relay server itself is already known to appear as a venv launcher/shim plus a real Python child. Therefore two matching OS processes are **not evidence of two logical HUD instances** until parent/child topology is checked.

## Repair committed on r29

- `e3e0126b1605dd84d6c344a84ebbea4f107846c6` restores the `hud.py --once` JSON snapshot-and-exit contract.
- `069efb1391e1375e5958b90c545cd0596ab6a168` adds a behavioral regression test for the `--once` contract.

These commits repair source/test coverage only. Live Windows staging/reload and startup-coupling acceptance remain outstanding.

## Required closure

1. Classify current `hud.py` processes by PID/PPID/executable path and count logical HUD trees rather than raw Python processes.
2. Inspect the actual Windows startup/supervisor wiring and prove which owner is responsible for starting/restarting HUD and relay.
3. Make relay recovery restore HUD visibility automatically without creating duplicate logical HUD instances.
4. Treat the named HUD mutex as the logical singleton boundary and add auditable process-budget/reconciliation telemetry.
5. Live-run `hud.py --once` after staging and require immediate JSON exit.
6. Fix stale lifecycle display so an old `action_received` cannot leave the HUD showing STARTING forever after the deadman interval.
7. Re-run the sustained relay soak; loss of HUD while relay is active is an observability/recovery incident.

No stable promotion is authorized from this repair alone.


## PCE7.417 logical HUD proof — 2026-10-06T0523Z

PCE7.417 proved the two matching `hud.py` Windows processes are one logical venv-launcher chain, not two HUD instances:

- venv `pythonw.exe` PID 18192;
- real Python 3.13 `pythonw.exe` PID 10564, parent PID 18192;
- classification: `venv_shim_parent_child_pair`.

Therefore raw process count == 2 is normal for one launched HUD on this machine. The process-budget and singleton acceptance rule must operate on logical process trees/the named HUD mutex, not raw interpreter count.

The outer HUD process currently has PPID 18044, which was not part of the persistent PowerShell baseline. Because this HUD was launched by the PCE7.415 recovery action, startup ownership still needs direct `run.ps1` / watchdog wiring inspection before relay+HUD automatic recovery can be called fixed.


## Source/live supervisor deployment-boundary finding — 2026-10-06T0525Z

PCE7.418 plus direct r29 source inspection exposed a deployment boundary that must be preserved during repair:

- live `Client\Relay\run.ps1` supervises the established engineering relay and, from the PCE7.418 lines, contains no HUD launch;
- r29 `windows-relay/run.ps1` is consumer-specific: it uses `GPTWindowsRelayConsumer` config/state and the `Local\GPTWindowsRelayConsumerSupervisor` mutex;
- r29 `sync-live.py` stages `hud.py` and `START-HUD.bat` but does **not** stage `run.ps1` or `relay-watchdog-loop.ps1`.

Therefore do not repair the current engineering instance by blindly copying the consumer `run.ps1` over the live supervisor. First read the remaining live startup wiring and then make HUD lifecycle ownership explicit at the correct product boundary. Any sync/install path that is supposed to own supervisor lifecycle needs a separate, deliberate contract and test.


## PCE7.419 automatic-start ownership proof — 2026-10-06T0525Z

Compact saved-result readback closed the main startup-ownership question for the current live engineering relay:

- HKCU Run entry `GPTWindowsRelayWatchdog` starts only `relay-watchdog-loop.ps1`;
- watchdog singleton is `Local\GPTWindowsRelayWatchdog`;
- watchdog checks the listener and, when 8766 is already listening, sleeps/continues without any HUD check;
- when listener + supervisor are absent it starts visible `run.ps1`;
- live `run.ps1` starts/restarts the relay backend but PCE7.418 found no HUD launch;
- `START-HUD.bat` exists and launches `.venv\Scripts\pythonw.exe hud.py`, but it is not referenced by the automatic chain proven above;
- only one relevant scheduled task was present, `GPTWindowsRelay-ActivateDeliveryV8-276`; it is not the startup owner.

This directly explains the operator-visible failure mode: relay/backend supervision can recover to ONLINE/ARMED while the HUD remains absent. Final repair should make the long-lived watchdog reconcile a missing logical HUD even while the listener is healthy, using the HUD's named mutex/singleton behavior to avoid duplicate logical instances.
