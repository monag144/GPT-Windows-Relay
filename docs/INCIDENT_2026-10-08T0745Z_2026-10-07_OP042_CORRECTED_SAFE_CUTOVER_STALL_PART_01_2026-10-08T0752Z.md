# Archived source fragment 1/2 — 2026-10-08T0752Z

# Incident: OP042 corrected safe cutover exceeded acceptable user-visible latency — 2026-10-08T0745Z

**Date:** 2026-10-07 UTC / 2026-10-06 local  
**Status:** Open / active investigation  
**Severity:** High for end-user operability  
**Affected operation:** `PCE8BOOT-OP042-arm-corrected-safe-cutover`  
**Related incident:** `docs/INCIDENT_2026-10-07_OP032_POST_DELIVERY_CUTOVER_STALL.md`

## Summary

The redesigned "safe" live cutover path introduced after the OP032 incident again failed the end-user experience requirement.

OP042 armed successfully and used the corrected pre-cutover handoff gate, `relay_result_send_accepted`, with a 15-second grace period. More than ten minutes later, the system was still visibly stuck in a cutover/delivery state instead of completing, rolling back, or reporting a bounded failure.

This is unacceptable for an end-user cutover path even if the underlying relay remains technically reachable.

## User-visible evidence

At approximately 22:37 local time, the user supplied screenshots showing:

- the relay HUD still reporting **DELIVERING**;
- packet: `PCE8BOOT-OP042-arm-corrected-safe-cutover`;
- relay status: **ONLINE / ARMED / pending 0**;
- Firefox status showing the previous action/result state roughly **697 seconds** old;
- the ChatGPT conversation still open in Firefox;
- an `about:debugging / this-firefox` tab still present;
- a visible **GPT Windows Relay** supervisor console on the desktop;
- taskbar previews showing two relay-related console windows, labeled **GPT One-Click Go Relay** and **GPT Windows Relay**.

The screenshots demonstrate that the operator was left staring at relay/debugging/supervisor UI for many minutes with no bounded completion or recovery message.

## Why this is a separate incident from OP032

OP032 failed because its helper waited for `relay_result_delivery_complete`, an event not emitted by the active Firefox delivery path.

That design defect was corrected before OP042:

- the helper now gates on `relay_result_send_accepted`;
- OP041 staged the exact committed cutover helper from canonical main;
- 388 live Windows tests passed;
- all browser JavaScript files passed syntax checks;
- critical live files matched canonical;
- OP042 preflight confirmed the backend was healthy and the intended ChatGPT/debugging tabs were present.

Therefore this stall occurs **after** the previously identified OP032 delivery-gate defect was corrected and must not be attributed to the old missing-event bug without new evidence.

## Impact

- More than ten minutes of visible cutover latency.
- No success wake-up.
- No failure wake-up.
- No bounded automatic rollback visible to the user.
- Debugging/supervisor UI remains exposed during the failure.
- The newer/cool HUD cutover path is not operationally acceptable yet.
- The cutover helper cannot currently be considered safe for routine or end-user use.

## Required design constraint

The cutover path must become **time-bounded and fail-closed**.

For the end-user path:

- every phase must have an explicit short timeout;
- total cutover time must be bounded;
- if the bound is exceeded, rollback must begin automatically;
- rollback must also have a bound;
- the helper must always write a final report and terminate its scheduled task/process;
- the UI must return to the intended ChatGPT conversation;
- visible debugging or supervisor consoles must not be left behind;
- the HUD must show either success or a clear bounded failure/recovery state, never indefinite **DELIVERING**.

A ten-minute wait is not an acceptable fallback behavior.

## Required forensic checks before another cutover attempt

Do not re-arm the cutover until a read-only inspection determines where OP042 stopped.

Inspect:

