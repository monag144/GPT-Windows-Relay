# Windows Relay task backlog — 2026-10-09

**Scope:** `monag144/GPT-Windows-Relay`, Pacific-local date. Revised after the Director permanently retired autonomous agent-switching. Historical rotation tasks are archived under `windows-relay/bin/AGENT_SWITCHING_RETIREMENT_2026-10-09.md`, not remaining milestones. This is a source/planning update, not a live Client rollout.

## P0 — safety and reliable command execution
- [ ] **Verify then repair if still relevant:** the **Client** still has the non-atomic action-ID lookup/claim sequence (PCE16.000 confirms), and PCE15.043 simulated a duplicate claim. There is **no new evidence of real duplicate shell executions**; run isolated repeat/concurrency tests with no side effects before a minimal durable fix.
- [ ] Investigate processed-ID retention and historical replay protection: Client source still evicts after 500 entries, while the observed state contains **501 entries** (PCE16.003). Determine whether any are INFLIGHT/non-evictable, and protect against post-eviction execution without clearing or replaying live records. No observed live duplicate is established.
- [ ] Preserve the **existing operator controls START / STOP / RESTART / OFF / KILL** and conversation ownership. **ARM is not a HUD button.** Keep its authenticated backend permission/quiescence mechanism under STOP/START to avoid a safety regression. PCE15.050 cross-conversation rejection was protective; do not bypass.
- [ ] Confirm authenticated localhost 8766 normal same-chat packet -> exactly-one Windows execution -> exact saved result -> one delivered visible reply, including failure/recovery. No GUI handoff automation necessary.

## P0 — prevent governance reintroduction into runtime

- [x] Proven PCE17.021 legacy code defect: the dispatcher called an incompatible audit-receipt preflight; .005/.010/.015/.020 were rejected despite existing GitHub audits.
- [x] Current GitHub execution policy abolishes operational governance and makes the compatibility helper nonblocking; current root backend has no checkpoint preflight.
- [ ] Run source regression and prove a safe live authenticated fifth-slot command without any audit receipt after approved local deployment. STOP/owner/token/dedup protections remain mandatory.

## P0 — canonical extension/backend transport contract mismatch (PCE17.022)
- [ ] `PCE17.022-launch-codex-independent-single-build-cutover-engineering` returned browser `ACTION_FAILED` with generic `RelayError`, **not** a native receipt. Treat Codex launch as **uncertain** until saved result, processed-ID state, worker PID and `PCE17-022-CodexCutover` logs are checked. Do not reissue .022 or start another Codex run blindly. See `docs/incidents/WINDOWS_RELAY_PCE17_022_CODEX_LAUNCH_ACTION_FAILED_2026-10-11.md`.
- [ ] WIP source inspection: `windows_relay.py` POST /action requires `issuance` and `owner` plus operator-bound backend owner, but matching `extension-persistent/service_worker.js` posts only `{packet}`. This is a **verified source contract mismatch** and possible cause of generic RelayError if canonical backend is active; actual loaded backend identity remains unknown. Repair and test secure issuance/owner propagation and explicit operator owner binding, **not** by weakening authenticated transport or STOP. Improve feedback to show sanitized specific error detail for diagnosis.
- [ ] After repairing and unit/integration tests, verify exact on-disk vs loaded Firefox extension bits, correct token pairing, root backend/HUD identities, and one harmless action. Do not perform a live cutover until browser transport compatibility and state rollback gates pass.

## P0 — stalled scanner and user rescue (reported 2026-10-11 PDT)
- [ ] **Reproduce and repair STALLED command pickup / response delivery.** Operator reports that reprinting an existing `[GPT_WINDOWS_ACTION]` block may prompt a stalled relay/Firefox scanner to resume. This is an observed operator workaround/hypothesis, **not** evidence that replay is safe or that reprinting actually fixes the failure. Capture HUD phase, browser and backend heartbeat, action discovery, ownership, dispatch, exact saved result and delivery acknowledgement; classify absence of a result separately from execution failure.
- [ ] **Self-recover without user command reprinting.** Implement bounded same-chat scanner reinspection/diagnostic FORCE/RETRY with observable HUD status and event timestamps; do not restart agent chats, relax STOP/authentication/owner gates, or make the operator paste PowerShell. Preserve the unified development build, single HUD and One-Click Go policy.
- [ ] **Never use duplicate execution as a recovery strategy.** PCE17.012-independent-cutover-worker-probe was issued, but a native receipt had not yet been shown when this was logged. Treat its execution/result as uncertain until inspected. Do not re-send PCE17.012 with the same ID; use a fresh uniquely identified **safe** diagnostic or check its persisted state first. Test deduplication and previously reported claim/eviction deficiencies.
- [ ] **Acceptance gate:** demonstrate automated return from STALLED without reprinting, exactly one harmless command execution and one visible receipt under ChatGPT streaming, page refresh, extension reload and temporary browser disconnection; log timing, no duplicate sends, operator rescue count and unresolved cases.
- [ ] **Classify READY outbound journal buildup before migration.** PCE17.017 observed 519 records marked READY with `outbound_owner=browser`; canonical WIP source records READY on completed command and allows only owner `windows` to claim Windows-side delivery. Do **not** equate 519 READY with 519 unsent messages. Investigate live nested runtime and browser-delivery acknowledgements, retention, and migration requirements read-only; never mass resend/clear on phase alone. See `docs/incidents/WINDOWS_RELAY_PCE17_017_PYTHON_ARGUMENT_QUOTING_AND_READY_JOURNAL_2026-10-11.md`.

