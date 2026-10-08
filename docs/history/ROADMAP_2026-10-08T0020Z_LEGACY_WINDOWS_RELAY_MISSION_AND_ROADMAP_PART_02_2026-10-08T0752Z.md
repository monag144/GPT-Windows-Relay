# Archived source fragment 2/3 — 2026-10-08T0752Z

### P3 — Clipboard / job-application helper foundation

Build primitives before app-specific automation:
- clipboard read/write;
- explicit target-field text entry;
- resume-data representation;
- prompt/field → answer mapping;
- audit-friendly action/result flow.

Then branch into a simple difficult-job-application helper using:
- resume data;
- copied form question/context;
- ChatGPT reasoning;
- relay input back into the application.

### P4 — Screenshot-on-request capability

Add:
- explicit screenshot request action;
- screen/window/region targeting;
- return path suitable for ChatGPT visual inspection;
- bounded storage/cleanup;
- no continuous capture unless a future feature explicitly requires it.

### P5 — Broader UI interaction adapters

Only after the primitives above are stable:
- richer Windows UI Automation helpers;
- app-specific adapters;
- optional higher-level workflows.

## Engineering process rule

Before new relay forensics:
1. read `docs/windows-relay-established-facts.md`;
2. search the engineering log;
3. consult relevant conversation/project history;
4. only then launch new probes.

New confirmed findings, root causes, false leads worth remembering, architecture decisions, and validation proofs must be logged back to GitHub promptly.


## Reliability-first roadmap amendment — 2026-10-06T0300Z

The consumer mission remains the complete Firefox -> Chrome -> Edge zero-touch acceptance program. This timestamped amendment changes engineering order because the live transport has materially regressed in practical autonomy.

### R0 — restore sustained relay forward progress
- Reproduce and measure the Director-reported regression instead of accepting one- or two-operation success as sufficient.
- Use the documented r25 passing baseline and the better historical operation range as comparison evidence; do not assume a regression commit without proof.
- Inspect scanner ownership, `DISCOVERED -> execution` settlement/reacquisition, operation locking, result delivery/finalization, browser lifecycle and recovery interactions.
- Harden `DISCOVERED -> execution` with a transition-specific watchdog and exact-once-aware recovery.
- Preserve immediate remount reacquisition, the approximately 15-second broad recovery pass, approximately five-minute dead-man, collapsed/folded recovery, delayed/out-of-order reconciliation and backend dedupe.
- Separate visible-result delivery from ChatGPT-turn completion so finalization recovery cannot re-execute the Windows action.
- Require sustained-operation/soak evidence with intervention counts before declaring relay autonomy restored.

### R1 — finish independent recovery
- Re-run the detached Plane-D readback-context probe and preserve exact read failures.
- Live-prove visible ChatGPT error detection, detected/cleared lifecycle and screenshot-before-repair behavior.
- Close durable recovery ownership/deadlines and exact-packet F-005 visibility.
- Provide an audited independent screenshot attachment path that can actually present recovery evidence to GPT when primary content integration is broken.

### R2 — finish the consumer browser matrix
- Firefox: zero-touch One-Click setup, automatic relay add-on recovery, normal mission, canonical sandwich, exactly-once execution, visible exact result, screenshot attachment and injected-failure recovery.
- Chrome: full One-Click E2E including injected recovery.
- Edge: full One-Click E2E including the historical false-ready/postload race.
- Verify GitHub and Google Drive connection persistence plus approval-surface UX.
- Preserve the clean-consumer rule: after initial mission submission, unplanned manual reload, Send, extension recovery, terminal work or physical diagnosis is an engineering incident.

### R2a — low-priority exact GitHub approval-card UX
- Director screenshot evidence at 2026-10-06T0259Z identifies the recurring native ChatGPT GitHub approval card at the bottom of the managed conversation: `Allow ChatGPT to use GitHub?` with `Always allow`, `Deny`, and `Allow once` controls.
- Requested behavior: when the managed conversation is already at the bottom and this exact positively identified GitHub approval surface is present under the Director's pre-authorized policy, automatically invoke the configured GitHub approval choice instead of leaving the run stranded.
- Do not generalize this into blind clicking of unknown providers, differently worded security surfaces, or ambiguous controls. Positive provider/text/control identity and bottom-of-conversation state are prerequisites.
- This is intentionally below relay forward-progress/recovery work in priority.

