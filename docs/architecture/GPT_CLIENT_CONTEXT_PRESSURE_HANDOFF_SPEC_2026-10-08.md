# GPT client continuity: context-pressure detection + durable agent-to-agent handoff

**SPECIFICATION — NOT IMPLEMENTED, ENABLED OR LIVE-TESTED.** User requested this on 2026-10-08 after repeated apparent conversation-length pressure during PC Engineering. This is **not native model memory compaction**. It is a GPT-client/Relay continuity protocol that creates a reproducible work dump and instructs a fresh assistant conversation to reconstruct context by reading authoritative operations, rather than silently squeezing history into an unreliable model summary.

## 0. Problem and diagnostic honesty
An extension can see its **own message/event history**, DOM state, and Relay transport metadata. It cannot reliably read the model's remaining context-token budget from ChatGPT internals. A long thread, a truncated Relay result (`stdout_truncated`), stalled response, or visible `Connection interrupted. Waiting for the complete answer` banner may indicate different failure mechanisms. **Do not conflate** message length, model context exhaustion, output truncation, and network/stream interruption. Preserve event provenance, classify confidence, and never claim a confirmed token-limit event without an explicit supported signal.

## 1. State machine
`NORMAL → PRESSURE_SUSPECTED → HANDOFF_REQUIRED → SNAPSHOT_IN_PROGRESS → SNAPSHOT_VERIFIED → ROTATION_CANDIDATE → NEW_CHAT_VERIFIED → RESUMED`

Alternative outcomes: `OBSERVATION_ONLY`, `WAIT_FOR_CURRENT_ACTION`, `BLOCKED_STOP`, `UNKNOWN_EXECUTION`, `NEEDS_OPERATOR`, `FAILED_HANDOFF`. Every transition journaled atomically by session/conversation ID and UTC monotonic local sequence, with a unique handoff ID and tamper-evident SHA256 manifest.

**Pressure discovery** (configurable signals; default to observation only): operation budget approaching 100, high same-chat assistant/user message count, high cumulative normalized content estimate, repeated aborted/collapsed generation, a user-issued rotation request, failed new-chat ability, or explicit UI limit banner. Preannounce before deadline, but NEVER interrupt or suppress a safely executing in-flight Windows action just to rotate. `stdout_truncated` causes *result evidence compaction* independently: save complete result locally and show concise result path, not artificial chat rotation.

Thresholds should be tested, not guessed; keep both hard engineering ordinal budget PCE11.000..100 and separately calibrated UI/context-pressure estimates. Include hysteresis/cooldown and avoid restart/rotation loops.

## 2. Snapshot envelope — minimum required data
Canonical durable Markdown + machine-readable JSON, with a content hash and root path:
1. `handoff_id`, schema_version, created_utc, source_chat identity (URL/ID sanitized), current agent/series and next *unused* ordinal; exact title only if independently verified.
2. User's original mission, current success criteria, constraints, explicit STOP, exclusions, deferred work, current intent and most recent priority/steering. Preserve exact wording of high-impact instructions as minimal quotes, not raw entire transcript.
3. Authoritative GitHub repo, target active branch and **observed commit SHA**, approved detached docs branch if any, clean worktree observation and source-vs-live SHA/provenance. Never imply code in the docs branch is live.
4. Full attempted-operation ledger: ordinal, unique packet ID, action kind, status (PASSED/FAILED/BLOCKED/UNKNOWN), execution confirmation, result path, incident, side effects, rollback identity, safe replay classification; summarize windows compactly but include links to all audit/review records.
5. Last PCE checkpoint audits and formal 20-operation review, next mandatory audit/review preconditions, five full-read controls with SHA256; source-only pass counts and runtime-canary results clearly distinguished.
6. Current live Relay port/PID/ARMED/outbound/pending/STOP generation as **timestamped last observed**, tab/window/loaded extension state if verified, mission status, unresolved duplicate/unknown result risk.
7. Named immutable backups, incident roots and rollback status (verified archive is not proof that restore was performed).
8. Residual RED/YELLOW blockers, unanswered questions and next *read-only* diagnostic/operation proposal with safe acceptance criteria.
9. Human/operator action required versus what an automated agent may do; historical commands marked **NON-EXECUTABLE EVIDENCE**, not instructions to replay.
10. Evidence files (GitHub permalinks, local paths, source hash), omission list, privacy/security redactions, end-of-generation state.

**No secrets**: never serialize auth tokens, cookies, account credentials, backup codes, unmasked access keys, private Gmail or other unrelated records. No unbounded raw chat dump; attach authorized sanitized source references.

