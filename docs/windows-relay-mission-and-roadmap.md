# GPT Windows Relay — Mission, Architecture Direction, and Priority Roadmap

This document defines the current mission and product direction for the Windows ↔ ChatGPT relay.

It is intentionally broader than a localhost command executor. The relay is becoming a low-friction Windows interaction bridge that lets ChatGPT reason about a task, request or receive the minimum needed machine context, and then carry out the approved computer-side steps with as little user babysitting as possible.

## Mission 1 — Reliable Windows execution with minimal user intervention

The primary mission is to make ChatGPT capable of reliably performing Windows-side work through a local relay while minimizing the amount of manual recovery, copying, clicking, reloading, terminal interaction, and debugging demanded from the user.

The desired experience is not merely “a command ran.” The desired experience is:

- ChatGPT emits an explicit relay action.
- The browser bridge recognizes only the intended assistant packet.
- The local relay executes the operation safely under the Windows user.
- The result returns to ChatGPT in a compact, usable form.
- Recoverable failures are retried or repaired automatically where safe.
- Completed work is not duplicated merely because a response was lost.
- The browser recovers from ordinary extension/background/content-script disruption.
- The user is kept in the correct place in the conversation without unnecessary scrolling or manual navigation.
- Routine failures consume machine effort before user effort.

The project should continuously reduce the number of times the user must:
- open a terminal;
- paste bootstrap commands;
- visit about:debugging;
- click Reload;
- refresh ChatGPT;
- re-pair;
- re-arm;
- manually inspect logs;
- explain previously established facts again.

The relay is therefore judged on reliability, recovery, continuity, and user effort—not only on command execution success.

## Mission 2 — Autonomous recovery, safe retry, and observable proof

The relay should recover automatically whenever the failure mode is recoverable without creating unsafe duplicate effects.

### Recovery goals

The intended steady-state behavior is:

- Backend crashes or listener loss:
  - supervisor/watchdog restores the relay;
  - relay returns to the intended armed state;
  - browser action transport retries within a bounded window;
  - completed operation IDs replay saved results rather than executing twice.

- Firefox MV3 background suspension:
  - persistent content↔background Port keeps the worker alive while a ChatGPT tab is active;
  - disconnects reconnect automatically;
  - pending browser work fails predictably rather than silently disappearing.

- Content-script or ChatGPT document replacement:
  - browser bridge reinitializes automatically;
  - scanner finds the current conversation using current ChatGPT role selectors;
  - recovery scroll finds the newest valid relay command once;
  - handoff behavior resumes from explicit runtime state where appropriate.

- Full Firefox restart:
  - production target is a signed persistent extension + policy path;
  - normal recovery must not depend on the development-only temporary add-on workflow.

- Windows/login restart:
  - supervised backend should return automatically;
  - persistent browser installation should recover without routine re-pair/reload steps.

### Retry safety

Retries must distinguish transport failure from operation failure.

The relay must preserve:
- durable operation IDs;
- completed-result replay;
- duplicate-inflight suppression;
- interrupted-restart handling;
- ID collision refusal;
- bounded browser retry windows.

The objective is to retry communication without accidentally retrying side effects.

### Proof requirement

A feature is not considered complete merely because source code exists or a static marker is present.

For browser/runtime behavior, prefer one or more of:
- live runtime identity;
- browser telemetry;
- direct UI/runtime inspection;
- end-to-end result proof;
- reproducible regression tests.

The project should make failures diagnosable without asking the user to act as the primary sensor.

## Mission 3 — Architecture direction: a general Windows interaction bridge

### Command execution transport

The command layer remains:

1. plain `command` for simple operations;
2. native `shell:"python"` as the preferred path for complex/multiline orchestration;
3. `command_b64` as a permanent resilience/compatibility fallback;
4. `command_lines` where structured multiline transport is clearer.

Base64 remains intentional redundancy and must not be removed merely because the Python path is preferred.

### Broader interaction model

The relay should evolve beyond shell execution into a small set of explicit, composable Windows interaction capabilities.

The near-term design direction includes:

- **Clipboard text input/output**
  - user can copy difficult form text or app content;
  - ChatGPT reasons over that text;
  - relay can place the resulting answer back onto the clipboard or into the target UI.

- **Troublesome job-application helper branch**
  - future tool can read structured information from the user's resumes;
  - user can copy/paste difficult application prompts or fields to ChatGPT;
  - ChatGPT performs the reasoning/mapping;
  - relay pastes or types the resulting values back into the application;
  - initial version should stay intentionally simple rather than attempting a giant autonomous browser agent;
  - the core loop is: app text → ChatGPT reasoning → relay input.

- **On-request screenshot capture**
  - relay should eventually capture a requested screen/window/region screenshot;
  - image is returned to ChatGPT only when requested;
  - ChatGPT can inspect the screenshot and decide the next action;
  - this provides a visual fallback when DOM/UI Automation/clipboard text is insufficient;
  - screenshot acquisition should be explicit and bounded, not a continuous surveillance feed by default.

- **UI Automation / targeted interaction**
  - use Windows UI Automation where it is more reliable than generic coordinate clicking;
  - favor identifiable controls and state checks;
  - visual/coordinate interaction is a fallback when semantic controls are unavailable.

These capabilities should remain modular. The executor/protocol should not have to be rewritten every time another input/output adapter is added.

## Windows HUD mission

A Windows HUD/control surface is a separate product mission from the existing Android HUD history.

The Windows version should inherit only the useful principles already proven elsewhere:
- visible status should reflect real relay/automation state;
- arm/power controls must be synchronized with the actual backend state;
- the HUD should remain useful even when automation is paused;
- it should expose actionable state rather than decorative telemetry.

