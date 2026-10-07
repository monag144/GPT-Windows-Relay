# Incident — PCE7.408 stuck at STARTING after live Firefox cutover

Timestamp: 2026-10-06T03:55Z  
Operation: `PCENG-PCE7.408-live-firefox-cutover-and-rebind`  
Branch: `consumer/r29-firefox-offline-tray`  
Status: **OPEN — live acceptance failed**

## User-visible evidence

The operator reported the relay locked on **STARTING for 425 seconds** and supplied a screenshot. The screenshot shows the current `PC Engineering 7` ChatGPT tab and the relay HUD with:

- `STARTING`
- `Relay ONLINE • ARMED • pending 0`
- `Firefox IDLE • action_received • 417s`
- `STARTING • extension posted action to Windows relay • 417s`
- `LAST PCENG-PCE7.408-live-firefox-cutover-and-rebind / OK`

The PCE7.408 action sandwich remained visible in the conversation, but no `[GPT_WINDOWS_RESULT]` for 408 had been delivered back into the chat after more than the deadman interval.

## What this proves

This is not the same failure shape as A6.400.

The screenshot is evidence that PCE7.408 was detected/posted to the Windows relay and that the backend/HUD has a terminal-looking `OK` entry for that exact operation while the Firefox side is idle and the UI state remains STARTING. The safest current interpretation is:

1. the Windows operation likely completed and its result is durable in the backend;
2. the extension reload/page refresh intentionally crossed the browser-request lifetime boundary;
3. the newly loaded/remounted browser integration did **not** rediscover/replay/deliver the exact 408 result within 425 seconds;
4. therefore the live cutover/rebind acceptance **failed**, even if backend execution itself succeeded.

Do not call 408 successful until backend result state, saved result, and exact visible-user-turn state are independently read back.

## Why this matters

PCE7.407 staged the strengthened durable-recovery code and the late-packet cursor after V8 syntax validation plus contract tests. PCE7.408 was specifically designed to prove that a content-script/add-on remount could recover its own severed result through backend exact-once replay. The screenshot shows that the result-delivery/rebind redundancy still has a live hole.

The existing per-tab recovery obligation is stored in `sessionStorage` by the content script only after that content script has observed a packet. Reloading the add-on can destroy the original content-script execution context before the replacement has established or restored the obligation. Recovery must therefore have a second owner outside the disposable content-script instance (background/service worker, backend/supervisor, or independently reconstructable durable cursor) and must actively reconcile backend terminal results with visible ChatGPT user-result turns.

## Immediate next forensic order

1. Read backend processed/result-file state for PCE7.408 without re-executing it.
2. Read browser event telemetry across the reload boundary, including content-script start, reconnect, recovery-obligation restore, packet rediscovery, duplicate/exact-once response, and delivery events.
3. Verify the loaded add-on/content version after the cutover.
4. Determine whether `sessionStorage` recovery state survived and whether the service-worker operation cursor suppressed or admitted 408.
5. Repair the post-reload reconciliation path so a backend-terminal result cannot remain stranded while the HUD is STARTING.
6. Re-run the cutover proof only with a new unique operation id after the exact-once state of 408 is known.

No stable promotion is authorized.

## Manual reload escalation — 2026-10-06T0423Z

A second operator screenshot after an explicit manual `reload-addon` plus refresh of the `PC Engineering 7` tab still showed the same stranded PCE7.408 state at approximately **2133 seconds**:

- `STARTING`
- `Relay ONLINE • ARMED • pending 0`
- `Firefox IDLE • action_received • 2133s`
- `LAST PCENG-PCE7.408-live-firefox-cutover-and-rebind / OK`

The ChatGPT page was visibly reloading/waiting for `chatgpt.com`, but the relay HUD did not transition away from the old 408 STARTING state and PCE7.409 had not been recovered.

This rules out a one-off missed first reload as sufficient explanation. Containment decision: restore only the two live Firefox extension files from the exact pre-cutover backup created by PCE7.407 at `C:\\Users\\<LOCAL_USER>\\Downloads\\Dev\\GPT\\Client\\Relay\\rollback\\PCE7.407-20261006T034645Z`, then reload the add-on and current ChatGPT tab. Do **not** revert GitHub history and do **not** delete backend exact-once/result state. PCE7.409 is read-only if it is recovered after rollback.

## Adapter recovery failures during manual containment — 2026-10-06T0429Z

The operator supplied the exact CMD transcript:

- first `reload-addon --addon-name "GPT Windows Relay"` succeeded against Firefox PID 6332 and exactly one existing add-on card;
- the immediately following `refresh-tab --contains "PC Engineering 7"` failed with `FIREFOX_CHROME_RELOAD_BUTTON_COUNT_0`;
- the two PCE7.407 rollback files then copied successfully into the live extension directory;
- the following `reload-addon` failed with `FIREFOX_ADDON_CARD_COUNT_0`.

Therefore the rollback file copy itself succeeded, but the rolled-back files were **not yet activated**. Firefox's temporary add-on registration/card disappeared or became unavailable between adapter calls, and the adapter's browser-chrome reload-button assumption also failed against the current Firefox UI. Recovery must use the existing `ensure-addon` branch to reinstall the temporary add-on from the live `manifest.json`, then refresh/reload the ChatGPT document by a path that does not depend on a missing `reload-button` AutomationId.

