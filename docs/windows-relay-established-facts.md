# GPT Windows Relay — Established Facts / Read This First

This is the canonical short-form knowledge base for the Windows↔ChatGPT Firefox relay.

**Before starting new relay debugging or forensics, read this file and the engineering log first.** Do not rediscover facts already proven here unless new evidence directly contradicts them.

Long-form chronology and proof live in:
- `docs/windows-relay-engineering-log-2026-10-01.md`

## Canonical project locations

- GitHub repository: `monag144/GPT-Windows-Relay`
- Active branch: `main`
- Canonical local clone: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\GPT-Termux-Relay`
- Active live relay tree: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay`
- Temporary Firefox manifest: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay\extension\manifest.json`
- Persistent-extension source: `...\Client\Relay\extension-persistent`
- Engineering log: `docs/windows-relay-engineering-log-2026-10-01.md`

GitHub is the canonical engineering/audit record. Confirmed findings, root causes, fixes, false leads worth remembering, and proof of validation should be logged there.

## Relay packet / rendering contract

Canonical procedure: `docs/relay-sandwich-procedure.md`.

Every Windows relay command shown in ChatGPT must use the **sandwich technique**:

1. ordinary visible prose header;
2. one bare Markdown fenced block with no language tag;
3. inside the fence, only:
   - `[GPT_WINDOWS_ACTION]`
   - the JSON packet
   - `[/GPT_WINDOWS_ACTION]`
4. ordinary visible prose footer after the fence.

Never end the response immediately after the relay block.

Every relay command stdout must end exactly:

`Reply to this with the sandwich technique`

This prevents the Android/ChatGPT rendering failure where relay commands can collapse into an inaccessible status artifact.

## Backend architecture

- Backend: `windows_relay.py`
- Bind address: `127.0.0.1:8766`
- Local token authentication
- Supervised recovery returns the backend ARMED
- Only explicit `platform:"windows"` + `action:"EXEC"` packets are accepted
- Supported shells: `powershell`, `pwsh`, `cmd`, `python`
- Native Python path executes with the relay Python runtime using UTF-8
- Timeout/process-tree handling is implemented
- Full raw results are persisted locally before browser previewing

### Result policy

Default browser-visible result mode is compact:

- stdout preview: ~1,800 chars
- stderr preview: ~1,200 chars
- full result persisted under `%LOCALAPPDATA%\GPTWindowsRelay\results\<safe-id>.json`
- `result_mode:"full"` is the explicit larger-output escape hatch

Large browser payloads previously contributed materially to Firefox bloat. Compact results are a deliberate performance feature.

## Command transport policy

Provide exactly one of:

- `command`
- `command_lines`
- `command_b64`

Preferred order:

1. plain `command` for simple operations;
2. **Python-first** for complex/multiline engineering and orchestration;
3. `command_b64` as a permanent resilient fallback whenever JSON/CMD/PowerShell quoting, multiline transport, or terminal behavior becomes unreliable.

**Base64 is not deprecated. Do not remove it as dead compatibility code.** Redundancy exists to reduce required user intervention.

## Duplicate / retry guarantees

Operation IDs are part of the safety model.

Established behavior:

- same ID + same completed payload → replay saved result, do not re-execute;
- same ID currently executing → duplicate-inflight handling;
- stale prior-process inflight → interrupted-restart handling;
- same ID + different payload → ID collision, refuse execution;
- browser action transport retries transient localhost/network/5xx failures for roughly 45 seconds;
- lost HTTP response after successful command completion is recovered via saved-result replay rather than duplicate execution.

Do not casually change duplicate/replay semantics.

## Firefox / scanner architecture

### Temporary extension

Development workflow:

- open `about:debugging#/runtime/this-firefox`
- load/reload `Client\Relay\extension\manifest.json`
- a full Firefox exit removes the temporary add-on

The temporary extension is development-only.

### Persistent production goal

The zero-touch production goal is:

- signed persistent XPI;
- stable extension ID;
- Firefox policy installation / force-install;
- persistent pairing token in `storage.local`;
- backend, Firefox, and Windows restart recovery with no routine user intervention.

Unsigned temporary loading is not the final architecture.

### Scanner

Current scanner family is V11:

- event-driven / mutation-local assistant discovery;
- stable `main` observer;
- no mutation-triggered whole-conversation rescans;
- bounded attempted packet history;
- 15-second recovery fallback;
- one-shot recovery scroll to the newest valid assistant relay command;
- manual scrolling remains authoritative after recovery;
- smart bottom-follow is throttled;
- explicit user turns fail closed.

