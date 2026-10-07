# Incident: OP032 post-delivery live cutover stalled on Firefox debugging screen

**Date:** 2026-10-07 UTC / 2026-10-06 local  
**Status:** Open / investigation required  
**Scope:** Windows relay live cutover, Firefox extension reload, result delivery  
**Affected operation:** `PCE8BOOT-OP032-arm-post-delivery-cutover`

## Summary

A staged live cutover from the running v16 browser bridge to the promoted v17 + whole-stop + conversation-owner runtime stalled after OP032 successfully armed the independent post-delivery helper.

The user observed the relay HUD/state remaining on **DELIVERING for more than ten minutes**. During the stall, Firefox was left on the **about:debugging / This Firefox developer add-on screen**. The expected automatic wake-up message from the cutover helper did not arrive.

This incident occurred after the OP032 result itself had returned successfully to ChatGPT, so the failure is downstream of OP032 packet execution and task registration.

## Pre-incident state

Canonical GitHub main had already been promoted to:

`332581d55266af6500357fbf3afedf0088bb9ed5`

OP030 staged the full promoted Windows relay tree into the live relay directory with a rollback snapshot and reported:

- 88 tracked Windows-relay files staged.
- 0 hash mismatches.
- 383 Windows tests passed.
- All five browser JavaScript files passed `node --check`.
- Critical live files matched canonical.
- No backend restart, Firefox reload, or HUD restart had yet occurred.

Rollback snapshot:

`%USERPROFILE%\Downloads\Dev\GPT\Client\Relay\backups\pce8-op030-20261006-215322`

OP031 then created and compile-checked the independent cutover helper:

`%LOCALAPPDATA%\GPTWindowsRelay\pce8-op031-cutover-helper.py`

The helper contract included:

- wait for OP032 `relay_result_delivery_complete`;
- backend rotation;
- watchdog/HUD replacement;
- Firefox temporary add-on ensure/reload;
- ChatGPT tab refresh;
- v17 + `owner-v1` runtime verification;
- canonical hash verification;
- HUD cardinality/health verification;
- rollback on failure;
- self-removal of the scheduled task.

OP031 completed with `COMPILE_RC=0`.

## Trigger

OP032 registered and started the scheduled cutover task:

`GPTWindowsRelay-PCE8-OP032-LiveCutover`

OP032 itself returned successfully with:

- `REGISTER_RC=0`
- task state `Running`
- `ARMED=True`
- `CUTOVER_WAITING_FOR_THIS_RESULT_DELIVERY=True`

The intended design was that the helper would remain idle until the browser emitted `relay_result_delivery_complete` for OP032, then perform the live cutover out of process.

## Observed failure

At approximately 2026-10-06 22:11 local time, more than ten minutes after OP032 completed, the user reported:

- relay state remained **DELIVERING**;
- Firefox was stuck on the **Firefox developer add-on / about:debugging screen**;
- no automatic cutover-complete or rollback wake-up message arrived.

The visible Firefox state strongly suggests the helper progressed at least as far as opening the debugging UI, but this is not yet sufficient to prove whether it stalled in:

1. temporary add-on detection;
2. add-on reload / ensure-addon UI automation;
3. ChatGPT tab refresh;
4. post-refresh v17 runtime detection;
5. result/wake-up delivery after the browser transition.

## Important constraints / prior evidence

This should **not** be conflated with the earlier OP027 packet rejection.

OP027 was rejected before execution because the decoded relay command exceeded the relay's `MAX_CMD=20000` contract. OP029 confirmed the exact validator limit. OP030-OP032 were split specifically to stay below that limit.

OP032 itself executed successfully; therefore this incident is a live cutover/helper-state failure, not a packet-size validation failure.

## Impact

- The live transition did not complete cleanly from the operator's perspective.
- The browser was left on a debugging/developer screen.
- The relay remained in a long-running delivery state.
- Automatic recovery/wake-up did not prove completion.
- The intended removal of physical/manual browser-interaction barriers is **not proven**.
- v17 + conversation-owner behavior must not be treated as live/verified until post-incident inspection confirms the actual runtime.
- The legacy HUD retirement outcome is unknown until process/hash inspection is performed.

## Required forensic checks before further mutation

Do not immediately re-run the cutover.

First inspect, read-only:

- `%LOCALAPPDATA%\GPTWindowsRelay\pce8-op032-cutover-report.json`
- `%LOCALAPPDATA%\GPTWindowsRelay\pce8-op032-cutover.log`
- current Task Scheduler state for `GPTWindowsRelay-PCE8-OP032-LiveCutover`
- current backend listener PID and process ancestry
- current watchdog and HUD process cardinality
- current live/canonical hashes
- recent browser events around:
  - `relay_result_delivery_complete`
  - `content_script_started`
  - browser disconnect/reconnect
  - approval/debugging events
- current Firefox tabs and selected tab
- current live content-script runtime identity

Determine whether rollback already ran before attempting any new live mutation.

## Success criteria for recovery

Recovery is complete only when all of the following are demonstrated with live evidence:

- exactly one healthy backend listener;
- exactly one intended watchdog/supervisor chain;
- exactly one canonical HUD process;
- Firefox returned from the debugging UI to the intended ChatGPT conversation;
- live content script reports the v17 whole-stop + owner-v1 runtime;
- live critical hashes match canonical;
- a **subsequent** relay operation is accepted by the new worker and proves current-conversation ownership;
- cross-conversation stale/default-session suppression is demonstrated live;
- no manual Firefox approval/reload interaction is required for the normal path.

## Root cause

**Not yet determined.**

The debugging-screen observation is evidence of the failure location, not a confirmed root cause. Do not close this incident until the helper report/log and live browser/process state are reconciled.
