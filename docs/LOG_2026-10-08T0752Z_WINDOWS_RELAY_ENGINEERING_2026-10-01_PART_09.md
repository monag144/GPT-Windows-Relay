# Archived source fragment 9/23 — 2026-10-08T0752Z

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

