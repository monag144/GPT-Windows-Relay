# Archived source fragment 1/3 — 2026-10-08T0752Z

# Frozen Windows Relay mission/roadmap snapshot — 2026-10-08T0020Z

This is the frozen pre-PCE10 mission/roadmap preserved before making the per-turn roadmap entry point compact.

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

