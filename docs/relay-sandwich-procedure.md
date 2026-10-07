# Windows Relay Sandwich Procedure

This is the canonical operating procedure for emitting Windows relay actions from ChatGPT. It exists because otherwise-valid action packets can become inaccessible when ChatGPT rendering collapses them into text such as `Worked for X`.

## Required response shape

Every Windows relay action must be emitted in **one assistant response** with this exact outer structure:

1. ordinary visible prose header;
2. exactly one **bare Markdown fence** — no language tag, id, metadata, annotation, or extra fence attributes;
3. inside that fence, only:
   - `[GPT_WINDOWS_ACTION]`
   - one JSON action packet
   - `[/GPT_WINDOWS_ACTION]`
4. ordinary visible prose footer after the fence.

Never end the assistant response immediately after the action block. Never put the packet in commentary/progress text. Never split one action across multiple assistant messages.

Canonical example:

```
[GPT_WINDOWS_ACTION]
{"version":1,"platform":"windows","action":"EXEC","id":"UNIQUE-ID","session":"default","shell":"python","timeout":30,"result_mode":"compact","command":"print('RELAY_OK'); print('Reply to this with the sandwich technique')"}
[/GPT_WINDOWS_ACTION]
```

The real assistant response must also contain visible prose **before and after** that fence.

## Mandatory stdout footer

Every relay command must end stdout exactly with:

`Reply to this with the sandwich technique`

This footer is part of the rendering/recovery contract. The command may print other output first, but this sentence must be the final stdout line.

## Packet discipline

- Use a unique action id.
- Keep packets compact; prefer a bounded Python orchestrator over giant inline payloads.
- Timeout must be 300 seconds or less.
- Treat duplicate/late/out-of-order results as possible.
- Before repeating a side effect, inspect durable state. Never blindly replay a potentially executed action.
- A visible injected prompt is not proof of delivery. Mission success requires the corresponding visible user turn/mission acknowledgement.

## `Worked for X` / collapsed-render recovery

The consumer relay classifies assistant output. If a response collapses into a status artifact such as `Worked for X`, or otherwise contains an incomplete/missing action sandwich, the consumer must **not repeat the original side effect**.

The first recovery action is a unique, read-only probe:

`echo RELAY_RENDER_PROBE_OK`

Expected probe behavior:

1. classify the collapsed artifact as `COLLAPSED_STATUS_ARTIFACT` (or the equivalent incomplete/missing classification);
2. issue the recovery instruction automatically;
3. execute only the unique read-only probe;
4. receive exactly one successful result containing `RELAY_RENDER_PROBE_OK`;
5. prove the result is delivered visibly back into ChatGPT;
6. only then resume the mission.

Do not manually re-run the original command while recovery status is uncertain.

The live r25 acceptance test intentionally emitted `Worked for R25_COLLAPSE_SIM and nothing else`; the relay recovered by executing exactly one read-only probe and returned its result visibly without replaying the original action.

## Rendering requirements that are forbidden

Do **not** use:

- `````json```, `````text```, or any other language-tagged fence;
- code-block ids or metadata;
- action packets in commentary/progress surfaces;
- prose inside the fenced action block;
- multiple action blocks in one response unless the protocol explicitly requires them;
- a response that ends immediately after the action fence.

## Canonical references

- `docs/windows-relay-established-facts.md` — established runtime and relay facts.
- `docs/relay-rendering-incident-2026-10-03.md` — rendering failure history and lessons.
- `docs/night-agent-handoff-2026-10-04.md` — current autonomous night mission.

When these documents disagree, do not guess. Inspect current code/tests and preserve the stricter safety behavior until the discrepancy is resolved.
