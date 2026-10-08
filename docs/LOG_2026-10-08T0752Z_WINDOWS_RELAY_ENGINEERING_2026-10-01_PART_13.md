# Archived source fragment 13/23 — 2026-10-08T0752Z

## Extension version ownership clarified

Actions 199-201 plus direct inspection of `sync-live.py` established the extension version ownership model:

- `windows-relay/extension/manifest.json` is the temporary/live-source manifest and currently declares `0.1.1`
- `windows-relay/extension-persistent/manifest.json` is the packaged extension manifest and currently declares `0.3.14`
- `build-extension-xpi.ps1` packages `extension-persistent`
- `sync-live.py::build_xpi()` explicitly reads `live/extension-persistent/manifest.json`, parses its `version`, and names the XPI from that value

Therefore the V6 release bump must:
- leave the temporary `extension/manifest.json` version untouched
- bump `extension-persistent/manifest.json` from 0.3.14 to 0.3.15
- update the builder's default XPI filename from 0.3.14 to 0.3.15

This replaces the incorrect all-manifests-same-version assumption that stopped Action 197.


## Scroll-v6 one-shot deferred by PC Engineer 3

The Director authorized one final contained attempt at scroll-v6, then instructed engineering to move on. The V6 experiment and test output were preserved under `%LOCALAPPDATA%\GPTWindowsRelay\engineering-backups\scroll-v6-*`. The full suite remained non-green after correcting the stale `anchor.scrollIntoView()` assertion, so scroll work was deferred without further redesign. The canonical worktree was restored to the last committed baseline and engineering priority moved to P1 Windows HUD.


## P1 Windows HUD MVP source implementation

Added a dependency-free Python/Tkinter HUD with backend ONLINE/OFFLINE + ARMED/DISARMED state, pause-sentinel visibility, telemetry-derived Firefox bridge/content runtime state, current/last relay action, compact error display, and live Arm/Disarm controls. Browser state is intentionally labeled ACTIVE/SEEN/STALE/UNKNOWN from telemetry age rather than falsely claiming connectivity. Added `--once` JSON diagnostics, singleton protection, HUD tests, START-HUD.bat, and sync-live inclusion. Full relay regression suite passed before commit.


## P1 Windows HUD MVP live proof — GREEN

The committed HUD was staged through `sync-live.py`, which reran the live relay regression suite and completed successfully. `hud.py --once` returned a valid live snapshot with backend health/ARMED state plus telemetry-derived browser state. The Tkinter HUD was then launched detached with the live relay virtualenv and its process remained alive after launch. P1 MVP therefore has source, tests, live staging, machine-readable state proof, and a running GUI process.


## INCIDENT — stale Action 215 result delivered after Action 216 was issued

After PC Engineer 3 issued Action 216, ChatGPT received Action 215 again instead of the new action result. The Director had to surface the stale duplicate manually. Classification: HUMAN-INVOLVED AUTONOMY INCIDENT. Root cause remains unresolved pending state/result/browser-event evidence; do not assume backend re-execution.


## AUDIT — PC Engineer 3 operations 215–219

- 215 proved Action 214 itself completed successfully; the delayed self-kill interrupted relay state after completion, so 214 was a flawed lifecycle-test design rather than a filesystem-permission failure.
- 216 was issued but never reached the Windows backend.
- 217 proved 216 had no state entry/result file and logged the stale-215 human-intervention incident.
- 218 exposed overlapping delivery telemetry: an older packet could still be sending while a newer packet entered delivery.
- 219 found zero new content-script starts in the incident window but repeated Port reconnects, and showed normal result delivery plus same-packet draft recovery running concurrently.

Root cause: `recoverExistingRelayDraft()` can adopt a composer draft for packet X while X is already present in the in-memory `inflight` set under normal `injectConfirmed()` delivery. Because the active-operation guard only rejects a *different* packet ID, two send owners can race for the same packet. Corrective invariant: draft recovery must defer while `inflight.has(draft.id)` and may adopt the draft only after normal delivery relinquishes ownership.


