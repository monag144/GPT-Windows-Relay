# Archived source fragment 3/3 — 2026-10-08T0752Z

- browser-delivery retries must never re-execute the Windows action;
- duplicate ChatGPT result posts are a reliability incident even when backend duplicate safety prevents duplicate command execution.

The delivery-v1 failure that motivated this rule caused replay spam until the Director manually disabled the Firefox extension. Do not remove these anti-spam guards without equivalent proof.


## Manual command interface rule

**Never give the Director/user manual PowerShell commands.**

Operator-facing command policy:
- prefer autonomous relay execution whenever possible;
- if human terminal interaction is truly unavoidable, provide ordinary terminal/CMD-compatible commands only;
- do not instruct the user to open or use PowerShell;
- do not present PowerShell snippets as the manual recovery path;
- PowerShell may still be used internally by the relay/automation when the user does not have to type or operate it directly.

This is a hard UX rule for the Windows relay project.


## Pre-injection ChatGPT idle invariant

Relay result text must **not** be inserted into the ChatGPT composer while the current ChatGPT assistant response is still active, interrupted, or waiting to complete.

Current delivery-v4 contract:
- before `setText(result)`, wait for ChatGPT to become idle;
- active generation/Stop controls count as busy;
- visible interrupted/waiting live status counts as busy;
- while busy, keep the relay result out of the composer;
- only after idle may the bridge inject result text;
- after injection, wait for an enabled Send control without burning retry budget;
- then click once and confirm acceptance using user-result-turn or stable composer-clear confirmation;
- on idle timeout, defer delivery rather than parking payload text in the composer.

This invariant was added after Action 179 visibly left a relay result in the composer while ChatGPT displayed `Connection interrupted. Waiting for the complete answer`, requiring manual intervention.


## Composer single-owner / relay-draft recovery invariant

The ChatGPT composer is a **single-owner relay resource**.

Current delivery-v5 contract:
- only one relay packet ID may own the operation/delivery pipeline at a time;
- if the composer already contains a relay-owned `[GPT_WINDOWS_RESULT]` draft, that draft takes priority over every newer relay action;
- newer relay actions must be deferred before backend execution while another relay draft is unresolved;
- on content-script startup, detect and adopt any pre-existing relay-result draft that survived a reload;
- if that draft is already visible as a user result, clear only the relay-owned draft and mark the packet attempted;
- otherwise wait for ChatGPT idle, submit the exact existing draft, confirm delivery, and only then release the operation lock;
- never overwrite one relay-result draft with another packet's result;
- browser/content-script reloads must not orphan relay-owned composer state.

This invariant was added after Action 181's result survived the V4 activation reload and remained parked in the composer while later Action 182 executed.

## Current execution state after P5 completion

- Stable browser runtime: `v11-scroll-v5-delivery-v8`.
- P0 scroll experimentation is intentionally **deferred** after the contained V6 regression/revert; do not treat the old V4 activation bullets as current work.
- P1 Windows HUD: complete/live-proven.
- P2 lifecycle: backend-only restart complete/live-proven; full Firefox and Windows/login restart remain blocked on obtaining/installing a Mozilla-signed persistent XPI.
- P3 clipboard/job-application foundations: complete/live-proven.
- P4 on-request screenshots: complete/live-proven, including real image return into ChatGPT and post-delivery managed-file deletion.
- P5 broader Windows interaction: complete/live-proven, including semantic UIA controls, Firefox browser-tab adapter, and fixed-allowlist workflow composition with fail-closed screenshot fallback.
- Native Python `command_lines` transport: end-to-end GREEN.

The next actionable product milestone is therefore the signed persistent Firefox extension gate for P2, not another scroll rewrite.


## DO NOT ATTEMPT — relay rendering failures observed 2026-10-03

Three consecutive GPT-to-Windows relay packets collapsed in the Android/ChatGPT UI because the canonical sandwich rendering contract was not followed exactly.

Do not repeat these patterns:

1. **DO NOT use a language-tagged fence** such as ```text, ```json, ```powershell, or any other fence metadata around a relay packet.
2. **DO NOT split header, packet, and footer across separate assistant/rendering segments.** The visible header, bare fenced packet, and visible footer must be emitted together as one assistant response.
3. **DO NOT rely on merely having prose before and after a packet if the fence itself is not bare.** The exact contract is required, not an approximation.

Known-good rendering contract:

- ordinary visible prose header;
- one **bare** Markdown fenced block with no language tag;
- inside the fence, only `[GPT_WINDOWS_ACTION]`, the JSON packet, and `[/GPT_WINDOWS_ACTION]`;
- ordinary visible prose footer after the fence;
- never end the assistant response immediately after the packet;
- command stdout ends exactly with `Reply to this with the sandwich technique`.

When a relay packet collapses, first inspect the assistant rendering shape against this contract before debugging the relay backend, parser, Firefox extension, or localhost transport.

## Relay packet size / completion invariant

Keep assistant-authored relay packets compact enough to complete rendering promptly. A correct bare-fence sandwich can still fail if the assistant message is so large that streaming stalls or the closing packet envelope never renders.

**DO NOT ATTEMPT:** giant inline scripts, full databases/profiles, or very large `command_b64` blobs in one relay response. Use bounded multi-step local writes or reuse existing files instead. `command_b64` is retained for quoting resilience, not bulk data transport through the chat UI.

## Delayed / out-of-order relay ingestion evidence

On 2026-10-03, packet `PCENG4-RELAY-035-bare-sandwich-proof` initially appeared to produce no result, but later executed successfully **after** packet 036 had already completed. Treat this as evidence that an apparently stranded packet can remain discoverable and execute later through scanner/recovery behavior.

Operational implications:
- Do not conclude "packet never executed" solely from lack of an immediate GPT_WINDOWS_RESULT.
- Preserve unique operation IDs and duplicate/replay guarantees because delayed discovery can occur.
- Before resending the same intended action under a new ID, prefer a harmless proof/read-only check or inspect saved results where practical.
- Rendering failures and scanner/recovery ordering are separate failure domains.

## Final-response-only relay rendering invariant

A compact, bare-fenced packet still collapsed when emitted through an intermediary/commentary update. The known-good packet was emitted through the final assistant response.

Therefore every GPT_WINDOWS_ACTION sandwich must be emitted wholly in **one final assistant response**. Do not place relay packets in commentary/progress/status updates, and do not split the sandwich across commentary and final surfaces.


## Sandwich contract enforcement added after 2026-10-03 folding incident

The consumer migration packet `PCENG5-CONSUMER-110-MIGRATE-002` folded after the assistant violated the canonical rendering contract by emitting the packet through commentary, using a language-tagged fence, and making the packet unnecessarily large.

Incident record:

- `docs/INCIDENT_2026-10-03_RELAY_PACKET_FOLDING_SANDWICH_VIOLATION.md`

The contract is now reinforced in product code, not left only to operator memory:

- every browser-visible `GPT_WINDOWS_RESULT.stdout` is automatically terminated with exactly `Reply to this with the sandwich technique`;
- the first GPT One-Click consumer mission automatically primes the receiving ChatGPT conversation with the complete sandwich contract;
- regression tests protect both behaviors.

Raw saved command output remains raw; the reminder is added to the browser-visible serialized result that is returned to ChatGPT.

