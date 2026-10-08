# Archived source fragment 4/23 — 2026-10-08T0752Z

Each test is successful only if a newly issued assistant relay packet executes end-to-end without manual extension intervention.


## Action 107 non-pickup — nested marker parser bug

Action 107 did not reach the Firefox background worker. The action's outer JSON command string intentionally contained another literal `[GPT_WINDOWS_ACTION] ... [/GPT_WINDOWS_ACTION]` block in order to submit a duplicate inner packet to localhost. Scanner V9's inherited `extract()` implementation used `lastIndexOf(OPEN)`, so it selected the inner marker embedded inside the JSON string instead of the actual outer command. The inner text was escaped command data rather than a valid top-level JSON packet, parsing failed, and the content script returned no action.

This also explains why Firefox showed the extension background as STOPPED: Firefox Manifest V3 background scripts are non-persistent event pages. Because the content script rejected Action 107 before calling `runtime.sendMessage()`, no extension event occurred to wake the background page. STOPPED in this instance was an idle state, not evidence of an extension crash.

Fix:
- packet delimiters must now occupy their own lines
- extraction iterates matching top-level-looking blocks and keeps the newest valid packet
- literal marker strings embedded inside JSON command data no longer shadow the outer packet
- regression marker: `GPT_WINDOWS_LINE_ANCHORED_PACKET_PARSER_V1`
- regression coverage verifies `lastIndexOf(OPEN)` is gone

This parser fix must be loaded into Firefox before the nested-packet replay test is repeated. Until then, relay test commands should avoid embedding literal complete relay delimiters inside the outer command text.


## Action 110 — duplicate replay live proof

The retry-safe backend behavior was proven live with a side-effect counter.

An inner operation was submitted twice with the same action ID:
- first request returned output containing `INNER_EXECUTION_COUNT=1`
- second request returned the same saved result with `"replayed": true`
- second response still contained `INNER_EXECUTION_COUNT=1`
- side-effect file final count remained exactly `1`

Therefore the second request did not execute the command again. Completed actions whose HTTP response is lost can now be recovered by retrying the same operation ID without duplicating command side effects.


## Firefox MV3 STOPPED/result-loss diagnosis — persistent message port fix

A later failure mode clarified that Firefox's background event-page lifecycle, not localhost reachability, was dropping the browser-side result path. The relay console still showed successful CORS/action traffic (204/200), while no ChatGPT diagnostic/result appeared and about:debugging showed the extension background as STOPPED.

Firefox Manifest V3 uses non-persistent background/event pages. They may unload when idle. Mozilla documents that a background page does not unload while message ports remain open, and recommends connection-based messaging when delivery to a specific extension endpoint must be reliable.

Architecture change:
- ChatGPT content script opens a long-lived `runtime.connect({name:'gpt-windows-relay-content'})` Port
- the Firefox background listens with top-level `runtime.onConnect`
- relay actions and results flow over that Port
- the open Port keeps the MV3 event page alive while the ChatGPT tab is present
- port disconnect rejects pending requests, schedules reconnection, and re-inspects the active packet
- backend duplicate-result replay remains the safety net if a disconnect occurs after execution
- one-shot `runtime.sendMessage({type:'action',...})` is no longer the primary action transport

Regression marker: `GPT_WINDOWS_PERSISTENT_BACKGROUND_PORT_V1`.

Do not replace this with heartbeat polling or artificial busy loops. The port is both the intended WebExtension messaging primitive and the Firefox-native event-page lifetime mechanism.


## Manual bootstrap sync for persistent background port

The user performed the V9/persistent-port bootstrap directly from Windows Terminal using CMD + the relay Python runtime, avoiding PowerShell multiline parsing issues.

Observed:
- canonical branch fast-forwarded from bc53c8a to 884ee44d9a05a02ef67f40c4b1e1b557f5841cc4
- live relay/browser files synchronized from the canonical checkout
- complete live regression suite: 36 tests in 0.870 seconds, all OK
- persistent Firefox package built successfully:
  C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay\dist\gpt-windows-relay-0.3.1.xpi
