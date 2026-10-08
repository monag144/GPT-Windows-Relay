# Archived source fragment 3/23 — 2026-10-08T0752Z

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