## AUDIT — PC Engineer 3 operations 220–224

- 220 fixed the confirmed delivery-v5 ownership race by preventing draft recovery from adopting the same packet while normal delivery remains in `inflight`; runtime identity advanced to `v11-scroll-v5-delivery-v6`; tests passed and commit `f1e4acc7` was pushed.
- 221 staged delivery-v6 into the live relay, rebuilt persistent XPI 0.3.15, and confirmed the active Firefox content script was still delivery-v5, establishing a clean activation boundary.
- 222 extracted the staged/live proof and confirmed the old runtime remained active.
- 223 recovered the historical fact that Task Scheduler had previously provided a successful post-result Firefox activation boundary.
- 224 narrowed historical evidence further but did not recover the exact helper payload.

Current gate: recover/reconstruct the proven Task Scheduler activation helper, activate delivery-v6 without user interaction, and require fresh `content_script_started` telemetry before lifecycle testing continues.


## AUDIT — PC Engineer 3 operations 225–229

- 225 wrote the 220–224 audit and confirmed Task Scheduler as the proven post-result ownership boundary for Firefox lifecycle work.
- 226 narrowed activation discovery to executable/local artifacts.
- 227 recovered the historical 157–160 proof: scheduled activation, live temporary-extension Reload, ChatGPT tab selection/document reload, and fresh runtime telemetry.
- 228 confirmed the original helper script was no longer available as a clean reusable artifact.
- 229 reconstructed the proven activation sequence as a self-logging fail-closed Task Scheduler helper targeting the live `Client\Relay\extension` temporary extension.

Operation 230 verifies the reconstructed helper using fresh `content_script_started` telemetry before lifecycle testing resumes.


## AUDIT — PC Engineer 3 operations 230–234

- 230 verified the first reconstructed activation helper and rejected activation: helper failed and no fresh delivery-v6 content runtime appeared.
- 231 exposed a false-positive UIA target: conversation text containing the historical live-extension path was mistaken for the about:debugging card.
- 232 cleanly established `HELPER_GREEN=False`, `FRESH_DELIVERY_V6_START_COUNT=0`, and `RELAY_RELOAD_BUTTON_NOT_FOUND`; historical marker strings embedded in the false match were explicitly treated as untrustworthy.
- 233 scheduled a non-mutating about:debugging UI Automation structure probe.
- 234 verifier hit a transient output-file sharing race while the scheduled probe still owned the file; this was a verifier synchronization defect, not an extension/UIA verdict.


## AUDIT — PC Engineer 3 operations 235–239

- 235 synchronized on scheduled-task exit and proved the about:debugging structure probe GREEN.
- 236 showed Firefox accessibility includes browser chrome and background-tab content, so global text/Reload matching is unsafe.
- 237 added visibility, geometry, and Document-ancestor telemetry without mutating the extension.
- 238 identified the real visible `GPT Windows Relay` temporary-extension card as a `ControlType.ListItem` inside the `Debugging - Runtime / this-firefox` document, containing the exact live extension location and extension metadata.
- 239 established the safe activation ownership boundary: bind the exact visible relay ListItem first, then search only its descendants for the Reload button.


## P2 backend-only restart recovery — GREEN

Action 242 armed a Task Scheduler helper that was forbidden to kill the relay until browser telemetry recorded `relay_result_delivery_complete` for Action 242. The browser confirmed delivery at 2026-10-03T08:11:54Z. The helper then terminated listener PID 8472; the supervisor/watchdog restored listener PID 14312 approximately three seconds later. Action 243 subsequently reached the recovered backend through the still-loaded delivery-v6 Firefox extension. No content-script restart, extension reload, re-pair, re-arm, or user rescue occurred.

The helper's unauthenticated `/status` request returned HTTP 401; this is not a recovery failure because the port was live and the authenticated relay action path immediately succeeded with Action 243.


## AUDIT — PC Engineer 3 operations 240–244

- 240 scheduled structurally bound activation using the exact visible GPT Windows Relay temporary-extension ListItem and its sole descendant Reload button.
