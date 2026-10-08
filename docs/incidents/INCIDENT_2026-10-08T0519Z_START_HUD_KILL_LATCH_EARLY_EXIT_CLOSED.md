# INCIDENT — 2026-10-08T05:19Z — START-HUD silently exits under relay kill latch

**Status: CLOSED (Director-directed, provisional operational closure).**  
**Live verification: NOT PERFORMED; deferred confirmation is not a claim that the HUD opened.**  
**Scope:** `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay` / canonical Windows source `monag144/GPT-Windows-Relay`, branch `pce10/reconcile-control-and-rotation`.

## Observation / reported failure

The Director requested diagnosis and repair because `START-HUD` was not opening a HUD window. Codex inspected `START-HUD.bat`, `hud.py`, process inventory, latch files, and watchdog logs in the live workspace and canonical checkout.

The batch launcher was intact:

```bat
@echo off
cd /d "%~dp0"
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0hud.py"
```

But the previously deployed `hud.py` contained an early exit at the very beginning of `run_ui()`:

```python
if (Path(__file__).with_name(".relay-kill")).exists() and not (Path(__file__).with_name(".relay-kill-failed")).exists():return 0
```

Codex reported `.relay-kill` actually present. This made `pythonw.exe` exit before opening `tk.Tk()` when START-HUD was invoked, with little visible error feedback. The watchdog log also showed attempts to recover the absent HUD, which could not succeed while the early-exit condition remained.

## Root cause

**Unintended coupling of HUD visibility to backend kill state.** The operator kill latch appropriately stops backend/watchdog activity, but the HUD is also an operator-facing status/control surface. The startup guard prevented the HUD from displaying its already implemented `KILLING RELAY` state. A valid batch launcher appeared nonfunctional because its child process returned without creating a window.

## Repair by Codex — as reported by the Director

- Codex modified `windows-relay/hud.py` in the canonical local checkout and `hud.py` in the active live workspace.
- Removed/replaced the premature `.relay-kill` exit guard while retaining the Windows single-instance mutex, window startup and `KILLING RELAY` presentation.
- First search/replace attempt failed because the expected exact guard text did not match; Codex inspected source, corrected its edit and observed the desired local diff.
- Committed locally as **`d5df0b3 Keep HUD available during relay kill state`**, reporting one insertion and one deletion in `windows-relay/hud.py`.
- Codex explicitly reported it **did not launch the HUD and did not run tests**.

### Source-provenance qualification at incident logging time

At 2026-10-08T05:19Z, the GitHub connector **could not resolve the abbreviated commit `d5df0b3` remotely** (HTTP 422). The fetched canonical GitHub branch still displayed the old kill-latch early-exit guard in `windows-relay/hud.py`. This is consistent with Codex's fix being **committed locally but not pushed**. Do not claim it is remote-published or that the live copy and remote repository have been reconciled. In particular, do not sync/copy old remote `hud.py` over the repaired local/runtime versions without explicit diff reconciliation first.

## What is resolved versus unproven

- **Reported fixed:** Corrected local source/live copy removes the HUD-only early exit under `.relay-kill`; preserved single-instance mutex and KILLING RELAY presentation.
- **Not proven:** actual GUI launch, source or runtime test result, clean behavior of the control panel while kill latch is present, or remote push of `d5df0b3`.
- **Not changed:** backend/Firefox watchdog and PCE10 discovery-stall recovery; separate open incidents cover those failures.

## Director disposition and next maintenance step

The Director expressly requested **CLOSED, for now**. This record therefore closes the single `START-HUD` failure report administratively, without certifying runtime success.

On the next safe Windows acceptance opportunity, verify the repaired live `hud.py` behavior using a bounded HUD launch observation; confirm exactly one HUD process and KILLING RELAY presentation when the kill latch exists, preserve STOP/KILL semantics, and reconcile/push `d5df0b3` to the canonical Windows branch. **Reopen this incident if the HUD still fails to appear, duplicate HUD processes result, the kill state is misrepresented, or the local fix is overwritten.**

## Learning / prevention

Do not use an operator kill latch as a reason to hide the user-facing diagnostic interface. A status/control HUD should remain able to display an explicitly killed or stopped backend where operator policy permits it. Maintain separate frontend and backend lifecycle latches, report launcher child-process early exits, and verify source-to-live parity before promoting or overwriting repaired runtime files.

**Incident closure at documentation time:** CLOSED PROVISIONALLY / LOCAL FIX REPORTED / DEPLOYMENT AND LAUNCH VALIDATION PENDING.
