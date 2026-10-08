# Archived source fragment 2/23 — 2026-10-08T0752Z

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

