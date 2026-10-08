# Archived source fragment 1/2 — 2026-10-08T0752Z

# Overnight Relay Hardening Mission — 2026-10-04 — 2026-10-08T0745Z

## Incident: cross-device ChatGPT conversation desynchronization

Observed failure mode: the phone and Windows/Firefox ChatGPT clients were not showing the same current conversation state. Relay commands and follow-up diagnostics appeared available from the assistant side, but the PC-side browser monitored by the relay did not receive the new turn in time. This produced repeated apparent relay stalls and required the user to physically return to the computer and investigate.

Classification: **unnecessary human intervention / autonomy incident**.

Important distinction: this incident does **not** by itself prove a Windows relay backend failure. The relay already had recent evidence of a healthy canonical dev backend, active Firefox telemetry, and a live HUD. Cross-device conversation sync is now a first-class dependency that the relay must detect and route around rather than silently waiting forever.

### Required design rule

A relay mission must not depend on ChatGPT account/device synchronization as its only transport guarantee. The Windows browser participating in the relay is authoritative for execution. A locally persisted mission must remain recoverable even if a phone, another browser, or another ChatGPT client is stale.

## Items that must not be lost from the immediately preceding work

The following work was requested immediately before this incident and is now an explicit mission backlog:

1. Capture a live Windows screenshot showing the HUD and return the managed PNG to ChatGPT as visual proof.
2. Produce photo/screenshot proof of the complete consumer path:
   - obtain/update from GitHub;
   - launch **GO**;
   - run **Check for update**;
   - launch the user's chosen supported browser;
   - load a test prompt;
   - push the prompt into ChatGPT;
   - observe ChatGPT generate a relay action;
   - execute the Windows action;
   - return the result into ChatGPT;
   - preserve evidence for every important stage.
3. Add a consumer prompt harness that automatically appends the relay generation contract to every mission submitted through GO. The user writes the task naturally; the harness supplies the relay protocol instructions.
4. The appended contract must be machine-readable by ChatGPT and include a valid example relay JSON packet plus the sandwich rendering rules.
5. Add a validator/recovery harness so malformed or collapsed relay output does not require the user to diagnose it.
6. Detect the known UI symptom where an operation collapses into a status artifact such as **“Worked for X”** instead of exposing a usable relay packet.
7. When collapse/stall is detected:
   - report the condition back to ChatGPT in a compact recovery prompt;
   - request a minimal read-only sandwich probe;
   - verify the probe result;
   - if successful, record/lock the proven rendering method for the remainder of the session;
   - continue the original mission without requiring operator rescue.
8. Preserve the proven canonical rendering contract documented in `windows-relay-established-facts.md` and `relay-rendering-incident-2026-10-03.md`:
   - visible prose header;
   - one truly bare Markdown fence;
   - only `[GPT_WINDOWS_ACTION]`, JSON, and `[/GPT_WINDOWS_ACTION]` inside the fence;
   - visible prose footer;
   - entire sandwich in one final assistant response;
   - no language tag, fence metadata, commentary-surface packet, or giant packet;
   - stdout ends exactly `Reply to this with the sandwich technique`.

## Consumer prompt harness contract

Every GO-submitted user mission should be converted to a structured prompt envelope before injection into ChatGPT. The exact representation may evolve, but it must carry at least:

```json
{
  "relay_harness_version": 1,
  "mission_id": "<durable unique mission id>",
  "user_request": "<verbatim or clearly delimited user mission>",
  "relay_contract": {
    "platform": "windows",
    "action": "EXEC",
    "rendering": "visible header -> bare fenced GPT_WINDOWS_ACTION packet -> visible footer, all in one final assistant response",
    "stdout_footer": "Reply to this with the sandwich technique",
    "compact_packets": true,
    "example": {
      "version": 1,
      "platform": "windows",
      "action": "EXEC",
      "id": "EXAMPLE-UNIQUE-ID",
      "session": "default",
      "shell": "cmd",
      "command": "echo example&&echo Reply to this with the sandwich technique",
      "timeout": 15,
      "result_mode": "compact"
    }
  }
}
```

