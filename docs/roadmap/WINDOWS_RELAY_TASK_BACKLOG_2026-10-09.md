# Windows Relay task backlog — 2026-10-09

**Scope:** `monag144/GPT-Windows-Relay`, Pacific-local date. Revised after the Director permanently retired autonomous agent-switching. Historical rotation tasks are archived under `windows-relay/bin/AGENT_SWITCHING_RETIREMENT_2026-10-09.md`, not remaining milestones. This is a source/planning update, not a live Client rollout.

## P0 — safety and reliable command execution
- [ ] Make backend action-id lookup and claim one durable atomic transaction. Isolated PCE15.043 reproduced concurrent duplicate synthetic executions; block identical-ID parallel commands, changed-payload collisions, unsafe restart cases and uncertain outcomes.
- [ ] Prevent post-500 processed-ID eviction from enabling re-execution. Keep durable replay tombstones/identity hashes and enforce pre-execute collision checks across restarts. PCE15.047 source-level proof, PCE15.049 memory-only prototype; **not fixed in Client**.
- [ ] Preserve and verify operator STOP/ARM and exact-conversation sender ownership, without allowing same-session stale packets from old chats. PCE15.050 cross-conversation rejection was protective; don't bypass it.
- [ ] Confirm authenticated localhost 8766 normal same-chat packet -> exactly-one Windows execution -> exact saved result -> one delivered visible reply, including failure/recovery. No GUI handoff automation necessary.

## P1 — tested deployment and user-visible delivery
- [ ] Determine GitHub/development/Client/loaded Firefox extension and backend identity. Reconcile G04 deployment drift, G16 unresolved originating-tab/loaded extension identity. A file existing on disk is not loaded-code attestation.
- [ ] Build and verify a coherent signed/persistent five-file Firefox release, with rollback; avoid historical XPI backup contamination. Do not deploy automatically as part of archive changes.
- [ ] Demonstrate independently witnessed real ChatGPT sends and receipts under exact identity/STOP/collision tests (last G26 **0/60**), then 12h and 24h endurance (G27 **0/2**). Static-marker unit tests and headless readiness do not count.
- [ ] Test controlled browser, service and Windows restart/recovery behavior, preserve screenshot evidence, no duplicate sends and no user rescue under specified failures. Verify Chrome/Edge consumer compatibility where supported.

## P1 — standardize confirmed one-shot operator workflows
- [ ] Record and verify the existing `Client/Relay/test/Run-Copy-Contents.cmd`, `Copy-Contents-To-ChatGPT.ps1`, and `Copy Contents.txt` without rewriting a working script. Source agent derives next PCE number by verified current series +1; no fixed successor; user requests launch explicitly; confirm posted user turn, not just new chat/Enter dispatched.
- [ ] Prefer bounded scripted *machine actions* for directly requested UI tasks when evidence supports them; maintain focus/input/readback safeguards and explicit user control. **Do not** use this goal to restore unattended agent switching.
- [ ] After separate authorization and source+test review, roll out retirement to the installed Client and positively attest that no legacy rotation timer or extension trigger remains loaded. Repository changes alone are not activation.

## P2 — operator experience and optional features
- [ ] Improve HUD state labels, STOP, retry, incident/screenshot visibility and user-facing diagnostics; preserve successful existing capabilities.
- [ ] Continue consumer one-click installation, governed source/Client sync, update safety and downstream user-requested workflows (e.g. job applications) as separately scoped projects.

## Governance and evidence
- Preserve GitHub-first five-operation audits, twenty-operation reviews, issued-ID consumption and unique PCE ordinals. PCE16 starts at `PCE16.000`; `PCE15.050` was emitted and rejected, **not free to retry**. No GitHub Actions usage while credits unavailable.
- **Permanent retirement:** Do not implement/test operation-count rotation, extension-driven new-agent navigation, UIA fallback transfers, scheduled agent watchers or the replacement switching project. Existing UIA/clipboard/tab tools are temporarily suspended **for agent switching only**, not removed from normal relay execution or recovery. Reference the dated policy `docs/policy/SCRIPT_ONLY_AGENT_HANDOFF_2026-10-09.md`.
- Last verified product grade **F / BLOCKED**, 11/28; G16 unknown, G26 0/60, G27 0/2. New grades require new real evidence.
