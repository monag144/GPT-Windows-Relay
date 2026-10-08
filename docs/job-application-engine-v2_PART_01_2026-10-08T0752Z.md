# Archived source fragment 1/6 — 2026-10-08T0752Z

# Job Application Engine v2 — Historical Engineering Record — 2026-10-08T0650Z

Status: initial implementation started after successful Spokane County JR100708 submission on 2026-10-03.

## Objective

Replace one-off, model-authored browser commands with a local closed-loop application controller:

```text
page perception
    ↓
compact semantic state
    ↓
grounded applicant-fact lookup
    ↓
deterministic planner
    ↓
optional reasoning request only for unresolved fields
    ↓
local action executor
    ↓
mutation verification
    ↓
fresh perception
    ↓
step/review verification
```

The engine should reduce assistant token use and intervention by keeping routine perception, fact lookup, action selection, and verification on the user's machine.

## Core design rules

1. **Deterministic first.** Exact profile mappings and known application context are resolved locally.
2. **No invention.** Unknown credentials, employment facts, education, legal facts, health facts, dates, and similar claims become explicit unresolved reasoning requests.
3. **Semantic actions, not coordinates, by default.** Actions identify controls by role/name/automation ID. Coordinates are a provider-specific fallback.
4. **Every mutation has a verifier.** A set-text action expects value readback; a toggle expects state; a hierarchy selection expects a terminal selected pill; navigation expects the current-step marker to change.
5. **Final Review is authoritative.** Required-field validation is not enough. Review assertions must prove critical answers are semantically correct.
6. **Backward edits invalidate downstream trust.** After returning to an earlier step, all later steps must be revalidated.
7. **Legal certification and final submission are explicit policy gates.** The planner cannot certify or submit merely because the controls exist.
8. **Sensitive self-identification is never inferred.** A privacy-preserving decline can be selected when policy requests it; otherwise the engine must ask.
9. **LLM use is sparse.** Only unresolved semantic questions should leave the deterministic local path.

## First implementation

`windows-relay/job_application_engine_v2.py` provides:

- normalized page/control model;
- current Workday step recognition;
- error recognition;
- selected-pill recognition;
- compact snapshots for low-token reasoning;
- deterministic profile-backed text planning;
- hierarchical source-path intent (for example `Website → Spokane County`);
- legal-certification policy gating;
- Step-5 name/date/privacy-decline restoration;
- final Review assertions;
- final-submit policy gating;
- JSON CLI:
  - `compact --snapshot ...`
  - `plan --profile ... --snapshot ... [--policy ...] [--context ...]`

The v2 planner emits **abstract verified action intents**. The next milestone is the local executor that consumes those intents and feeds fresh snapshots back into the planner until the workflow reaches done, blocked, or needs-reasoning.

## Failure cases captured from Spokane County

The regression suite specifically protects against:

- treating a hierarchical parent source category as a committed answer;
- accepting validation success without semantic review verification;
- automatically accepting a legal certification without explicit authorization;
- assuming Step-5 state survives an earlier-step edit;
- inferring disability status rather than using the configured decline response;
- submitting when Review contains semantic mismatches or validation errors.

## Next milestone: local provider loop

Implement a Workday provider adapter with three components:

1. **snapshot** — enumerate the active Firefox document through UI Automation and emit the v2 snapshot schema;
2. **execute** — implement `set_text`, `set_toggle`, `invoke`, and `select_hierarchy` with provider-specific strategies and mandatory readback;
3. **run** — iterate snapshot → plan → execute → verify until:
   - `done`,
   - `blocked`,
   - `needs_reasoning`,
   - or a bounded iteration limit is reached.

The optional reasoning provider will receive only the compact question packet plus the minimum applicant context needed for that field. API keys must remain local and must never be written to GitHub or relay logs.


## Live milestone — 2026-10-03

The v2 stack passed its first real browser smoke test against the still-open Spokane County Workday confirmation page.

Validation:
- Python compile: **PASS**
- Engine + runner regression suite: **16/16 PASS**
- Live UIA snapshot: **PASS**
- Snapshot correctly exposed the visible `Application Submitted` text.
- Closed-loop runner result:
  - `status=done`
  - `iterations=1`
  - reason: `provider page indicates application completion`

This is the first confirmed end-to-end closed-loop milestone where the local engine itself performed perception → semantic state → planning → termination without a model-authored browser operation for that page.

### Remaining v2 gaps

1. Reasoning broker for unresolved semantic questions.
2. Optional user-key API adapters, with keys stored locally and never written to repository/log output.
3. Provider-side dropdown/radio semantics beyond the proven Workday source hierarchy.
4. Resume/file-upload intent in the abstract planner/executor.
5. Application-level context persistence and downstream invalidation/revalidation tracking across restarts.
6. A live mutation smoke test on a non-production/safe form before trusting multi-step autonomous mutation on a new application.


## Choice-engine milestone — 2026-10-03

The ancestry-aware question model is now implemented and validated.

Capabilities added:
- UIA snapshots include named ancestor-group paths for interactive controls.
- Generic Workday radio choices are grouped by their containing question rather than by ambiguous labels such as `Yes` / `No`.
- Explicit application context can select a known answer deterministically.
- Non-sensitive unresolved choice questions can be sent to the constrained reasoning broker.
- Broker output must match one of the options actually exposed by the page.
- Sensitive/demographic/legal choice groups are excluded from generic AI inference.
- `select_choice` actions are verified by fresh UIA selection state scoped to the question ancestry.

Validation:
- Full v2 regression suite: **27/27 PASS**
- Local static choice-reasoning smoke: **PASS**
- Live Workday confirmation-page snapshot: **PASS**
- Live closed-loop termination: **done in 1 iteration**

### Next blocker
Resume/attachment upload is still outside the abstract planner/provider interface. The proven native Firefox `File Upload` dialog workflow should become a verified `upload_file` intent before calling v2 a bare-minimum end-to-end Workday applicant.


## Attachment-engine milestone

A verified `upload_file` action is now part of the v2 abstraction.

The Workday provider:
1. requires an explicit existing local file path;
2. requires the configured expected filename to equal the path basename;
3. invokes the configured upload control;
4. locates the Firefox-owned native `#32770` window titled `File Upload`;
5. enters the path using the proven filename-field workflow;
6. restores the prior text clipboard after the dialog interaction;
7. waits for both the exact filename and the configured success marker in a fresh Workday document;
8. fails closed if any of those checks fail.

The planner never invents or searches for a resume path. Attachment paths are application context supplied by the caller.


## Restart-safe application sessions

The runner can optionally receive an `application_id`. When present, operational continuity is stored only under the user's local application-data directory.

Persisted:
- last observed step;
- highest observed step;
- earliest downstream step requiring revalidation after backward navigation;
- grounded reasoning answers already produced for that application.

Never persisted:
- `allow_submit`;
- `allow_legal_certification`;
- `certify_truthfulness`;
- API keys.

A restart can therefore resume semantic/revalidation state, but it cannot inherit legal or final-submit authorization silently.


## Session-continuity milestone

The restart-safe session layer has been validated end to end.

Validation:
- Full v2 regression suite: **36/36 PASS**
- Local session restart simulation: **PASS**
- Backward navigation from step 5 to step 2 persisted downstream invalidation beginning at step 3.
- Revalidation advanced stepwise through the previously trusted range and cleared correctly.