A major prior root cause was **stale ChatGPT assistant selectors**. Current ChatGPT role selectors include `data-message-author-role="assistant"` and conversation-turn wrappers. Do not assume older search-unit selectors are sufficient.

## Firefox background lifetime

Firefox MV3 background/event pages are nonpersistent.

The relay therefore uses a long-lived content↔background `runtime.connect()` Port while a ChatGPT tab is active. This is intentional: an open Port keeps the Firefox MV3 event page alive.

Established telemetry includes:

- `content_port_connected` — emitted by the worker whenever a content Port connects/reconnects;
- `content_script_started` — emitted once by a newly executing content-script context and carries the runtime identity;
- `scanner_snapshot`
- `action_received`
- `action_result`
- handoff-scroll start/resume/end events for viewport proof.

**Important telemetry lesson:** older builds emitted `content_script_loaded` from inside `connectBackgroundPort()`, so every Port reconnect looked like a fresh content-script load. Do not use historical `content_script_loaded` cadence as proof of document reload or reinjection.

The persistent Port architecture was added after one-shot message flows could lose result delivery when Firefox unloaded the background page.

## Known performance history

Old poisoned Firefox session:
- ~5.26 GB working set
- ~7.02 GB private
- ~21.6% aggregate idle CPU
- hottest process ~3.9 GB WS / ~5.4 GB private

Clean V7 baseline:
- 13 processes
- ~2.13 GB WS
- ~1.76 GB private
- ~16.2% idle CPU

V8 after reload:
- 11 processes
- ~2.14 GB WS
- ~2.02 GB private
- ~5.7% idle CPU

Post large-output stress with compact result path:
- 11 processes
- ~2.08 GB WS
- ~1.97 GB private
- ~3.4% idle CPU

Important caution: older scanner samples were noisy. Do not attribute a single idle CPU reading to one scanner version without a fresh restart/reload baseline.

For A/B performance comparisons, use a fresh Firefox restart + temporary-extension reload baseline.

## Operational lessons already learned

- Prefer relay automation over asking the user to perform terminal work when the relay can do it itself.
- Verify the actual shell before giving shell-specific commands. PowerShell syntax has previously been pasted into CMD.
- On this machine, when Git path ambiguity matters, use:
  `C:\Program Files\Git\cmd\git.exe`
- Use `windows-relay\sync-live.py` to stage live browser/backend files and run tests instead of giant manual paste/bootstrap sequences.
- `sync-live.py --restart-backend` can stage and intentionally restart the supervised backend.
- Machine effort should be spent before user effort. Recoverable failures should not become unnecessary manual steps.
- When a test fails after an architecture change, check whether the **test contract is stale** before concluding the implementation is broken. V4 scroll staging hit exactly this failure mode.
- Static source presence is not equivalent to active browser runtime proof. For browser features, verify the actual loaded runtime/telemetry before declaring success.

## Historical Firefox temporary-extension facts

These are confirmed observations from the October 2–3, 2026 debugging session, not universal constants.

Active Firefox profile observed:
- `3awtt83g.default-release`

Historical relay temporary IDs observed:
- `789b9cccc135a95bdd457f81c61d1f92e5acf18e@temporary-addon` — historical, installed=False
- `a246f5d3d4411a21157d03eb0b0b350de6b91797@temporary-addon` — historical, installed=False
- `415ba89c48af03b9a3da9331f264187d086ef1ee@temporary-addon` — historical, installed=False
- `55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon` — current during the observed session, installed=True

Live `about:debugging` UI Automation later proved:

- Temporary Extensions count: 1
- live relay location: `C:/Users/<LOCAL_USER>/Downloads/Dev/GPT/Client/Relay/extension/`
- live extension ID: `55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon`
- internal UUID during that session: `2583b6b1-f194-48c9-a8ab-cc1add6602ec`
- background script: Running

Therefore:
- multiple historical temp IDs in Firefox profile metadata do **not** imply multiple currently installed relay extensions;
- `installed=False` is the important distinction for historical reconciler entries;
- the one live temp extension was already proven to point at the expected `Client\Relay\extension` directory.

Do not redo profile archaeology merely to rediscover that source path. Use the live `about:debugging` card / UI Automation first if the active temporary instance needs to be checked again.

## Current scroll work status

The user requested a user-benefit behavior where relay result injection brings the conversation down to the newest turn and follows the beginning of the next assistant response briefly, then yields manual scroll control.

Progress through V4:

