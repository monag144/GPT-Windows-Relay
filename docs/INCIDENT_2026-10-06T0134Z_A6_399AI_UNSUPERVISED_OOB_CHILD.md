# Incident — 2026-10-06T0134Z — A6.399ai detached Plane-D child was not supervised

**Class:** RECOVERY SUPERVISION / USER INTERVENTION  
**Observed at:** 2026-10-06T0134Z (2026-10-05 18:34 PDT)  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Operation:** `PCENG-A6.399ai-plane-d-oob-prompt-live-probe`

## User intervention U-006

A6.399ai successfully scheduled an independent process intended to insert the Plane-D recovery prompt after the relay action returned. The relay result reported `PLANE_D_OOB_PROMPT=SCHEDULED`, Firefox PID 19240, and an evidence path at `%LOCALAPPDATA%\GPTWindowsRelay\plane-d-oob-send.json`.

Approximately 166 seconds later, the Director intervened because no independent recovery prompt had appeared.

Screenshot evidence showed the HUD primary state as:
- `READY`;
- relay ONLINE / ARMED / pending 0;
- Firefox SEEN with last event `relay_result_delivery_complete`;
- `READY • result visibly delivered • 166s`;
- packet still A6.399ai.

The primary relay result really was visibly delivered. The defect is that the detached follow-on recovery task was outside the HUD/watchdog lifecycle, so successful scheduling was allowed to look like terminal mission success even though the promised recovery action had not been proven.

## Classification

This is not the earlier F-005 case where a different historical packet falsely owned READY. Here the A6.399ai relay result itself was delivered, but its scheduled recovery child became an untracked obligation.

Root cause of the child failure is pending inspection of `plane-d-oob-send.json`.

## Finding F-006 — recovery sub-operations require durable supervised state

Severity: RELEASE BLOCKER

A recovery operation that schedules, delegates, or detaches follow-on work must not be considered end-to-end complete merely because its parent relay action returned OK.

The independent supervisor/HUD must persist and expose:
- incident ID;
- recovery phase;
- child/delegated action;
- deadline;
- evidence/result path;
- last transition age;
- success/failure/timeout disposition.

A missing expected recovery transition must promote to RECOVERING/STALLED according to the recovery architecture without waiting for the Director to notice a stale READY display.

## Immediate next evidence

Read the detached-child evidence file through the now-working relay. Do not clear LocalAppData before capturing it.

After root cause is known, harden recovery supervision before resuming browser acceptance.

## Root cause captured — A6.399aj

A6.399aj read the preserved evidence file. The detached worker ran on schedule at `2026-10-05T18:31:30.8396357-07:00` and exited with code 2. No matching child process remained.

The adapter's argparse error ended with:

`firefox_adapter.py: error: unrecognized arguments: semantic recovery prompt received.} [/GPT_RELAY_RECOVERY_ADVICE]`

Therefore the immediate prompt-insertion failure was an unsafe PowerShell/native argv boundary: multi-word natural-language recovery text was not transported as a mechanically opaque argument.

Corrective implementation:
- Firefox adapter CLI gains a mutually exclusive `--prompt-b64` transport and strict base64 UTF-8 decode; raw `--prompt-text` remains supported for direct structured callers.
- Recovery supervisor persists the out-of-band incident before send, including incident ID, phase, operation, classification and deadline, and advances durable phases through prompt send, advice wait, advice received/failed, whitelisted repair and recovery/failure.
- This does not weaken F-006: the evidence file proved the failure was knowable within seconds, so a production recovery obligation must surface it without Director intervention.
