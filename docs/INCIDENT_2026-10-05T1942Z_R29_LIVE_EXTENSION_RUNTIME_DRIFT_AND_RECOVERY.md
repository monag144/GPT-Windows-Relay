# Incident: r29 live extension runtime drift and recovery

Date: 2026-10-05
Branch: `consumer/r29-firefox-offline-tray`
Stable baseline: `consumer/one-click-go` at `d5b9db7ad785b5cae8dc3b64219303b9fcfa634a`

## Symptom

The Windows relay backend returned HTTP 200 and the HUD showed READY / content port connected, but a visible `[GPT_WINDOWS_ACTION]` packet could remain unconsumed. A later ChatGPT assistant message could wake the scanner and cause the earlier packet to execute. Reloading the extension could also replay an already-completed packet; backend replay protection correctly returned the cached result instead of re-executing it.

## Root cause

The active Firefox content script was older than the r29 GitHub source. In the GitHub scanner, recovery also had a blind spot: a recovery pass could find the already-watched assistant unit but decline to re-inspect it. A DOM remount or later assistant mutation could therefore become the event that finally retriggered inspection.

The previous HUD readiness state only established backend/browser connectivity. It did not prove scanner progress or packet discovery, so a stalled scanner could look healthy.

## r29 hardening

- Force reinspection of the newest valid, unconsumed relay packet on the 15-second recovery cycle.
- Add a five-minute bounded stall watchdog. A visible packet can escalate to page refresh; a prolonged lost extension runtime can escalate to extension reload.
- Preserve folded/collapsed rendering recovery and the sandwich-technique coaching path.
- Emit packet/lifecycle events so scanner progress is independently observable.
- Persist and deduplicate a Firefox chat-rotation counter. Every 100 relay operations starts a fresh ChatGPT chat.
- Persist exact active/last instruction state in the backend.
- Show RUNNING, DISCOVERED, WAITING, DELIVERING, STALLED, RECOVERING and related lifecycle reasons/ages in the compact HUD; expanded HUD exposes the exact decoded instruction.

## Live deployment drift

The active development relay was `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay`, not the Git checkout. Its backend and extension files had diverged from both r28 and r29.

Before overlaying the r29 recovery features, the live deployment was backed up to:

`C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay\backups\r29-recovery-20261005T193549Z`

The live backend was patched narrowly for active/last instruction state instead of being replaced wholesale. The live Firefox worker retained its development architecture and received the r29 rotation/browser-id additions. The content scanner and HUD were updated to the tested r29 versions.

## Verification

Automated:
- consumer suite: 59 tests OK
- relay suite: 249 tests OK
- targeted content/HUD contracts: PASS
- Python compile and JavaScript syntax gates: PASS

Live:
- backend restart exposed the active action ID/status/shell/exact command.
- HUD visual capture showed `RUNNING`, `Windows process executing`, elapsed age, current packet ID, and a command preview while the action was actually in flight.
- disk activation gate showed r29 files were present but the old Firefox runtime was still loaded.
- after one Firefox extension reload plus ChatGPT page refresh, packet `PCENG-A6.382-r29-first-message-live-acceptance` executed on the first assistant message and logged both `relay_packet_discovered` and the exact current packet ID:
  - `ACTION_EXECUTED=PASS`
  - `R29_LIFECYCLE_EVENT=PASS`
  - `CURRENT_PACKET_EVENT=PASS`
  - `FIRST_MESSAGE_INGESTION=PASS`

This directly accepts the fix for the observed "new assistant message wakes the previous packet" failure.

## Release boundary

Do not move `consumer/one-click-go` / r28 as part of this incident. r29 remains an isolated feature branch until the rest of its workstream and promotion gates are intentionally completed.


## Windows venv process-cardinality correction

Post-acceptance process forensics initially reported two backend Python processes and two HUD Python processes. These were not duplicate application launches.

- backend launcher: `.venv\\Scripts\\python.exe` PID 19024 → base Python 3.13 PID 9900; only PID 9900 owned TCP 127.0.0.1:8766.
- HUD launcher: `.venv\\Scripts\\pythonw.exe` PID 7476 → base Python 3.13 `pythonw.exe` PID 8580.
- corrected logical-leaf counting reported one backend instance, one HUD instance, and one port-8766 listener: `VENV_LOGICAL_INSTANCE_PROOF=PASS`.

The first logical-leaf probe (A6.386) was itself invalid because it attempted to assign PowerShell's case-insensitive reserved automatic variable `$PID`; A6.387 corrected the variable name and used terminating error behavior. Operational health checks must not use raw interpreter process count as application cardinality.