- V1/V2/V3 experiments established telemetry and lifecycle issues;
- V4 moved handoff ownership to the reliable worker result path:
  - worker sends `relay_handoff_scroll`
  - then sends `relay_action_result`
  - content script handles the ordered scroll-control message
- source/tests staged successfully in persistent package v0.3.7;
- runtime identity marker: `runtime:'v11-scroll-v4'`
- marker: `GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V4`
- marker: `GPT_WINDOWS_WORKER_DRIVEN_SCROLL_CONTROL_V1`

**Do not modify the scroll algorithm again until a freshly loaded content script is proven active.**

At the last proven point:
- all known relay `content.js` copies on disk had identical current V4 content;
- live about:debugging pointed to the correct `Client\Relay\extension` source;
- but the ChatGPT tab's `content_script_loaded` telemetry still lacked the V4 runtime identity.

That narrowed the remaining issue to **content-script reload/document lifecycle**, not wrong source directory or multiple live temporary relay copies.

## Preflight checklist before new debugging

Before launching new forensics:

1. Read this file.
2. Search the engineering log for the subsystem/action already investigated.
3. Check whether the fact is already established in conversation/project history.
4. Distinguish:
   - source file state;
   - staged/live-tree state;
   - Firefox extension instance state;
   - actual injected content-script runtime state.
5. For browser behavior, require runtime telemetry or direct live UI proof before blaming source code.
6. Prefer live `about:debugging` / UI Automation for temporary-extension identity before deep profile archaeology.
7. Log new confirmed findings, root causes, fixes, and validation proof back to GitHub immediately.

The purpose of this document is to prevent repeated investigation of solved facts and minimize user intervention.


## Current product priority order

1. **P0 — Scroll / conversation-follow UX:** prove a genuinely fresh V4+ content runtime, then validate worker-driven handoff scroll end to end.
2. **P1 — Windows HUD:** compact real-state display for relay armed state, backend health, Firefox bridge/runtime state, last/current action, and synchronized pause/arm control.
3. **P2 — Lifecycle hardening:** backend restart, Firefox restart, Windows/login restart, signed persistent extension/policy path.
4. **P3 — Clipboard + troublesome job-application helper:** resume-backed field mapping; copied application text → ChatGPT reasoning → relay input.
5. **P4 — Screenshot on request:** explicit bounded screen/window/region capture returned to ChatGPT for visual reasoning.
6. **P5 — Broader Windows UI interaction adapters.**

The job-application branch is intentionally simple at first: the user copies difficult form text/context to ChatGPT, ChatGPT reasons using resume data, and the relay pastes/types the answer back. Screenshot capture is on-demand, not continuous by default.


## Human-intervention incident policy

Any unintentional user action required to keep an otherwise autonomous relay workflow moving is an engineering incident and must be logged in the canonical engineering record.

Examples include:
- manually submitting a relay result that should have been sent automatically;
- manually reloading Firefox or ChatGPT when automatic recovery was expected;
- manually visiting about:debugging to rescue the temporary extension outside an explicitly planned development test;
- manually re-pairing, re-arming, copying, pasting, clicking, or restarting something because the relay stalled;
- manually surfacing a stranded result or command.

Log the confirmed human action and mission impact immediately. Keep the technical root cause explicitly unresolved until telemetry or other evidence proves it. Do not normalize accidental user rescue as part of the expected workflow.


## Browser result-delivery contract

A Windows action result is **not delivered merely because the Send button was clicked**. The browser bridge must confirm that a user turn containing the packet ID exists before persisting that packet as attempted.

If ChatGPT rejects a send or leaves the result stranded in the composer, retry the same already-fetched result with bounded backoff. Do not re-execute the Windows command. Duplicate-ID saved-result replay remains the safety net after browser/content recovery.

A manually rescued stranded composer result is an autonomy incident and must be logged.


## Browser delivery anti-spam invariant

A backend result with `replayed:true` means **do not re-execute the Windows action**; it does not mean the browser should blindly post the result again.

Current delivery contract (delivery-v2):
- successful browser delivery may be confirmed either by an existing user `[GPT_WINDOWS_RESULT]` turn containing the packet ID or by the composer clearing and remaining clear without a send-error for the stability window;
- completed packet IDs persist in page `sessionStorage` across content-script/document reloads;
- startup recovery also hydrates completed IDs from existing user `[GPT_WINDOWS_RESULT]` turns;
- if a result for packet ID X is already visible in the conversation, `run(X)` must suppress backend replay/injection before calling the Windows backend;
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

