# Incident: OP042 corrected safe cutover exceeded acceptable user-visible latency

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
