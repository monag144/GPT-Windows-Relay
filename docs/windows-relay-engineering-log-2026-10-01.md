# Windows Relay Engineering Log — 2026-10-01

## Scope

This log records the Windows/Firefox ChatGPT relay hardening and recovery work performed on 2026-10-01. The active Windows relay workspace is:

`C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay`

The relay listens on `127.0.0.1:8766`, uses token authentication, and is intended to accept only assistant-authored `[GPT_WINDOWS_ACTION]` packets from the ChatGPT DOM via a Firefox extension.

## Relay protocol and parser status

The backend parser/execution path was brought to a stable state with support for:

- `command`
- `command_b64`
- `command_lines` JSON string arrays joined by newline
- shells: Windows PowerShell, pwsh, cmd, and native Python
- Python launched with `-X utf8 -c`
- approximately 20 KB decoded command ceiling
- protocol v1 compatibility
- strict envelope parsing
- output and timeout limits
- duplicate/replay protection
- process-tree termination
- CLIXML filtering

A native UTF-8 Python live proof succeeded with nested JSON and stdout/stderr. Thirteen parser regression tests were passing at that point.

## Assistant-only DOM trust boundary

The content script was constrained to assistant message containers only:

- `[data-content-search-unit-key$=":assistant"]`
- `[data-chatgpt-search-unit-key$=":assistant"]`

The scanner must never be broadened to `document.body.innerText`, because user-authored messages can contain relay packets and must not become executable input.

Composer selectors in use include:

- `[data-composer-markdown][contenteditable="true"][role="textbox"]`
- Ask ChatGPT fallbacks
- `#prompt-textarea`

## Major content-script failure discovered and repaired

A previous no-scroll patch accidentally left malformed JavaScript in `autoScrollChatGPT()`, including an orphaned `catch{}` and extra braces. That caused the entire content script to fail parsing even though the backend and extension background worker were healthy.

The repaired implementation replaced the scroll helper with a no-op:

```js
function autoScrollChatGPT(){
  return;
}
```

The live and persistent content-script copies were synchronized after repair and verified to contain no `scrollIntoView`, `window.scrollBy`, or `window.scrollTo` calls.

A subsequent end-to-end action succeeded, proving:

assistant packet -> DOM content script -> extension background -> localhost relay -> PowerShell execution -> feedback injection -> auto-send.

## Relay ARMED policy

The requested policy is explicit: after restart/recovery, the relay should come back ARMED.

Changes made:

- initial relay state defaults to armed
- startup sets armed state
- restart/recovery returns armed
- shutdown no longer forces a persisted disarm
- manual `/arm` remains available during a running process
- `/arm` transitions log origin and user-agent without logging the token
- extension 423 backoff exists
- content fetch abort/in-flight recovery exists
- service-worker fetch timeout is approximately 15 seconds

## Client disconnect crash handling

A browser-abort failure had caused a WinError 10053 while sending a response, followed by another exception when the server attempted to write an error response to the same dead socket.

The relay was hardened so response sending tolerates:

- BrokenPipeError
- ConnectionResetError
- ConnectionAbortedError
- OSError

The server now logs a client disconnect instead of cascading through another failed response.

## Supervision architecture

The desired model is:

1. visible PowerShell supervisor console running `run.ps1`
2. relay backend as a supervised Python child
3. hidden watchdog process
4. watchdog reopens a visible supervisor if the supervisor disappears
5. supervisor internally restarts a failed relay backend after a short delay

Singleton mutexes are used for both supervisor and watchdog.

The watchdog is registered at user startup under the HKCU Run key and remains hidden. The supervisor is launched with a visible window.

### Verified process chain

A controlled failover test initially appeared to fail because the verification request landed during the recovery window. Logs later showed watchdog detection followed by supervisor launch and server startup.

Recovered steady state was verified with:

- one relay listener
- one supervisor
- one watchdog
- relay ARMED
- visible supervisor window titled `GPT Windows Relay`

The actual process ancestry was then traced:

```text
listener python.exe
  -> venv python.exe launcher
    -> visible run.ps1 PowerShell supervisor
      -> hidden watchdog parent
```

The supervisor was therefore confirmed as an ancestor of the socket-owning relay process.

## Firefox HUD attempt and rollback

A top-right diagnostic HUD was attempted after supervision became stable.

The first HUD implementation was appended directly into `content.js`. This was the wrong isolation boundary. The appended code later proved syntactically broken, including malformed `return` tokens, so a HUD syntax error could kill the entire relay content script.

A second HUD version was moved toward a separate `hud.js` content script with a Shadow DOM, but this also introduced another page-wide MutationObserver and contributed to concern about page performance.

The current direction is:

- remove/disable HUD code from the active relay path
- restore the core content script first
- do not couple HUD syntax/runtime health to packet ingestion
- if the HUD returns, keep it independently loaded and timer-driven rather than adding another whole-page mutation scanner

## Current browser-side performance problem

The backend can run, but browser-side packet ingestion has become unreliable and the ChatGPT page performance has degraded.

The likely hot path is the core content scanner:

- it watches a very large, actively streaming ChatGPT conversation
- mutation activity can be extremely high
- the scanner can repeatedly query assistant message containers across the conversation history
- repeated full-history rescans during token streaming are expensive

The next redesign should be incremental rather than full-history:

- inspect only new or changed assistant nodes
- debounce/coalesce mutation storms
- retain strict assistant-only trust boundaries
- execute a completed packet exactly once
- keep a slower fallback poll only for missed mutation events
- avoid all automatic scrolling
- keep HUD work independent of packet ingestion

## Current operational caveat

During the latest browser-side failure, the relay backend had to be bootstrapped manually from PowerShell because action packets could not be trusted to reach the backend while the content script was broken.

Manual bootstrap command used:

```powershell
$root='C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay'; Remove-Item "$root\.relay-paused" -Force -ErrorAction SilentlyContinue; & "$root\.venv\Scripts\python.exe" "$root\windows_relay.py" server
```

When the browser bridge is unhealthy, diagnostics and repairs must not be attempted through `[GPT_WINDOWS_ACTION]`; use direct PowerShell or file inspection first.

## Security incident discovered during relay hardening

A separate persistence audit found unwanted 360/Qihoo-related software and a scheduled persistence mechanism.

Key findings included:

- scheduled task `executor_stack_win32_lts`
- startup shortcut targeting the same payload
- `XServer.exe` identified as 360 Total Security-related and holding the payload
- live external connection observed from that process
- task disabled
- startup shortcut moved into evidence
- process terminated
- evidence preserved under the relay workspace

This incident is separate from the relay architecture but was discovered while investigating unexplained system/resource behavior.

## Working rules going forward

- Keep the visible-header -> bare fenced `[GPT_WINDOWS_ACTION]` -> visible-footer sandwich format for relay commands.
- Every relay command should emit: `Reply to this with the sandwich technique`.
- Never intentionally add a language tag or metadata to the relay fence.
- Never broaden packet scanning to user-authored DOM.
- Never patch scrolling behavior into the relay scanner.
- Do not make the HUD part of the core packet-ingestion failure domain.
- When the browser bridge is broken, repair it from direct PowerShell rather than through the relay.
- Keep live and persistent extension copies synchronized after each known-good browser-side change.

## Next engineering steps

1. Restore and verify a minimal known-good `content.js` with no HUD.
2. Confirm reliable packet pickup with several small consecutive actions.
3. Replace whole-history mutation rescanning with a debounced incremental scanner.
4. Measure page responsiveness on a long/streaming ChatGPT thread.
5. Re-run relay failover tests after browser-side stabilization.
6. Reintroduce the HUD only as an isolated, low-frequency component.
7. Rebuild the persistent XPI after the content-script architecture is stable.
8. Complete Firefox persistent signing/install last, minimizing manual user interaction.


## Browser repair package completed

The uploaded live content script was inspected directly and confirmed to be syntactically invalid. `node --check` failed at the HUD V1 block because several `return` keywords had been truncated to `retur`. This proved that the HUD append could prevent the entire core relay content script from loading.

The same uploaded file also showed the browser-performance regression clearly:

- core `MutationObserver(scan)` ran on every subtree/character mutation
- each scan called `newest()`
- `newest()` queried the entire set of assistant turns and could walk backward through a long conversation
- the HUD added a second page-wide MutationObserver
- the HUD independently rescanned assistant turns and also polled every two seconds

A replacement `content.js` was built and passed `node --check`. Its browser scanner now uses an incremental design:

- one MutationObserver only
- mutation callbacks identify only the assistant turn that changed
- affected turns are deduplicated in a Set
- mutation storms are coalesced with a 200 ms flush
- packet content settles for 500 ms before execution
- packet extraction uses `textContent` rather than `innerText` to avoid forced layout/reflow
- startup recovery scans only the newest six assistant turns once
- fallback polling runs every five seconds and inspects only the newest four turns
- assistant-only trust selectors remain unchanged
- no automatic scrolling code is present
- HUD is removed from the active failure domain

A repair bundle was created containing:

- optimized `content.js`
- `install-browser-fix.ps1`
- README/install notes

The installer backs up both extension trees, copies the same optimized content script into live and persistent trees, removes `hud.js` from both manifests, disables any existing HUD file, and verifies hashes/scroll-call counts after installation.

Artifacts were uploaded to the existing Google Drive `Relay` folder:

- `gpt-windows-relay-browser-fix-2026-10-01.zip`
- `content.optimized.js`

Packaged `content.js` SHA-256:

`5517B413FF62577565805A5C17D8E841EA9D747B298DA17F916A85B932F70984`


## Performance scanner V3 installed

After V2 was functionally stable, a five-second Firefox sample still showed approximately 25% aggregate CPU on a 4-logical-CPU system, with one Firefox content process accounting for essentially the entire sample. Because V2 still used one document-wide MutationObserver, the browser-side relay was changed again.

V3 removes the page-wide MutationObserver entirely. It now:

- performs a one-time startup/recovery scan of the newest six assistant turns
- polls only the newest two assistant turns once per second
- continues to use textContent rather than innerText
- keeps all automatic scrolling disabled
- preserves assistant-only packet trust boundaries
- keeps live and persistent extension content scripts identical

The GitHub source was updated in commits ending at ea4d530. The working Windows relay was then updated from the GitHub checkout and verified with:

- POLLING_SCANNER_V3=True
- PAGE_WIDE_OBSERVER=0
- OLD_DIRECT_SCAN=False
- POLL_1000MS=True
- CONTENT_FILES_MATCH=True
- SCROLL_CALLS=0

Working live SHA-256 after installation:

F4B0FB4EA828FC4F4E9A5F2F4C036E08695E01756137D79163639208794A1ABB

A Firefox extension reload and page refresh are still required before measuring V3 browser performance.


## Performance scanner V4 installed locally

V4 was pulled into the working Windows relay and copied to both live and persistent extension trees. Verification from the Windows relay returned:

- WATCHED_TURN_SCANNER_V4=True
- DOCUMENT_OBSERVER=False
- TOTAL_MUTATION_OBSERVERS=1
- DISCOVERY_3000MS=True
- OLD_V3_1000MS=False
- CONTENT_FILES_MATCH=True
- SCROLL_CALLS=0

Working live SHA-256:

DEBE8E9F0543E9216CAA9C2B85A0804B8533F68F1FEF0A599D746350D25659F2

The remaining observer is scoped only to the currently watched assistant turn; there is no document-wide observer. Firefox extension reload and ChatGPT page refresh are required before V4 runtime performance can be measured.


## Browser action timeout diagnosis and fix

The first V4 runtime benchmark packet (PC-ENGINEER-RELAY-067-V4-RUNTIME-PERFORMANCE-PROOF) produced browser feedback with detail 23. Inspection showed the live extension service worker used AbortSignal.timeout(15000) for all relay requests. The benchmark intentionally included a 3-second settle plus a 10-second CPU sample, so the browser bridge could abort the HTTP request before the relay response returned.

Backend state later confirmed the command itself completed successfully:

- 067_BACKEND_STATUS=OK
- 067_BACKEND_EXIT_CODE=0
- 067_BACKEND_FINISHED=2026-10-02T02:54:28+00:00

The service workers were updated so ordinary status/control calls retain a 15-second default timeout while action execution requests use 315 seconds, matching the relay's maximum execution envelope with margin.

Local install verification returned:

- LIVE_ACTION_315S=True
- LIVE_DEFAULT_15S=True
- PERSISTENT_ACTION_315S=True
- PERSISTENT_DEFAULT_15S=True
- ACTION_TIMEOUT_FIX=INSTALLED

A Firefox extension reload is required for the updated service worker to become active before re-running the V4 performance benchmark.


## Smart auto-scroll V5 installed locally

V5 was pulled into the working Windows relay and copied to both live and persistent extension trees. Local verification returned:

- WATCHED_TURN_SCANNER_V5=True
- SMART_AUTOSCROLL=True
- DOCUMENT_OBSERVER=False
- TOTAL_MUTATION_OBSERVERS=1
- DISCOVERY_3000MS=True
- SCROLL_THROTTLE_400MS=True
- NEAR_BOTTOM_THRESHOLD_320=True
- ACTION_TIMEOUT_315S=True
- CONTENT_FILES_MATCH=True
- LIVE_SHA256=7AC6A9D696BA125267BC1C7EF3FA5B43BDEEA2EFD11A7EEF608B694D14192255

V5 preserves the watched-turn scanner architecture and restores bottom-follow scrolling using a throttled 400 ms adjustment that only runs while the user is already near the bottom. Manually scrolling upward suspends auto-follow. Firefox extension reload and ChatGPT page refresh are required before runtime validation.


## V5 runtime performance result

After reloading the V5 extension and refreshing ChatGPT, runtime validation succeeded:

- V5_PACKET_PICKUP=GREEN
- WATCHED_TURN_SCANNER_V5=True
- SMART_AUTOSCROLL=True
- DOCUMENT_OBSERVER=False
- DISCOVERY_3000MS=True
- SCROLL_THROTTLE_400MS=True
- NEAR_BOTTOM_THRESHOLD_320=True
- relay action completed normally through the 315-second browser action timeout

Ten-second Firefox sample:

- TOTAL_CPU_PERCENT_APPROX=12.5
- WORKING_SET_MB=4572.4
- PRIVATE_MEMORY_MB=6116.8
- WORKING_SET_DELTA_MB=-22.6
- PRIVATE_MEMORY_DELTA_MB=-27.6
- hottest Firefox content process PID 16248: 12.5% aggregate-system CPU, 3230.9 MB working set, 4460.8 MB private memory

Earlier comparison samples were approximately 15.0% for the older full scanner and 25.0% for V2. V5 therefore cut the measured CPU sample in half relative to V2 and was below the older 15% sample, while total and hottest-process working set also decreased. These are short runtime samples, not controlled laboratory benchmarks, so an idle follow-up sample is still needed to separate relay overhead from ChatGPT/Firefox rendering cost.


## Event-driven scanner V6 installed locally

V6 was pulled into the working Windows relay and copied to both live and persistent extension trees. Local verification returned:

- EVENT_DRIVEN_SCANNER_V6=True
- SMART_AUTOSCROLL=True
- DOCUMENT_OBSERVER=False
- OLD_3_SECOND_FULL_SCAN=False
- TOTAL_MUTATION_OBSERVERS=2
- LIVE_DUPLICATE_SUPPRESSION=True
- PERSISTENT_DUPLICATE_SUPPRESSION=True
- LIVE_ACTION_TIMEOUT_315S=True
- PERSISTENT_ACTION_TIMEOUT_315S=True
- CONTENT_FILES_MATCH=True
- LIVE_CONTENT_SHA256=267403E99695A91B4A02F4E1B8BB628E52AECE4FC63D30A23941DD0617BACD89

V6 removes periodic whole-conversation discovery. It uses one MutationObserver scoped to the active assistant turn and one childList-only observer scoped to the conversation branch, while retaining smart auto-scroll. The service workers also suppress duplicate backend pickup results instead of injecting DUPLICATE_IGNORED messages back into ChatGPT. Firefox extension reload and ChatGPT refresh are required before runtime validation.


## V7 relay recovery after V6 missed new turns

After V6 was activated, the browser bridge stopped discovering newly generated assistant packets reliably. The V6 conversation observer watched only direct childList changes on a lowest-common-ancestor node with subtree=false. ChatGPT can insert new turns deeper in that branch, so the observer could miss them entirely.

V7 keeps the event-driven architecture but makes discovery reliable:

- the conversation-branch observer now watches childList changes with subtree=true
- mutations whose target is inside the currently watched assistant turn are ignored, so token streaming does not trigger conversation rediscovery
- structural mutations elsewhere in the conversation branch schedule a coalesced local discovery
- there is still no document-wide observer and no periodic whole-conversation scan
- smart auto-scroll remains enabled
- duplicate relay pickups are now classified as duplicate_suppressed rather than relay_disarmed, and the content script marks them attempted without injecting a duplicate result

All three content-script copies were updated to the same V7 source. The persistent service worker parses successfully; the live service worker is an ES module and retains its normal import statement.


## V7 end-to-end proof

After manually installing V7 and reloading the temporary Firefox extension, packet PC-ENGINEER-RELAY-076-V7-END-TO-END-PROOF completed successfully end-to-end.

Result:
- V7_END_TO_END=GREEN
- relay PID 9684
- command duration about 3.3 seconds
- browser result injection succeeded

This confirms V7 restored reliable new-turn discovery after the V6 regression. Do not roll back solely because of the earlier missed-turn concern; preserve V7 unless further runtime evidence shows a new regression.


## Firefox add-on scope audit

Active third-party Firefox add-ons were inspected for broad page injection scope.

Broad-scope add-ons:
- uBlock Origin: <all_urls>, 3 content-script groups
- DuckDuckGo Search & Tracker Protection: broad all-URL access, 3 content-script groups
- Ruffle - Flash Emulator: <all_urls>, 1 content-script group
- justsayit: <all_urls>, 1 content-script group
- TWP - Translate Web Pages: broad all-URL access, 4 content-script groups

Low relevance to ChatGPT content injection:
- Zoom Recording Downloader: no broad/chatgpt content-script scope found
- Firefox DevTools ADB Extension: no broad/chatgpt content-script scope found

Current optimization interpretation:
- keep uBlock Origin for now because it can reduce page/network work
- first candidates to disable while engineering on ChatGPT: DuckDuckGo, Ruffle, TWP, and justsayit (if not actively needed)
- biggest remaining expected win is still moving PC Engineering to a fresh ChatGPT thread and restarting Firefox, because the current ChatGPT content process has reached multi-gigabyte memory usage
- hardware acceleration should remain enabled unless a later controlled A/B test shows otherwise
- V7 packet discovery remains the current known-good relay architecture
- smart auto-scroll throttle has been increased from 400 ms to 900 ms


## Firefox pressure hardening — scanner V8 and compact results

After a true Firefox restart, the clean baseline dropped to roughly 2.13 GB working set and 1.76 GB private memory, confirming that the previous giant browser session was a major source of pressure. Further source audit found two relay-side amplification paths: broad conversation-subtree rediscovery from V7 mutation callbacks and unrestricted browser injection of large relay results.

Changes:
- backend result mode now defaults to `compact`
- compact previews are capped at 1,800 stdout characters and 1,200 stderr characters
- full stdout/stderr is saved locally under the relay state directory before browser previewing
- packets may explicitly request `"result_mode":"full"` when needed
- scanner V8 replaces observer-triggered conversation `querySelectorAll` rescans with mutation-local assistant discovery
- whole-branch recovery scanning is reduced to one 15-second fallback
- attempted packet history is capped at 256 IDs
- smart auto-scroll throttle increased to 1,200 ms
- browser performance contract tests added
- installer verification updated for V8 markers
- README/runtime policy documentation brought in line with Firefox + ARMED behavior

Do not roll back to V7 unless new evidence shows V8 misses turns. Validate V8 end-to-end after installing the updated files, then measure a fresh idle CPU/RAM sample.


## Actions 100-101 — V8 live proof and first performance baseline

Action 100 completed successfully after reloading the Firefox temporary extension:
- V8 file marker present
- bounded attempted history present
- observer-triggered conversation rescan removed
- smart-scroll V2 present
- compact backend metadata returned with a saved-result path

Action 101 measured the first post-V8 Firefox baseline over 10 seconds:
- Firefox processes: 11
- working set: 2138.1 MB
- private memory: 2024.3 MB
- aggregate idle CPU: 5.7% of the 4-logical-CPU machine
- hottest process CPU: 3.6%
- hottest process working set: 1108.2 MB
- hottest process private memory: 1080.7 MB