## 3. Two-phase atomic handoff
**Phase A: Prepare and prove.** Require no uncertain in-flight action: consult backend `/packet-status`/processed ledger for the last packet, wait for acknowledgements, quarantine unknown side effects. Generate snapshot in a fresh temp folder, write Markdown, JSON and evidence manifest, fsync/atomic replace, verify hashes by independent reopen, and optionally push via GitHub-first isolated docs branch. Preserve original chat and last result even if snapshot fails; never mark successful handoff before the files exist.

**Phase B: Controlled new-chat transfer.** Only when `SNAPSHOT_VERIFIED` and explicit rotation policy/user instruction authorizes; exact target Firefox process/window/tab/conversation identified, operator STOP inactive, no unsent/unknown operation. Establish a fresh ChatGPT chat through the verified UI; submit a **single short read-only bootstrap prompt** containing the handoff location and directive to read original records, not the preceding runnable relay packet. Verify new chat URL/title/conversation ID, and ask the new agent to report reconciliation and next ordinal. Do not delete/archive prior chat automatically. If UI detection or submission is ambiguous, preserve handoff and report `NEEDS_OPERATOR`, without opening multiple chats or retransmitting commands.

Recovery if ChatGPT response visibly stalls is a *separate* state machine described by `docs/incidents/INCIDENT_2026-10-08T1928Z_PCE11_USER_REPORTED_CONNECTION_INTERRUPTED_WAITING_COMPLETE_ANSWER.md`. A partial assistant answer does not imply a Windows packet failed, nor license resubmission.

## 4. Bootstrap prompt contract for successor
> You are inheriting the GPT Windows Relay engineering mission. First read **the complete handoff** and its linked operation ledger, canonical `consumer/control_harness.py`, `windows-relay/TASKS.md`, active roadmap `docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md`, `docs/windows-relay-established-facts.md`, and `docs/relay-sandwich-procedure.md`. Read all referenced audit/review and incidents, especially the last five ordinals; compute or verify SHA256 in the current clean checkout and run `engineering_preflight(repo,next_ordinal,series=11)` before any numbered action. Query the backend ledger for uncertain/missing packet outcomes. Never replay a prior packet or assume a source test equals live runtime acceptance. Preserve backups, user STOP and exact-once behavior. Report a concise reconciliation (verified facts, blockers, next SAFE ordinal) before any mutation.

The bootstrap must not claim that ChatGPT automatically imported old conversations or acquired true hidden model memory. The new agent reconstructs from durable artifacts and source links.

## 5. Separation of concerns and implementation sketch
- `extension/content.js` and persistent mirror: low-noise DOM/banner sensing, measured message inventory, stable selected-conversation identity, bounded generation/idle transitions; no raw scraping of unrelated tabs.
- background/service-worker persistent port: event journal, last result ID/hash and backend execution truth, cooldown, STOP preemption.
- `consumer/recovery_supervisor.py`: policy classification of context pressure versus stream interruption, no phantom repair effects.
- new `consumer/continuity_handoff.py`: pure deterministic redaction, JSON/Markdown serializer, manifest hash, atomic persistence, audit retrieval and idempotent state transitions. Unit tests should be source-only and network-free.
- optional GitHub publishing: separate documentation branch, preserving the active release branch's exact pinned SHA. No automatic merge into release branch mid-canary.
- HUD: unobtrusive state `HANDOFF READY` with evidence location and BLOCKED reasons; never label a submitted but unacknowledged packet as DONE.

**Testing requirements**: model budget unknown, false-positive length signal, hard ordinal 100, user STOP, backend action INFLIGHT/UNKNOWN, duplicate/late results, PCE10 old DISCOVERED suppression, stdout-truncated output, cancelled assistant answer, multiple Firefox windows/tabs, stale URL/title, failed upload, stale Git branch, user side effects, interrupted refresh, power loss, malformed manifest, redaction, new-chat idempotency and browser restart. Require targeted and full Windows/consumer suites, JS syntax and mirror checks; test in a *disposable* ChatGPT conversation, not active production.

## 6. Audit, review and promotion gates
At a five-slot boundary, create the preceding audit **before** the numbered multiple-of-five; at a 20-slot boundary, additionally publish/reconcile 20-operation review. Handoff after PCE11.033 is INTERIM: .034 result unknown, so do not fabricate .030–.034 full audit and do not issue .035 on this document alone. At PCE11.100 rotate to PCE12 rather than .101. Separate human-requested early rotation can occur at any safe checkpoint but does not consume/reassign numbered backend operation IDs.

Success metrics: every handoff artifact complete/independently reopenable; no skipped attempts or lost constraints; zero duplicate execution; every resumed agent verifies source/ledger before acting; no manual rescue needed for ordinary high-pressure rotation; a visible, trustworthy failure on uncertainty instead of false success. **Status on creation: design requested and documented only.**