Initial Windows HUD scope should stay small:
- relay ARMED/DISARMED state;
- backend health;
- Firefox bridge/content-script state;
- last action status / current activity;
- clear pause/resume or arm/disarm control;
- compact error indicator with a path to details.

Do not overbuild the HUD before the core relay lifecycle is stable.

## Priority roadmap

### P0 — Finish scroll / conversation-follow UX

This is the immediate mission.

Goal:
- after a relay result is delivered, bring the user to the newest conversation edge;
- follow the beginning of the next assistant response for a short bounded handoff window;
- then yield manual scrolling back to the user.

Current important fact:
- the V4 algorithm is already staged in source;
- the live temporary extension points to the correct source directory;
- the unresolved blocker is fresh content-script lifecycle/runtime activation, not the scroll algorithm itself.

Do not redesign the scroll algorithm again until fresh runtime activation is proven.

### P1 — Windows HUD MVP

Once scroll is proven:
- define the minimal HUD data model;
- expose real backend/browser state;
- provide synchronized arm/pause controls;
- keep it lightweight and independent of ChatGPT DOM rendering.

### P2 — Zero-intervention lifecycle hardening

Complete and validate:
- intentional backend restart while extension remains loaded;
- full Firefox restart;
- Windows/login restart;
- persistent signed extension/policy path;
- removal of routine about:debugging dependency.

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
- The named HUD mutex remains the singleton boundary and startup/reconciliation must be auditable.
- A stale browser lifecycle event such as old `action_received` must age into an explicit STALLED/STALE state rather than display STARTING indefinitely.
- Incident: `docs/INCIDENT_2026-10-06T0455Z_HUD_STARTUP_AND_ONCE_CONTRACT_DRIFT.md`.


### R2a priority escalation — 2026-10-06T0528Z

The exact GitHub ChatGPT approval surface is no longer merely low-priority annoyance. Director screenshot evidence at 05:28Z showed the engineering workflow actively blocked on the native card while the relay HUD correctly reported `APPROVAL REQUIRED • ChatGPT tool approval • GitHub`.

Immediate acceptance policy is deliberately narrow:

- exact provider/card identity: `Allow ChatGPT to use GitHub?`;
- exact controls must include `Always allow`, `Deny`, and `Allow once`;
- the approval surface's conversation scroll root must already be at the bottom;
- only the Director-preauthorized `Always allow` control may be invoked;
- Google Drive, unknown providers, ambiguous text, missing controls, disabled/hidden controls, or non-bottom state remain fail-closed;
- emit explicit auto-approval telemetry.

Implementation: `dc5afa8fab1b182de64a3537e2f52da40e4087b6`; regression assertion: `5a5d0cd2077c91d2a6d1e2328cb970a1c137810c`. Live activation/proof remains required.


### R0 operator authority over redundancy — 2026-10-06T0618Z

Reliability means **keep the relay alive at all costs unless the human explicitly says stop**. Recovery redundancy must never fight an intentional operator shutdown.

Acceptance requirements:

- one obvious HUD STOP control sets the durable `.relay-paused` interlock before stopping the backend;
- watchdog/supervisor respect that interlock and do not resurrect the relay while it is set;
- HUD remains available while paused and visibly reports PAUSED so the operator has a recovery surface;
- one obvious HUD START control and easy-to-find `START-RELAY.bat` clear the interlock and restore supervision;
- an easy-to-find `STOP-RELAY.bat` provides the same emergency stop outside the HUD;
- intentional STOP/START is distinct in telemetry/logging from crash recovery;
- no redundancy plane may override explicit operator intent.


### Operator-control UX amendment — 2026-10-06T0641Z

- The HUD must not expose hidden mouse gestures that destroy the operator recovery surface.
- In particular, right-click must not close the HUD or imply relay shutdown.
- Relay START/STOP remains explicit and visible; intentional operator STOP continues to override all redundancy planes through the durable pause interlock.
- If a HUD-only exit is ever needed, it must be an explicit labeled control whose scope is unambiguous and distinct from stopping the relay.


### Result submit-once acceptance amendment — 2026-10-06T0647Z

PCE7.429 live evidence makes result submission a state-machine boundary, not a generic retry loop:

- ChatGPT send acceptance (`generation_started` or stable `composer_cleared`) permits exactly one transition to SUBMITTED.
- SUBMITTED persists across content-script reload and immediately suppresses automatic result resend/replay for that packet.
- The next state is `WAITING FOR GPT TURN END`; this watchdog may inspect DOM state, reconcile exact result visibility, capture/recover evidence, or escalate STALLED.
- The post-submit watchdog must not contain a Send path or Windows action path. Uncertain exact-turn visibility is not permission to submit the same result again.
- Only positive exact user-result recognition emits delivery-complete/operation-counted. Rotation accounting must therefore remain downstream of exact result visibility.
- Backend exact-once remains mandatory and independent; this change strengthens the browser delivery plane without removing watchdogs, leases, durable obligations, replay safety, or recovery redundancy.


### Whole-product STOP and rollback-first amendment — 2026-10-06T0701Z

- Explicit HUD/operator STOP must quiesce browser automation as well as the Windows listener. PAUSED is not accepted as a whole-product state while content-script result send/recovery loops continue.
- Browser delivery/recovery timers, deferred work, packet discovery and autonomous Send must yield to the durable operator pause until explicit START.
- This requirement must be implemented without weakening normal keep-alive/self-healing behavior when operator pause is absent.
- Every live candidate deployment now requires a new rollback snapshot of all files it changes. If the candidate breaks, restore the preceding snapshot first; do not stack speculative live edits on the broken candidate.
- Timestamped rollback evidence is indexed in `docs/ROLLBACK_INDEX_2026-10-06T0701Z_RELAY_RECOVERY_BOUNDARIES.md`.
