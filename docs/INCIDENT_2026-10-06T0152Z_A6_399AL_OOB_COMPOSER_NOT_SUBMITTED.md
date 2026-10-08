# Incident — A6.399al out-of-band composer populated but not submitted — 2026-10-06T0152Z

**Class:** USER INTERVENTION / PLANE-D LIVE ACCEPTANCE FAILURE  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Operation:** `PCENG-A6.399al-plane-d-oob-b64-live-retest`  
**Recovery incident:** `RECOVERY-A6.399AL-OOB-B64`

## Observation

A6.399al scheduled an independent Firefox semantic-UIA child after the ordinary relay result had completed. The child used the new base64-safe prompt transport added after A6.399ai.

The complete recovery prompt subsequently appeared in the ChatGPT composer intact, including the incident ID and bounded `[GPT_RELAY_RECOVERY_ADVICE]` contract. However, it was **not submitted automatically**. At 2026-10-05 18:52 PDT the Director intervened and pressed Enter, causing the already-populated recovery prompt to become the next ChatGPT user turn.

## Classification

This is a new user intervention and a failed zero-touch Plane-D acceptance.

It also proves a useful partial success: A6.399ai's PowerShell→Python argv corruption is fixed. The base64-safe path preserved the complete natural-language prompt across the process boundary and the semantic UIA path found and populated the intended ChatGPT composer.

The remaining failure is at the **composer submission / positive send confirmation** stage, not prompt serialization.

## Safety / evidence rule

Do not infer the exact submit failure mechanism from the user's Enter intervention alone. Before changing Firefox state, preserve and inspect:

`%LOCALAPPDATA%\GPTWindowsRelay\plane-d-oob-b64-send.json`

The adapter must distinguish at minimum:

1. composer found;
2. exact text populated and read back;
3. submit control or Enter semantic action attempted;
4. user turn positively observed after submission;
5. timeout/failure reason.

A populated composer is never equivalent to a submitted recovery request.

## Required repair contract

- Semantic composer insertion must positively verify exact text before submission.
- Submission must have a bounded primary action and a bounded fallback suitable for the identified ChatGPT composer.
- Success requires positive evidence that the prompt left the composer / became a user turn; invocation alone is insufficient.
- Failure to confirm submission must transition the durable recovery obligation to `OOB_FAILED` or `RECOVERY STALLED` with the exact reason and deadline.
- The independent recovery path must not require the Director to press Enter.
- The production recovery supervisor remains responsible for durable incident/phase/deadline state; a detached harness result must not be allowed to disappear behind a generic READY state.

## Acceptance status

- Base64-safe out-of-band prompt transport: **LIVE PARTIAL PASS**.
- Semantic composer discovery/insertion: **LIVE PASS**.
- Zero-touch semantic submission: **FAIL**.
- Independent GPT response readback: **NOT YET PROVEN** because the prompt required user submission.
- Broken-primary-transport recovery: **NOT YET PROVEN**.

Stable promotion remains blocked.


## Preserved A6.399al child evidence — 2026-10-06T0210Z

A6.399aq read the original child record without mutation. The worker exited 1 with `RuntimeError: FIREFOX_CHATGPT_SEND_BUTTON_COUNT_0`. This proves A6.399al did not falsely report a Send-button invocation: the text was inserted and read back, but ChatGPT never exposed a semantic Send control after UIA ValuePattern mutation. The Director's later manual Enter submitted the existing composer value.

Repair direction: architecture-approved guarded clipboard paste to trigger the actual UI input path; retry semantic Send; only if still absent use focused Enter on the positively identified composer; require bounded composer-clear confirmation. Production `browser_manager.py` also must use the already-added base64 CLI boundary rather than raw `--prompt-text`.