### R3 — rotation and release closure
- Working series for this agent is `PCE7.400` through `PCE7.499`, per Director instruction.
- At `PCE7.500`, create the complete timestamped handoff and exercise automatic fresh-chat/next-agent rotation.
- A failed primary rotation must fall back to the independent recovery plane; a handoff cannot be stranded solely because the browser-resident transport being tested failed.
- Close the screenshot/result/recovery evidence bundle and dated audit/index work.
- Do not promote `consumer/one-click-go` until the complete acceptance matrix passes.

### Evidence discipline
- The r25 handoff proves the specific recorded PASS items; it does not, by itself, prove an all-night uninterrupted runtime duration.
- The Director's long-autonomy and present approximately-two-operation observations are valuable field evidence and should be reproduced and quantified.
- At the 2026-10-06T0257Z comparison checkpoint, r29 SHA `3d8ef23ab9f281ef8961aaf016f94c34f9e2cce9` was exactly 200 commits ahead of audited stable `d5b9db7ad785b5cae8dc3b64219303b9fcfa634a` and behind by 0. This is a regression-search boundary, not causal attribution.
- Preserve newer safety/recovery capabilities while restoring the simpler practical reliability demonstrated by the older baseline.


## Rotation/session identity amendment — 2026-10-06T0310Z

Incident `INCIDENT_2026-10-06T0309Z_PCE7_SESSION_ESCAPE_AND_UNNAMED_ROTATION.md` adds a concrete acceptance requirement to R3:
- managed rotation must never strand the Director on generic ChatGPT/home or require manual navigation back to the engineering conversation;
- a fresh managed engineering chat must be positively created/selected, automatically given the configured agent/chat name, receive the handoff, and have its identity verified before rotation is considered complete;
- deferred rotation/control actions require stale-series/session-generation protection so an obsolete rotation cannot hijack a later PCE series;
- manual return or manual renaming is an engineering incident, not successful rotation.

### Reliability-first roadmap amendment — 2026-10-06T0340Z

PCE7.405 produced no result and the live HUD reached about 500 seconds since the last action detected. This is a new R0 acceptance failure: the recovery system must preserve an **outstanding-work obligation independently of whether ChatGPT currently materializes the command turn in the DOM**.

R0 now additionally requires:

1. A discovered-but-unresolved relay packet keeps a durable per-tab recovery obligation across DOM virtualization, content-script remount, and page reload.
2. Temporary absence of the command turn must never clear that obligation; only exact matching visible user-result proof or an explicit terminal disposition may clear it.
3. A stale `activeRelayOperationId` gets a bounded lease. After the deadman interval, if no execution is genuinely inflight, recovery must release stale ownership and use the backend exact-once boundary for safe replay.
4. Recovery reloads must be rate-limited so the stronger deadman cannot become a refresh storm.
5. The live Firefox runtime must be updated and proven; source commits alone are not acceptance.

Initial source implementation: `104f9e80d0f9fa8670cfb4f49bc5dd55abe2e010`; regression contract: `2917a8b1d6737f2593773e7df7528145969c87c3`.



### R0 HUD observability/recovery amendment — 2026-10-06T0455Z

The PCE7.410–PCE7.415 recovery sequence adds a reliability acceptance requirement: **relay recovery and HUD recovery must be coupled at the supervised product boundary without multiplying logical HUD instances**.

- `hud.py --once` is a documented diagnostic contract and must remain covered by a behavioral test.
- Process-budget checks must count logical parent/child trees, not mistake a venv shim plus real interpreter for duplicate logical services.
- The actual startup owner must ensure relay + HUD recover together; manually booting only `windows_relay.py server` is not full product recovery.