ChatGPT remains responsible for reasoning from the user's natural-language task and generating the appropriate command. The harness exists to make the protocol/routing rules impossible to forget.

## Required redundancy stack

### 1. Durable local mission journal

Persist mission ID, raw user request, harnessed prompt, browser target, timestamps, and phase transitions before browser injection. A mission must survive browser/tab/client desynchronization and process restart.

Suggested phases:

- CREATED
- BROWSER_SELECTED
- BROWSER_LAUNCHED
- CHAT_READY
- PROMPT_INJECTED
- USER_TURN_CONFIRMED
- ASSISTANT_GENERATION_STARTED
- ACTION_PACKET_SEEN
- ACTION_ACCEPTED
- ACTION_EXECUTING
- RESULT_READY
- RESULT_INJECTED
- RESULT_TURN_CONFIRMED
- COMPLETE
- RECOVERY_REQUIRED
- FAILED_TERMINAL

### 2. Two-sided acknowledgement

Do not treat text injection as success. Require confirmation that the user turn containing the mission ID is actually visible in the PC browser conversation before waiting for assistant output.

### 3. Cross-device/client divergence detection

If the local GO mission is pending but the monitored PC conversation does not contain the mission ID after a bounded timeout, classify it as a conversation/client divergence event rather than a backend timeout.

Recovery should prefer, in order:

1. reacquire the target ChatGPT tab;
2. refresh/reopen the authoritative PC conversation when safe;
3. re-inject the **same durable mission ID** only after proving the prior user turn is absent;
4. never create a duplicate side-effecting action merely because another client was stale.

### 4. Browser watchdog

Track browser process, extension/content-script health, target tab identity, current conversation URL/identity, last scanner event, and last successful user/assistant turn acknowledgement.

### 5. Rendering validator

The browser scanner should explicitly classify assistant output as:

- VALID_SANDWICH
- INCOMPLETE_SANDWICH
- METADATA_FENCE
- LANGUAGE_TAGGED_FENCE
- COMMENTARY_SURFACE_OR_NONFINAL
- OVERSIZED_OR_STALLED
- COLLAPSED_STATUS_ARTIFACT
- NO_ACTION_PACKET
- VALID_NONRELAY_RESPONSE

Only `VALID_SANDWICH` may proceed to backend execution.

### 6. “Worked for X” / collapsed artifact detector

Detect known collapsed status UI text or DOM structure associated with inaccessible assistant tool/status artifacts. When detected during a relay mission, emit telemetry and initiate the minimal recovery probe rather than waiting indefinitely.

### 7. Minimal recovery probe

Recovery probe must be compact, read-only, uniquely identified, and use the canonical sandwich contract. It should prove:

- current assistant rendering path;
- scanner visibility;
- browser-to-backend transport;
- result delivery back to ChatGPT.

A successful probe should mark the current rendering/session method as proven and allow the original durable mission to resume.

### 8. Out-of-order / delayed packet handling

The October 3 incident showed that a packet can appear to fail and then execute later. Maintain attempted/seen packet IDs and do not assume absence means permanent rejection. Reconcile late arrivals against the local mission journal and duplicate-safety rules.

### 9. Backend duplicate safety

Retain durable operation IDs, saved-result replay, duplicate-inflight suppression, interrupted-restart handling, and ID collision refusal. Browser recovery must never trade reliability for duplicate side effects.

### 10. Result-delivery watchdog

After backend completion, require confirmation of a ChatGPT user turn containing the result packet ID. Composer injection or Send-button click alone is not delivery proof.

### 11. Screenshot/attachment watchdog

For screenshot missions, separately prove:

- PNG created;
- PNG passes managed screenshot validation;
- attachment metadata is present in the relay result;
- browser retrieves/attaches the managed image;
- the image is visible in the ChatGPT conversation.

If any stage fails, log the exact stage rather than reporting generic success.

### 12. Startup self-test

GO should perform a lightweight startup preflight:

- package/update state;
