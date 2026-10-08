# Incident — A6.399al recovery advice visible but unconsumed — 2026-10-06T0200Z

**Class:** USER INTERVENTION / RECOVERY OWNERSHIP FAILURE  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Recovery incident:** `RECOVERY-A6.399AL-OOB-B64`

## Observation

After the Director manually submitted the A6.399al out-of-band recovery prompt, GPT returned the requested bounded `[GPT_RELAY_RECOVERY_ADVICE]` envelope. Nothing automatically consumed the advice or advanced recovery. The Director intervened again at approximately 2026-10-05 19:00 PDT.

## Forensic cause

The returned envelope itself is valid for the recovery contract; it is intentionally **not** a `[GPT_WINDOWS_ACTION]` packet.

The production consumer supervisor already owns the correct parser: `_extract_gpt_recovery_advice()` in `consumer/recovery_supervisor.py`, called by `_consult_gpt_out_of_band()`. It only accepts the matching incident ID and whitelisted repair names.

A6.399al was an ad-hoc development live harness. Its detached child sent the prompt and then exited. It did not register a production supervisor wait/readback obligation for `RECOVERY-A6.399AL-OOB-B64`. Consequently no process owned the returned valid advice.

Separately, `windows-relay/extension/content.js` currently classifies any assistant response without a Windows action sandwich as `NO_ACTION_PACKET`. It does not distinguish a valid or malformed recovery-advice envelope. That makes the secondary redundancy path blind to an orphaned recovery response.

## User-visible contract violation

A recovery transaction must not silently stop after GPT answers. The system needs a second observer independent of the primary supervisor:

- recognize `GPT_RELAY_RECOVERY_ADVICE` distinctly from ordinary no-action conversation;
- surface the incident ID and valid/invalid envelope status in lifecycle/HUD telemetry;
- production supervisor owns execution and must positively claim the matching incident;
- if advice for the expected incident is malformed, the supervisor gets one bounded independent coaching retry telling GPT the exact accepted schema;
- if valid advice remains unclaimed, surface it as recovery work still pending instead of READY;
- never reinterpret recovery advice itself as arbitrary executable shell/code.

## Status

This is user intervention **U-008**.

Plane D remains blocked. A6.399al now proves:
- base64 prompt serialization: LIVE PASS;
- composer population: LIVE PASS;
- automatic submit: FAIL;
- GPT bounded advice generation: PASS after Director submitted;
- automatic advice ownership/readback: FAIL in the ad-hoc live harness.

Stable promotion remains blocked.
