# PCE7 managed-session escape and unnamed rotation incident — 2026-10-06T0309Z

Timestamp: 2026-10-06T0309Z (2026-10-05 20:09 PDT)  
Class: INCIDENT / SESSION IDENTITY / ROTATION / USER INTERVENTION  
Branch: `consumer/r29-firefox-offline-tray`  
Disposition: OPEN — exact late-execution state requires backend/event proof

## Director-observed facts

After the successful read-only PCE7.401 forensics result, managed Firefox left the intended PCE7 engineering conversation and displayed the generic/normal ChatGPT screen. The Director had to navigate Firefox back to this PCE7 engineering conversation manually.

The Director also had to rename the agent/chat manually. Automatic naming is now an explicit Director requirement for managed fresh-chat/next-agent rotation so the new conversation has the intended engineering identity without human cleanup.

PCE7.402 had been emitted immediately before the Director reported this incident. No PCE7.402 result had been observed at the time of the report. Do not infer execution or failure; query backend exact-once state before any replacement action.

## Immediately preceding evidence

PCE7.401 proved that historical rotation packet `PCENG-A6.400-rotate-to-agent7` had no backend reservation and no saved result at the instant PCE7.401 read state, but browser events showed A6.400 repeatedly queued/deferred behind stale owner `PCENG-A6.399ay-supervisor-hardening-and-detached-read-context`.

Representative lifecycle:
- `relay_action_queued`, reason `active_operation`, owner A6.399ay;
- `relay_action_deferred_for_active_operation`;
- repeated `relay_packet_discovered` / queue/defer cycles.

This tied the A6.400 rotation failure to stale browser-side operation ownership rather than proving a simple 500 ms settle-timer failure.

## Causal hypothesis — not yet proven

A6.400 may have remained in the in-memory deferred-action queue and drained only after PCE7.401 result handling released or changed the stale owner state. If so, the historical rotation operation executed late and navigated Firefox away from the PCE7 engineering conversation after the new agent series was already underway.

This hypothesis fits the observed navigation but is not evidence until a post-incident check finds the A6.400 backend reservation/result and matching lifecycle timestamps. Alternative causes remain open.

## Why this is a release-blocking reliability concern

The repository already requires:
- browser target/tab/conversation identity tracking;
- no unplanned user action after initial mission submission;
- exact safe autonomous return/navigation to the designated engineering conversation;
- idempotent fresh-chat rotation every 100 operations;
- autonomous new-agent takeover.

This incident violated the session-return/no-user-intervention requirement. A delayed stale rotation, if confirmed, also means a previously deferred control-plane action can hijack a later valid engineering session.

The automatic naming requirement is a Director clarification added by this incident. Older reviewed documentation explicitly requires fresh-chat rotation and conversation identity/return, but the reviewed text did not state automatic chat renaming as explicitly; do not misquote it retroactively.

## Required investigation and repair

1. Query exact backend state and saved results for historical A6.400 after 03:04Z.
2. Query exact backend state for PCE7.402 before issuing any same-purpose replacement.
3. Inspect browser lifecycle timestamps proving what navigation/rotation occurred.
4. If A6.400 executed late, classify the path that released/drained it and preserve its exact result.
5. Add an epoch/session-generation or equivalent stale-control-action gate so an obsolete rotation cannot hijack a later agent/session.
6. Keep backend exact-once safety authoritative; do not blindly replay A6.400 or PCE7.402.
7. Fresh-chat rotation must positively establish/select the intended new conversation, verify its identity, automatically apply the configured agent/chat name, deliver the handoff, and verify the designated engineering session state.
8. Failure to establish the intended session must enter recovery rather than landing silently on generic ChatGPT/home.
9. Re-run rotation acceptance without Director navigation or renaming.

## Evidence rule

The manual return and manual rename are engineering incidents even if a late rotation is ultimately shown to have executed successfully. Navigation to some ChatGPT surface is not successful rotation; success requires the intended conversation identity, handoff delivery, configured naming, and zero unplanned Director action.


## 2026-10-06T0322Z — PCE7.403 post-incident correction

PCE7.403 disproved the late-A6.400 causal hypothesis. At 03:22:40Z:
- `PCENG-A6.400-rotate-to-agent7` still had no backend processed record and no result file;
- `PCENG-PCE7.402-owner-mutex-forensics` also had no backend processed record and no result file;
- PCE7.401 remained the last confirmed earlier probe in the queried set.

A6.400 browser evidence is nevertheless severe: the event journal records 78 `relay_packet_discovered`, 78 `relay_action_queued`, and 78 `relay_action_deferred_for_active_operation` events, all without backend execution. The observed owner in the captured sequence is A6.399ay.

Therefore:
1. do not attribute the generic-ChatGPT navigation to A6.400;
2. keep the session escape/unnamed-chat incident open with cause unknown;
3. treat PCE7.402 as never executed, not as a completed probe;
4. separately investigate A6.399ay stale operation ownership and the 78-cycle no-forward-progress loop;
5. the repeated queue/defer loop must become a bounded transition failure rather than indefinitely re-reporting discovery.