Compared with the clean pre-V8 baseline (2126 MB working set, 1758.9 MB private, 16.2% idle CPU), V8 reduced aggregate idle CPU by about 65% while aggregate working set stayed essentially flat. Private memory increased modestly during the longer-lived active session and should continue to be monitored. Compared with the poisoned pre-restart session (5264.1 MB working set, 7024 MB private), memory remains dramatically lower.


## Actions 102-103 — large-result stress test

Action 102 exercised the new compact-result path with approximately 20 KB stdout and 8 KB stderr.
Observed:
- raw stdout chars: 20,095
- raw stderr chars: 8,002
- browser-facing stdout/stderr both truncated to compact previews
- full result persisted locally
- no connection abort
- no duplicate injection
- no Firefox crash

Action 103 immediately remeasured Firefox over 10 seconds:
- processes: 11
- working set: 2078.9 MB
- private memory: 1969.9 MB
- aggregate idle CPU: 3.4%
- hottest process CPU: 1.9%
- hottest process working set: 1043.9 MB
- hottest process private memory: 1014.1 MB

Compared with Action 101 before the large-result stress test (2138.1 MB WS, 2024.3 MB private, 5.7% idle CPU), Firefox did not grow after the stress test; memory and CPU both decreased. This is strong evidence that compact result injection removes the previous large-output DOM amplification path.


## Next browser UX requirements — zero-intervention recovery

The next browser-layer work is now defined by two user-facing requirements.

### 1. Return to the newest relay command automatically

When the ChatGPT tab, relay content script, or extension recovers/reloads, the browser should automatically locate the newest assistant turn containing a valid `[GPT_WINDOWS_ACTION]` packet and bring that turn into view.

Acceptance criteria:
- perform a one-shot recovery/load scroll to the newest valid assistant relay command
- do not continuously force the viewport to the bottom
- do not override subsequent manual user scrolling
- do not reintroduce whole-document observers or mutation-triggered full-conversation scans
- reuse the existing assistant-only trust boundary
- keep recovery discovery bounded/low-frequency so V8 performance gains remain intact

This is distinct from token-stream bottom-follow scrolling: its purpose is recovery/navigation, not continuous viewport control.

### 2. Zero-intervention Firefox/relay restart

The normal operating experience must not require the user to manually restart or reload the Firefox extension.

Target behavior:
- relay backend restart: extension reconnects automatically when localhost returns
- extension background/event-page suspension: Firefox wakes it automatically on the next relevant event/message
- full Firefox restart: relay extension is already installed and becomes active automatically
- Windows/login restart: watchdog/supervisor restores the backend and Firefox's installed extension remains available when Firefox starts
- saved pairing token survives through `chrome.storage.local`
- normal recovery requires no visit to `about:debugging`, no temporary-addon reload, no manual ChatGPT refresh, no re-pairing, and no re-arming

The temporary Firefox add-on path is therefore development-only. The production solution for surviving full Firefox restarts is the signed persistent XPI plus the existing Firefox policy deployment path.

Validation must include three explicit zero-touch tests:
1. backend-only restart
2. full Firefox restart
3. Windows/login restart

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

The production parser logic was not broken. The failing test asserted an exact explanatory comment string, but the comment had been reworded from 'embedded inside JSON command strings' to 'embedded inside JSON command data'. The underlying line-anchored parser and validPacketBody behavior remained present.

The regression test was corrected to assert behavior-bearing source invariants instead of comment prose:
- blockRe exists
- blockRe iteration exists
- validPacketBody(match[1]) is used
- legacy lastIndexOf(OPEN) extraction remains absent

Commit: 25da536cdaea4f816c69c5f877400d2a87f8aa17

## V11 live recovery proof — GREEN

Action PC-ENGINEER-RELAY-120-V11-RECOVERY-PROOF completed successfully after a temporary-extension reload and ChatGPT refresh.

Observed end-to-end evidence:
- content_script_loaded events reached the backend
- content_port_connected events reached the backend
- scanner_snapshot reported main_present=true
- scanner_snapshot reported candidate_count=5 and assistant_count=5 in the active conversation
- action_received was logged for request_id action-murmcjan-1
- the relay executed the action through shell=python with status OK and exit_code 0
- result injection returned the structured GPT_WINDOWS_RESULT to ChatGPT
- V11_RECOVERY_END_TO_END=GREEN

This validates the V11 current-DOM selector fix plus the persistent runtime Port and backend execution path. The action_result event is expected to be absent from the command's own telemetry tail because that event is emitted by the worker only after the backend response is received; a subsequent action can confirm it.

## V11 continuous-operation proof — GREEN

Action PC-ENGINEER-RELAY-121-V11-CONTINUOUS-OPERATION executed immediately after Action 120 with no extension reload, page refresh, terminal command, or other user intervention.

Observed:
- status OK, exit_code 0
- CONTINUOUS_ACTION_EXECUTED=True
- NO_MANUAL_RELOAD_SINCE_120=True
- ACTION_RESULT_EVENTS=1
- ACTION_RECEIVED_EVENTS=2
- the prior Action 120 result was logged as action_result with ok=true
- V11_CONTINUOUS_OPERATION=GREEN

This proves the V11 scanner + persistent runtime Port + worker + localhost backend + result-injection loop can carry successive relay actions continuously after bootstrap.

## Relay handoff auto-scroll UX

Added a bounded relay-specific scroll handoff for user convenience.

Behavior:
- after the browser bridge injects and sends a relay result, it forces the conversation to the newest edge
- it continues following the newest edge for 8 seconds at 500 ms intervals, covering the result send and start of the next assistant response
- during that brief relay-owned handoff window, incidental scroll events do not disable follow mode
- after 8 seconds, normal near-bottom/manual-scroll authority resumes
- recovery/load one-shot scrolling remains separate and unchanged

Marker: GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V1
Persistent extension version: 0.3.4

## Handoff scroll v0.3.4 staging — GREEN

Action PC-ENGINEER-RELAY-122-STAGE-HANDOFF-SCROLL-V034 completed successfully through the live relay.

Observed:
- HANDOFF_SCROLL_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- persistent XPI built as gpt-windows-relay-0.3.4.xpi
- SYNC_LIVE=GREEN
- HANDOFF_SCROLL_UPGRADE_STAGED=GREEN

Browser files are staged on disk. The running temporary Firefox extension still requires one reload to activate the new content script before live UX validation.

## Handoff scroll v0.3.4 runtime activation proof

Action PC-ENGINEER-RELAY-124-HANDOFF-SCROLL-LIVE-PROOF completed successfully after the Firefox extension reload.

Confirmed:
- relay action execution remained healthy
- GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V1 is present in the active live content-script file
- the 8-second bounded handoff window is present
- manual near-bottom scroll authority restoration is present

Important qualification: Action 124 validated that the intended browser code was staged/active on disk and that the relay remained operational. It did not independently prove that the user's visible Firefox viewport moved correctly. Do not mark the UX behavior itself fully validated until visually observed or browser-side scroll telemetry confirms the actual scroll root and post-scroll position.

## Handoff scroll V2 — self-validating viewport telemetry

Action 125 proved relay execution but still required the user to visually confirm whether Firefox actually moved to the newest turn. That manual observation requirement conflicts with the relay's design goal of minimizing necessary user input.

V2 adds browser-side scroll telemetry:
- handoff_scroll_start records the selected scroll root, distance from bottom before the forced handoff, and distance immediately after
- handoff_scroll_end records the final distance from bottom and near_bottom state after the bounded 8-second follow window
- telemetry travels through the existing persistent content Port into browser-events.jsonl

This allows the relay to verify its own scroll behavior rather than asking the user to report whether the viewport moved.

Markers:
- GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V2
- GPT_WINDOWS_SCROLL_TELEMETRY_V1

Persistent extension version: 0.3.5

## Scroll V2 telemetry staging — GREEN

Action PC-ENGINEER-RELAY-126-STAGE-SCROLL-V2-TELEMETRY completed successfully through the live relay.

Observed:
- HANDOFF_SCROLL_V2_STAGED=True
- SCROLL_TELEMETRY_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- persistent XPI built as gpt-windows-relay-0.3.5.xpi
- SYNC_LIVE=GREEN
- SCROLL_V2_SELF_VALIDATION_STAGED=GREEN

One temporary-extension Reload plus ChatGPT refresh remains necessary to activate the new content script before self-validating the viewport movement.

## Scroll V2 self-validation test ordering correction

Action PC-ENGINEER-RELAY-127-SCROLL-V2-SELF-VALIDATION reported zero handoff_scroll_start/end events, but this did not indicate a browser scroll failure.

Root cause was the validation sequence itself: Action 127 slept inside the backend command waiting for telemetry. Handoff scrolling begins only after that command returns, the worker receives the backend result, and the content script injects/sends the result into ChatGPT. Therefore the telemetry being awaited could not exist until after Action 127 completed.

Correct validation is two-phase:
1. a fast relay action returns and thereby triggers the browser handoff scroll;
2. a subsequent relay action reads the telemetry emitted by the previous result injection.

Do not interpret Action 127's 0/0 telemetry counts as a scroll implementation failure.

## Handoff scroll V3 — pre-send arming and reconnect resume

Action 130 confirmed action_result telemetry continued to arrive while no handoff_scroll events were emitted. This isolated the failure to the post-result injection phase.

The previous inject ordering armed the handoff only after await send(). ChatGPT result submission can replace or reconnect the content-script context quickly enough that post-click handoff setup is not reliable.

V3 changes:
- beginRelayHandoffScroll() now runs before await send()
- the handoff deadline is persisted in sessionStorage under gptWindowsRelayHandoffUntil
- a reloaded/reconnected content script resumes any still-valid handoff window
- handoff_scroll_resumed telemetry records reconnect recovery
- handoff_scroll_start/end telemetry remains machine-verifiable

Regression requirements:
- beginRelayHandoffScroll must occur before await send()
- session handoff deadline persistence must remain present
- resumePersistedHandoff must run during content-script startup

Markers:
- GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V3
- GPT_WINDOWS_SCROLL_TELEMETRY_V2

Persistent extension version: 0.3.6

## Handoff scroll V3 staging — GREEN

Action PC-ENGINEER-RELAY-131-STAGE-SCROLL-V3 completed successfully through the live relay.

Observed:
- HANDOFF_SCROLL_V3_STAGED=True
- SCROLL_TELEMETRY_V2_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- persistent XPI built as gpt-windows-relay-0.3.6.xpi
- SYNC_LIVE=GREEN
- SCROLL_V3_RECONNECT_SAFE_STAGED=GREEN

One temporary-extension Reload plus ChatGPT refresh remains necessary to activate the V3 content script before live validation.

## V4 staging false-negative — stale V3 regression test

Action PC-ENGINEER-RELAY-134-STAGE-SCROLL-V4 failed during the browser contract suite before staging completed.

Root cause: test_handoff_scroll_starts_before_send_click still enforced the superseded V3 architecture by requiring beginRelayHandoffScroll() inside inject() before await send(). V4 intentionally removes handoff ownership from inject() and moves it to the worker, which sends relay_handoff_scroll immediately before relay_action_result over the same ordered Port.

The stale test was replaced with a V4 ownership assertion: inject() must not start the handoff itself, while the separate worker-order and content-control tests enforce that the worker owns scroll startup.

Implementation code was not identified as failing in Action 134; the failure was a regression-contract mismatch.

## Worker-driven handoff scroll V4 staging — GREEN

Action PC-ENGINEER-RELAY-135-STAGE-SCROLL-V4-RETRY completed successfully through the live relay after correcting the stale V3 regression test.

Observed:
- HANDOFF_SCROLL_V4_STAGED=True
- SCROLL_TELEMETRY_V3_STAGED=True
- WORKER_DRIVEN_SCROLL_STAGED=True
- RUNTIME_IDENTITY_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- persistent XPI built as gpt-windows-relay-0.3.7.xpi
- SYNC_LIVE=GREEN
- SCROLL_V4_WORKER_DRIVEN_STAGED=GREEN

The next live validation must confirm runtime identity v11-scroll-v4 after Firefox temporary-extension reload, then observe handoff_scroll_start/end telemetry generated by the worker-driven control message.

## Firefox scroll-runtime forensics — confirmed findings through Action 141

These findings are now part of the canonical relay engineering record and should be preserved when the Firefox/runtime issue is resolved.

### Confirmed
- Action 137 proved the intended V4 scroll runtime was not actually active in Firefox: the newest content_script_loaded event had no runtime identity, ACTIVE_RUNTIME=None, V4_RUNTIME_ACTIVE=False, and no handoff_scroll telemetry.
- This means the failure at that point was not evidence that V4 scroll logic itself was executing incorrectly; Firefox was still executing an older content-script generation.
- Action 138 compared all relay content.js copies under both the canonical repo and the live Client\\Relay tree. Every discovered relay content.js had the same SHA-256 prefix e4f19c57f2fb26bf and contained both GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V4 and runtime:'v11-scroll-v4'.
- Therefore the stale runtime was not coming from an outdated content.js file in either known source tree.
- The live temporary-extension manifest at Client\\Relay\\extension\\manifest.json remains version 0.1.1; the separately packaged persistent extension is versioned independently.
- Action 139/140 found multiple Firefox temporary-addon permission records for the relay host permissions in the active profile 3awtt83g.default-release.
- Four observed temporary add-on IDs are:
  - 789b9cccc135a95bdd457f81c61d1f92e5acf18e@temporary-addon
  - a246f5d3d4411a21157d03eb0b0b350de6b91797@temporary-addon
  - 415ba89c48af03b9a3da9331f264187d086ef1ee@temporary-addon
  - 55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon
- extensions.json did not enumerate those temporary relay instances, so Firefox temporary-extension state must be traced through other profile/runtime records.
- Action 141 confirmed those IDs persist in extension-preferences.json, prefs.js, and weave/addonsreconciler.json; one ID also appears in targeting/telemetry state.
- addonStartup.json.lz4 exists and is likely authoritative for startup registration, but the relay Python environment currently lacks the optional lz4 module, so that file was not decoded in Action 141.

### Working hypothesis
Firefox is executing a cached or separately registered temporary relay instance that is distinct from the current on-disk source trees. Multiple historical temporary-addon records make duplicate/stale temporary extension state a primary suspect.

### Next forensic step
Inspect prefs.js and weave/addonsreconciler.json for the four exact IDs to recover timestamps/state metadata, then inspect or decode Firefox startup/runtime registration as needed. Do not change scroll implementation again until the active extension instance/source is identified.

## Firefox temporary add-on state — Action 143

Action PC-ENGINEER-RELAY-143-COMPACT-TEMP-ADDON-STATE reduced the four relay-related temporary IDs to current vs historical state using Firefox Sync's addonsreconciler.json.

Observed:
- 789b9cccc135a95bdd457f81c61d1f92e5acf18e@temporary-addon: enabled=True, installed=False, scope=16, modified 2026-10-01T17:44:35.450Z
- a246f5d3d4411a21157d03eb0b0b350de6b91797@temporary-addon: enabled=True, installed=False, scope=16, modified 2026-10-01T20:57:14.450Z
- 415ba89c48af03b9a3da9331f264187d086ef1ee@temporary-addon: enabled=True, installed=False, scope=16, modified 2026-10-02T04:27:53.052Z
- 55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon: enabled=True, installed=True, scope=16, modified 2026-10-02T04:57:54.915Z

Interpretation:
- the first three IDs are historical temporary relay registrations, not currently installed add-ons
- 55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon is the current temporary relay registration according to Firefox's reconciler state
- therefore the stale V4 runtime problem is no longer best explained as four simultaneously installed relay copies
- the next question is which source/startup registration backs the current 55840853... instance, and why its live ChatGPT content script still reports no V4 runtime identity

Do not delete historical Firefox profile records merely because enabled=True appears in reconciler metadata; installed=False is the key state distinction.

## Current Firefox temp relay source-path search — Action 144

Action PC-ENGINEER-RELAY-144-MAP-CURRENT-TEMP-ADDON-SOURCE searched the active Firefox profile for the current relay temp ID 55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon and for known relay source-path strings.

Confirmed:
- the current temp ID is present in extension-preferences.json and prefs.js, consistent with the existing permission/storage migration metadata
- the readable profile records inspected did not expose a definitive unpacked source path for the current temporary relay instance
- therefore readable profile metadata alone is insufficient to identify which on-disk extension source Firefox is executing

Next step: decode addonStartup.json.lz4, which is the remaining authoritative startup-registration record likely to contain the temporary add-on path/source URI.

## Firefox startup registry decode — Action 145

Action PC-ENGINEER-RELAY-145-DECODE-CURRENT-FIREFOX-STARTUP-REGISTRATION installed the small lz4 Python dependency into the relay venv and successfully decoded the active profile's addonStartup.json.lz4.

Observed:
- decoded startup registry size: 15,594 bytes
- top-level sections: app-profile, app-builtin-addons, app-builtin
- current temporary relay ID 55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon is absent
- structural hit count for that ID: 0
- no relay/GPT source-like strings associated with the current temp ID were found in the decoded startup registry

Interpretation:
- the current relay temporary add-on is not persisted as a normal Firefox startup-registered add-on in addonStartup.json.lz4
- this is consistent with a temporary about:debugging install whose authoritative state lives in the running Firefox debugging session rather than startup registration
- historical/current permission and reconciler metadata can persist even though the temporary add-on itself is not present in startup registration

Next step: determine whether Firefox temporary-addon IDs are deterministically derived from the loaded manifest/root path; if so, map the current 55840853... ID to the exact relay source directory by hashing candidate paths/URIs.

## Temporary add-on ID/path derivation test — Action 146

Action PC-ENGINEER-RELAY-146-MAP-TEMP-ID-TO-SOURCE-PATH tested whether Firefox's 40-hex temporary add-on IDs were simple SHA-1 derivations of the known relay manifest/root paths.

Observed:
- eight candidate manifest/root paths were tested across the canonical repo and live Client\\Relay trees
- multiple path normalizations/URI forms and UTF-8/UTF-16LE encodings were tried
- none matched any of the four observed Firefox temporary-addon IDs

Interpretation:
- do not assume Firefox temporary-addon IDs can be reverse-mapped by a simple SHA-1 of the extension path
- the current temp ID 55840853... must be mapped from live Firefox runtime/debugging state rather than guessed from the ID formula

Next step: inspect the live about:debugging temporary-extension card through Windows UI Automation, which previously proved capable of seeing the relay card and Reload control.

## Live Firefox temporary relay mapping — Action 147

Action PC-ENGINEER-RELAY-147-LIVE-ABOUT-DEBUGGING-UIA-FORENSICS used Windows UI Automation against Firefox's live about:debugging page and definitively mapped the currently loaded temporary relay instance.

Confirmed live state:
- Temporary Extensions count: 1
- Name: GPT Windows Relay
- Location: C:/Users/<LOCAL_USER>/Downloads/Dev/GPT/Client/Relay/extension/
- Extension ID: 55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon
- Internal UUID: 2583b6b1-f194-48c9-a8ab-cc1add6602ec
- Manifest URL: moz-extension://2583b6b1-f194-48c9-a8ab-cc1add6602ec/manifest.json
- Background script: Running

Interpretation:
- Firefox is not loading the relay from an unknown or stale source directory
- the one live temporary relay instance points exactly at Client\\Relay\\extension, which Action 138 proved contains the current V4 content.js hash and runtime marker
- therefore the missing runtime:'v11-scroll-v4' telemetry from the ChatGPT tab is now best explained by stale injected content-script context / extension reload lifecycle rather than wrong source selection
- historical temporary-addon IDs remain profile residue only; about:debugging shows exactly one live temporary extension

Next step:
- verify/reload the live temporary extension instance and force a fresh ChatGPT document load, then require content_script_loaded to report runtime:'v11-scroll-v4' before testing handoff scroll again
- do not alter scroll implementation further until fresh-runtime activation is proven

## Canonical established-facts knowledge base added

To prevent repeated investigation of facts already proven in prior relay work, a short-form canonical knowledge base now lives at `docs/windows-relay-established-facts.md`.

Policy:
- read the established-facts file and search this engineering log before launching new relay forensics
- carry forward prior conversation/project-history facts when already established
- separate source state, staged live-tree state, Firefox extension-instance state, and actually injected content-script runtime state
- log newly confirmed findings, root causes, fixes, false leads worth remembering, and proof back to GitHub as they are established
- prefer machine effort over user intervention and avoid asking the user to repeat or manually rediscover known facts

