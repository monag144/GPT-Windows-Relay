# Archived source fragment 5/23 — 2026-10-08T0752Z

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

