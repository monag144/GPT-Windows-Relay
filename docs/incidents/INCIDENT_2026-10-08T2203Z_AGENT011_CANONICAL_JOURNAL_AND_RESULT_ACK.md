# Incident: supervisor reads wrong Relay journal; browser result ACK remains uncertain

**Discovery:** Agent 011, operations PCE11.010–.011 on 2026-10-08 at 22:01–22:03 UTC.
**Classification:** Recovery telemetry divergence + separate result-turn acknowledgement gap.
**Severity:** Recovery is impaired in live consumer supervisor; an executed-and-sent action is not reliably marked as browser-confirmed. No known replay or data loss established.

## Evidence

- PCE11.010 read the WRONG events path LOCALAPPDATA/GPTWindowsRelayConsumer/browser-events.jsonl and returned zero send-complete events for PCE11.009. This absence was inconclusive.
- PCE11.011 inspected the Relay server's canonical journal at LOCALAPPDATA/GPTWindowsRelay/browser-events.jsonl; file was 13,211,225 bytes, and contained 21,174 relevant event lines. The supervisor path and server path were NOT equal. Backend state persisted at LOCALAPPDATA/GPTWindowsRelay/state.json, but consumer/recovery_supervisor.py also read its active-operation state from LOCALAPPDATA/GPTWindowsRelayConsumer/state.json.
- PCE11.009 durable /packet-status EXECUTION_CONFIRMED, processed=OK, outbound phase READY, saved result exists. Canonical browser events for PCE11.009 included relay_result_send_attempt, relay_result_send_clicked, relay_result_send_progress, relay_result_send_accepted, relay_result_waiting_for_gpt_turn_end, relay_result_turn_match_diagnostic and relay_result_turn_end_watchdog_expired, but NOT relay_result_delivery_complete or relay_result_send_confirmed. The result is clearly visible in the conversation; a UI user-result turn does not automatically turn an ambiguous local ACK into a verified ACK.
- The browser's own sender intentionally treats an accepted-but-unconfirmed send as no-resend, so **the event gap does not justify retrying or replaying**. The backend's outbound phase READY is expected when browser owns delivery and does not itself prove failure.
- Relay server windows-relay/windows_relay.py POST /browser-event appends to self.server.state.path.parent/'browser-events.jsonl'. This agrees with actual backend journal and disproves consumer/recovery_supervisor.py legacy EVENT_PATH.
- Canonical event journal has grown large enough that reading the whole text every 2 seconds is wasteful and can delay recovery.

## GitHub-first corrective work

On canonical repository monag144/GPT-Windows-Relay branch pce11/one-click-go-recovery-and-doc-hygiene, in source commit bf6562ad05a9b7dd38eae9de4da32f2fa4455f03:
1. Bind consumer recovery supervisor read-only RELAY_STATE_PATH and EVENT_PATH to LOCALAPPDATA/GPTWindowsRelay, the existing backend directory.
2. Preserve consumer supervisor's OWN mutable recovery state/evidence under LOCALAPPDATA/GPTWindowsRelayConsumer.
3. Tail at most 1 MiB from the canonical journal rather than reading the entire accumulated log, discarding a possibly truncated first record.

Follow-up GitHub commit 51f0b5c1e15b42213a555a54bc25dd6a750e2f49 adds four automated regressions: canonical path contract; UI-error/delivery-event consumption; bounded tail with partial first record; missing/malformed journal handling.

**This is source only until a later validated deployment.** Current Firefox extension remains on original live content script SHA 34500934b214423afc2d3c267877a961cd0ec46521e5860ed149502d7f4e2ae5. Candidate new content SHA fbdbf44bc157da217f375662b83b43ec4bbceb32c6168fd056e6c5ace5eea239 remains isolated in Client/Relay/bin/PCE11_009_AGENT011_RECOVERY_CONTENT_STAGE_20261008, with exact rollback and no live activation.

## Remaining independent issue and gates

- Determine why the browser sees send_accepted but its exact result-turn matcher expires after 120 seconds. Do NOT automatically retry, reload, abandon current conversation or infer server result loss. Read cached receipt and compare candidate user-turn semantics with current ChatGPT UI (virtualization, role selectors, moved DOM). Create a targeted test grounded in the observed failure before shipping matcher changes.
- The recovery supervisor is external to the extension and may need separate safe consumer release/cutover. Pulling/test-green GitHub code is NOT proof that running consumer process loaded new code.
- Before ANY activation require the exact Firefox temporary add-on and managed ChatGPT URL; new source and old rollback digests; operator STOP/arm and outbound owner; reconcile 2 preserved pending missions; ensure triggering relay command is fully delivered before independent, bounded activation. Do not overwrite both service workers or adapters just because they differ from source.
- Preserve all old incidents/audits, including the fresh-epoch five-slot audits; no blind replays.

**Verdict:** Source repair staged in GitHub; no runtime repair or live result ACK acceptance claimed.