The README now links this preflight requirement prominently.

## Fresh-runtime automation failure + telemetry semantics correction — Actions 148–149

Action 148 scheduled a detached PowerShell helper intended to reload the live temporary Firefox relay extension and then reload the ChatGPT document. Action 149 found no helper log, so the deferred helper did not successfully execute.

Action 149 also exposed a telemetry naming flaw:
- connectBackgroundPort() currently emits event content_script_loaded every time a Port is established/re-established
- therefore repeated content_script_loaded events do not necessarily represent fresh content-script injection or document reload
- the ~30-second cadence seen in the event log is compatible with Port reconnect behavior and must not be interpreted as repeated page loads

Implications:
- Action 149 did not prove that Firefox repeatedly loaded the stale content script; it proved only that the currently running stale content script repeatedly established a background Port
- runtime:'v11-scroll-v4' remains absent because the currently executing content-script context is still the older generation
- fresh-runtime activation remains unproven

Required fixes:
- distinguish true content-script startup telemetry from content-port-connected/reconnected telemetry
- replace the failed detached activation helper with a simpler deferred launcher whose execution can be proven independently
- do not use the old content_script_loaded event as a proxy for document injection until telemetry semantics are corrected

## v0.3.8 staging false-negative — stale content-load telemetry test

Action PC-ENGINEER-RELAY-150-STAGE-V038-AND-DEFERRED-LAUNCHER-PROBE failed during the browser contract suite before the deferred-launch probe ran.

Root cause:
- test_content_load_and_scanner_snapshot_telemetry still enforced the obsolete event name content_script_loaded and marker GPT_WINDOWS_CONTENT_LOAD_TELEMETRY_V1
- the implementation had already moved to one-time content_script_started telemetry with GPT_WINDOWS_TRUE_CONTENT_START_TELEMETRY_V1

Correction:
- regression test renamed/reframed around true content-script startup semantics
- old content_script_loaded assertion removed
- obsolete GPT_WINDOWS_CONTENT_LOAD_TELEMETRY_V1 source marker removed from canonical/live/persistent content-script copies

Interpretation:
- Action 150 does not indicate a runtime or relay failure
- the deferred-launch probe did not execute because sync-live exited on the stale test first
- staging and launcher validation must now be retried separately so failures remain isolated

## v0.3.8 staging false-negative — brittle content-start syntax assertion

Action PC-ENGINEER-RELAY-151-STAGE-V038-CLEAN failed in test_content_start_and_scanner_snapshot_telemetry.

Root cause:
- the implementation correctly emits content_script_started through emitRelayEvent('content_script_started', ...)
- the regression test incorrectly required the literal object-fragment syntax event:'content_script_started'
- this was a brittle source-shape assertion, not a behavioral failure