- bootstrap marker: BOOTSTRAP_SYNC=GREEN

At this point the new files are on disk but the already-running temporary Firefox extension still has the previous content/background scripts in memory. One manual temporary-extension Reload plus ChatGPT page refresh is required to cross into the new persistent-port runtime. This should be treated as a one-time development bootstrap, not the final operational workflow.

## Repeated no-action failure after healthy background — scanner V10 redesign

A post-reload test showed:
- Firefox extension background remained Running
- localhost /status requests returned 200
- no /action request occurred for the newest assistant relay command

This isolates the failure upstream of the worker/network path: the content script did not recognize/bind the newly generated assistant turn.

The recurring weakness was the computed conversation subtree used by V8/V9. ChatGPT can replace, virtualize, or restructure conversation containers, so a lowest-common-ancestor-derived observer root can become too narrow or stale even while the extension and backend remain healthy.

Scanner V10 changes:
- observe the stable main region with one childList + subtree MutationObserver
- mutation callbacks still inspect only mutation-local nodes/owners; they do not run whole-conversation querySelectorAll
- active-turn streaming remains separately coalesced
- packet extraction now prefers rendered pre/code blocks from the assistant turn, then falls back to line-anchored combined text
- this removes dependency on how a particular ChatGPT DOM build concatenates prose and code-block textContent
- persistent runtime Port remains the Firefox MV3 background lifetime mechanism

Local browser telemetry was also added:
- content_port_connected
- action_received
- action_result

These events are written by the relay under its state directory in browser-events.jsonl and also emitted as BROWSER_EVENT server log lines. Future stalls can therefore be classified directly as scanner, port/worker, localhost/backend, or response-injection failures instead of inferred from generic 200/204 traffic.

Regression markers:
- GPT_WINDOWS_EVENT_DRIVEN_SCANNER_V10
- GPT_WINDOWS_STABLE_MAIN_OBSERVER_V1
- GPT_WINDOWS_CODEBLOCK_PACKET_EXTRACTION_V1
- GPT_WINDOWS_PERSISTENT_BACKGROUND_PORT_V1

## V11 — current ChatGPT assistant selectors and content-load telemetry

A repeated post-reload failure showed the background worker Running and /status returning 200, but no /action request for the newest assistant command. This isolated the failure to assistant-turn discovery.

Publicly maintained ChatGPT DOM tooling from the same period consistently uses data-message-author-role=assistant and conversation-turn wrappers, while the relay still primarily selected older data-content-search-unit-key / data-chatgpt-search-unit-key forms.

V11 changes:
- add [data-message-author-role=assistant] as a primary assistant selector
- add article[data-turn=assistant]
- retain legacy/rollout assistant search-unit selectors
- recognize article/section conversation-turn wrappers only when an explicit assistant descendant proves role
- explicitly reject any node/wrapper carrying an explicit user role
- preserve stable-main mutation-local observation and rendered code-block packet extraction

V11 also adds content-side telemetry over the persistent runtime Port:
- content_script_loaded: proves the content script actually injected
- scanner_snapshot: reports main_present, candidate_count, and assistant_count before packet execution

This removes ambiguity between content-script injection failure and selector mismatch. If an action fails after V11, browser-events.jsonl can show whether the script loaded, how many turn candidates were found, whether the worker received the action, and whether the result returned.

Regression markers:
- GPT_WINDOWS_EVENT_DRIVEN_SCANNER_V11
- GPT_WINDOWS_CURRENT_CHATGPT_ROLE_SELECTORS_V1
- GPT_WINDOWS_CONTENT_LOAD_TELEMETRY_V1

## V11 bootstrap false-positive test failure

The first V11 sync aborted during tests with 42 tests run and exactly one failure: test_nested_marker_text_cannot_shadow_outer_packet.