## P1 — tested deployment and user-visible delivery
- [ ] Determine GitHub/development/Client/loaded Firefox extension and backend identity. Reconcile G04 deployment drift, G16 unresolved originating-tab/loaded extension identity. A file existing on disk is not loaded-code attestation.
- [ ] Build and verify a coherent **privately distributed, Mozilla-signed unlisted Firefox XPI** using existing signing and installation policy scripts, with rollback and actual installed-profile/loaded-code attestation. Do not publish publicly or claim unlisted means hidden from Mozilla.
- [ ] Demonstrate independently witnessed real ChatGPT sends and receipts under exact identity/STOP/collision tests (last G26 **0/60**), then 12h and 24h endurance (G27 **0/2**). Static-marker unit tests and headless readiness do not count.
- [ ] Test controlled browser, service and Windows restart/recovery behavior, preserve screenshot evidence, no duplicate sends and no user rescue under specified failures. Verify Chrome/Edge consumer compatibility where supported.

## P1 — standardize confirmed one-shot operator workflows
- [ ] Preserve and verify the existing **working** `Client/Relay/test/Run-Copy-Contents.cmd` and companion. Source engineer derives next PCE number from verified current series +1 and stages `Copy Contents.txt`; one user-requested launch, then prove actual posted turn. Never recreate broken automatic switching.
- [ ] Prefer bounded scripted *machine actions* for directly requested UI tasks when evidence supports them; maintain focus/input/readback safeguards and explicit user control. **Do not** use this goal to restore unattended agent switching.
- [ ] After separate authorization and source+test review, roll out retirement to the installed Client and positively attest that no legacy rotation timer or extension trigger remains loaded. Repository changes alone are not activation.

## P1 — HUD and failure detection (prioritized by operator request)
- [ ] **Preserve the installed five working buttons.** PCE16.002 confirms Client HUD has START/STOP/RESTART/OFF/KILL; development has RETRY, and neither has FORCE. Avoid replacing the installed HUD with GitHub's older three-button source.
- [ ] **HUD operator conversation controls (design recorded 2026-10-10):** implement visible **FOCUS CHAT** (foreground only the verified exact Firefox ChatGPT tab), **SELECT CHAT / CLAIM–CONNECT** (operator-initiated selection and positively acknowledged legitimate conversation ownership), and a **FORCE HUD button** (bounded reinspection of the current authorized packet, not a typed FORCE command). Present bound vs active conversation, claim state/rejection and last FORCE outcome. All must respect STOP, ownership, dedupe and permanent no-automatic-handoff policy. **Design only—unimplemented.** See [Windows Relay HUD conversation controls](../design/WINDOWS_RELAY_HUD_CONVERSATION_CONTROLS_2026-10-10.md).
- [ ] Add **RETRY** with explicit selected-tab/delivery safeguards and **FORCE** to promptly re-inspect the *currently visible* ChatGPT relay packet. FORCE must not clear persisted action IDs, circumvent STOP/owner checks, or automatically resend uncertain output. Native content script has `forceRecoveryPacketInspect()` but no external FORCE listener (PCE16.003).
- [ ] Expand visible-error, network/stream, throttling/rate-limit, and prolonged hitch detection. The content script already detects several error surfaces; classify unknowns as evidence, capture diagnostics and escalating incident context. After bounded same-chat recovery failure, **prepare** the approved one-shot successor handoff; don't silently revive automatic switching.
- [ ] Reconcile **two queued Chrome-only consumer missions** from October 4 (IDs `consumer-20261004T052926Z-293c16e0` and `consumer-20261004T052951Z-afbbaf68`). Do not execute, dequeue or expose their text until their ownership/purpose is verified and cleanup approved.

## P2 — operator experience and optional features
- [ ] Improve HUD clarity, incident/screenshot visibility, and user-facing diagnostics without changing functioning controls.
- [ ] Continue consumer one-click installation, controlled source/Client sync, update safety and downstream user-requested workflows (e.g. job applications) as separately scoped projects.

## Engineering evidence; NEVER runtime governance

- No five-operation audit, twenty-operation review, checkpoint receipt, per-operation GitHub source reread or benchmark is required to execute a Windows command.
- Maintain historical action-ID records and technical test/benchmark evidence when useful; they never authorize execution. Backend identity, STOP, token, owner and durable deduplication provide runtime safety.
- Operator-controlled one-shot handoff only; no autonomous switching or hidden rotation. Historical incidents are evidence, not operating instructions.
- The prior strict F / 11-of-28 benchmark and real-message/endurance gaps concern release acceptance, not governance.
