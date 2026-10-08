# PCE11 user-observed ChatGPT answer interruption — 2026-10-08T19:28Z

**Classification:** USER-OBSERVED INCIDENT / CHATGPT ANSWER-STREAM DELIVERY STALL / AUTOMATIC CONTINUATION GAP

**Status:** OPEN — user investigating. **Do not claim a verified browser, network, model, extension or backend root cause.** No browser repair or automatic recovery has been activated for this report.

## Human report (first-hand)

The user reported a visibly partial assistant reply immediately after PCE11.033 was accepted:

> ## PCE11.033 — Host-
> Connection interrupted. Waiting for the complete answer

The user states that the failure has appeared in the **last three days** (approximately October 5–8, 2026), and requested the relay to eventually recognize the banner and either refresh the exact conversation or recover the latest safe prompt in a new ChatGPT chat. The user explicitly said: **"Log this as an incident involving the user. I will investigate that."**

No confirmed frequency, session request ID, network error code, screenshot, DOM ancestry, recovery outcome or causal mechanism was supplied. Do not manufacture them. The user needed to intervene to report this; record **at least one human intervention** linked to this incident, not a claimed total count.

## Distinguish ChatGPT response from the completed Windows action

The immediately preceding operation `PCE11.033-corrected-native-proof-provenance-full-host-source-acceptance` returned `status=OK`, `exit_code=0` at 2026-10-08T11:04:12Z. The untruncated section reported source Git SHA `e4e89c4075ddc49e6bb6bae8db8bed2e48cad280`, passing tests: v16 target 12, host ownership 9, containment 12, Windows full 493, consumer 119, and JS 4. The result stdout was truncated, so do not invent its complete contents. The subsequent ChatGPT **assistant-answer stream** was visibly interrupted. This does **not** establish a failure or replay requirement for PCE11.033.

## Existing detection and gap, source inspected 2026-10-08

- `windows-relay/extension/content.js` and `windows-relay/extension-persistent/content.js` already have `visibleInterruptedWaitState()`: scan visible alert/status/aria-live content for `connection interrupted|waiting for the complete answer`. It is currently used by `chatBusyReason()` / `waitForChatIdle()` to avoid sending results while the chat is busy.
- The separate `chatGPTUiErrorFromText()` classifies `connection interrupted` as `network_or_generation_error` when `inspectChatGPTUiError()` sees a visible error node/button. `chatgpt_ui_error_detected` is emitted; this detection depends on selector coverage and current DOM visibility.
- `consumer/recovery_supervisor.py` reads these events and presently classifies visible ChatGPT errors to `capture_diagnostic` / `CHATGPT_UI_ERROR`. Its allowed GPT-proposed remedies are limited to `rebuild_browser_integration`, `audited_update`, `restart_relay`; automatic ChatGPT refresh / latest-prompt New Chat transfer is **not a proven accepted repair path**.
- Prior related but distinct incident: `docs/incidents/INCIDENT_2026-10-08T0803Z_PCE011_ASSISTANT_INPUT_STREAM_INTERRUPTION.md` reports the wording **"Error in input stream"** earlier that day. Whether the two ChatGPT errors share a backend cause is unknown.

## Proposed recovery state machine (SPECIFICATION ONLY; NOT ENABLED)

1. **DETECT:** Capture exact visible banner `Connection interrupted. Waiting for the complete answer` on the **verified selected ChatGPT conversation/tab**, using existing event hooks. Persist UTC time, sanitized event kind, current URL identity (not tokens), selected browser/tab identity, assistant generation state, latest delivered relay packet ID, last submitted user prompt ID/hash, and resulting snapshot provenance. Include screenshot only when safe and with sensitive content redacted.
2. **SETTLE:** Debounce/transient network recovery with a bounded stable observation window; distinguish still-streaming, completed, retry button, UI-stalled, auth-expired, tool-approval prompt, operator STOP and browser tab gone. Never treat one transient banner as immediate reload permission.
3. **IDEMPOTENCY CHECK:** Determine whether the latest Windows action/mission actually finished, whether its `[GPT_WINDOWS_RESULT]` was delivered/acknowledged, and whether the assistant reply completed elsewhere. A previously executed command must **never be auto-resubmitted** with a new ID; uncertain work must be classified `UNKNOWN` and investigated, not replayed.
4. **REFRESH CANDIDATE:** If continued interruption is positively demonstrated and exact tab/conversation identity is still verifiable, plan a single **bounded same-tab refresh** with pre-refresh durable context and rollback/STOP-aware guards. After refresh, explicitly re-resolve the exact URL and inspect whether ChatGPT resumed or completed the answer. Do not perform this step merely from cached window title or stale PID.
5. **NEW CHAT FALLBACK:** Only if the original chat cannot recover and user/operator policy allows, create a new chat through the **current verified browser UI**, with a bounded continuation note: last verified user intent; last known operation ID and returned status; repository/commit/task/audit context; exact error and uncertainty; **read/reconcile evidence first, do NOT replay commands**. The original conversation remains preserved. Do not copy secrets, private tokens, raw credentials, unbounded chat transcript or previous actions as runnable instructions. Do not submit a historic prompt that would repeat side effects.
6. **POSTFLIGHT:** Verify new chat identity, receive actual assistant continuation, preserve original incident evidence, and record outcome/cooldown and maximum attempt budget. In any ambiguity, STOP or operator override, **escalate without refresh or New Chat mutation**.

Required tests: banner visible/invisible DOM variants; duplicate/late relay results; in-progress code execution; current vs stale tab; STOP race; browser restart; authentication; chat navigation mid-action; partial/truncated assistant response; refresh failure; New Chat context boundedness; and false-success prevention. Preserve synchronized extension mirrors, consumer source-only tests and exact-once semantics.

## Current decision and operator investigation

**Log only.** User is investigating prevalence and possible root cause. No automatic refresh, chat rotation, live relay cutover, silent resend or web UI manipulation was run in this incident response. Do not displace current PCE11.034 isolated v16 runtime safety gates without a separately accepted decision. Follow-up engineering should be GitHub-first, with source/targeted/full suite tests and reversible staged canary; no fix is promoted merely on detecting a banner.

Useful follow-up evidence if available: when the banner appeared (local or UTC), whether assistant generation eventually resumed on its own, whether Refresh restored the original conversation, and a screenshot or sanitized console/network error. User-owned investigation findings will supersede these hypotheses.
