# Relay Rendering Incident — 2026-10-03

## Summary

Three consecutive GPT-to-Windows relay attempts collapsed in the Android/ChatGPT UI before the Windows relay could reliably consume them.

## Root cause

The canonical relay record already specified a strict rendering contract:

- visible ordinary prose header;
- one **bare** Markdown fenced block with **no language tag**;
- packet body only: `[GPT_WINDOWS_ACTION]`, JSON, `[/GPT_WINDOWS_ACTION]`;
- visible ordinary prose footer;
- never end immediately after the packet.

The failed attempts deviated from that contract. In particular, language-tagged fences such as ```text were used, and some responses distributed the sandwich components across different rendered assistant segments.

## DO NOT ATTEMPT

- Do not use ```text.
- Do not use ```json.
- Do not use any language identifier or metadata on the relay fence.
- Do not emit the header, packet, and footer as separate assistant/rendering segments.
- Do not treat prose-before/prose-after alone as sufficient if the fence is not bare.
- Do not debug the backend first when the UI symptom is a collapsed relay packet.

## Required recovery test

The next relay test must be a **minimal no-op/read-only command** rendered in one assistant response as:

visible header

```
[GPT_WINDOWS_ACTION]
{...}
[/GPT_WINDOWS_ACTION]
```

visible footer

The fence above is illustrative; the actual relay message must likewise use a bare fence.

## Existing source of truth

See `docs/windows-relay-established-facts.md`, section **Relay packet / rendering contract**.

The existing engineering log also already states:

> Keep the visible-header -> bare fenced [GPT_WINDOWS_ACTION] -> visible-footer sandwich format for relay commands.

and:

> Never intentionally add a language tag or metadata to the relay fence.

## Impact

No evidence indicates a backend/parser/Firefox regression from these three attempts. The failure occurred at the assistant/UI rendering layer before those subsystems should be blamed.

## Incident 4 — packet visible, no relay/system response

The fourth attempt rendered visibly, but no GPT_WINDOWS_RESULT/system relay response appeared. Inspection of the assistant output showed the Markdown fence was emitted with metadata: `\`\`\` id="gfndkz"` rather than a truly bare `\`\`\`` fence.

This is another violation of the established rendering contract. A relay fence is considered bare only when the opening fence contains exactly three backticks and nothing else — no language identifier, no id attribute, no metadata, no writing-block annotation.

### Human-intervention incident

The user had to notice and report that the packet rendered but produced no relay/system response. That manual diagnosis is an autonomy/human-intervention incident under the existing project policy. Do not normalize this rescue step as expected workflow.

### Updated DO NOT ATTEMPT

- Do not emit `\`\`\`text`.
- Do not emit `\`\`\`json`.
- Do not emit `\`\`\` id="..."` or any other fence attributes/metadata.
- Do not use writing-block/code-block metadata for relay packets.
- The opening and closing fences must each be exactly three backticks.

### Next test

Use a minimal read-only packet with the exact wrapper, in one assistant response: visible prose header, truly bare fenced packet, visible prose footer.

## Incident 5 — oversized relay packet stalled assistant output and never executed

A subsequent attempt used the correct visible-header -> bare-fence -> visible-footer structure, but embedded an extremely large `command_b64` payload directly in the assistant response.

Observed behavior:
- the assistant message remained in an unfinished/streaming state for roughly five minutes;
- the relay packet collapsed / never completed as a usable command;
- no `GPT_WINDOWS_RESULT` was returned;
- the user had to report the stalled state and lack of execution.

### Root cause / classification

The immediate failure was not the Windows backend. The assistant output itself was too large to reliably complete/render as one relay packet. Because the closing envelope/footer were not reliably completed, the browser bridge had no complete packet to execute.

This is both a **relay-rendering incident** and a **human-intervention incident**.

### DO NOT ATTEMPT — additional rule

- Do not embed giant scripts, full applicant databases, long JSON documents, or very large base64 blobs directly inside one chat relay packet.
- `command_b64` remains a valid transport fallback for quoting problems, but it is **not** a license to create enormous assistant messages.
- For large state writes, use small orchestration commands that create/update local files incrementally, reuse existing local/source files, or use direct connected-source writes where appropriate.
- Keep relay packets compact enough that the assistant response can complete promptly and the closing `[/GPT_WINDOWS_ACTION]` plus footer are guaranteed to render.

### Recovery direction

Persist the applicant profile in bounded steps: create the directory/file with a compact seed, then append/update sections in several short relay actions or generate it locally from already-available source files. Do not resend the giant payload.

## Incident 4 correction — packet 035 eventually executed out of order

New evidence arrived later as `GPT_WINDOWS_RESULT` for `PCENG4-RELAY-035-bare-sandwich-proof`:

- status: **OK**
- exit code: 0
- started/finished: 2026-10-03T20:42:50Z
- stdout: `BARE_SANDWICH_PROOF=OK` plus the required sandwich-technique footer line

This packet executed **after** packet 036 had already executed successfully at approximately 20:33Z. Therefore the previous characterization of packet 035 as simply "visible but unexecuted" was incomplete.

### Revised classification

- Packet 035 was eventually discoverable/executable by the browser bridge.
- The observed failure was **delayed and out-of-order packet ingestion/execution**, not proven permanent wrapper rejection.
- The user's manual report remains a valid human-intervention incident because normal autonomous progress stalled and required user observation.
- The earlier hypothesis that fence metadata alone prevented execution is **not proven** by the final evidence and must not be treated as established root cause.
- Continue using truly bare fences because that is still the canonical/proven rendering contract, but investigate scanner/recovery ordering separately from Markdown rendering.

## Incident 6 — bare fence collapsed when emitted from commentary/update surface

Packet `PCENG4-JOBAUTO-037-profile-state-audit` used a visually bare Markdown fence and a compact payload, yet the user reported that it collapsed and no usable relay result appeared.

### Differential diagnosis against the proven success

The important rendering difference was not packet size or fence syntax:

- Proven packet `PCENG4-RELAY-036-true-bare-fence-proof` was delivered as the **final assistant response** and executed successfully.
- Packet 037 was emitted inside an **intermediary/commentary update**, followed by a separate empty final response.
- This split means the header -> packet -> footer sandwich did not travel through the same final-response rendering path as the known-good proof.

### Revised rendering invariant

For GPT-to-Windows relay commands, the complete sandwich must be emitted in the **final assistant message**, not in commentary/progress/update messages.

**DO NOT ATTEMPT:**
- relay packets in commentary/update/status messages;
- relay packet in commentary plus a separate final response;
- splitting any part of header -> bare fence -> footer across assistant message surfaces/channels.

Use exactly one final assistant response containing visible header -> bare fenced GPT_WINDOWS_ACTION packet -> visible footer.

### Human-intervention classification

The user again had to identify/report the collapsed command. This is a human-intervention incident under the established autonomy policy.
