# Windows Relay task backlog — 2026-10-09

**Scope:** `monag144/GPT-Windows-Relay`, Pacific-local date. Revised after the Director permanently retired autonomous agent-switching. Historical rotation tasks are archived under `windows-relay/bin/AGENT_SWITCHING_RETIREMENT_2026-10-09.md`, not remaining milestones. This is a source/planning update, not a live Client rollout.

## P0 — safety and reliable command execution
- [ ] **Verify then repair if still relevant:** the **Client** still has the non-atomic action-ID lookup/claim sequence (PCE16.000 confirms), and PCE15.043 simulated a duplicate claim. There is **no new evidence of real duplicate shell executions**; run isolated repeat/concurrency tests with no side effects before a minimal durable fix.
- [ ] Investigate processed-ID retention and historical replay protection: Client source still evicts after 500 entries, while the observed state contains **501 entries** (PCE16.003). Determine whether any are INFLIGHT/non-evictable, and protect against post-eviction execution without clearing or replaying live records. No observed live duplicate is established.
- [ ] Preserve the **existing operator controls START / STOP / RESTART / OFF / KILL** and conversation ownership. **ARM is not a HUD button.** Keep its authenticated backend permission/quiescence mechanism under STOP/START to avoid a safety regression. PCE15.050 cross-conversation rejection was protective; do not bypass.
- [ ] Confirm authenticated localhost 8766 normal same-chat packet -> exactly-one Windows execution -> exact saved result -> one delivered visible reply, including failure/recovery. No GUI handoff automation necessary.

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
- [ ] Add **RETRY** with explicit selected-tab/delivery safeguards and **FORCE** to promptly re-inspect the *currently visible* ChatGPT relay packet. FORCE must not clear persisted action IDs, circumvent STOP/owner checks, or automatically resend uncertain output. Native content script has `forceRecoveryPacketInspect()` but no external FORCE listener (PCE16.003).
- [ ] Expand visible-error, network/stream, throttling/rate-limit, and prolonged hitch detection. The content script already detects several error surfaces; classify unknowns as evidence, capture diagnostics and escalating incident context. After bounded same-chat recovery failure, **prepare** the approved one-shot successor handoff; don't silently revive automatic switching.
- [ ] Reconcile **two queued Chrome-only consumer missions** from October 4 (IDs `consumer-20261004T052926Z-293c16e0` and `consumer-20261004T052951Z-afbbaf68`). Do not execute, dequeue or expose their text until their ownership/purpose is verified and cleanup approved.

## P2 — operator experience and optional features
- [ ] Improve HUD clarity, incident/screenshot visibility, and user-facing diagnostics without changing functioning controls.
- [ ] Continue consumer one-click installation, governed source/Client sync, update safety and downstream user-requested workflows (e.g. job applications) as separately scoped projects.

## Governance and evidence
- **Before each PCE operation**, reread canonical GitHub `consumer/control_harness.py` and current dated roadmap, and compare the actual installed files when relevant. Preserve GitHub-first five-operation audits, drift-focused twenty-operation reviews, issued-ID consumption, and unique PCE ordinals. PCE16.000–.003 completed OK in read-only mode; PCE16.004 is next. Before .005, commit and read back the .000–.004 audit on `main`. `PCE15.050` was emitted and rejected, **not free to retry**. No GitHub Actions usage while credits unavailable.
- **Permanent retirement:** Do not implement/test operation-count rotation, extension-driven new-agent navigation, UIA fallback transfers, scheduled agent watchers or the replacement switching project. Existing UIA/clipboard/tab tools are temporarily suspended **for agent switching only**, not removed from normal relay execution or recovery. Reference the dated policy `docs/policy/SCRIPT_ONLY_AGENT_HANDOFF_2026-10-09.md`.
- Last verified product grade **F / BLOCKED**, 11/28; G16 unknown, G26 0/60, G27 0/2. New grades require new real evidence.