Correction:
- the test now asserts the actual behavior-bearing emitRelayEvent('content_script_started' call
- no runtime implementation change was required for this failure

## v0.3.8 clean staging — GREEN

Action PC-ENGINEER-RELAY-152-STAGE-V038-CLEAN-RETRY completed successfully through the live relay.

Observed:
- V11_STAGED=True
- HANDOFF_SCROLL_V4_STAGED=True
- SCROLL_TELEMETRY_V4_STAGED=True
- WORKER_DRIVEN_SCROLL_STAGED=True
- TRUE_CONTENT_START_TELEMETRY_STAGED=True
- RUNTIME_IDENTITY_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- persistent XPI built as gpt-windows-relay-0.3.8.xpi
- SYNC_LIVE=GREEN
- V038_CLEAN_STAGING=GREEN

Interpretation:
- v0.3.8 is now the clean staged baseline for the scroll/lifecycle mission
- remaining blocker is live activation of the fresh content-script runtime, not source staging or regression coverage
- deferred launcher validation should be tested independently before using it to automate Firefox reload

## Deferred child-process probe — Actions 153–154

Action PC-ENGINEER-RELAY-153-DEFERRED-LAUNCHER-ISOLATED-PROBE successfully created a detached PowerShell child process and returned PID 12988. The child was instructed to wait two seconds and write `%LOCALAPPDATA%\\GPTWindowsRelay\\deferred-launcher-probe.txt`.

Action PC-ENGINEER-RELAY-154-VERIFY-DEFERRED-LAUNCHER-PROBE found:
- PROBE_EXISTS=False
- DEFERRED_LAUNCHER_PROOF=FAILED

Backend inspection after the failure confirmed:
- `windows_relay.py` launches the action process with CREATE_NEW_PROCESS_GROUP
- normal successful completion does not explicitly kill descendants
- `taskkill /PID <pid> /T /F` is used only on command timeout

Therefore:
- a relay-command-spawned detached child is not a reliable post-result execution mechanism in the current environment
- the exact external reason the detached child disappeared is not yet proven by backend source and must not be stated as established root cause
- do not use ordinary detached child processes for post-result Firefox lifecycle actions

Next approach:
- use Windows Task Scheduler as an external process-ownership boundary
- create/run a scheduled task that performs a delayed marker write, verify it survives after the relay result returns, then reuse the proven scheduler primitive for Firefox extension/document reload

## Task Scheduler post-result execution primitive — Actions 155–156 — GREEN

Action PC-ENGINEER-RELAY-155-TASK-SCHEDULER-DEFERRED-PROBE created and immediately ran the one-shot task `\\GPTWindowsRelay-DeferredProbe`. The task waited three seconds and wrote a marker outside the relay action lifetime.

Action PC-ENGINEER-RELAY-156-VERIFY-TASK-SCHEDULER-DEFERRED-PROBE confirmed:
- PROBE_EXISTS=True
- TASK_SCHEDULER_DEFERRED_PROOF=GREEN
- Task Scheduler Last Result=0
- Logon Mode=Interactive only
- Run As User=<LOCAL_USER>
- the probe task was deleted after verification

Established design fact:
- Windows Task Scheduler is a proven external ownership boundary for work that must execute after a relay result has already returned
- ordinary detached descendants spawned directly by a relay command are not reliable for this purpose in the current environment
- use a short-lived scheduled task for deferred Firefox lifecycle operations until a cleaner native relay mechanism is implemented

Immediate use:
- P0 scroll mission: schedule delayed live temporary-extension Reload followed by ChatGPT document Reload, then require a one-time `content_script_started` event carrying runtime `v11-scroll-v4` before resuming handoff-scroll validation

## INCIDENT — Unintentional human intervention during Action 158 result delivery

Incident trigger:
- the user found the completed result for `PC-ENGINEER-RELAY-158-VERIFY-FRESH-V038-RUNTIME-ACTIVATION` sitting in the ChatGPT/relay flow and had to submit it manually

Confirmed facts:
- Action 158 itself completed successfully at the Windows relay (`status=OK`, `exit_code=0`)
- the result existed and was recoverable
- automatic continuation/delivery did not complete without human intervention
- the user explicitly had to notice the stranded result and manually submit it

Mission impact:
- this is a reliability incident because routine relay operation is intended to require no manual user rescue
- the incident must be treated separately from the success/failure of the underlying Firefox activation action

Root cause status:
- NOT YET PROVEN
- do not assume whether the failure was result injection, Send-button activation, scanner continuation, post-reload recovery, or another browser-side handoff stage until telemetry is inspected

Required follow-up:
- inspect browser telemetry surrounding Action 158 and the Firefox reload window
- determine the exact point where automatic result delivery/continuation stopped
- add a regression/proof mechanism for this failure mode once identified
- future unintentional user rescue/manual submission events must be logged as incidents in the canonical engineering record

## Reliability flaw found during Action 158 incident analysis — result marked attempted before browser send succeeds

Source inspection of `windows-relay/content.js` found a confirmed retry hole in the successful action path:
- `run(p)` receives an OK relay result
- it calls `rememberAttempted(p.id)`
- it removes the packet from `inflight`
- only then does it call `await inject(r.result)`

Consequence:
- if composer injection or the ChatGPT Send click fails after the relay result has already been fetched, the packet ID is already recorded as attempted
- subsequent scanner recovery sees the packet as attempted and will not automatically retry delivery
- this can strand a relay result in the composer/UI and force manual user intervention

Incident relationship:
- this flaw is confirmed in source
- it is a strong candidate mechanism for the Action 158 manual-rescue incident
- it is NOT yet claimed as the exact incident root cause until the 157–159 runtime evidence is narrowed

Required correction:
- instrument result delivery stages explicitly (inject start/text set/send attempt/send click/send success/failure)
- mark a successful relay packet attempted only after browser result delivery reaches a defined success point
- on delivery failure, clear inflight state and leave the packet eligible for bounded automatic retry/recovery
- add regression coverage that a fetched result is not permanently suppressed when browser send fails

## Fresh v0.3.8 Firefox content runtime activation — GREEN

Actions 157–160 closed the stale-runtime blocker.

Confirmed:
- Task Scheduler activation helper completed GREEN
- live temporary relay extension Reload was invoked from the proven Client\\Relay\\extension source
- the PC Engineering 2 ChatGPT tab was selected and reloaded
- two genuine post-157 `content_script_started` events were recorded
- both true-start events carried `runtime: v11-scroll-v4`
- `POST_157_TRUE_START_COUNT=2`
- `FRESH_V038_RUNTIME_ACTIVE=True`
- `FRESH_V038_ACTIVATION_PROOF=GREEN`

True-start timestamps:
- 2026-10-03T01:02:45+00:00
- 2026-10-03T01:02:54+00:00

Interpretation:
- the stale content-script lifecycle/source-activation blocker is resolved
- Firefox is now proven to be executing the current V4 scroll-capable content script
- further scroll validation should use live handoff telemetry, not more runtime/source forensics

Next P0 gate:
- use a relay result delivered while V4 is active as the trigger
- require `handoff_scroll_start` and `handoff_scroll_end` telemetry
- require final `near_bottom=true`
- only then mark the scroll mission fully GREEN

## V4 handoff scroll runtime proof — control path GREEN, viewport result FAILED

Action PC-ENGINEER-RELAY-161-VERIFY-V4-HANDOFF-SCROLL-FROM-160 validated Action 160's result delivery while the fresh V4 runtime was active.

Observed:
- HANDOFF_START_COUNT=1
- HANDOFF_END_COUNT=1
- start root: `div.thread-scroll-container.overflow-x-hidden.overflow-y-auto`
- before_distance=8775
- after_distance=8483
- end_distance=9261
- end near_bottom=false
- V4_HANDOFF_SCROLL_PROOF=FAILED

Interpretation:
- worker-driven `relay_handoff_scroll` control is live and reaches the current V4 content script
- handoff start/end telemetry is functioning
- the remaining P0 defect is the actual viewport/bottom movement logic
- stale runtime/source selection and worker-control delivery are no longer the active blockers

Next investigation:
- inspect scroll-root selection and the force-to-bottom mechanism
- determine whether `div.thread-scroll-container` is the real writable scroll surface or whether ChatGPT requires a different scrolling API/target
- do not revisit lifecycle/source forensics unless new evidence contradicts the fresh-runtime proof

## V5 handoff-scroll design — robust newest-edge forcing

After Action 161 proved the V4 worker/control path but failed the viewport result, the scroll implementation was revised to V5.

V4 failure characteristics:
- live control path and start/end telemetry were GREEN
- selected root was `div.thread-scroll-container...`
- direct `scrollTop=scrollHeight` reduced distance only from 8775 to 8483 px
- end distance later grew to 9261 px
- near_bottom=false

V5 changes:
- reacquire the newest conversation edge on every force operation rather than trusting only the previously bound scroll root
- prefer the last conversation-turn element as the anchor, with the composer/main region as fallback
- call `anchor.scrollIntoView({block:'end', behavior:'auto'})`
- reinforce with `root.scrollTo({top:root.scrollHeight, behavior:'auto'})` and direct `root.scrollTop=root.scrollHeight`
- if reacquisition identifies a different real scroll root, rebind the scroll listener to that root
- emit `handoff_scroll_tick` telemetry with root, anchor, and remaining distance on each 500 ms handoff tick
- runtime identity advanced to `v11-scroll-v5`

Rationale:
- ChatGPT's thread UI is dynamic/virtualized; repeatedly targeting the newest rendered edge is more robust than assuming a single stale scrollHeight/scrollTop assignment will remain authoritative as turns grow
- manual-scroll authority remains unchanged outside the bounded eight-second relay-owned handoff window

## v0.3.9 V5 staging false-negative — brittle handoff tick telemetry assertion

Action PC-ENGINEER-RELAY-162-STAGE-V039-V5-SCROLL failed in the browser contract suite before live activation.

Root cause:
- V5 correctly emits handoff tick telemetry through `emitRelayEvent('handoff_scroll_tick', ...)`
- the new regression test incorrectly required the literal inline object fragment `event:'handoff_scroll_tick'`
- this is the same class of brittle source-shape false-negative previously seen with content-start telemetry

Correction:
- the regression test now asserts the behavior-bearing `emitRelayEvent('handoff_scroll_tick'` call
- no V5 runtime implementation change was required

Process lesson:
- source-contract tests for relay events should assert the actual event-emission API call or behavior, not incidental object-literal syntax

## INCIDENT — Unintentional human intervention during Action 163 result delivery

Incident trigger:
- the user had to manually surface/submit the completed result for `PC-ENGINEER-RELAY-163-STAGE-V039-V5-SCROLL-RETRY`

Confirmed facts:
- Action 163 completed at the Windows relay and returned a result payload
- the result did not continue through the ChatGPT relay flow without user assistance
- the user explicitly reported manual human interaction and requested incident logging

Mission impact:
- this violates the relay requirement that routine continuation should consume machine effort before user effort
- this is a separate reliability incident from Action 163's staging verdict

Root cause status:
- NOT YET PROVEN
- do not conflate the browser/result-delivery incident with the staging verifier failure

Required follow-up:
- continue the result-delivery hardening work already opened after the Action 158 incident
- add explicit inject/send stage telemetry and move attempted-state persistence until after successful browser delivery
- treat any further manual rescue/submission/reload/click as an incident automatically

## Action 163 staging false-negative — stale V4 runtime-identity verifier

Action PC-ENGINEER-RELAY-163-STAGE-V039-V5-SCROLL-RETRY reached `SYNC_LIVE=GREEN`, built `gpt-windows-relay-0.3.9.xpi`, and reported all V5 scroll markers GREEN except `RUNTIME_IDENTITY_STAGED=False`.

Root cause:
- `sync-live.py` still defined `runtime_identity_marker="runtime:'v11-scroll-v4'"`
- V5 source and regression tests correctly use `runtime:'v11-scroll-v5'`
- therefore Action 163's runtime-identity staging failure was a stale verifier false-negative

Correction:
- update the staging verifier to require `runtime:'v11-scroll-v5'`
- no V5 runtime implementation change required

Important separation:
- the Action 163 manual-submission event remains a real autonomy incident
- the staging verdict failure was independently caused by the stale verifier

## v0.3.9 / V5 clean staging — GREEN

Action PC-ENGINEER-RELAY-164-STAGE-V039-V5-SCROLL-FINAL completed successfully.

Observed:
- HANDOFF_SCROLL_V5_STAGED=True
- SCROLL_TELEMETRY_V5_STAGED=True
- WORKER_DRIVEN_SCROLL_STAGED=True
- TRUE_CONTENT_START_TELEMETRY_STAGED=True
- RUNTIME_IDENTITY_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- XPI built as gpt-windows-relay-0.3.9.xpi
- SYNC_LIVE=GREEN
- V039_V5_SCROLL_STAGING=GREEN

Interpretation:
- V5 source, regression coverage, live staging, and build are all clean
- remaining P0 gate is live Firefox activation of runtime `v11-scroll-v5`, followed by end-to-end viewport proof

## INCIDENT — Action 166 ChatGPT send failure required manual human intervention

User-visible evidence:
- after `PC-ENGINEER-RELAY-166-VERIFY-V039-V5-ACTIVATION-AND-SCROLL` completed, its `[GPT_WINDOWS_RESULT]` payload was visibly present in the ChatGPT composer
- ChatGPT displayed the red UI error: `Could not send this ChatGPT message`
- the result remained stranded in the composer instead of continuing the relay loop
- the user manually intervened to submit/surface the result

This screenshot materially narrows the delivery failure stage:
- relay execution succeeded
- browser result retrieval succeeded
- result injection into the ChatGPT composer succeeded
- a ChatGPT send attempt occurred far enough for the application to report a send failure
- automatic recovery did not retry or recover the stranded composer result

Incident classification:
- REAL autonomy/reliability incident
- not expected development interaction
- violates the mission requirement that routine continuation should not require human rescue

Relationship to the previously confirmed retry hole:
- source inspection already proved that `run(p)` marks the packet attempted before `await inject(r.result)` completes
- this incident is directly compatible with that retry hole: after a result is injected, a failed ChatGPT send can leave the packet marked attempted and therefore suppress automatic scanner retry
- this screenshot is stronger evidence than prior incidents because it places the failure after composer injection and at/after the ChatGPT send attempt

Root-cause boundary:
- exact upstream reason ChatGPT rejected/failed the send is not yet proven
- however the relay-side recovery defect is now concrete: failed post-injection sends must not permanently suppress the packet or require manual user submission

Required fix:
- instrument delivery stages: result_received, composer_text_set, send_attempt, send_click, send_confirmed/send_failed
- do not persist the packet as attempted until browser delivery reaches a confirmed success point
- if ChatGPT reports/send behavior indicates failure, keep the packet eligible for bounded automatic retry
- detect a stranded composer result and retry sending it without re-executing the Windows action
- preserve duplicate-ID replay semantics so retries recover the saved result rather than rerunning side effects


## Entry-failure recovery implementation — v0.3.10 delivery-v1

Implemented in response to the Action 166 stranded-composer incident.

Behavioral changes:
- successful Windows execution no longer marks the relay packet attempted before browser delivery succeeds
- result delivery now uses `injectConfirmed(text, packetId)`
- a delivery is confirmed only when a user turn containing the original packet ID appears in the conversation
- result text already stranded in the composer is preserved rather than blindly duplicated
- ChatGPT send is retried up to six times with bounded exponential backoff
- explicit send-error UI is detected when available and triggers retry
- browser-delivery retries reuse the already-fetched/saved Windows result; they do not re-execute the Windows command
- after six unsuccessful local send attempts, the packet remains un-attempted and a delayed scanner retry is scheduled, allowing duplicate-ID saved-result replay rather than command re-execution

New telemetry:
- `relay_result_received`
- `relay_result_text_set` / `relay_result_text_preserved`
- `relay_result_send_attempt`
- `relay_result_send_clicked`
- `relay_result_send_confirmed`
- `relay_result_send_rejected` / `relay_result_send_exception`
- `relay_result_send_retry`
- `relay_result_delivery_failed`
- `relay_result_delivery_complete` / `relay_result_delivery_retry_deferred`

Runtime identity: `v11-scroll-v5-delivery-v1`.


## INCIDENT — Action 168 manual human intervention during result delivery

Incident trigger:
- the user had to manually surface/submit the completed result for `PC-ENGINEER-RELAY-168-DIAGNOSE-V0310-TEST-FAILURE`

Confirmed:
- Windows relay execution completed and produced the result
- automatic browser continuation did not complete without user intervention
- this is another real autonomy failure, not expected development interaction

Relationship to the entry-failure work:
- this incident occurred while the old live content runtime was still active
- the v0.3.10 delivery-v1 fix was not yet staged/activated because Action 167 stopped on a regression-test failure
- therefore this incident reinforces the urgency of completing and activating delivery-v1 but is not evidence that delivery-v1 itself failed

Required handling:
- complete the pending delivery-v1 commit/stage/activation
- validate that future send failures are retried locally without user rescue or Windows command re-execution


## Action 169 delivery-v1 staging false-negative — regression test scoped from global initialization

Action `PC-ENGINEER-RELAY-169-LOG-INCIDENT-FIX-V0310-AND-STAGE` stopped in `test_result_delivery_is_confirmed_before_attempted`.

Root cause:
- the test searched from the first `relayDisarmedUntil=0;` occurrence in the entire source file
- that first occurrence is the global initialization `let relayDisarmedUntil=0;`, not the successful `run(p)` delivery branch
- the overly broad slice therefore contained unrelated earlier `rememberAttempted(p.id)` calls and falsely reported that delivery-v1 marks a packet attempted before confirmation

Correction:
- anchor the test at `async function run(p)`
- find the successful branch's indented `relayDisarmedUntil=0;` from that point
- assert that no `rememberAttempted(p.id)` occurs between that branch start and `await injectConfirmed(r.result,p.id)`
- assert the first success-path `rememberAttempted(p.id)` occurs only after confirmed delivery

No delivery-v1 runtime implementation change was required for this failure.

## v0.3.10 delivery-v1 clean staging — GREEN

Action `PC-ENGINEER-RELAY-170-FIX-V0310-TEST-SCOPE-COMMIT-STAGE` completed successfully.

Confirmed:
- targeted delivery-order/retry tests GREEN
- full browser contract suite GREEN
- delivery recovery marker present
- `injectConfirmed(text, packetId)` present
- temporary and persistent content-script mirrors exactly match canonical source
- persistent manifest version 0.3.10
- XPI build target gpt-windows-relay-0.3.10.xpi
- `RESULT_DELIVERY_RECOVERY_STAGED=True`
- `RUNTIME_IDENTITY_STAGED=True`
- `HANDOFF_SCROLL_V5_STAGED=True`
- `SCROLL_TELEMETRY_V5_STAGED=True`
- `SYNC_LIVE=GREEN`
- `ENTRY_FAILURE_FIX_V0310_STAGED=GREEN`

Commit created by the relay: `67bcafe` (`windows relay: confirm and retry ChatGPT result delivery`).

Next gate:
- activate runtime `v11-scroll-v5-delivery-v1` in Firefox
- require true content-script start telemetry for that runtime
- require a replayed/new relay result to reach a real user turn with `relay_result_send_confirmed` / `relay_result_delivery_complete` and no manual intervention
- if ChatGPT rejects the first send, require automatic resend of the same saved result without Windows command re-execution


## INCIDENT — Delivery-v1 replay spam forced Director to disable extension

Incident trigger:
- after activating runtime `v11-scroll-v5-delivery-v1`, repeated saved-result payloads for Actions 169, 171, and 172 were automatically injected/sent into the ChatGPT conversation
- the repetition became spammy enough that the Director manually disabled the Firefox extension to stop the loop and stabilize the conversation
- this manual extension shutdown is an unintended human intervention and therefore a formal autonomy incident

Confirmed mechanism:
- backend duplicate safety worked correctly: repeated Windows results were marked `replayed:true`, so commands were not re-executed
- the browser delivery layer was the failure domain
- delivery-v1 treated successful send acceptance as unconfirmed unless the packet ID was detected in a rendered user-turn selector
- when that DOM confirmation was missed, `injectConfirmed(...)` could re-inject the same already-accepted result and click Send again
- attempted packet history was memory-only, so content-script/document reloads also forgot prior successful IDs and could rediscover historical relay commands

Impact:
- no evidence of duplicate Windows side effects
- duplicate ChatGPT result messages were produced
- human intervention was required to disable the extension
- therefore delivery-v1 failed the autonomy/no-spam requirement even though backend duplicate execution protection remained intact

Fix — delivery-v2 / extension 0.3.11:
- stable composer-clear acceptance: after Send, if the packet leaves the composer and no send-error appears for 1.5 seconds, delivery is confirmed even if user-turn DOM detection misses
- exact user-result confirmation remains available as a second success path
- delivery attempts reduced from six to three
- completed packet IDs persist in `sessionStorage` through content-script/document reloads
- startup recovery hydrates attempted IDs from existing user `[GPT_WINDOWS_RESULT]` turns in the conversation
- `run(p)` suppresses backend replay immediately when an existing user result for the same packet ID is already present
- new telemetry: `relay_result_replay_suppressed` and confirmation method `composer_cleared` vs `user_result_turn`
- runtime identity advanced to `v11-scroll-v5-delivery-v2`

Safety invariant:
- result resend retries may repeat browser delivery only when acceptance is not established
- an already-visible `[GPT_WINDOWS_RESULT]` for a packet ID must prevent backend replay/injection after reload
- saved-result replay remains a backend recovery feature, not permission to duplicate the ChatGPT message


## Operator UX directive — no manual PowerShell

Director directive:
- no more PowerShell commands should be given to the user for manual execution;
- manual user interaction, when unavoidable, must use terminal/CMD-compatible commands only;
- relay/automation should remain the preferred path;
- internal automation may use PowerShell if it remains invisible to the user and requires no manual PowerShell interaction.

This directive supersedes prior recovery instructions that asked the user to run PowerShell manually.


## v0.3.11 delivery-v2 anti-spam staging proof — GREEN

Manual terminal sync completed successfully after the Director disabled the extension to stop the delivery-v1 spam incident.

Observed staging proof:
- 57 tests ran
- test suite result: OK
- V11_STAGED=True
- STABLE_MAIN_STAGED=True
- CODEBLOCK_PARSER_STAGED=True
- CURRENT_ROLE_SELECTORS_STAGED=True
- HANDOFF_SCROLL_V5_STAGED=True
- SCROLL_TELEMETRY_V5_STAGED=True
- WORKER_DRIVEN_SCROLL_STAGED=True
- TRUE_CONTENT_START_TELEMETRY_STAGED=True
- RESULT_DELIVERY_RECOVERY_STAGED=True
- RESULT_ANTISPAM_V2_STAGED=True
- RUNTIME_IDENTITY_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- XPI built: `gpt-windows-relay-0.3.11.xpi`
- SYNC_LIVE=GREEN

Interpretation:
- delivery-v2 anti-spam source is staged into the live relay tree
- regression suite is green
- the next gate is live Firefox activation and runtime telemetry proving `v11-scroll-v5-delivery-v2`
- historical packet IDs already visible as user `[GPT_WINDOWS_RESULT]` messages must be suppressed before backend execution/replay
- no duplicate ChatGPT result spam is acceptable during this activation test


## Replay-spam incident closure — delivery-v2 live proof GREEN

Action `PC-ENGINEER-RELAY-173-VERIFY-V0311-ANTISPAM-LIVE` provided the first live post-reactivation proof for extension 0.3.11 / runtime `v11-scroll-v5-delivery-v2`.

Observed:
- `DELIVERY_V2_START_COUNT=1`
- `DELIVERY_V2_RUNTIME_ACTIVE=True`
- no historical backend events for Actions 169, 171, or 172
- no historical `relay_result_received` events for Actions 169, 171, or 172
- `HISTORICAL_SPAM_FREE=True`
- `ANTISPAM_LIVE_PROOF=GREEN`
- no manual intervention was required during the 173 proof

Interpretation:
- the delivery-v1 replay-spam failure is closed
- previously completed historical relay packets are no longer resurrected into backend replay/result injection after the content-script restart
- backend duplicate safety remains intact
- delivery-v2 anti-spam guards are active in the live Firefox runtime

Note:
- `HYDRATION_EVENT_COUNT=0` during this proof does not contradict the result; suppression can be satisfied by restored attempted-ID state without conversation hydration adding new IDs
- the decisive invariant is zero historical backend/result activity after the delivery-v2 runtime start

Incident status: CLOSED for replay-spam regression.

Remaining separate reliability work:
- continue validating result-send confirmation/retry behavior on ordinary live actions
- return to the V5 scroll/bottom-follow P0 proof now that delivery spam no longer destabilizes the test loop


## Delivery-v2 live recovery proof + send-readiness defect

Action `PC-ENGINEER-RELAY-175-READ-174-FINAL-VERDICTS` confirmed the delivery path for Action 173:

- attempt 1: send button not found/enabled after the old 8-second send wait
- attempt 2: same condition; composer payload preserved
- attempt 3: send button became available, click succeeded
- delivery confirmation: `method="composer_cleared"`
- `relay_result_delivery_complete` followed
- no manual rescue was required for Action 173

Interpretation:
- delivery-v2 recovered correctly and did not duplicate the composer payload while waiting
- however ChatGPT send readiness was incorrectly counted as a delivery retry condition
- this is not a send rejection; it is a readiness/timing condition while the assistant/UI is still busy
- burning delivery attempts on temporary Send-button unavailability reduces reliability unnecessarily

Fix — delivery-v3 / extension 0.3.12:
- add an explicit send-readiness gate
- wait up to 90 seconds for an enabled Send button before consuming/failing a delivery attempt
- poll every 250 ms
- preserve the result already present in the composer
- emit `relay_result_send_waiting` and `relay_result_send_ready` telemetry
- only true readiness timeout, send exception, send rejection, or unconfirmed delivery should advance to the next retry attempt
- runtime identity advanced to `v11-scroll-v5-delivery-v3`

Goal:
- normal relay results should require one delivery attempt even when the assistant response is still finishing
- browser retry budget remains reserved for actual send/delivery failures rather than UI readiness latency


## Action 176 delivery-v3 staging false-negative — stale send() assertion

Action `PC-ENGINEER-RELAY-176-STAGE-V0312-DELIVERY-V3` stopped in the browser contract suite before live staging.

Root cause:
- delivery-v3 intentionally changed the confirmed-delivery path from `await send();` to `await send(packetId,attempt);`
- `test_delivery_retry_does_not_reexecute_windows_action` still asserted the old bare `await send();` call
- the legacy `inject(text)` path still legitimately uses bare `await send();`, so only the delivery-retry test was stale

Correction:
- update the delivery-retry regression test to require `await send(packetId,attempt);`
- no delivery-v3 runtime implementation change required

Classification:
- regression-test false-negative
- not a live runtime failure
- no manual-human-intervention incident was reported for Action 176


## v0.3.12 delivery-v3 send-readiness staging proof — GREEN

Action `PC-ENGINEER-RELAY-177-STAGE-V0312-DELIVERY-V3-RETRY` completed successfully.

Observed:
- full browser contract suite GREEN
- V11_STAGED=True
- STABLE_MAIN_STAGED=True
- CODEBLOCK_PARSER_STAGED=True
- CURRENT_ROLE_SELECTORS_STAGED=True
- HANDOFF_SCROLL_V5_STAGED=True
- SCROLL_TELEMETRY_V5_STAGED=True
- WORKER_DRIVEN_SCROLL_STAGED=True
- TRUE_CONTENT_START_TELEMETRY_STAGED=True
- RESULT_DELIVERY_RECOVERY_STAGED=True
- RESULT_ANTISPAM_V2_STAGED=True
- SEND_READINESS_GATE_STAGED=True
- RUNTIME_IDENTITY_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- XPI built as `gpt-windows-relay-0.3.12.xpi`
- SYNC_LIVE=GREEN
- DELIVERY_V3_V0312_STAGED=GREEN

Interpretation:
- delivery-v3 source/tests/build are clean and staged into the live relay tree
- anti-spam V2 remains present
- the next gate is fresh Firefox activation of runtime `v11-scroll-v5-delivery-v3`
- live proof must show one delivery attempt waiting for ChatGPT send readiness rather than consuming retries while Send is unavailable


## INCIDENT — Action 179 result injected while ChatGPT turn was interrupted/incomplete

Director reported manual human interaction was required during/after `PC-ENGINEER-RELAY-179-VERIFY-V0312-DELIVERY-V3-ACTIVATION`.

Screenshot evidence:
- ChatGPT visibly displayed: `Connection interrupted. Waiting for the complete answer`
- the active stop control was still present, indicating the current assistant response had not reached an ordinary idle/send-ready state
- the full `[GPT_WINDOWS_RESULT]` payload for Action 179 was already inserted into the composer
- the user had to intervene manually

Failure boundary:
- Windows execution succeeded
- delivery-v3 runtime activation succeeded
- browser result injection occurred
- injection occurred **before ChatGPT became idle after the current assistant response**
- delivery-v3's send-readiness gate prevented an immediate send while Send was unavailable, but it did not prevent the result payload from being parked visibly in the composer during an interrupted/unfinished assistant turn

Root-cause status:
- confirmed relay-side ordering defect: result text is inserted before an explicit assistant-idle / connection-stable gate
- the underlying network interruption itself is external and is not attributed to the relay
- the relay must tolerate that state without exposing a stranded payload or requiring human rescue

Required fix:
- add a pre-injection ChatGPT-idle gate
- wait until no generation/stop control is active and no interrupted/waiting-for-complete-answer state is visible before inserting relay result text
- emit idle-wait/idle-ready telemetry
- only after idle should the bridge inject result text, wait for enabled Send, click once, and confirm delivery
- preserve the existing anti-spam and saved-result duplicate guarantees

Classification:
- REAL autonomy incident
- manual human intervention required
- distinct from the earlier replay-spam incident


## v0.3.13 delivery-v4 pre-injection idle staging proof — GREEN

Action `PC-ENGINEER-RELAY-180-STAGE-V0313-DELIVERY-V4-IDLE-GATE` completed successfully.

Observed:
- full browser contract suite GREEN
- V11_STAGED=True
- STABLE_MAIN_STAGED=True
- CODEBLOCK_PARSER_STAGED=True
- CURRENT_ROLE_SELECTORS_STAGED=True
- HANDOFF_SCROLL_V5_STAGED=True
- SCROLL_TELEMETRY_V5_STAGED=True
- WORKER_DRIVEN_SCROLL_STAGED=True
- TRUE_CONTENT_START_TELEMETRY_STAGED=True
- RESULT_DELIVERY_RECOVERY_STAGED=True
- RESULT_ANTISPAM_V2_STAGED=True
- SEND_READINESS_GATE_STAGED=True
- PREINJECTION_IDLE_GATE_STAGED=True
- RUNTIME_IDENTITY_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- XPI built as `gpt-windows-relay-0.3.13.xpi`
- SYNC_LIVE=GREEN
- DELIVERY_V4_V0313_STAGED=GREEN

Interpretation:
- delivery-v4 source/tests/build are clean and staged into the live relay tree
- the next gate is fresh Firefox activation of runtime `v11-scroll-v5-delivery-v4`
- live proof must show idle wait occurs before composer injection when ChatGPT is busy/interrupted
- once idle, send-readiness waiting may occur without consuming retry budget
- successful delivery must complete without manual intervention or duplicate result posting


## INCIDENT — Pre-existing relay-result draft survived V4 activation

Screenshot after Action `PC-ENGINEER-RELAY-182-VERIFY-V0313-DELIVERY-V4-ACTIVATION` showed a relay-owned draft still present in the ChatGPT composer while the page displayed `Connection interrupted. Waiting for the complete answer`.

Important distinction from the Action 179 incident:
- the visible composer payload was Action 181's result
- Action 181 was returned through the previously-live delivery-v3 bridge before the deferred V4 activation completed
- the V4 extension/document reload preserved the already-populated ChatGPT draft
- V4 then started successfully, but had no startup recovery path for a relay-result payload that predated the new content-script instance

Confirmed architectural gap:
- result-delivery state is serialized only per action ID in memory
- a relay-owned composer draft can outlive the content-script instance that created it
- startup recovery restores attempted IDs and scans historical conversation turns, but does not adopt or recover a currently populated `[GPT_WINDOWS_RESULT]` draft
- newer relay actions can therefore coexist with an unresolved older relay draft

Required fix:
- detect relay-owned `[GPT_WINDOWS_RESULT]` drafts in the composer on startup and before executing a new packet
- parse the draft packet ID
- if that packet is already visible as a user result, clear only the relay-owned stale draft and mark it attempted
- if it is not yet delivered, wait for ChatGPT idle and recover/send that exact existing draft before allowing any newer relay command to execute
- introduce a global relay-operation/delivery lock so different packet IDs cannot concurrently own the composer
- never overwrite a different relay-owned draft with a newer result
- emit draft-detected/recovered/cleared/deferred telemetry

Classification:
- reliability/autonomy incident
- distinct root cause from V3's pre-injection ordering defect
- no evidence of duplicate Windows execution


## Delivery-v5 design — relay draft recovery and serialized ownership

Implemented after the post-V4 screenshot showed Action 181's relay result draft surviving the extension/document reload.

Delivery-v5 / extension 0.3.14 adds:
- `relayDraftFromComposer()` to identify relay-owned `[GPT_WINDOWS_RESULT]` drafts and packet IDs
- `clearOwnedRelayDraft(packetId)` to safely remove only relay-owned stale drafts
- `recoverExistingRelayDraft()` for startup/periodic recovery
- global `activeRelayOperationId` ownership
- `run(p)` defers newer packets before backend execution when another relay draft exists
- `run(p)` also defers different packet IDs while an operation owner is active
- startup draft recovery begins before normal assistant-command recovery
- delivery failure with an owned draft keeps that packet as owner and schedules draft recovery instead of allowing a newer action to overwrite the composer

New telemetry:
- `relay_result_draft_detected`
- `relay_result_draft_cleared`
- `relay_result_draft_recovered`
- `relay_result_draft_recovery_deferred`
- `relay_result_draft_deferred`
- `relay_action_deferred_for_existing_draft`
- `relay_action_deferred_for_active_operation`

Runtime identity: `v11-scroll-v5-delivery-v5`.

Goal:
- content-script/Firefox reloads may interrupt delivery, but they must never orphan a relay result in the composer or allow a later packet to collide with it.


## v0.3.14 delivery-v5 staging + deferred activation scheduled — GREEN

Action `PC-ENGINEER-RELAY-183-STAGE-AND-ACTIVATE-V0314-DELIVERY-V5` completed successfully.

Observed staging proof:
- full browser contract suite GREEN
- V11_STAGED=True
- STABLE_MAIN_STAGED=True
- CODEBLOCK_PARSER_STAGED=True
- CURRENT_ROLE_SELECTORS_STAGED=True
- HANDOFF_SCROLL_V5_STAGED=True
- SCROLL_TELEMETRY_V5_STAGED=True
- WORKER_DRIVEN_SCROLL_STAGED=True
- TRUE_CONTENT_START_TELEMETRY_STAGED=True
- RESULT_DELIVERY_RECOVERY_STAGED=True
- RESULT_ANTISPAM_V2_STAGED=True
- SEND_READINESS_GATE_STAGED=True
- PREINJECTION_IDLE_GATE_STAGED=True
- RELAY_DRAFT_RECOVERY_STAGED=True
- RUNTIME_IDENTITY_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- XPI built as `gpt-windows-relay-0.3.14.xpi`
- SYNC_LIVE=GREEN
- DELIVERY_V5_V0314_STAGED=GREEN
- deferred activation task created and started for runtime `v11-scroll-v5-delivery-v5`

Next gate:
- confirm the deferred helper completed
- confirm a fresh `content_script_started` event for delivery-v5
- inspect draft-detection/recovery/clear telemetry after activation
- verify newer packet execution was deferred whenever an older relay draft owned the composer


## Delivery-v5 post-activation proof — normal path GREEN, startup draft branch unexercised

Actions 184-187 isolated telemetry strictly after the first true `v11-scroll-v5-delivery-v5` content-script start.

Confirmed normal-path behavior:
- Action 184: result received -> idle wait -> idle ready -> send wait -> send ready -> one click -> send confirmed -> delivery complete
- Action 185: same successful sequence
- no post-V5 result activity for historical Actions 181, 182, or 183
- no duplicate-result spam
- no manual intervention reported for these deliveries

Important limitation:
- `POST_V5_DRAFT_DETECTED=False`
- `POST_V5_DRAFT_RESOLVED=False`
- `POST_V5_OWNERSHIP_DEFER_COUNT=0`
- therefore the new startup draft-recovery/ownership-deferral branch is implemented and regression-tested, but was not naturally exercised in this live post-V5 window

Status:
- normal delivery-v5 pipeline: LIVE PROOF GREEN
- anti-spam behavior: still GREEN
- pre-injection idle ordering: LIVE PROOF GREEN
- send-readiness gate: LIVE PROOF GREEN
- startup orphaned-draft recovery branch: NOT YET LIVE-EXERCISED
- do not claim that branch proven until a real or deliberately controlled draft-survival event occurs

Next priority:
- resume the original P0 V5 scroll/bottom-follow proof now that delivery stability is no longer contaminating the measurement loop.


## V5 scroll live proof — reaches bottom transiently but fails retention

Action `PC-ENGINEER-RELAY-189-READ-V5-SCROLL-FINAL-VERDICT` measured the clean delivery-v5 result cycle for Action 187.

Observed:
- TARGET_CONFIRMED=True
- TARGET_COMPLETE=True
- SCROLL_START_COUNT=1
- SCROLL_TICK_COUNT=10
- SCROLL_END_COUNT=1
- start root: `div.thread-scroll-container.overflow-x-hidden.overflow-y-auto`
- start anchor: `div.ProseMirror.ProseMirror-focused`
- start before distance: 7719 px
- start after forced scroll: 7579 px
- minimum tick distance: 0 px
- last tick distance: 8383 px
- end distance: 8384 px
- end near_bottom=False
- V5_SCROLL_LIVE_PROOF=FAILED

Interpretation:
- V5 is capable of reaching the bottom at least transiently; this is no longer a basic 'cannot scroll' failure
- the remaining defect is bottom retention during subsequent ChatGPT DOM growth, anchoring, virtualization, or root/anchor changes
- because the distance later jumps from 0 to ~8.3k px despite the active handoff loop, the next forensic step must inspect every tick's root/anchor/distance/timestamp rather than redesigning blindly
- P0 scroll remains OPEN


## V5 scroll root-cause correction — false bottom on composer wrapper

Action `PC-ENGINEER-RELAY-192-READ-V5-SCROLL-JUMP-SUMMARY` isolated the apparent bottom hit from the Action 187 handoff trace.

Observed transition:
- ticks before the apparent bottom used root `div.thread-scroll-container.overflow-x-hidden.overflow-y-auto` and remained ~7605 px from bottom
- the one tick reporting distance 0 switched root to `div.text-size-chat...pe-10`, a composer-adjacent wrapper
- the anchor remained `div.ProseMirror.ProseMirror-focused`
- the very next tick reacquired `div.thread-scroll-container...` and reported ~8383 px from bottom
- distinct roots therefore included both the real thread scroller and the composer wrapper

Corrected interpretation:
- V5 did **not** reach the real conversation bottom and then lose it
- the zero-distance sample was a false success measured against the wrong root
- `findScrollRoot(anchor)` is unsafe when the anchor is the composer because it selects the nearest scrollable ancestor and may promote a composer wrapper
- `newestConversationEdge()` is also falling back to the ProseMirror composer instead of a conversation turn in this live ChatGPT DOM

P0 remains OPEN.

Next forensic/fix direction:
- pin handoff scrolling to the real conversation/thread scroller rather than the nearest composer ancestor
- stop using the composer itself as the preferred conversation-edge anchor
- inspect whether ChatGPT exposes a native accessible 'scroll to bottom' control and prefer that native mechanism if available


## Scroll-v6 design decision — pin thread root, remove composer fallback

Action 193 inspected Firefox's live accessibility tree for a native ChatGPT viewport-bottom control. No usable ChatGPT scroll-to-bottom control was exposed. The relevant live ChatGPT control was `Stop`; unrelated page-content buttons such as `Follow The Latest` were also present but are not viewport controls.

Action 192 already proved the V5 false-bottom mechanism:
- real root: `div.thread-scroll-container.overflow-x-hidden.overflow-y-auto`
- false-zero root: composer-adjacent `div.text-size-chat...pe-10`
- anchor remained `div.ProseMirror.ProseMirror-focused`

V6 implementation decision:
- prefer/pin ChatGPT's explicit `.thread-scroll-container` as the relay handoff root
- never use the composer as `newestConversationEdge()` fallback
- use explicit conversation role/turn nodes or the already-watched assistant unit as optional anchors
- keep direct `scrollTo` + `scrollTop` reinforcement and existing bounded 8-second handoff semantics
- retain manual-scroll authority after the relay handoff window
- emit a new runtime identity `v11-scroll-v6-delivery-v5` so live proof cannot be confused with V5

This is a targeted P0 correction; delivery-v5 semantics remain unchanged.


## Action 194 launcher failure — relay PATH omits Git

Action `PC-ENGINEER-RELAY-194-IMPLEMENT-SCROLL-V6-STABLE-THREAD-ROOT` failed before touching repository state.

Root cause isolated by Actions 195-196:
- canonical repo exists and contains `.git`
- `shutil.which('git') == None` inside the relay-launched Python process
- Git is installed at `C:\Program Files\Git\cmd\git.exe` and `C:\Program Files\Git\bin\git.exe`
- the relay process PATH omits Git's install directories
- failure was `FileNotFoundError: [WinError 2]` on the first subprocess launch of `git pull`

Engineering consequence:
- relay-side automation must not assume interactive-user PATH contents
- repository automation should resolve or pin Git explicitly until relay environment bootstrap includes it
- no V6 source modification occurred in Action 194 before failure


## Action 197 partial V6 worktree — patch present, version assertion failed

Action `PC-ENGINEER-RELAY-197-IMPLEMENT-SCROLL-V6-WITH-PINNED-GIT` successfully:
- resolved Git via explicit `C:\Program Files\Git\cmd\git.exe`
- fast-forwarded the local clone to `c0c4fe8bbd27991e666ca056ce5b6cf19e2a7dba`
- applied the V6 root-pin/runtime/test/sync edits locally

It then stopped on the version-bump precondition:
- `EXPECTED_0314_NOT_FOUND=windows-relay/extension/manifest.json`

Action 198 audited the partially modified checkout before any retry:
- dirty files are limited to:
  - `windows-relay/content.js`
  - `windows-relay/extension/content.js`
  - `windows-relay/extension-persistent/content.js`
  - `windows-relay/sync-live.py`
  - `windows-relay/tests/test_browser_contract.py`
- V6 markers are present in all intended source/test/sync files
- `GPT_WINDOWS_SCROLL_ROOT_PIN_V1=True`
- handoff/telemetry V6 markers present
- runtime identity `v11-scroll-v6-delivery-v5` present
- old composer-edge fallback absent
- persistent manifest and XPI builder still report `0.3.14`
- `windows-relay/extension/manifest.json` exists but the simple UTF-8 regex scan found no `0.3.x` version token, so its exact representation/encoding must be inspected before resuming

No commit or push of the V6 source patch has occurred yet. Resume must be idempotent and preserve the verified partial edits.


## Manifest version divergence discovered during V6 recovery

Action `PC-ENGINEER-RELAY-199-INSPECT-EXTENSION-MANIFEST-REPRESENTATION` proved that `windows-relay/extension/manifest.json` is valid UTF-8 JSON and currently declares version `0.1.1`.

This differs from:
- `windows-relay/extension-persistent/manifest.json`: `0.3.14`
- `windows-relay/build-extension-xpi.ps1`: `0.3.14`

Therefore Action 197's assumption that all extension manifests should already contain `0.3.14` was incorrect. Before changing the temporary/live-source manifest, the build/sync scripts must be inspected to determine whether the `0.1.1` manifest is intentionally versioned independently or is stale.

The partial V6 code/test/sync edits remain local and uncommitted.


## Extension version ownership clarified

Actions 199-201 plus direct inspection of `sync-live.py` established the extension version ownership model:

- `windows-relay/extension/manifest.json` is the temporary/live-source manifest and currently declares `0.1.1`
- `windows-relay/extension-persistent/manifest.json` is the packaged extension manifest and currently declares `0.3.14`
- `build-extension-xpi.ps1` packages `extension-persistent`
- `sync-live.py::build_xpi()` explicitly reads `live/extension-persistent/manifest.json`, parses its `version`, and names the XPI from that value

Therefore the V6 release bump must:
- leave the temporary `extension/manifest.json` version untouched
- bump `extension-persistent/manifest.json` from 0.3.14 to 0.3.15
- update the builder's default XPI filename from 0.3.14 to 0.3.15

This replaces the incorrect all-manifests-same-version assumption that stopped Action 197.


## Scroll-v6 one-shot deferred by PC Engineer 3

The Director authorized one final contained attempt at scroll-v6, then instructed engineering to move on. The V6 experiment and test output were preserved under `%LOCALAPPDATA%\GPTWindowsRelay\engineering-backups\scroll-v6-*`. The full suite remained non-green after correcting the stale `anchor.scrollIntoView()` assertion, so scroll work was deferred without further redesign. The canonical worktree was restored to the last committed baseline and engineering priority moved to P1 Windows HUD.


## P1 Windows HUD MVP source implementation

Added a dependency-free Python/Tkinter HUD with backend ONLINE/OFFLINE + ARMED/DISARMED state, pause-sentinel visibility, telemetry-derived Firefox bridge/content runtime state, current/last relay action, compact error display, and live Arm/Disarm controls. Browser state is intentionally labeled ACTIVE/SEEN/STALE/UNKNOWN from telemetry age rather than falsely claiming connectivity. Added `--once` JSON diagnostics, singleton protection, HUD tests, START-HUD.bat, and sync-live inclusion. Full relay regression suite passed before commit.


## P1 Windows HUD MVP live proof — GREEN

The committed HUD was staged through `sync-live.py`, which reran the live relay regression suite and completed successfully. `hud.py --once` returned a valid live snapshot with backend health/ARMED state plus telemetry-derived browser state. The Tkinter HUD was then launched detached with the live relay virtualenv and its process remained alive after launch. P1 MVP therefore has source, tests, live staging, machine-readable state proof, and a running GUI process.


## INCIDENT — stale Action 215 result delivered after Action 216 was issued

After PC Engineer 3 issued Action 216, ChatGPT received Action 215 again instead of the new action result. The Director had to surface the stale duplicate manually. Classification: HUMAN-INVOLVED AUTONOMY INCIDENT. Root cause remains unresolved pending state/result/browser-event evidence; do not assume backend re-execution.


## AUDIT — PC Engineer 3 operations 215–219

- 215 proved Action 214 itself completed successfully; the delayed self-kill interrupted relay state after completion, so 214 was a flawed lifecycle-test design rather than a filesystem-permission failure.
- 216 was issued but never reached the Windows backend.
- 217 proved 216 had no state entry/result file and logged the stale-215 human-intervention incident.
- 218 exposed overlapping delivery telemetry: an older packet could still be sending while a newer packet entered delivery.
- 219 found zero new content-script starts in the incident window but repeated Port reconnects, and showed normal result delivery plus same-packet draft recovery running concurrently.

Root cause: `recoverExistingRelayDraft()` can adopt a composer draft for packet X while X is already present in the in-memory `inflight` set under normal `injectConfirmed()` delivery. Because the active-operation guard only rejects a *different* packet ID, two send owners can race for the same packet. Corrective invariant: draft recovery must defer while `inflight.has(draft.id)` and may adopt the draft only after normal delivery relinquishes ownership.


## AUDIT — PC Engineer 3 operations 220–224

- 220 fixed the confirmed delivery-v5 ownership race by preventing draft recovery from adopting the same packet while normal delivery remains in `inflight`; runtime identity advanced to `v11-scroll-v5-delivery-v6`; tests passed and commit `f1e4acc7` was pushed.
- 221 staged delivery-v6 into the live relay, rebuilt persistent XPI 0.3.15, and confirmed the active Firefox content script was still delivery-v5, establishing a clean activation boundary.
- 222 extracted the staged/live proof and confirmed the old runtime remained active.
- 223 recovered the historical fact that Task Scheduler had previously provided a successful post-result Firefox activation boundary.
- 224 narrowed historical evidence further but did not recover the exact helper payload.

Current gate: recover/reconstruct the proven Task Scheduler activation helper, activate delivery-v6 without user interaction, and require fresh `content_script_started` telemetry before lifecycle testing continues.


## AUDIT — PC Engineer 3 operations 225–229

- 225 wrote the 220–224 audit and confirmed Task Scheduler as the proven post-result ownership boundary for Firefox lifecycle work.
- 226 narrowed activation discovery to executable/local artifacts.
- 227 recovered the historical 157–160 proof: scheduled activation, live temporary-extension Reload, ChatGPT tab selection/document reload, and fresh runtime telemetry.
- 228 confirmed the original helper script was no longer available as a clean reusable artifact.
- 229 reconstructed the proven activation sequence as a self-logging fail-closed Task Scheduler helper targeting the live `Client\Relay\extension` temporary extension.

Operation 230 verifies the reconstructed helper using fresh `content_script_started` telemetry before lifecycle testing resumes.


## AUDIT — PC Engineer 3 operations 230–234

- 230 verified the first reconstructed activation helper and rejected activation: helper failed and no fresh delivery-v6 content runtime appeared.
- 231 exposed a false-positive UIA target: conversation text containing the historical live-extension path was mistaken for the about:debugging card.
- 232 cleanly established `HELPER_GREEN=False`, `FRESH_DELIVERY_V6_START_COUNT=0`, and `RELAY_RELOAD_BUTTON_NOT_FOUND`; historical marker strings embedded in the false match were explicitly treated as untrustworthy.
- 233 scheduled a non-mutating about:debugging UI Automation structure probe.
- 234 verifier hit a transient output-file sharing race while the scheduled probe still owned the file; this was a verifier synchronization defect, not an extension/UIA verdict.


## AUDIT — PC Engineer 3 operations 235–239

- 235 synchronized on scheduled-task exit and proved the about:debugging structure probe GREEN.
- 236 showed Firefox accessibility includes browser chrome and background-tab content, so global text/Reload matching is unsafe.
- 237 added visibility, geometry, and Document-ancestor telemetry without mutating the extension.
- 238 identified the real visible `GPT Windows Relay` temporary-extension card as a `ControlType.ListItem` inside the `Debugging - Runtime / this-firefox` document, containing the exact live extension location and extension metadata.
- 239 established the safe activation ownership boundary: bind the exact visible relay ListItem first, then search only its descendants for the Reload button.


## P2 backend-only restart recovery — GREEN

Action 242 armed a Task Scheduler helper that was forbidden to kill the relay until browser telemetry recorded `relay_result_delivery_complete` for Action 242. The browser confirmed delivery at 2026-10-03T08:11:54Z. The helper then terminated listener PID 8472; the supervisor/watchdog restored listener PID 14312 approximately three seconds later. Action 243 subsequently reached the recovered backend through the still-loaded delivery-v6 Firefox extension. No content-script restart, extension reload, re-pair, re-arm, or user rescue occurred.

The helper's unauthenticated `/status` request returned HTTP 401; this is not a recovery failure because the port was live and the authenticated relay action path immediately succeeded with Action 243.


## AUDIT — PC Engineer 3 operations 240–244

- 240 scheduled structurally bound activation using the exact visible GPT Windows Relay temporary-extension ListItem and its sole descendant Reload button.
- 241 proved delivery-v6 truly active with helper GREEN, one card-scoped Reload, ChatGPT document reload, and fresh `content_script_started` telemetry carrying `v11-scroll-v5-delivery-v6`.
- 242 armed a backend restart helper gated on browser `relay_result_delivery_complete` for that exact packet.
- 243 proved backend-only lifecycle recovery end to end: PID 8472 was replaced by PID 14312 and the next browser action reached the recovered backend without browser lifecycle intervention.
- 244 records the proof, updates the P2 checklist, and inspects signed persistent-extension readiness before any destructive Firefox restart.


## P2 signed persistent-extension gate — external prerequisite

Action 244 confirmed the backend-only restart path is GREEN, but full Firefox restart and Windows/login restart cannot be safely validated yet. No `gpt-windows-relay-signed.xpi` exists in the repo or live tree, no Mozilla Firefox enterprise policy is installed under HKLM/HKCU, and no persistent `gpt-windows-relay@local` registration was found in the active Firefox profile. The currently working relay is a development-only temporary add-on, which Firefox removes on full restart.

Therefore full Firefox/Windows restart validation is explicitly gated on Mozilla unlisted signing plus persistent policy installation. Do not destroy the live temporary add-on merely to demonstrate the known failure mode. Continue non-blocked roadmap work while this external prerequisite remains unresolved.


## P3 clipboard read/write primitives — GREEN

Added dependency-free native Win32 Unicode clipboard primitives in `windows-relay/windows_tools.py`: explicit read, write, and clear operations with bounded OpenClipboard retry behavior. Full relay tests passed, `sync-live.py` staged the adapter into the live relay tree, and an explicit Unicode round-trip succeeded. The pre-existing clipboard text was restored after the proof.


## P3 semantic target-field text entry — GREEN

Actions 246–252 added and live-proved fail-closed semantic Windows UI Automation text entry. WinForms was rejected as a proof target because its TextBox surfaced as `ControlType.Pane` without `ValuePattern`; no unsafe fallback was added. A WPF harness exposed exactly one visible enabled `ControlType.Edit` with Name `Application Answer`, AutomationId `application_answer`, and `ValuePattern=True`. Action 251 then exposed one implementation defect: PowerShell requires the variable passed by `[ref]` to exist before `TryGetCurrentPattern`, so `[ref]$pattern` failed because `$pattern` was undeclared. Action 252 initializes `$pattern=$null`, adds regression coverage for that requirement, re-stages the live primitive, successfully sets the Unicode value using `ValuePattern.SetValue`, and verifies exact read-back.


## AUDIT — PC Engineer 3 operations 250–252

- 250 proved the WinForms TextBox compatibility boundary: it surfaced as a Pane and provided no ValuePattern.
- 251 proved the WPF harness exposes the intended semantic UIA contract and isolated the remaining failure to an undeclared PowerShell `[ref]` variable.
- 252 repaired that defect, added regression coverage, re-staged live, and completed exact semantic field-entry/read-back proof.


## P3 resume-data representation and deterministic lookup — GREEN

Added `resume_profile.py` with schema versioning, local JSON loading/validation, normalized exact aliases for common factual application fields, exact normalized custom-field lookup, and an explicit `needs_reasoning` path for unmapped questions. The default representation covers identity/contact/links, work authorization, experience, education, certifications, skills, availability, and custom factual fields; it does not commit any real resume data. Unknown prompts are never guessed: they return structured resume context for higher-level reasoning. Full relay tests and live staging passed, and a synthetic local profile proved deterministic aliases, valid False booleans, custom lookup, and the reasoning handoff.


## AUDIT — PC Engineer 3 operations 250–254

- 250 proved the disposable WinForms field surfaced as `ControlType.Pane` without `ValuePattern`, establishing that it was an unsuitable semantic text-entry proof target.
- 251 proved the WPF harness exposed exactly one visible enabled Edit with the expected Name/AutomationId and `ValuePattern=True`; the remaining defect was an undeclared PowerShell variable passed by `[ref]`.
- 252 initialized `$pattern=$null`, added regression coverage, re-staged live, completed exact semantic field write/read-back proof, and pushed commit `169a9a1`.
- 253 was issued for the resume-data foundation, but the user received a stale duplicate result for Action 252 instead.
- 254 proved Action 253 never reached the Windows backend: no saved 253 result exists and no backend state entry was present.


## INCIDENT — stale Action 252 delivered instead of issued Action 253

User-visible symptom: after Action 253 was issued, the browser submitted the previously completed Action 252 result again. Action 254 proved Action 253 had no backend result and therefore did not execute. This is a browser-side continuity incident and required user-visible rescue.

Action 256 provisional classification was `CONFIRMED_DEFERRED_PACKET_LOST_NO_QUEUE`; Action 257 superseded the permanent-loss portion of that conclusion because Action 253 later executed successfully and pushed commit `56aa655`. The confirmed failure mode is delayed/out-of-order execution while an older result retains browser delivery ownership.


## INCIDENT — Action 255 diagnostic syntax error

Action 255 failed before execution because the generated Python diagnostic omitted a closing parenthesis in a `print()` statement. No repo mutation occurred. This was an avoidable assistant-authored relay-command defect; Action 256 reruns the intended diagnostic with corrected syntax.


## Delivery-v7 root cause and staged repair

The 252→253 incident showed that Action 252 was submitted once, but delivery confirmation timed out even though its composer payload was no longer present. While ChatGPT generated the next assistant turn, the old result retained `activeRelayOperationId`, waited for generation to stop, and later retried the already-submitted 252 result. Action 253 was consequently delayed and eventually executed out of order rather than being permanently lost.

Delivery-v7 adds two narrow safeguards: (1) after the existing pre-send idle gate, a cleared relay payload plus the appearance of the ChatGPT generation stop control is treated as positive acknowledgement that the send was accepted (`method:generation_started`); and (2) packets encountered while a draft or another operation owns the channel are stored in a bounded 16-entry deferred-action queue and explicitly drained when ownership is released. This removes dependence on a later DOM recovery scan for deferred command survival.


## AUDIT — PC Engineer 3 operations 255–259

- 255 failed before execution due to an assistant-authored Python syntax error; no repo mutation occurred.
- 256 reran the diagnostic, committed the then-provisional deferred-packet incident classification, and exposed the long 252 delivery retry interval.
- 257 proved Action 253 eventually executed successfully, changing the diagnosis from permanent loss to delayed/out-of-order execution.
- 258 compact state-machine probe backend-result presence at Action 259 time: `True`.
- 259 stages delivery-v7 with generation-start acknowledgement and a bounded explicit deferred-action queue, plus regression tests and package version 0.3.16.


## Backend atomic persistence transient-lock hardening

Action 262 reached the v7 browser/backend path but returned HTTP `PermissionError` before a normal relay result was persisted. Actions 263–264 localized the failure to backend persistence: the result directory was writable, Action 262 had no saved result, its state later appeared as `INFLIGHT`, and a stranded `.state.json.*` temporary file existed. Harmless atomic replace probes subsequently succeeded, establishing a transient Windows file-lock/replace failure rather than a persistent ACL denial.

The backend now retries transient `PermissionError`/Windows sharing violations during atomic `os.replace` with bounded exponential backoff. State mutations also snapshot and roll back in-memory state when persistence fails, preventing a failed reservation/mark from later becoming a ghost record during an unrelated successful save. Failure-injection tests cover both behaviors. Action 262 is not re-executed because its exact execution boundary is not sufficiently proven; the scheduled backend restart will conservatively convert the stale `INFLIGHT` reservation to `INTERRUPTED_RESTART`.


## AUDIT — PC Engineer 3 operations 260–264

- 260 armed the proven structurally bound Firefox activation helper behind an exact result-delivery gate.
- 261 proved delivery-v7 live with fresh `v11-scroll-v5-delivery-v7` content telemetry and both v7 markers present.
- 262 reached the backend promptly but returned a raw `PermissionError`, revealing a separate backend persistence defect rather than the old browser starvation path.
- 263 ruled out result-directory ACL failure and showed no persisted Action 262 result.
- 264 showed Action 262 as stale `INFLIGHT`, found an abandoned `.state.json.*` atomic-write temp file, and proved atomic create/replace currently succeeds in both state and result directories.


## Hardened backend activation + delivery-v7 handoff proof — GREEN

Action 265 staged and committed transient-lock persistence hardening, then armed a backend restart only after browser delivery completion. Action 266 reached the replacement backend, proving browser-to-backend continuity. The helper replaced listener PID 14312 with 8800, the live backend contains atomic replace retry and state rollback safeguards, and stale Action 262 was conservatively reconciled to `INTERRUPTED_RESTART` without re-execution.

The same 265→266 transition provides the renewed delivery-v7 regression: Action 265 was confirmed by `generation_started`, produced zero send retries and zero long idle waits, and Action 266 reached the backend without draft/active-owner deferral. The stale-owner/out-of-order behavior observed at 252→253 did not recur.


## INCIDENT — Action 267 live-proof import harness defect

Action 267 created the P3 helper, passed the full source test suite, and staged it live, but its synthetic live-proof harness loaded `job_application_helper.py` with `importlib.util.spec_from_file_location` without adding the live relay directory to `sys.path`. The helper therefore could not resolve sibling module `resume_profile` and the operation stopped before any P3 commit or real application interaction. Action 268 corrected only the proof harness by reproducing normal script module resolution; no product fallback or path hack was added.


## P3 simple difficult-job-application loop — GREEN

Added `job_application_helper.py` as a small orchestration layer over the proven clipboard, resume-profile, and semantic UIA primitives. Exact factual fields resolve deterministically; mapped-but-empty facts stop as `missing_profile_data`; subjective or unmapped prompts return a structured `needs_reasoning` packet with copied application context, local profile context, and explicit no-invention constraints. Only a separate explicit apply step can write an answer to a semantically identified field.

The live proof used synthetic data only: clipboard text `E-mail address` resolved to `ada@example.invalid` and was written/read back through a disposable WPF field; a subjective `Why do you want to work here?` prompt stopped at `needs_reasoning` without generating or applying an answer. The original clipboard was restored and all synthetic proof artifacts were removed. P3 is complete.


## INCIDENT — Action 269 screenshot bitmap constructor parsing defect

Action 269 passed the source test suite and staged the initial P4 capture implementation, but its synthetic window proof failed before image creation because PowerShell `New-Object System.Drawing.Bitmap $w,$h,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb` parsed the enum expression as a string. No normal desktop capture occurred. Action 270 replaced that expression with the direct .NET constructor `[System.Drawing.Bitmap]::new(...)`; no fallback capture mechanism was introduced.


## P4 screenshot capture + bounded storage foundation — GREEN

Added an explicit on-request PNG capture primitive supporting the Windows virtual screen, one exact visible top-level window (optionally PID constrained), or an explicit rectangle. Captures are written only to `%LOCALAPPDATA%\GPTWindowsRelay\screenshots`; default retention is at most 20 PNG files and 24 hours, enforced during capture, with no background timer or continuous feed. Results include target bounds, MIME type, byte count, SHA-256, managed path, and retention status. Action 270 proved exact-window capture against a disposable synthetic WPF window and deleted the proof PNG afterward. The remaining P4 item is the return path suitable for ChatGPT visual inspection.


## AUDIT — PC Engineer 3 operations 265–269

- 265 added transient atomic-replace retry plus state rollback and armed the post-delivery backend restart.
- 266 proved hardened backend activation and delivery-v7 handoff GREEN; stale 262 was reconciled as `INTERRUPTED_RESTART` without re-execution.
- 267 built the P3 job helper but its live-proof import harness failed before commit.
- 268 corrected only the proof-loader issue, completed synthetic deterministic-field + reasoning-stop proof, and closed P3 at `9f08e395`.
- 269 staged P4 capture/retention but exposed a PowerShell bitmap-constructor parsing defect during the synthetic-window proof; no ordinary desktop image was captured.


## Delivery-v8 screenshot transport regression suite — GREEN

Actions 271–274 exposed only browser-contract test drift while staging the screenshot return path. Six tests still searched for the v7 function signature after `injectConfirmed` gained an attachment parameter, and one additional assertion still searched for the old two-argument call site. Action 275 updates that final stale assertion to the v8 call `injectConfirmed(r.result,p.id,r.attachments||[])`; the complete Windows relay test suite is GREEN and the source has been synchronized to the live tree. No backend restart or Firefox content-runtime reload has occurred yet, so delivery-v8 is staged but not activated.


## AUDIT — PC Engineer 3 operations 270–274

- 270 corrected the PowerShell bitmap constructor, proved exact-window PNG capture live against a disposable WPF window, deleted the proof image, and committed bounded P4 capture/retention at `a864cb72`.
- 271 staged the authenticated one-shot screenshot return architecture but stopped before commit when legacy browser-contract tests failed.
- 272 showed the failing tests were stale source-boundary assertions after the deliberate v8 `injectConfirmed(...,attachments=[])` extension; v8 implementation markers were present.
- 273 updated six legacy signature searches, then stopped because one separate assertion still expected the old two-argument `injectConfirmed` call.
- 274 isolated that sole remaining failure exactly; no additional implementation defect was demonstrated.


## AUDIT — PC Engineer 3 operations 280–284

- 280 enumerated Firefox UIA tab identities and established exact visible browser-tab names for `Debugging - Runtime / this-firefox` and `PC Engineering 3`.
- 281 armed a structural Firefox-only activation helper, but the generated PowerShell contained a syntax defect and therefore never entered its helper body.
- 282 correctly detected that no `HELPER_STARTED` record or fresh v8 telemetry existed; Firefox remained unchanged.
- 283 attempted a read-only PowerShell parser probe, but the probe itself supplied the parser path incorrectly and did not resolve the helper syntax failure.
- 284 corrected the parser invocation and localized the actual Action 281 helper defect to line 25: a nested `New-Object PropertyCondition(...)` expression inside `FindAll(...)` was missing a closing parenthesis.


## INCIDENT — Action 281 activation helper syntax defect

The Action 281 scheduled helper never executed because of an assistant-authored PowerShell syntax error in the ListItem condition used for extension-card discovery. Task Scheduler returned exit code 1 before `HELPER_STARTED`, so no Firefox selection, extension reload, or ChatGPT refresh occurred. Action 285 replaces the nested expression with a separately constructed UI Automation condition and parser-validates the complete helper before scheduling it.


## Delivery-v8 full backend + Firefox activation — GREEN

Action 285 parser-validated the corrected structural Firefox activation helper before scheduling it. After exact Action 285 browser delivery, the helper bound the single visible Firefox `MozillaWindowClass`, selected the exact existing `Debugging - Runtime / this-firefox` tab, matched one `GPT Windows Relay` extension card using relay identity plus the live extension path and extension metadata, invoked its single card-scoped Reload control, selected the unique `PC Engineering 3` tab, refreshed it, and observed a fresh `v11-scroll-v5-delivery-v8` content-script start. Together with the already-live replacement backend from Action 276, delivery-v8 is now active across both boundaries. The final P4 gate is one end-to-end synthetic managed PNG attachment returned through ChatGPT and deleted only after confirmed delivery.


## P4 screenshot-on-request capability — COMPLETE GREEN

Action 287 completed the first true end-to-end screenshot return. A disposable topmost WPF window containing only synthetic proof text was captured through the live exact-window screenshot primitive. The action result advertised one managed PNG, delivery-v8 fetched that PNG through the authenticated basename-only backend route, the content script attached it to the ChatGPT composer, and the image arrived visibly in the same user result turn. Action 288 verified `relay_attachment_attached` telemetry before/at result delivery, zero send retries, confirmed result delivery, and deletion of the managed local PNG after delivery. No ordinary desktop image was used.

P4 is complete: explicit screen/window/region capture, bounded 20-file/24-hour managed storage, authenticated one-shot return suitable for ChatGPT visual inspection, and post-delivery cleanup are all live and proven. Continuous screenshot capture remains absent by design.


## AUDIT — PC Engineer 3 operations 285–288

- 285 parser-validated and armed the corrected structural Firefox v8 activation helper behind an exact result-delivery gate.
- 286 proved full backend + Firefox delivery-v8 activation GREEN with fresh `v11-scroll-v5-delivery-v8` telemetry.
- 287 captured a disposable synthetic WPF window and returned its managed PNG as an actual ChatGPT image attachment through delivery-v8.
- 288 verifies attachment telemetry, delivery ordering, zero retry behavior, managed PNG cleanup, and closes all P4 task items.


## INCIDENT — Action 289 orchestration helper returned None

Action 289 failed immediately after a read-only `git status --porcelain`. Its assistant-authored Python `q()` helper placed `return p` on the same semicolon-controlled line as the error branch, so successful commands returned `None` and the operation raised `AttributeError` before any repository or live-tree mutation. Action 290 replaces the helper with an unconditional return path.


## P5 semantic UI Automation control adapter v1 — STAGED

Action 290 begins P5 by extending the existing exact-window UI Automation model rather than adding coordinate clicking. `windows_tools.py` gains bounded semantic inspection plus exact control InvokePattern, SelectionItemPattern, and desired-state TogglePattern operations. Mutating operations require a control type plus Name and/or AutomationId, reject ambiguous matches, require visible/enabled targets, and verify selection/toggle readback where a semantic state exists. The adapter contains no SendKeys path. `sync-live.py` now carries the new adapter script into the live tree.


## AUDIT — PC Engineer 3 operations 285–289

- 285 repaired and parser-validated the Firefox v8 activation helper.
- 286 proved backend + Firefox delivery-v8 activation GREEN.
- 287 completed the first true synthetic PNG return to ChatGPT.
- 288 verified attachment ordering, zero retries, post-delivery managed-file cleanup, and closed P4.
- 289 failed before mutation due to an assistant-authored Python orchestration return-path defect; only read-only git status executed.


## INCIDENT — Action 290 full-suite invocation used wrong working directory

Action 290 successfully compiled the P5 adapter and passed its focused seven-test contract suite. Its later full-suite invocation was launched from the repository root while supplying an absolute tests directory, so legacy tests using plain imports could not resolve `windows_relay`, `resume_profile`, or `job_application_helper`. Action 291 recovered the full saved stderr and proved all four failures were import-path errors from that invocation shape, not adapter regressions. Action 292 restores the canonical test working directory (`windows-relay`) before evaluating the staged implementation.


## P5 semantic UI Automation control adapter v1 — LIVE GREEN

Action 292 corrected the prior full-suite working-directory error, passed the complete source regression suite, synchronized the new adapter through `sync-live.py`, and passed the complete live-tree suite. A disposable WPF harness then proved bounded semantic Button inspection, exact AutomationId InvokePattern with application-side effect, desired-state CheckBox TogglePattern On→Off readback, exact ListItem SelectionItemPattern readback, and fail-closed refusal of an ambiguous duplicate-name Button match. No coordinate clicking or SendKeys path was used.


## P5 Firefox browser-tab adapter v1 — STAGED / SUPERSEDED BY LIVE PROOF

Action 293 established the semantic discriminator for real Firefox browser tabs: visible enabled `TabItem` controls whose immediate parent is the Firefox `ControlType.Tab` with `AutomationId=tabbrowser-tabs`. This excludes page-internal tab controls such as Gmail categories. Action 294 packages that rule into the first P5 app-specific adapter with exact/unique tab selection and SelectionItem readback; no coordinate or SendKeys fallback is used.


## INCIDENT — Action 294 cached dynamic Firefox tab title across tab switch

Action 294 staged and pushed Firefox tab adapter v1 after 98 source tests and a successful live-tree sync. Its first live selection of the exact debugging tab succeeded. The proof then attempted to return using the ChatGPT tab's previously cached exact accessible Name and the adapter refused with `FIREFOX_TAB_MATCH_COUNT_0`. The adapter therefore failed closed rather than guessing. Action 295 re-enumerated live browser tabs and recovered the unique ChatGPT tab using the stable semantic substring `PC Engineering 3`, proving that exact browser-tab names must be treated as dynamic across selection/title updates. Future workflow proofs must re-resolve or use an intentionally unique stable substring rather than cache an exact dynamic title.


## P5 Firefox browser-tab adapter v1 — LIVE GREEN

Action 296 completed the first app-specific P5 adapter proof against the active Firefox instance. The adapter enumerated only browser-level `TabItem` controls under Firefox `tabbrowser-tabs`, excluded page-internal Gmail tabs, selected the exact existing `Debugging - Runtime / this-firefox` browser tab with SelectionItem readback, re-enumerated after the switch, then returned to the unique `PC Engineering 3` tab using a stable semantic substring and verified selected-state readback. This closes the live proof without coordinate clicking, SendKeys, page-DOM guessing, or reuse of a stale dynamic exact tab title.


## AUDIT — PC Engineer 3 operations 290–294

- 290 staged the semantic UIA adapter and passed its focused contract suite, but the full-suite invocation used the wrong working directory and failed on legacy import resolution before live sync or commit.
- 291 recovered the full saved result and proved those failures were test-harness import-path errors rather than product regressions.
- 292 reran the suite from the canonical `windows-relay` working directory, passed 95 source tests and the full live-tree suite, then live-proved semantic inspect/invoke/toggle/select plus ambiguous-match refusal.
- 293 read the Firefox UIA hierarchy and established `tabbrowser-tabs` as the semantic boundary separating real browser tabs from page-internal tab controls.
- 294 implemented, tested, synced, committed, and partially live-proved Firefox tab adapter v1; exact debugging-tab selection succeeded, while returning with a cached exact ChatGPT tab title failed closed after that title changed dynamically.


## P5 workflow composition v1 — STAGED

Action 297 adds a deliberately small workflow runner over already-proven primitives. Workflow v1 accepts at most 32 prevalidated steps from a fixed operation allowlist: clipboard read/write/clear, semantic UIA field/control operations, Firefox browser-tab list/select, and explicit screenshot capture. It has no arbitrary shell, eval, coordinate click, templating, or implicit branching. Plans are validated completely before the first side effect, execution stops on the first failed step, and an explicitly declared window/region `fallback_screenshot` can return `needs_visual_reasoning` plus a ChatGPT image attachment rather than guessing the next interaction. Automatic full-screen fallback is intentionally disallowed.


## INCIDENT — Action 299 closeout verifier null-detail assumption

Action 299 was a read-only closeout verifier and failed before any repository mutation because its browser-event filter called `.get()` on event records whose `detail` field was explicitly null. Action 300 corrected the parser to normalize null/non-object detail values before packet filtering. The underlying Action 298 workflow result, visible ChatGPT image attachment, and managed-file lifecycle were unaffected.


## P5 workflow composition v1 — LIVE GREEN / P5 COMPLETE

Action 298 live-proved workflow composition across three already-proven adapters: clipboard write/read, Firefox browser-tab discovery/selection, and semantic UI Automation inspect/invoke. The success workflow completed all six ordered steps and produced the intended synthetic button side effect. A second workflow intentionally targeted two identically named buttons; semantic UIA refused the ambiguous mutation with `CONTROL_MATCH_COUNT_2`, the workflow stopped before the following clipboard step, and the explicitly declared exact-window screenshot fallback returned `needs_visual_reasoning` with a managed PNG attachment. The user-visible relay turn contained that synthetic image. Action 300 verified attachment telemetry preceded send confirmation and delivery completion, observed no send retry, and verified delivery-v8 deleted the managed PNG afterward. The original clipboard was restored.

P5 is complete: richer fail-closed semantic UIA primitives, a live Firefox app adapter, and a fixed-allowlist higher-level workflow layer with bounded visual fallback are all implemented and live-proven. The workflow language contains no arbitrary shell/eval execution, no implicit coordinate clicking, and stops on the first failed step rather than guessing.


## AUDIT — PC Engineer 3 operations 295–299

- 295 recovered the ChatGPT browser tab using fresh semantic substring resolution after 294 correctly refused a stale exact title.
- 296 completed the Firefox tab adapter live proof with structural browser-tab scoping, dynamic re-resolution, and selection readback.
- 297 implemented and staged workflow composition v1; focused workflow tests, the 103-test source suite, and live-tree synchronization all passed.
- 298 live-proved the normal clipboard + Firefox + semantic-UIA workflow and the fail-closed ambiguous-control path with exact-window screenshot fallback returned to ChatGPT.
- 299 attempted final telemetry/cleanup verification but its read-only parser assumed every event detail was an object; a null detail raised `AttributeError` before mutation.


## Native Python command_lines end-to-end validation — GREEN

Action 301 itself was delivered through the relay using `shell:"python"` plus `command_lines` and no `command`/`command_b64`. The executed program verified the canonical working directory, Unicode text, mixed quote/backslash punctuation, and embedded multiline string preservation before mutating project records. This proves native Python `command_lines` transport end to end through assistant packet parsing, browser bridge, localhost relay parsing, Python execution, result persistence, and browser result delivery.


## Roadmap reconciliation after P5 and command_lines proof

Action 302 reconciled the backlog against canonical Git history rather than stale V4-era checklist text. Commit `381b5416` establishes the contained scroll-V6 defer/revert; `7f1db855` establishes backend-only restart recovery; P1, P3, P4, and P5 completion commits are present; and Action 301 proved native Python `command_lines` end to end. The backlog now treats P0 as intentionally deferred, P2 as partially complete but externally gated by Mozilla signing, and P1/P3/P4/P5 as complete. The next actionable product milestone is obtaining/installing the signed persistent XPI so full Firefox and Windows/login restart recovery can be tested honestly.


## P2 signed persistent extension gate — local preflight prepared

Action 303 rebuilt and validated the current persistent extension package from `extension-persistent`, verified its manifest version/ID and exact package membership, inventoried Firefox/policy and local signing tooling without exposing credential values, and added `sign-extension.ps1`. The signing runner uses only environment-provided `WEB_EXT_API_KEY` / `WEB_EXT_API_SECRET`, invokes `web-ext sign` for the unlisted channel, and copies the produced artifact to the canonical `dist\gpt-windows-relay-signed.xpi`. The policy installer remains gated on that signed file and is parser-validated. No signing or policy installation is claimed unless an actual signed artifact is produced and verified.


## P2 local AMO signing toolchain — READY

Action 304 corrected the Action 303 preflight conclusion: AMO credentials were not the only missing prerequisite because Node/npm/npx/web-ext were also absent from the relay environment. Action 304 installed or discovered user-scope Node.js LTS without requesting elevation, verified native Node and npx execution, resolved `web-ext` through npx without contacting AMO for signing, and hardened `sign-extension.ps1` to locate user-scope/WinGet Node installations even when the long-running relay process has an older PATH. After this action, the local signing toolchain is executable; absent AMO API credentials are the remaining external authorization gate.


## P2 Mozilla AMO authorization boundary — classified

Action 305 opened the official AMO API-key page and Firefox redirected into Mozilla Accounts. Safe UI Automation inspection read only visible labels/control metadata and no field values, clipboard contents, passwords, JWT issuer values, or JWT secrets. Action 306 classifies the visible authorization state so the relay can stop exactly at the user-controlled authentication/authorization boundary rather than guessing or soliciting secret material through ChatGPT.

## 2026-10-03 — Human-intervention incident: visible relay packet produced no result
- The user had to report that the minimal relay packet was visible but produced no GPT_WINDOWS_RESULT/system response.
- Root cause in assistant rendering: opening Markdown fence contained metadata (`id="gfndkz"`) instead of being exactly three backticks.
- This counts as human intervention under the canonical incident policy because manual user diagnosis was required to continue an otherwise autonomous workflow.
- Correct contract: one assistant response containing visible prose header -> truly bare fence -> GPT_WINDOWS_ACTION envelope -> truly bare closing fence -> visible prose footer.
- Treat any language tag, id attribute, or fence metadata as a DO NOT ATTEMPT pattern.

## 2026-10-03 — Relay sandwich rendering recovery proven
- Recovery proof packet: `PCENG4-RELAY-036-true-bare-fence-proof`.
- End-to-end result: **OK**, exit code 0.
- Stdout contained `TRUE_BARE_FENCE_PROOF=OK` and the required final line `Reply to this with the sandwich technique`.
- This closes the immediate rendering incident: the correct assistant packet shape was accepted by the Firefox bridge, executed by the Windows relay, and returned automatically to chat.
- The preceding failed/collapsed attempts remain documented as DO NOT ATTEMPT patterns and human-intervention incidents.
- Future relay operations must preserve the proven visible-header -> bare fenced packet -> visible-footer technique.

## 2026-10-03 — Human-intervention incident: oversized command packet stalled
- A very large `command_b64` relay message remained unfinished/streaming for about five minutes and produced no GPT_WINDOWS_RESULT.
- The user had to report the stalled state and absent system response.
- The known-good sandwich wrapper was not sufficient because the assistant message itself was too large to complete reliably.
- New invariant: keep chat relay packets compact; do not transport whole profiles/databases/giant scripts inline. Use bounded multi-step file writes or existing local/source files.
- Backend execution was not proven to have started; do not misclassify this as a Windows relay backend failure.

## 2026-10-03 — Human-intervention incident: relay packet emitted through commentary surface
- Packet PCENG4-JOBAUTO-037-profile-state-audit was compact and visually bare-fenced but collapsed/no usable result appeared.
- Difference from known-good proof: 037 was emitted in commentary/update output rather than the final assistant response.
- User had to report the failure.
- New hard rule: relay sandwiches are final-response-only. Never emit them in commentary/progress/status messages or split commentary/final surfaces.


## 2026-10-03 — Job-application profile persistence and Git divergence recovery
- Canonical local applicant profile validated with 18 employment records extending to 2012.
- Current Post Falls application reached the pre-signature gate with confirmed non-signature fields staged and audited.
- Local commit `d6f1539` was created successfully, but its push was rejected because `development/runtime-control` had newer remote commits from direct GitHub incident logging.
- This was a branch-divergence/push ordering issue, not loss of the local profile or application state.
- The reusable defaults file was then created directly on the remote branch through the GitHub connector.
- Signature/agreement/submit remain intentionally untouched pending explicit authorization.

## 2026-10-03 — Job-application profile persistence and Git PATH incident
- Canonical local profile validated with 18 employment records extending to 2012.
- Post Falls application reached the pre-signature gate with confirmed non-signature fields staged.
- Action 046 failed because native Python could not resolve `git` from PATH. No repository write occurred from that failed action.
- Recovery uses the established explicit Git path: `C:\Program Files\Git\cmd\git.exe`.
- Signature/agreement/submit remain intentionally untouched pending explicit authorization.


## Reliability-regression evidence, GitHub approval-card UX, and PCE7 boundary — 2026-10-06T0300Z

### Evidence carried forward
- The 2026-10-04 night-agent handoff records the r25 consumer baseline as: normal live E2E PASS; live `Worked for X` collapse recovery PASS; relay suite 245/245 with zero exclusions; consumer suite 47/47; consumer Chrome connected at preflight; branch clean and matching origin.
- At the 2026-10-06T0257Z comparison checkpoint, GitHub comparison from audited stable `consumer/one-click-go` SHA `d5b9db7ad785b5cae8dc3b64219303b9fcfa634a` to r29 SHA `3d8ef23ab9f281ef8961aaf016f94c34f9e2cce9` reported r29 ahead by exactly 200 commits and behind by 0. This is a comparison boundary, not proof that any particular commit caused the regression.
- The Director reports a material practical reliability regression: an earlier relay era could operate autonomously for long periods and roughly the operation-182-to-200 era behaved materially better, while the present live path often struggles to progress through more than about two operations without intervention. Treat this as Director-observed field evidence requiring measured reproduction; do not rewrite it as a repository-proven duration claim.
- The 2026-10-06T0246Z Agent 6->7 handoff remains authoritative historical evidence for its boundary: A6.400 was discovered but never executed. Its documented open blockers remain on the release board.

### Engineering priority amendment
- Restore sustained relay forward progress before expanding unrelated feature surface. This does not authorize deleting newer recovery/safety work.
- Use r25 and the better historical operation range as differential evidence across scanner ownership, settlement/reacquisition, operation locking, delivery/finalization, browser lifecycle and recovery transitions.
- First reliability repair target is `DISCOVERED -> execution`: bounded transition-specific deadline, screenshot/evidence before repair mutation where required, exact-once backend state check before replay, and recovery without waiting for the approximately five-minute dead-man.
- Result visibility and ChatGPT turn finalization are separate states. Finalization recovery must never re-execute the completed Windows action.
- Preserve immediate remount reacquisition, approximately 15-second forced broad reinspection, approximately five-minute dead-man, collapse/folded recovery, delayed/out-of-order protection, backend dedupe, durable recovery ownership and honest HUD state.
- Add measured sustained-operation/soak acceptance. One or two consecutive successful packets are insufficient evidence that autonomy is restored.
- Do not blindly revert r29 to r25; preserve or equivalently replace the newer exact-once, approval, screenshot, out-of-band recovery and lifecycle safeguards.

### GitHub approval-card screenshot finding
- Director screenshot at 2026-10-06T0259Z positively identifies the recurring native ChatGPT GitHub approval surface at the bottom of the conversation: `Allow ChatGPT to use GitHub?` with `Always allow`, `Deny`, and `Allow once`.
- Low-priority requested UX: when the managed conversation is already at the bottom and this exact positively identified GitHub approval surface appears under the Director's pre-authorized policy, automatically invoke the configured GitHub approval choice so the run is not stranded.
- This must remain narrow: do not blindly click unknown providers, differently worded security surfaces, or ambiguous controls. Provider/text/control identity plus bottom-of-conversation state are prerequisites.
- The screenshot also explains the immediately preceding GitHub documentation-write interruption: the connector write was waiting on this approval surface rather than proving a repository failure.

### PCE7 boundary
- Director superseded the proposed Agent-7 `A7.1` working numbering for this conversation. Engineering proceeds as `PCE7.400` through `PCE7.499`.
- `PCE7.500` is the mandatory timestamped handoff/rotation boundary and should ideally exercise automatic fresh-chat/next-agent startup.
- Historical failed `A6.400` remains a separate incident; do not renumber it or count it as a successful rotation.
- If the primary PCE7.500 rotation fails, independent/out-of-band fallback must preserve and deliver the handoff rather than leave it stranded at `DISCOVERED`.


## PCE7 stale operation owner after completed result delivery — 2026-10-06T0324Z

PCE7.401/PCE7.403/PCE7.404 confirmed the first concrete forward-progress root defect in the present relay.

- A6.399ay executed once and finished `COMMAND_FAILED` at 02:30:31Z; its saved backend result exists.
- Browser delivery then succeeded: send clicked/confirmed and `relay_result_delivery_complete` emitted at 02:32:27Z.
- At 02:32:51Z a leftover/reappearing A6.399ay relay-result draft was detected. Draft recovery reacquired A6.399ay as `activeRelayOperationId`, attempted another send, and at 02:34:22Z deferred with `Send button not ready within 90000ms`.
- That recovery failure retained the global owner. Historical A6.400 subsequently accumulated 78 discoveries, 78 queue events, and 78 `relay_action_deferred_for_active_operation` events behind A6.399ay, while never reaching backend reservation or execution.
- PCE7.403 at 03:22:40Z still proved A6.400 had no processed record/result. It also proved PCE7.402 never executed.
- The earlier hypothesis that A6.400 late-executed and caused the 03:09Z generic-ChatGPT navigation is therefore disproved. The session-escape/manual-return/manual-rename incident remains real with cause still open.

Source finding:
- `recoverExistingRelayDraft()` can reacquire ownership for a stale draft after normal delivery and does not first reject a packet already recorded as delivered/attempted.
- Its deferred/failure path intentionally retains ownership, while the no-draft path does not reconcile a stale owner against exact visible result evidence.
- `drainDeferredActions()` refuses to drain with any active owner, turning this stale draft into a global deadlock.
- `waitForDeliveryConfirmation()` also treats generation-start or stable composer-clear as semantic delivery confirmation. That contradicts F-005 / Operational Rule 12, which require the matching live `[GPT_WINDOWS_RESULT]` user turn.

Repair contract:
1. matching user-result-turn evidence is the only delivery-complete signal; generation-start/composer-clear are progress telemetry only;
2. already exactly delivered drafts are cleared without resend and cannot reacquire/retain the global owner;
3. no-draft stale owners are released only with exact matching user-result evidence; unresolved owners remain observable for bounded supervisor recovery;
4. preserve backend exact-once behavior and do not solve this by blindly clearing owners;
5. add regression coverage and live-prove consecutive packets after a delivered result without re-execution;
6. replace repeated active-owner defer spam with a bounded watchdog/recovery state.


## PCE7.402 delayed out-of-order execution — 2026-10-06T0329Z

PCE7.402 was emitted around 03:09Z, then the Director had to navigate back from an unintended generic ChatGPT screen. PCE7.403 proved at 03:22:40Z that PCE7.402 still had no backend record/result. PCE7.404 executed at 03:24:12Z–03:24:13Z. Only afterward, PCE7.402 finally executed at 03:24:18Z.

This is direct proof of unique-ID delayed/out-of-order ingestion: operation 402 executed after operations 403 and 404. It was read-only, so no harmful side effect occurred.

Reliability implication:
- backend exact-once protection prevents duplicate execution of the same ID but does not prevent an obsolete unique side-effecting packet from executing late;
- the existing rotation ordinal parser records delivered counts/100-operation rotation but does not enforce a monotonic operation cursor;
- a parseable older operation from the same/superseded engineering series must be classed as `LATE_PACKET` and suppressed before backend execution once a newer operation cursor has been accepted;
- series parsing must be dynamic and generation-aware (for example A6 -> PCE7) rather than hard-coded to one agent label;
- arbitrary packet IDs that do not match the explicit engineering-series grammar must not be assigned a misleading ordinal.

PCE7.405 had already been emitted when the delayed PCE7.402 result arrived. Do not issue a duplicate PCE7.405; allow exact backend evidence to determine whether it executes.

### PCE7.405 500-second no-action watchdog failure — 2026-10-06T0340Z

Observed live by the operator after issuing `PCENG-PCE7.405-r29-checkout-runtime-map`: the HUD reached about **500 seconds since last action detected** and no PCE7.405 result arrived. PCE7.405 is read-only, so a later execution is not side-effect dangerous, but the absence is direct evidence that the documented 15-second recovery scan plus ~5-minute deadman did not restore forward progress.

Source inspection found a concrete redundancy hole in `windows-relay/extension/content.js`:

- `forceRecoveryPacketInspect()` called `resetRecoveryPacketWatch()` whenever `newestRelayCommandUnit()` returned no currently materialized command. A packet temporarily absent because of ChatGPT DOM virtualization/remount therefore lost its recovery deadline.
- The deadman also refused page-refresh recovery whenever `activeRelayOperationId` was non-null. PCE7.401–PCE7.404 already proved that a stale owner can survive after backend completion/result delivery and block later operations, so this condition could disable the deadman indefinitely.
- A visible 5-minute constant was therefore not equivalent to a durable 5-minute recovery obligation.

Hardening committed on r29:

- `104f9e80d0f9fa8670cfb4f49bc5dd55abe2e010` — persist the recovery packet obligation in session storage across DOM disappearance/remount, retain its original first-seen deadline, rate-limit recovery reloads, and give stale operation ownership a bounded lease that releases into exact-once replay after the watchdog interval.
- `2917a8b1d6737f2593773e7df7528145969c87c3` — regression contract proving the durable-obligation and stale-owner-lease markers/semantics remain present.

This is source hardening only until the Windows r29 checkout is synced, tests/syntax pass there, and the exact live Firefox add-on is reloaded. Do not call the incident closed before live proof. Because PCE7.405 never returned, it remains **stranded/unknown** rather than “failed in backend.”

### PCE7.406 validation gate stopped staging — 2026-10-06T0343Z

`PCENG-PCE7.406-sync-test-stage-redundancy-hardening` reached backend execution promptly and failed in 4.990 s with `RuntimeError: node_not_found`. The operation had already located/synced the exact r29 checkout, but the script intentionally placed live backup/copy after JavaScript syntax validation; therefore the live Firefox extension was **not staged or reloaded** by PCE7.406.

This is a correct fail-closed validation outcome, not a relay-ingestion failure. Next recovery must use an actually available JavaScript parser/runtime (including a Chromium V8 syntax harness if Node is absent), preserve the Python contract-test gate, and only then stage the live extension.

### PCE7.407 hardening staged after independent V8 + contract validation — 2026-10-06T0346Z

`PCENG-PCE7.407-v8-validate-and-stage-hardening` completed OK in 17.441 s. The exact r29 checkout was `C:\\Users\\<LOCAL_USER>\\Downloads\\Dev\\GPT\\GPT-Termux-Relay-consumer`, fast-forwarded to `9b0fbeef353e9cf82e9fa93aa1164fb453e9b6b0`. The ChatGPT content contract passed. Because Node was unavailable, Microsoft Edge's installed Chromium/V8 engine independently parsed both staged JavaScript files successfully.

A rollback snapshot was created at `C:\\Users\\<LOCAL_USER>\\Downloads\\Dev\\GPT\\Client\\Relay\\rollback\\PCE7.407-20261006T034645Z`. Source and live SHA-256 matched for both staged files:

- `content.js`: `9aa16685c3695ca1bf81c194ab3e117b4579aa81fe6f60d39ab987b0b27cb54f`
- `service_worker.js`: `4053c08842cea815eb375f953e0026e682d070ca89f9fa5a957834e6ff6fa8be`

State at this point: **STAGED_NOT_RELOADED**. Live acceptance still requires the exact Firefox add-on reload, current-chat refresh/rebind, exact-result replay proof, and follow-up telemetry inspection.

### PCE7.408 live cutover stranded backend-OK result — 2026-10-06T0355Z

The operator reported `PCENG-PCE7.408-live-firefox-cutover-and-rebind` locked at **STARTING for 425 seconds**. Screenshot evidence at ~417 s showed `Relay ONLINE • ARMED • pending 0`, `Firefox IDLE • action_received`, and `LAST PCENG-PCE7.408-live-firefox-cutover-and-rebind / OK`, while no exact 408 result had appeared as a ChatGPT user turn.

This is a failed live cutover/rebind acceptance even if backend execution is terminal OK: the result was not reconciled/delivered after the add-on/page remount. Treat 408 as backend-state-known-only-from-HUD until independent readback confirms processed/result-file state. Incident: `docs/INCIDENT_2026-10-06T0355Z_PCE7_408_STARTING_STUCK_AFTER_CUTOVER.md`.



### PCE7.410–PCE7.415 HUD startup/diagnostic regression — 2026-10-06T0455Z

The relay bridge resumed backend execution, but the HUD recovery path exposed a separate regression. PCE7.410 timed out calling `hud.py --once`; direct r29 inspection proved current `hud.py` ignored `--once` and always entered the Tk mainloop, despite the earlier P1 log explicitly recording a successful `--once` diagnostic. PCE7.415 then launched the HUD but failed its own overly strict raw-process-count assertion after seeing two `hud.py` processes. Because the venv launcher is known to create a shim→real-interpreter pair for the relay server, this is not yet evidence of two logical HUDs.

Source commit `e3e0126b1605dd84d6c344a84ebbea4f107846c6` restores JSON snapshot-and-exit behavior; `069efb1391e1375e5958b90c545cd0596ab6a168` adds a behavioral test. Live staging, PID/PPID topology, actual startup wiring, automatic relay+HUD recovery, and stale-STARTING lifecycle handling remain open. Incident: `docs/INCIDENT_2026-10-06T0455Z_HUD_STARTUP_AND_ONCE_CONTRACT_DRIFT.md`.


### PCE7 GitHub approval blocker escalated — 2026-10-06T0528Z

Director screenshot evidence showed the native ChatGPT GitHub approval card visibly blocking the current engineering loop: `Allow ChatGPT to use GitHub?` with `Always allow`, `Deny`, and `Allow once`. The relay HUD independently detected the same state as `APPROVAL REQUIRED • ChatGPT tool approval • GitHub`, proving detection already worked while action was absent.

Per Director authorization, r29 commit `dc5afa8fab1b182de64a3537e2f52da40e4087b6` adds a narrowly gated auto-click of `Always allow` only for that exact GitHub surface when all expected controls are present and the relevant scroll root is at bottom. Commit `5a5d0cd2077c91d2a6d1e2328cb970a1c137810c` adds a regression assertion. Unknown/other providers remain fail-closed. Live Firefox staging/reload and telemetry proof are still required.


### PCE7.425 post-refresh replay duplicated visible result — 2026-10-06T0537Z

After PCE7.425 successfully forced a Firefox refresh, backend exact-once worked: the returned 425 result carried `replayed:true`. However the same 425 result was subsequently posted into ChatGPT again after an already-visible 425 result turn. This is a browser-delivery anti-spam incident, not duplicate Windows execution.

Source inspection found that visible-result recognition depended solely on `USER_SELECTOR`; if current ChatGPT user-turn wrappers are not matched, `waitForDeliveryConfirmation()` cannot observe the exact result and its bounded retry loop can post the saved result again. Commit `9a3cd5b00348d219ece22a877d510124be4b64ff` adds a result-only current-conversation-wrapper fallback, explicitly rejects assistant-role wrappers and the composer, and does **not** broaden the assistant-only action execution trust boundary. Commit `50ac686b141ede52cff8ff8c76d06d0fdbc5b99f` adds the regression assertion.

Do not call the GitHub approval auto-click live-proven until this delivery fix is activated and the approval-v3 telemetry is independently observed.


### PCE7.426 approval-v3 runtime activation proof — 2026-10-06T0539Z

Delayed PCE7.426 readback proved the new approval runtime did activate after the PCE7.425 refresh. Browser telemetry contained fresh `content_script_started` events at 05:36:15Z and 05:36:20Z with runtime `v11-scroll-v5-delivery-v11-collapse-recovery-approval-v3-uierror-v1`.

`autoapproved_count` was zero because no qualifying GitHub approval card event occurred in the post-refresh window. Therefore source/runtime activation is proven, but an actual auto-click is **not yet live-proven**. The next proof must intentionally encounter the exact GitHub approval surface (or an equivalent naturally occurring one) and require `chatgpt_tool_approval_autoapproved` telemetry plus disappearance/continuation of the approval surface.

PCE7.427 was already emitted to stage/activate the result-turn de-duplication fix after the duplicate PCE7.425 delivery incident; do not stack a newer Windows action ahead of that existing obligation.


#### Corroboration: PCE7.426 also duplicated — 2026-10-06T0541Z

The exact PCE7.426 result was posted visibly a second time after its first visible delivery. This confirms the currently loaded `delivery-v11` result-recognition failure is systematic across ordinary post-refresh relay results, not unique to PCE7.425. Backend execution remains exact-once; the defect is repeated browser delivery of an already-saved result.

PCE7.427, already present in the managed conversation, is the next outstanding operation and contains the staged activation of the `GPT_WINDOWS_RESULT_TURN_WRAPPER_FALLBACK_V1` fix. Do not introduce a higher operation ID ahead of it while the old runtime's bounded 426 delivery loop is still draining.


### PCE7.427 interrupted restart + Director rescue — 2026-10-06T0542Z

After repeated visible-result duplication from the loaded delivery-v11 runtime, the Director intervened manually to rescue the workflow. This is an autonomy incident under the human-intervention policy. Exact operator action is not yet established and must not be invented; record it as **operator detail pending** until direct evidence or Director clarification identifies what was changed/closed/restarted.

Immediately afterward, `PCENG-PCE7.427-stage-dedupe-fix-and-reactivate` surfaced as `INTERRUPTED_RESTART`. Backend evidence is explicit:

- started 2026-10-06T05:42:10Z;
- terminalized 2026-10-06T05:42:15Z;
- saved result unavailable;
- exact-once boundary refused re-execution;
- stderr: `The command was previously processed, but its saved result is unavailable; it was not executed again.`

Do not call PCE7.427 successful or failed-at-a-specific-script-line. Its command may have partially progressed before process interruption. Next operation must be read-only forensic reconciliation of live/source hashes, runtime marker, backend state and supervisor/watchdog logs before any new mutation.


### Director rescue details + self-healing observation — 2026-10-06T0609Z

The Director supplied the exact manual rescue sequence for the 425/426 delivery-spam incident:

1. reloaded the Firefox relay extension/integration;
2. set it disabled (Firefox equivalent);
3. observed the programmed recovery machinery turn the integration back on again without further manual enablement;
4. then removed the relay extension entirely to stop the runaway browser-delivery behavior.

This closes the previously pending operator-detail field. It is also valuable positive field evidence: the disable/recovery path restored the integration as designed. Preserve that recovery behavior while fixing result de-duplication.

Screenshot evidence at 06:09:39Z then showed:

- HUD headline: `DELIVERING`;
- backend: `Relay ONLINE • ARMED • pending 0`;
- browser: `Firefox IDLE • action_result • 1639s`;
- lifecycle: `DELIVERING • ChatGPT send control became ready • 1639s`;
- packet: `PCENG-PCE7.427-stage-dedupe-fix-and-reactivate`.

The `DELIVERING` headline is therefore stale-state evidence, not proof that delivery is currently active: both supporting browser/lifecycle events are approximately 27 minutes old. This independently confirms the HUD lifecycle-aging defect already on the roadmap: nonterminal phases such as DELIVERING/STARTING must age into an explicit stale/stalled state instead of persisting indefinitely.

At this checkpoint the backend is visibly online/armed, but browser integration cannot be inferred alive after the Director removed the extension merely from the stale HUD phase. Next guidance must require a fresh near-zero-age browser/content-script event before resuming relay mutations.


### Pre-spam rollback boundary + intentional operator stop/start — 2026-10-06T0618Z

Preserve the first practically useful pre-spam live browser state before installing further repairs. Exact rollback evidence already exists locally:

- `Client\Relay\rollback\PCE7.422-20261006T053422Z\content.js`
- pre-spam live content SHA-256 recorded by PCE7.422: `26ce6b9bcd63ef5acb2043bef0216eba5d42623aeaf733c98df264e183f83ed5`
- PCE7.407 rollback directory remains `Client\Relay\rollback\PCE7.407-20261006T034645Z` for the earlier paired extension files.

Do not delete these rollback snapshots while the delivery-v12 repair is being validated.

Operator-control architecture is now explicit: redundancy keeps the relay alive unless the human intentionally sets the existing `.relay-paused` interlock. HUD commit `cd76768d1f6e0388389e5c627fc6035251a4a7f5` adds STOP/START controls; `START-RELAY.bat` and `STOP-RELAY.bat` were repaired as real multi-line CMD launchers in `e183beb9f163e5431c0e47d06ff9552b1f770533` and `1c149a152d61aceb06515a4deb004dd700123423`. Watchdog source corruption from the earlier string-replacement edit was repaired in `8d645117e044fbf41b3d0e0a959936e35b96207d`; regression coverage is in `b822d2e89e989bb08823be79573c68c9c44714e1`.

Intentional STOP must win over every watchdog/recovery plane. START clears the interlock and returns ownership to supervision.


### Repaired checkout targeted validation — 2026-10-06T0633Z

With the live relay intentionally paused via `.relay-paused`, the Director fast-forwarded the consumer checkout to `5b2434fc6f9cbd75b4fa90f346c10a6332541354` and ran:

`python -m unittest discover -s tests -p test_hud.py -q`

Result: **17 tests, OK**.

Two preceding runs exposed only a newly-added assertion escaping mistake around the watchdog mutex string; the watchdog implementation itself was not changed for those failures. The assertion was simplified to count the stable mutex name and independently rechecked against source before the final passing run.

Do not stage/start live yet solely from this targeted gate; run the complete Windows-relay unit suite first, then create a fresh live rollback snapshot before copying repaired files.


### Repaired checkout full-suite validation — 2026-10-06T0635Z

While the live relay remained intentionally paused, the Director ran the complete `windows-relay/tests` suite from the repaired checkout using the live relay Python runtime.

Result: **265 tests in 4.050 s, OK**.

The two printed `ATOMIC_REPLACE_RETRY` lines were expected simulated transient-sharing-lock test behavior; the suite was green. This clears the source test gate for a paused, rollback-protected live staging of only the repaired content/HUD/watchdog/operator-launcher files. Starting/resuming the relay remains a separate acceptance step.


### Paused staging proof + old HUD process distinction — 2026-10-06T0637Z

The Director staged the repaired files behind a fresh rollback directory `Client\Relay\rollback\PCE7.428-pre-repaired-stage-20261006T0635Z`. All 12 copy operations succeeded; live targeted validation returned **17 tests, OK**; `hud.py --once` returned `online:false`, `title:"PAUSED"`, `backend:"Relay PAUSED • operator stop"`; and CMD printed `RELAY_REMAINS_PAUSED`.

A simultaneous screenshot still showed the *already-running* HUD window as `OFFLINE` with stale `DELIVERING` evidence aged ~3304 s. This does not contradict the staged HUD proof: an existing Python/Tk process does not reload when `hud.py` is replaced on disk. The visible instance was old in-memory code. Restart only the HUD process while leaving `.relay-paused` set; the newly launched HUD should then report PAUSED and expose the new START/STOP controls. Do not resume the relay merely to refresh the HUD.


## 2026-10-06T0641Z — PCE7 HUD hidden right-click close rejected

Director live acceptance of the repaired PAUSED HUD proved the explicit START/STOP operator controls are visible and usable. During that recovery, the Director identified the legacy right-click gesture that destroyed the entire HUD window as surprising and hostile to the operator-control mission.

Decision: remove the hidden `<Button-3>` → `root.destroy()` binding. Relay/HUD lifecycle actions must be explicit, visible controls; an incidental right-click must not remove the recovery surface. This is a source-release correction and does not require destabilizing the current paused/live bring-up solely to restage the HUD.

The repaired build remains rollback-protected by the PCE7.428 pre-stage backup. Basic relay + Firefox recovery is the next live acceptance step; watchdog runtime cutover remains deferred until ordinary relay execution is stable.


## 2026-10-06T0647Z — PCE7.429 live duplicate-result recurrence isolates post-submit resend defect

After the Director restarted the repaired relay and reloaded Firefox, PCE7.429 executed immediately and exactly once at the Windows boundary. Evidence: backend `ok=true`, `armed=true`, pause marker absent, fresh Firefox content-script start at 06:44:53Z, runtime `delivery-v12-result-wrapper-fallback-approval-v3-uierror-v1`, and a single immediate `DISCOVERED -> execution_requested -> action_received` path.

However, after the first PCE7.429 result reached ChatGPT, the identical saved result was injected into the conversation again instead of the next PCE7.430 probe taking ownership. This reproduces the 425/426 class without evidence of Windows re-execution: backend exact-once remains the safety boundary; browser result submission/retirement is the failing layer.

Source inspection found the concrete resend permission: `waitForDeliveryConfirmation()` already observed strong ChatGPT acceptance signals (`generation_started` or stable `composer_cleared`) but returned failure unless an exact user-result DOM turn was positively recognized. `injectConfirmed()` then interpreted that visibility uncertainty as permission to click Send again, up to three attempts.

Correction committed in `0c67c623d2036c93d318fcefdf346ca8236561c3`: delivery-v13 introduces a durable submit-once state. After generation starts or the composer is stably cleared, the packet becomes SUBMITTED and is persisted in session storage/attempted history. The relay then enters `WAITING FOR GPT TURN END`; its watchdog may observe and reconcile but contains no Send path and no backend action path. Exact user-turn recognition later emits delivery-complete/counting. Watchdog expiry emits explicit telemetry with `resend=false` and `reexecution=false`.

Regression contract: `a23835a8b6d3fde5d9b5916bbf987283b19f2b0d`. HUD vocabulary: `184ba68b0e8b536b8462fe55795e9b61d03fc3d6`. Remote V8 parse and structural invariants passed before live staging.


## 2026-10-06T0649Z — PCE7.430 confirms duplicate Send, not duplicate Windows execution

PCE7.430 eventually executed after the duplicate 429 result and supplied the exact event counts for PCE7.429. This supersedes the temporary conversational assumption that 430 had been displaced.

Confirmed PCE7.429 lifecycle:
- `relay_packet_discovered=1`
- `relay_action_execution_requested=1`
- `relay_result_received=1`
- `relay_result_text_set=2`
- `relay_result_send_attempt=2`
- `relay_result_send_clicked=2`
- `relay_result_send_unconfirmed=2`
- `relay_result_delivery_failed=1`
- `relay_result_delivery_retry_deferred=1`

The backend processed record remains a single completed PCE7.429 operation. Therefore the incident is positively isolated to browser result submission: one Windows execution produced a saved result, but the content runtime clicked ChatGPT Send twice because exact user-turn confirmation was not recognized. This is direct live justification for the delivery-v13 submit-once boundary in commit `0c67c623d2036c93d318fcefdf346ca8236561c3`.

PCE7.431 was already emitted to validate and stage delivery-v13. It must not be redundantly reissued merely because queue/recovery ordering delayed it.


## 2026-10-06T0654Z — PCE7.430 result also duplicated under delivery-v12

The PCE7.430 saved result itself appeared in ChatGPT a second time after its first successful arrival. This reproduces the same browser-side resend pathology on the very forensic probe that proved it for 429. The incident is therefore systematic in the active delivery-v12 runtime, not packet-specific.

No new operation is being issued while the old delivery owner exhausts its bounded attempts. PCE7.431 remains the already-emitted next obligation: validate the repaired source, create a new rollback boundary, and stage delivery-v13 without reloading mid-operation. This avoids worsening the queue and preserves backend exact-once.


## 2026-10-06T0655Z — PCE7.431 validation correctly blocks staging on stale runtime assertion

PCE7.431 reached the Windows backend and failed during the first targeted `test_browser_contract.py` run, before rollback creation or live-file staging. Live delivery-v12 therefore remained untouched.

The failing contract still asserted the older delivery-v11 runtime identity in two places. Delivery-v13 intentionally changes runtime identity so live activation can be distinguished. Both assertions were updated to require the full v13 identity in `23d77cc2021608831af0a45e9b1532848c1b487a`. Re-run must still pass targeted browser/HUD tests and the entire Windows-relay suite before staging.


## 2026-10-06T0657Z — Old PCE7.429 backend replay proves v12 can loop beyond three send attempts

After three visible PCE7.431 copies, the active v12 content runtime resurfaced PCE7.429 again. The returned envelope explicitly reported `replayed:true` with the original 06:46:37Z/06:46:38Z execution timestamps and saved-result path. Therefore the failure is broader than one three-attempt `injectConfirmed` loop: recovery can rediscover an old assistant action after that loop, call the backend with the same ID, receive the exact-once saved result, and re-enter result delivery. No Windows side effect re-executed, but browser result spam can repeat indefinitely.

This establishes a break-glass deployment requirement: when the currently loaded content runtime itself is the looping fault domain, disable/remove that extension runtime before staging/activating the repaired runtime. Backend exact-once is necessary but cannot by itself stop saved-result delivery spam.


## 2026-10-06T0701Z — Director STOP exposes browser-quiescence gap; rollback-first rule adopted

Director clicked HUD STOP during the v12 result-replay storm. HUD correctly changed to PAUSED, but saved-result spam continued. This is now a distinct incident: [INCIDENT_2026-10-06T0701Z_HUD_STOP_PAUSED_BUT_BROWSER_RESULT_SPAM_CONTINUED.md](./INCIDENT_2026-10-06T0701Z_HUD_STOP_PAUSED_BUT_BROWSER_RESULT_SPAM_CONTINUED.md).

The observation proves that the durable pause interlock currently owns backend/supervisor resurrection but does not synchronously cancel already-running browser result/recovery loops. Operator STOP acceptance is expanded to whole-product quiescence.

Director also established a deployment rule: create a fresh live rollback snapshot before every live change; when a candidate breaks, restore the previous snapshot before further experimentation. Known boundaries and non-boundaries are indexed in [ROLLBACK_INDEX_2026-10-06T0701Z_RELAY_RECOVERY_BOUNDARIES.md](./ROLLBACK_INDEX_2026-10-06T0701Z_RELAY_RECOVERY_BOUNDARIES.md).


## 2026-10-06T0704Z — PCE7.433 break-glass command blocked by dirty local source checkout before backup/staging

Director supplied the complete CMD output from the proposed PCE7.433 break-glass staging chain. The pull fast-forwarded the local checkout from `7e2cf19` to `2ae9f24`, then `test_browser_contract.py` failed 4 of 51 tests. Because the command was chained with `&&`, execution stopped at that targeted suite: the PCE7.433 rollback directory was not created and no live file was copied.

The failing test process read a local `windows-relay/extension/content.js` whose runtime was still `v11-scroll-v5-delivery-v11-collapse-recovery` and which lacked the v13 submit-once state.

GitHub forensic readback proves this is local worktree divergence, not a bad remote branch: both remote commit `7e2cf198becc2d1884f27339c597e3adde323635` and remote commit `2ae9f246bd8867e273f450249682bab72a17a221` contain the identical v13 content blob SHA `39572edf843e680add6e3566748d5414276c53d2`, length 81350, marker `GPT_WINDOWS_RESULT_SUBMIT_ONCE_V1`, runtime `v11-scroll-v5-delivery-v13-submit-once-result-wrapper-fallback-approval-v3-uierror-v1`.

Conclusion: the local Git checkout already had a modified older `windows-relay/extension/content.js`; the fast-forward did not touch that path because the incoming commit range did not modify it. The test gate correctly prevented that stale worktree file from being promoted live.

Recovery must follow the new rollback-first rule: preserve the dirty local source file before restoring that path from HEAD, prove the source path is clean, rerun targeted/full tests, then create a new live rollback boundary before any staging.

## 2026-10-07 — PCE8 OP077 discipline checkpoint
Marker: `PCE8_OP077_DISCIPLINE_CHECKPOINT`
Real progress: f04b925 startup fix promoted; v17 browser microactivation/resume proven earlier; OP070 proved main/consumer launcher collision; OP073 recorded 398 Windows tests green; OP074 recorded 101 consumer tests green and harness source gate green. Debt: repeated full-cutover scaffold delayed root-cause discovery; several test-root mistakes wasted operations; OP075 failed transport; OP076 was rejected for exceeding relay command-size limits. GitHub auto-approval source exists but live auto-click telemetry remains unproven. Rotation to 💻PC Engineering 9🔧 is now P0.

## 2026-10-07 — PCE8 OP078 retry/latest-wins
Marker: `PCE8_OP078_RETRY_LATEST_WINS`
Adds modern HUD RETRY, selected-PC-Engineering refresh retry, latest-instruction-wins for stale/deferred browser ownership, every-result operation-discipline reminder, direct watchdog launch hardening, and PCE9 rotation budget P0. Safety invariant remains: do not preempt a genuinely inflight Windows side effect or overwrite an unresolved result draft. GitHub auto-approve live click remains unproven.

## 2026-10-07 — PCE8 OP079 retry integration repair
Marker: `PCE8_OP079_RETRY_INTEGRATION_REPAIR`
OP078 contained real new functionality but failed its Windows integration gate due to a malformed test insertion and unsynchronized content-script copies. OP079 preserves the functionality, repairs those two integration defects, reruns complete Windows and consumer suites, and only then promotes. PCE9 rotation remains P0; GitHub auto-approval live click remains unproven.

## 2026-10-07 — PCE8 OP085 rotation trigger
Marker: `PCE8_OP085_ROTATION_TRIGGER`
Preserve and roll back failed OP082 HUD source, then replace generic-home rotation in canonical source with a durable PCE8→PCE9 trigger. Exactly delivered PCE8 operations at/after OP087 persist a rotation request containing exact title `💻PC Engineering 9🔧`, session `pce9.1`, and bounded handoff, then notify the content plane. Create/rename/verification handler follows in OP086. Rotation is P0.

## 2026-10-07 — PCE8 OP086 rotation trigger gate repair
Marker: `PCE8_OP086_ROTATION_TRIGGER_GATE_REPAIR`
OP085 correctly restored the promoted source boundary and built the durable PCE9 rotation trigger, but its new test was pytest-style and `unittest` ran zero tests. OP086 repairs only that harness defect, then runs complete Windows and consumer suites before promotion. Rotation remains P0; no live reload occurs in this operation.

## 2026-10-07 — PCE8 OP089 rotation trigger normalization
Marker: `PCE8_OP089_ROTATION_TRIGGER_NORMALIZATION`
Normalize the persistent worker back to exact promoted Git bytes, retain rotation only in the temporary/dev worker that owns delivered-operation counting, and fix forced-rotation precedence over normal modulo-100 calculation. OP092 is the first eligible automatic PCE8→PCE9 trigger, leaving OP090 for create/rename implementation and OP091 for activation proof.

## 2026-10-07 — PCE8 OP090 consumer rotation contract
Marker: `PCE8_OP090_CONSUMER_ROTATION_CONTRACT`
OP089 reached 401/401 Windows green. Consumer acceptance still asserted the retired generic-home rotation mechanism. OP090 changes that test to require the durable exact PCE9 trigger instead: exact title/session, `relay_chat_rotation_start`, and no generic-home `chrome.tabs.update`. Full Windows + consumer suites gate promotion.

## 2026-10-07 — PCE8 OP091 durable rotation handler
Marker: `PCE8_OP091_ROTATION_HANDLER`
Build the content-side handler for the already-promoted PCE9 trigger. Rotation state survives same-origin navigation in sessionStorage; the handler opens fresh ChatGPT, submits the handoff once, waits for a new `/c/...` identity, renames that exact conversation to `💻PC Engineering 9🔧`, and emits `chat_rotation_verified` only after exact title/path verification. No live reload occurs in this operation.

## 2026-10-07 — PCE8 OP093 rotation-handler promotion
Marker: `PCE8_OP093_HANDLER_PROMOTION`
Back up before cache cleanup, remove generated Python cache, restore the protected relay bootstrap ordering, and gate the durable fresh-chat/handoff/exact-rename handler through complete Windows and consumer suites. First eligible live rotation moves to OP095 so OP094 can stage/reload the promoted extension safely.

## 2026-10-07 — PCE8 OP094 rotation runtime activation
Marker: `PCE8_OP094_ROTATION_RUNTIME_ACTIVATION`
Source trigger/handler are promoted and fully gated. OP094 stages only the temporary Firefox extension worker/content into the live tree, preserves rollback copies, and schedules a delayed temporary-addon reload plus PCE8 tab refresh so OP094 result delivery is not disrupted. OP095 must first verify the activation receipt before serving as live rotation acceptance.

## 2026-10-07 — PCE8 OP096 rotation forensics
Marker: `PCE8_OP096_ROTATION_FORENSICS`
Non-trigger diagnostic operation. OP094 Reload/refresh calls were successful; its final-title acceptance was a transient-title false negative. OP095 post-delivery classification: **OP095_NOT_COUNTED_AFTER_EXACT_VISIBLE_RESULT**. Current Firefox URL observed by UIA: `None`. No rotation-triggering PCE8BOOT ID is used in OP096.

## 2026-10-07 — PCE8 OP097 result-turn recognition
Marker: `PCE8_OP097_RESULT_TURN_RECOGNITION`
Repair the exact-delivery boundary isolated by OP096: accept current element-agnostic `[data-turn=user]` and `[data-testid^=conversation-turn-]` wrappers while preserving explicit assistant rejection and composer exclusion. Move the first eligible engineering trigger to OP099 so OP098 can activate/prove the repaired runtime without retroactively rotating on OP095.