- `%LOCALAPPDATA%\GPTWindowsRelay\PCE8BOOT-OP042-arm-corrected-safe-cutover-cutover.jsonl`
- `%LOCALAPPDATA%\GPTWindowsRelay\PCE8BOOT-OP042-arm-corrected-safe-cutover-cutover-report.json`
- scheduled task `GPTWindowsRelay-PCE8-OP042-SafeCutover`
- helper process tree
- backend listener and supervisor ancestry
- watchdog/HUD process tree
- recent browser events around OP042
- active Firefox tabs and currently loaded temporary add-on identity
- whether the extension reload occurred
- whether the backend restart occurred
- whether the helper entered rollback and, if so, where rollback stopped

## Recovery policy

A new live cutover must not be attempted until the OP042 helper state is reconciled.

If the helper/task is still running, terminate it only after collecting its log/report and process state. If the live tree is mixed or browser/runtime state is uncertain, perform targeted recovery from the fresh OP041 rollback snapshot rather than blindly re-running the cutover.

## Root cause

**Not yet determined.**

The important confirmed fact is operational: the corrected cutover path remained user-visible and unresolved for more than ten minutes. The next step is forensic localization, not another cutover attempt.


## Forensic update — OP043 localization

OP043 localized the OP042 stall sequence precisely.

The helper log shows the corrected pre-cutover gate worked and the cutover itself progressed through the intended active phases:

- `helper_started`
- `send_accepted_observed`
- `backend_restarted`
- `hud_rotated`
- `addon_reloaded` (Firefox PID 18160)
- `chat_refreshed`
- failure after the v17 proof gate: `RuntimeError: v17 owner runtime not observed`
- rollback began and `snapshot_restored` was logged

No final cutover report was written. The scheduled task still reported **Running**, and the helper process tree remained alive, proving the rollback/finalization path did not terminate normally.

OP043 also exposed an additional operational regression: two visible relay supervisor stacks were present concurrently. One PowerShell `run.ps1` window was titled **GPT Windows Relay** and another was titled **GPT One-Click Go Relay**. Corresponding backend Python processes were present under both supervisor trees. This matches the user-supplied screenshot showing two relay console previews and explains why visible relay/supervisor UI remained after rollback.

### Updated failure chain

1. The corrected Firefox gate succeeded.
2. Backend/HUD rotation succeeded.
3. The existing temporary Firefox add-on was reloaded.
4. The ChatGPT tab was refreshed.
5. The helper failed to observe the expected v17 + owner-v1 `content_script_started` telemetry within its 45-second proof window.
6. Rollback restored the OP041 snapshot.
7. Rollback/finalization then failed to terminate cleanly: no final report, scheduled task remained running, helper remained alive, and duplicate visible supervisor/backend stacks remained.

### Operational conclusion

This is not a delivery-gate failure. The dominant defects are now:

- the post-reload v17 runtime proof mechanism did not observe the expected runtime despite the add-on reload and ChatGPT refresh;
- rollback/finalization is not hard-bounded and can hang after restoring files;
- supervisor restart logic can create a second visible relay stack instead of converging to one hidden canonical stack.

The next recovery step must first identify which backend stack owns the live listener and then normalize to one supervisor/listener before any further cutover work.


## Recovery update — OP044/OP045

OP044 established that the two visible relay consoles are not duplicate owners of the same endpoint. They are two intentional relay stacks with separate state/config roots and ports:

- **GPT Windows Relay** — main relay on 127.0.0.1:8766 using the GPTWindowsRelay state/config root.
- **GPT One-Click Go Relay** — consumer/One-Click relay on 127.0.0.1:8767 using the GPTWindowsRelayConsumer state/config root.

The main 8766 listener was owned by the GPT Windows Relay stack. The consumer stack was therefore preserved rather than killed as a duplicate.

OP044 also confirmed that neither state root contained any v17/owner runtime-start telemetry. The main Firefox state root still showed v16 as the latest observed content-script runtime, while the consumer state root contained older v11 lineage telemetry.

OP045 then completed targeted recovery:

- OP042 scheduled task removed;
- no OP042 helper processes remain;
- OP041 rollback snapshot verified exact: missing=0, mismatch=0, unexpected=0;
- main relay healthy on 8766 and armed;
- consumer/One-Click relay preserved on 8767;
- Firefox healthy with the PC Engineering 8 conversation selected;
- no v17 reattempt occurred.

