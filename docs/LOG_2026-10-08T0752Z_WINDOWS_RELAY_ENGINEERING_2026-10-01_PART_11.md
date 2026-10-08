# Archived source fragment 11/23 — 2026-10-08T0752Z

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
