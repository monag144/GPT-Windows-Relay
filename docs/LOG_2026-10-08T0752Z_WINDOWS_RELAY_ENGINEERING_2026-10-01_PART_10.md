# Archived source fragment 10/23 — 2026-10-08T0752Z

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
