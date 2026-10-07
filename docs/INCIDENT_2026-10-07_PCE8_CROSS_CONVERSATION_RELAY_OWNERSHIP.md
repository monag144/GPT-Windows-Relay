# Incident — Cross-conversation relay ownership bleed

**Date:** 2026-10-06/07  
**PCE:** 8.1  
**Severity:** High autonomy/reliability defect

## User-observed symptom

While the new PCE8 engineering conversation was active, the HUD showed an older packet identity (`PCE8.199A3...`). The operator also observed relay activity occur when the prior PCE7 conversation was briefly opened.

This established that relay execution ownership was not semantically bound to the engineering conversation that currently owned the work.

## Root causes

Two independent mechanisms combined:

1. **Ordinary relay actions had no conversation-owner gate.**
   Every connected ChatGPT content-script port could submit `relay_action` to the shared worker. Active-tab routing existed for consumer missions, but not for ordinary `GPT_WINDOWS_ACTION` execution.

2. **The global late-packet cursor overloaded project numbering as operation numbering.**
   The worker parsed identifiers like `PCE8.1-OP001` as generation 8 / ordinal 1. An older conversation containing an identifier like `PCE8.199A3...` therefore ranked ahead globally, even though it belonged to a different engineering thread/epoch.

Active-tab gating alone would not fix the defect: merely clicking an old conversation would make it active again.

## Fix

PCE8.1 introduces `GPT_RELAY_CONVERSATION_OWNER_V1` and `GPT_RELAY_LATE_PACKET_CURSOR_V2`.

### Conversation owner

Every content script now sends:

- `conversation_key` = ChatGPT origin + pathname
- `conversation_href`

The worker persists a single owner record in `chrome.storage.local` under:

`gptRelayConversationOwnerV1`

Rules:

- first owner claim must originate from the active/focused ChatGPT tab;
- the owning conversation can continue in the background;
- a different inactive conversation is suppressed;
- a legacy/default-session packet cannot take over an existing owner;
- the same explicit session cannot silently move to another conversation;
- ownership transfer requires either a newer recognized PCE session or explicit `owner_claim:true` from the active conversation;
- suppression emits `relay_cross_conversation_suppressed`;
- ownership claim/transfer emits dedicated telemetry.

### Operation cursor

The late-packet cursor is now scoped to the conversation owner and explicit `OP###` token rather than `PCE<generation>.<number>`.

Key:

`gptRelayOperationCursorV2`

This prevents project/subversion numbering from being mistaken for operation order across conversations.

## PCE8.1 session policy

Current engineering relay packets use:

`session: "pce8.1"`

The first post-cutover packet uses `owner_claim:true` to establish the current conversation as owner.

At PCE9 rotation, the new conversation must use `session:"pce9"` and claim/transfer ownership deliberately.

## Validation performed before live cutover

- all three content-script copies compile;
- both worker variants compile;
- all three content-script copies are byte-identical;
- both worker variants contain owner/default-session/cross-conversation guards;
- both worker variants use OP-token cursor V2;
- regression tests added for conversation identity transport, persisted owner enforcement, default-session takeover rejection, OP-token cursor semantics, and backend ownership-metadata compatibility.

## Live validation still required

Source validation is not live proof. Live cutover must verify:

1. current PCE8.1 conversation claims ownership;
2. owner telemetry identifies this conversation;
3. an old/default-session conversation is suppressed rather than executed;
4. current PCE8.1 OP sequence executes normally;
5. browser/result delivery remains healthy after extension reload.



## Confirmed live evidence from delayed OP001

A delayed result for `PCE8.1-OP001-reconcile-health-audit` later arrived with:

- packet session: `default`
- action start: `2026-10-07T04:11:48Z`
- action finish: `2026-10-07T04:11:52Z`
- immediately preceding PCE8 bootstrap OP003 had already finished at `2026-10-07T04:11:45Z`

This is direct live proof that an older, default-session packet remained executable and was admitted **after a newer PCE8.1 operation had already completed**.

The same OP001 telemetry showed:

- old content runtime still active: `v11-scroll-v5-delivery-v16-submit-once-backend-retired-scoped-recovery-draft-owner-release-approval-v3-uierror-v1`
- a fresh `action_received` event at `04:11:47Z`, immediately before OP001 began
- no conversation-owner telemetry, because the owner-boundary extension had not yet been deployed
- the live canonical Windows checkout path did not yet exist locally; the active local source checkout remained the old `GPT-Termux-Relay-consumer` clone
- duplicate live HUD processes were present, reinforcing the need for a separate HUD/process-health cutover after ownership is fixed

This converts the cross-conversation/stale-queue diagnosis from inference to reproduced live evidence.

