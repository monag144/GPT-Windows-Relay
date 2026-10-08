# Archived source fragment 12/23 — 2026-10-08T0752Z

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


