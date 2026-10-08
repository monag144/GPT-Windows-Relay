# Archived source fragment 8/23 — 2026-10-08T0752Z

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
