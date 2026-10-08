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
- Submit authorization, legal-certification authorization, and truthfulness attestation were confirmed absent from persisted session state.
- Live submitted Workday page still terminated at `done` in one iteration.

### Next functional gap

Repeating Workday sections such as Work Experience and Education require section-scoped targeting. Generic labels can repeat many times, so v2 must not target them globally. The next mapper will pair each repeated UI section with one canonical profile record and produce ancestry-scoped actions and verification.


## Repeating-section safety milestone

Section-scoped targets are now enforced for repeated form records.

Validation:
- Full v2 regression suite: **39/39 PASS**
- Duplicate labels in different named ancestor groups verify independently.
- Labels declared as part of a repeating-section schema are reserved from generic AI reasoning across every occurrence, including not-yet-mapped records.
- An unmapped duplicate `Company` field is therefore neither mutated nor sent to the reasoning broker.

### Discovery layer

`section_inventory()` and the `inventory` CLI command inspect the current page without profile values. They group interactive controls by named ancestor scope, derive simple repeated-family names such as `Work Experience 1` → `Work Experience`, order scopes by page position, and mark scopes unsafe when duplicate labels collapse under the same group name.

This discovery output is intended to drive automatic profile-record binding only when the UI exposes enough structure to distinguish each record safely.


## Automatic repeated-record binding

The engine can conservatively infer repeated Work Experience and Education bindings from page structure.

Rules:
- only named, structurally safe section scopes are eligible;
- section family must semantically match a supported source (`experience` or `education`);
- scopes are bound top-to-bottom to canonical profile records;
- at least two recognized input fields are required before an automatic binding is accepted;
- only a narrow alias map is automatic;
- unknown labels are reported but untouched;
- freeform descriptions such as Role Description are intentionally not auto-mapped because posting-specific instructions may require facts not present in the generic responsibilities field;
- explicit `repeating_sections` context overrides inferred bindings for the same group.

Set `auto_bind_repeating_sections=true` to allow these high-confidence inferred bindings to feed the deterministic planner. The default remains off.


## State-aware selector layer

Single-choice dropdown/combobox fields now use a verified `select_option` intent.

Provider rules:
- snapshot `ExpandCollapsePattern` state when available;
- snapshot currently selected child names through `SelectionPattern` when available;
- do not call `Expand()` when the control is already expanded;
- choose only an exact semantic option name;
- prefer an actionable ListItem/RadioButton/MenuItem wrapper over a text descendant;
- after selection, require the selector's fresh ValuePattern or SelectionPattern to equal the requested option;
- fail closed if exact selection cannot be proven.

Education auto-binding recognizes `Degree` as an exact-option field backed by the canonical education `credential`. No degree equivalence or taxonomy guessing is performed. A credential that does not exactly exist in the Workday option set is not silently substituted.


## One-mutation perception cycles

The runner now executes exactly one verified mutation from each planner result and then performs a fresh snapshot and a fresh plan.

This is intentional. Workday can rerender after nearly any field mutation, invalidating generated AutomationIds and changing nearby accessibility structure. A multi-action plan is therefore advisory only: the runner records how many actions were available, executes the first one, verifies it, and discards the rest before replanning from current UI state.

The default iteration budget is now 256 cycles (hard maximum 1000), which supports long employment-history applications while remaining bounded. This increases local UIA work but does not increase model use unless an unresolved reasoning question is actually encountered.


## Verified repeated-section creation

The planner supports application-specific `repeating_section_goals` for Work Experience and Education. A goal specifies a desired record count without making that count a global applicant default.

Behavior:
- fill and verify currently visible repeated records first;
- when current family count is below the goal, invoke exactly one scoped `Add Another` button;
- verify a fresh page has more sections in that family;
- discard the prior plan and bind the newly created scope on the next perception cycle;
- never request more sections than canonical profile records exist;
- block instead of advancing when the add control is missing or ambiguous.

This deliberately separates the mechanism for creating records from the policy decision of how many records a particular application requires.


## Read-only selector probing

Unknown single-choice selectors can now be resolved without positional guessing.

The planner emits `inspect_options` when an empty combobox has no cached option set. The Workday provider:
- records current semantic value/selection and expansion state;
- opens the selector only when needed;
- reads exact visible options from the Workday options list;
- strips accessibility-only `not checked` suffixes;
- restores the original collapsed/opened-by-fallback state without selecting an option;
- verifies value/selection did not change.

The runner stores the observed option list only for the current run and replans. Non-sensitive selectors then become constrained `choice_answer` reasoning requests whose output must exactly match an observed option. Sensitive selectors are not sent to AI; they block until an explicit answer is supplied.

Selector reasoning uses stable semantic keys such as `Availability::Schedule` rather than dynamic Workday AutomationIds.


### Rerender-safe verification identity

Execution targets may include the current Workday AutomationId, but fresh post-mutation verification cannot assume that generated ID survives a rerender.

Verifier matching now:
1. tries the exact pre-mutation target including AutomationId;
2. if that ID no longer exists, retries using stable semantic identity: control type + accessible name + ancestor-group scope;
3. still requires a unique match, so ambiguous duplicate controls fail closed.

This applies centrally to value, toggle, and selector verification.


## Verified semantic Review ledger

When an application has an `application_id`, the runner now records a local ledger from successfully verified semantic mutations.

Automatically ledgered:
- entered text values;
- exact combobox selections;
- exact radio selections;
- committed terminal hierarchy values such as `How Did You Hear About Us? → Spokane County`.

Not automatically ledgered:
- navigation clicks;
- checkbox/toggle state without an unambiguous Review-text representation;
- read-only selector probes;
- file-system paths.

At Review, a ledger assertion uses `review_field_value`: if Workday renders that field label, the verified value must also be present. Fields Workday omits from Review do not cause a false mismatch. Manual strict `contains_text` / `not_contains_text` expectations remain available for application-specific critical checks.

Backward navigation marks downstream ledger assertions untrusted. A downstream step's assertions become trusted again only after that step is deterministically rechecked and successfully advanced.

The runner also redacts the absolute local path from `upload_file` actions before writing action history; the expected filename remains available for diagnostics.


## Application-scoped browser tab pinning

The runner no longer assumes the currently focused Firefox tab is the application.

A run can specify exactly one browser selector:
- `--tab-name "Exact title"`, or
- `--tab-contains "unique substring"`.

When an `application_id` is present, that selector is persisted locally in the application session and reused on later runs unless explicitly replaced.

Before every page snapshot, including post-mutation verification snapshots, the runner re-selects and verifies the configured Firefox tab. Missing or ambiguous matches terminate with `browser_target_failed`; the runner never falls back to the currently focused tab.

This prevents a user switching to ChatGPT, email, or another browser tab from redirecting Workday automation at the wrong document.


## Durable submission checkpoint

A successful application is terminal local state once the runner has directly observed the exact page text `Application Submitted`.

For sessions with an `application_id`, the runner persists:
- status: `submitted`;
- UTC verification timestamp;
- evidence: exact `Application Submitted`.

Later runs return `done` from that local checkpoint before selecting a browser tab or reading the page. This prevents Workday's post-submit redirects (for example back to a public job listing or Candidate Home) from making a completed application look incomplete.

The checkpoint is **not** written for generic `done` states such as a Review page with no enabled Submit button. Exact terminal evidence is required.

`--force-live` bypasses the local completion short circuit for diagnostics only.


## Identity-anchored repeated-record binding

Automatic Work Experience/Education binding no longer assumes that screen order equals canonical profile order.

Binding priority:
1. **Prefilled identity anchor.** Existing employer/title or school values must match exactly one unused canonical record. That record is bound regardless of its screen position.
2. **Single blank starter.** If the page contains exactly one structurally valid blank section for that source, it may bind the first unused canonical record.
3. **Verified-created blank scope.** After the runner invokes `Add Another` and verifies exactly one new section scope appeared, that exact scope may bind the next unused canonical record during the active run.

Safety behavior:
- multiple arbitrary blank sections are not position-bound;
- a prefilled section whose identity does not match the canonical profile is skipped;
- ambiguous identity matches are skipped;
- a populated section with no usable canonical identity anchor is skipped;
- one profile record cannot be assigned to two visible scopes.

The runner's trust for a newly created blank scope is intentionally ephemeral. A restart before that row acquires an identity anchor fails safe rather than reconstructing creation order from screen position.


## Deterministic date formatting

Canonical profile dates remain ISO-like facts (`YYYY`, `YYYY-MM`, or `YYYY-MM-DD`). The engine does not blindly paste those strings into Workday date inputs.

The UIA provider now preserves each control's accessible `HelpText`. Repeated-section date fields are rendered only when the field exposes a deterministic format:
- `MM/YYYY` → month/year;
- `MM/DD/YYYY` → full date;
- `YYYY-MM` → ISO year/month;
- `YYYY-MM-DD` → full ISO date;
- explicit year-only fields such as `Graduation Year` → year.

Precision is never invented. A profile value like `2025-01` cannot satisfy `MM/DD/YYYY` because no day is known. Missing or unsupported format guidance becomes a blocking condition before `Save and Continue`.

Other safe fields on the page may still be filled first; once deterministic work is exhausted, unresolved date precision/format stops navigation.


## Record-local work-history narratives

Repeated employment narratives are never sent through generic global field reasoning.

For an identity-bound experience row:
- `Duties`, `Responsibilities`, and a plain `Role Description` use only that record's `responsibilities`;
- `Reason for Leaving` requires `reason_for_leaving` on that record or an explicit per-record override;
- a field whose accessible label/HelpText asks for both duties/responsibilities **and** reason for leaving is composed only when both facts are grounded.

Explicit overrides use:

```json
{
  "record_overrides": {
    "experience": {
      "0": {
        "reason_for_leaving": "Accepted another position."
      }
    }
  }
}
```

Overrides are scoped to one source and one canonical record index. They do not become authorization flags and are not inferred from another job.

If a required semantic component is absent, the planner emits `repeating_freeform_blockers` and will not advance with `Save and Continue` once other safe mutations are exhausted.


## Required-field coverage invariant

The Workday UIA snapshot now includes `AutomationElement.Current.IsRequiredForForm` as `required=true` for controls the accessibility tree marks required.

Before invoking `Save and Continue`, the planner requires every visible/enabled required semantic input to be satisfied after deterministic actions and grounded reasoning are exhausted.

Coverage rules:
- Edit/Spinner fields require a non-placeholder value.
- ComboBox fields require a semantic value or selected option.
- CheckBox fields marked required require `On`.
- RadioButton requiredness is evaluated by semantic question group: one selected option satisfies the group.
- Workday tokenized source inputs such as `How Did You Hear About Us?` count as satisfied when their verified terminal selected pill exists.
- Unknown optional fields do not block navigation merely because they are blank.

This gate is intentionally last in the fill/reason sequence: the engine can continue performing known safe mutations first. It becomes authoritative only when the next candidate operation would otherwise be page navigation.

If a required field remains unresolved, planner status is `blocked` with `required_field_blockers`; Workday's own validation is no longer the first mechanism expected to discover silently skipped required inputs.


## Validated application manifest

A fresh application can now be described by one local JSON manifest instead of a loose collection of runner flags and context fragments.

Example shape:

```json
{
  "schema_version": 1,
  "application_id": "example-employer-REQ123",
  "job": {
    "title": "Example Role",
    "employer": "Example Employer",
    "requisition_id": "REQ123"
  },
  "browser_target": {
    "tab_name": "Example Role"
  },
  "context": {
    "application_date": "2026-10-03",
    "auto_bind_repeating_sections": true,
    "source_path": ["Website", "Employer Site"],
    "repeating_section_goals": [
      {"source": "experience", "desired_count": 3}
    ],
    "record_overrides": {
      "experience": {
        "0": {"reason_for_leaving": "Accepted another position."}
      }
    },
    "choice_answers": {},
    "attachments": [
      {
        "path": "C:\\absolute\\local\\resume.pdf",
        "expected_filename": "resume.pdf",
        "target": {"name": "Select Files"},
        "success_text": "Successfully Uploaded!"
      }
    ],
    "review_expectations": []
  }
}
```

Run with:

```
python job_application_runner_v2.py run --profile <profile.json> --manifest <application.json>
```

Manifest preflight occurs before Firefox or Workday access. It validates:
- stable application ID syntax;
- one unambiguous browser-tab selector;
- ISO application dates;
- attachment path absoluteness, basename agreement, and local file existence;
- repeated-section goals against the number of canonical profile records;
- per-record override indexes and supported override facts;
- supported context shape.

Manifest mode cannot be mixed with legacy `--context`, `--application-id`, `--tab-name`, or `--tab-contains` inputs. One application run gets one application identity.

### Authorization boundary

The manifest is persistent application data, **not authorization**.

The validator recursively rejects persistent keys such as:
- `allow_submit`;
- `allow_legal_certification`;
- `certify_truthfulness`;
- API keys/tokens.

Those permissions remain ephemeral runtime policy/context and cannot silently survive in an application manifest or restart-safe session.


### Rich manifest structures are executable contracts

Canonical manifest validation is strict for the richer application-specific structures; passing preflight means the configured structure is executable by the planner rather than merely JSON-shaped.

`option_selections`:
- each item requires a nonempty exact value;
- target must identify a control by accessible name or AutomationId;
- if a control type is supplied, it must be `ControlType.ComboBox`;
- unsupported target/item fields are rejected.

`repeating_sections`:
- source must be `experience` or `education`;
- record index must exist in the canonical profile;
- group name must be nonempty and unique within the manifest;
- `fields`, `toggles`, and `options` map page labels to actual keys on that exact profile record;
- mapped facts must be populated;
- toggle facts must be booleans;
- text/option facts must be scalar non-boolean values;
- each explicit section must contain at least one executable mapping.

`review_expectations`:
- only `contains_text`, `not_contains_text`, and `review_field_value` are accepted;
- every expectation requires a nonempty value;
- `review_field_value` additionally requires a nonempty field label.

This prevents a malformed application manifest from passing preflight and then being silently ignored by the engine.


## Record-scoped final Review verification

Verified semantic actions already carry their repeated-section `group_name` into the restart-safe Review ledger. Final Review verification now uses that scope instead of treating a repeated field label as page-global.

For a scoped `review_field_value` assertion:
- when Workday exposes the requested Review group, both the field label and verified value must occur inside that group;
- a matching value in another repeated record does not satisfy the assertion;
- when group ancestry is missing but the field label is unique on Review, the engine may use the historical page-level fallback;
- when group ancestry is missing and the field label is repeated, the assertion is unverifiable and submission is blocked;
- application manifests preserve and validate an optional nonempty `group_name` on manual `review_field_value` expectations.

This closes the repeated-record false-positive case where, for example, `Employer B` elsewhere on Review could incorrectly satisfy the verified `Company` value for `Work Experience 1`.


## Manifest-bound restart safety

Manifest-mode applications are now bound to the exact normalized application manifest that created their local restart-safe session.

The manifest validator produces a canonical SHA-256 fingerprint from the normalized manifest. The session stores that fingerprint locally alongside operational continuity state.

On every `--manifest` run:
1. manifest syntax and local attachment preflight complete;
2. the canonical manifest fingerprint is computed;
3. the local application session is loaded by `application_id`;
4. the fingerprint is bound or compared **before** browser-tab persistence/selection;
5. only a matching session may reuse reasoned answers, Review assertions, browser identity, or durable submission completion.

Fail-closed cases:
- changing source path, attachment configuration, repeated-record goals, per-record overrides, explicit choices/options, browser target, job identity metadata, or Review expectations changes the fingerprint;
- a changed fingerprint with the same `application_id` returns `manifest_session_mismatch` with zero browser iterations;
- a legacy session that has operational history but no manifest fingerprint cannot silently adopt a manifest later;
- a completed session cannot short-circuit to `done` under a different manifest.

Legacy runs that use `--application-id` without `--manifest` remain supported and do not receive a synthetic fingerprint.


## Offline application readiness compiler

`job_application_intake_v2.py` compiles a canonical profile plus one application manifest into a non-mutating readiness report before Firefox or Workday are touched.

Run:

```
python job_application_intake_v2.py --profile <profile.json> --manifest <application.json>
```

The compiler:
- validates the complete manifest and attachment files;
- reports the canonical manifest fingerprint used for restart-safe session binding;
- reports profile record counts and application-specific repeated-record goals;
- summarizes configured source path, explicit selector/choice contracts, attachment filenames, and Review expectation counts;
- flags potential record-local facts such as missing responsibilities or reason-for-leaving values only as **live conditional dependencies**, because the application may never request them;
- lists page semantics that necessarily require live discovery, including required fields, dropdown options, date formats, repeated-section identities, and final Review rendering;
- confirms that persistent submit/legal authorization is absent and remains a runtime-only decision.

The report intentionally does **not** emit canonical applicant field values or absolute local attachment paths. It is safe for diagnostic logs while the full applicant profile remains local.

A successful offline report means the supplied application package is structurally ready to inspect live. It does not claim the unknown live form is already satisfiable.


### Canonical runner preflight command

The normal runner now exposes the offline readiness compiler directly:

```
python job_application_runner_v2.py preflight --profile <profile.json> --manifest <application.json>
```

This is the canonical first command for a manifest-driven application.

`preflight`:
- validates the same profile and manifest that a later `run --manifest` will consume;
- checks configured attachment files by default;
- emits the same canonical manifest fingerprint used for restart-safe session binding;
- produces the non-PII readiness report from `job_application_intake_v2.py`;
- never selects a Firefox tab;
- never snapshots or mutates Workday;
- never loads, creates, or updates the application session.

A failed preflight therefore cannot contaminate restart-safe state. Passing preflight confirms that the offline application package is structurally valid; unknown live-page semantics are still discovered and verified only during a later run.


## Read-only live discovery

The runner provides a semantic inspection step between offline preflight and mutation:

```
python job_application_runner_v2.py discover --profile <profile.json> --manifest <application.json>
```

Recommended manifest workflow:

```text
preflight → discover → run
```

`discover` is intentionally read-only:
- validates the same manifest/profile contract as `run --manifest`;
- requires the configured Firefox tab selector to resolve to exactly one tab;
- records the currently selected Firefox tab before inspection;
- selects the application tab only when necessary;
- takes exactly one Workday UIA snapshot;
- restores the original Firefox tab after the snapshot, including on snapshot failure;
- never calls the Workday executor;
- never loads or writes restart-safe application session state.

The discovery report is structural rather than applicant-valued. It includes:
- current step metadata;
- control counts;
- required control descriptors and populated/unpopulated booleans;
- dropdown descriptors without selected values;
- radio-question option names and a boolean indicating whether some option is selected, without identifying the selected answer;
- repeated-section families/scopes and field labels without field values;
- important navigation/upload button names;
- completion/error counts.

Observed applicant values, phone numbers, employer values, salaries, freeform responses, selected sensitive answers, and local file paths are intentionally omitted from the diagnostic report.

If the manifest browser selector is ambiguous, or the original tab cannot be restored uniquely after switching, discovery fails closed before a snapshot or mutation can be trusted.


## Redacted live execution preview

After offline `preflight` and read-only `discover`, the runner exposes a read-only planner preview:

```
python job_application_runner_v2.py preview --profile <profile.json> --manifest <application.json>
```

`preview` selects the manifest-bound Firefox tab, snapshots the live Workday surface, runs the real deterministic planner with submit/legal authorization disabled, restores the original Firefox tab, and emits a redacted execution preview.

The preview never:
- calls the provider executor;
- mutates the application;
- loads or writes restart-safe session state;
- persists authorization;
- emits applicant text values, configured choice answers, attachment paths/filenames, reasoning profile context, or Review expected values.

The report preserves:
- planner status and reason;
- action count and the first one-mutation-cycle action;
- operation type, semantic field/group, grounded source path, and verifier kind;
- reasoning-request field/key and option count;
- safe blocker categories;
- Review mismatch count without expected applicant values;
- visible public entrypoint buttons such as `Apply` without inventing permission to click them.

The intended application lifecycle is now:

```text
preflight -> discover -> preview -> run
```

Only `run` is allowed to execute application mutations or persist operational application state.


## Runtime-stable Firefox tab identity

Firefox tab titles can change while the same tab remains alive, especially when a public Workday listing transitions into the candidate/application flow.

The Firefox adapter now exposes each live tab's UI Automation runtime ID and supports exact selection by that ID.

Runner behavior:
- the manifest/session still starts from a human-readable exact title or substring selector;
- after the first successful selection in a live runner invocation, the runner adopts that tab's runtime ID as an **in-memory pin**;
- verification snapshots and later perception cycles select the same live tab by runtime ID even if its title changes;
- the runtime ID is not treated as durable cross-restart identity and is not written into the manifest as authorization or application policy.

This is a lifecycle-safety primitive for the later public-listing → candidate-flow transition. It does not itself click Apply, certify anything, or submit an application.


### Runtime-stable read-only restoration

Read-only `discover` and `preview` now restore the exact Firefox tab that was selected before inspection by UI Automation runtime ID when available.

This removes a title-race from the inspection path:
- the initial application target is still matched from the manifest's semantic title selector;
- the caller's currently selected tab is captured with both title and runtime ID;
- after the single read-only Workday snapshot, restoration uses the runtime ID rather than the possibly changed title;
- duplicate original tab titles are therefore safe when a runtime ID is available;
- legacy/no-runtime-ID environments retain exact-title restoration and fail closed if that title is ambiguous.

The same runtime-ID primitive is used by the active runner after its initial title pin, so both read-only inspection and mutation cycles now have stable tab identity.


### Transient runtime-ID disambiguation

Read-only `discover` and `preview` commands can accept an ephemeral Firefox tab runtime ID:

```
python job_application_runner_v2.py discover --profile <profile.json> --manifest <application.json> --runtime-id <id>
python job_application_runner_v2.py preview  --profile <profile.json> --manifest <application.json> --runtime-id <id>
```

This exists only to disambiguate duplicate tabs that satisfy the manifest's semantic `browser_target`.

Safety rules:
- the runtime ID is never written into the durable application manifest or its fingerprint;
- the runtime-ID tab must still satisfy the manifest's exact-title or contains-title contract;
- an unrelated runtime ID is rejected before a Workday snapshot;
- discovery/preview remain read-only and session-free;
- the original selected Firefox tab is restored by runtime ID whenever available, even when duplicate tab titles exist.

This keeps durable application identity semantic while allowing a live browser instance to be targeted exactly.


## Manifest-bound live-run gate

A read-only preview can now hand the mutation runner an ephemeral exact-tab binding without making Firefox runtime IDs durable application identity.

When `preview` is invoked with `--runtime-id`, its report includes:

- the validated Firefox `runtime_id`;
- the exact canonical `expected_manifest_fingerprint`.

A mutation run can consume both:

```
python job_application_runner_v2.py run \
  --profile <profile.json> \
  --manifest <application.json> \
  --runtime-id <preview-runtime-id> \
  --expected-manifest-fingerprint <preview-fingerprint>
```

Before loading or mutating restart-safe session state, the runner requires:
- both live-binding arguments together;
- manifest mode;
- the expected fingerprint to equal the freshly computed manifest fingerprint;
- the runtime ID to resolve to exactly one current Firefox tab;
- that tab's current title to still satisfy the manifest's semantic `browser_target`.

Only after those checks pass may the normal runner begin. The runtime ID is used as an in-memory pin for that invocation and is never persisted into the application session. The durable session continues storing only the semantic title/substring target.

A stale manifest, closed/replaced tab, or runtime ID that now belongs to an unrelated tab therefore fails before provider perception, execution, or application-session mutation.

The intended high-assurance lifecycle is:

```text
preflight -> discover --runtime-id ... -> preview --runtime-id ...
          -> run --runtime-id ... --expected-manifest-fingerprint ...
```

Legacy application-id and semantic-title runner modes remain available, but manifest-driven production runs should use the live binding after preview.


## First-mutation rehearsal gate

Before a fresh application performs its first write, the runner can now create a read-only rehearsal binding:

```
python job_application_runner_v2.py rehearse \
  --profile <profile.json> \
  --manifest <application.json> \
  --runtime-id <validated Firefox runtime id>
```

The rehearsal:
- validates that the runtime tab still satisfies the manifest browser target;
- captures a fresh live page and restores the user's original Firefox tab;
- runs the deterministic planner with submit and legal-certification authorization disabled;
- never loads or saves application session state;
- never executes a mutating provider action;
- emits only the existing redacted action summary plus a SHA-256 fingerprint of the complete first planned mutation;
- refuses to call a read-only `inspect_options` probe a mutation. If a selector probe must happen first, rehearsal reports `read_only_probe_required`.

When rehearsal reaches a concrete first mutation, its `live_run_binding` contains:
- `runtime_id`;
- `expected_manifest_fingerprint`;
- `expected_first_mutation_fingerprint`.

A live manifest run can require all three:

```
python job_application_runner_v2.py run \
  --profile <profile.json> \
  --manifest <application.json> \
  --runtime-id <runtime id> \
  --expected-manifest-fingerprint <manifest sha256> \
  --expected-first-mutation-fingerprint <action sha256>
```

The runner recomputes the complete action fingerprint immediately before the first mutation. A mismatch returns `rehearsal_mismatch` **before** `provider.execute` is called.

Read-only selector probes may occur before that comparison and do not consume the gate. The first later mutating action must still match the rehearsed fingerprint exactly.

This keeps profile values, selected option values, and local upload paths out of the diagnostic handshake while still binding execution to the precise grounded action that was rehearsed.


## Manifest-bound public listing entrypoint

A fresh application may begin on a public job listing before Workday exposes an application step marker. The engine will not guess that an `Apply`-like button is permission to enter the application flow.

A manifest may explicitly configure one entrypoint:

```json
{
  "context": {
    "entrypoint": {
      "target": {
        "control_type": "ControlType.Button",
        "name": "Apply"
      },
      "verify": {
        "kind": "control_absent",
        "name": "Apply"
      }
    }
  }
}
```

Safety contract:
- the target must be an exact named `ControlType.Button`;
- the configured button must resolve to exactly one visible enabled live control;
- zero or multiple matches block;
- the only accepted entrypoint verifier currently requires that exact invoked button to disappear after the transition;
- once a real Workday `current step N of M` marker exists, the entrypoint contract is ignored and normal step planning takes over;
- the entrypoint is ordinary manifest data, so changing it changes the manifest fingerprint;
- `preview` reports it without invoking it;
- `rehearse` fingerprints the complete entrypoint action when it is the first mutation;
- a rehearsal-bound `run` must reproduce that exact fingerprint immediately before invoking the button.

The entrypoint contract does not authorize account creation/sign-in guesses, legal certification, or final submission. If the post-entrypoint surface has no recognized Workday step and no separately grounded safe action, the engine blocks.


## Disposable Firefox UIA provider lab

Before exercising new provider mutations against a real employer form, use the local-only lab page:

`windows-relay/job_application_provider_lab_v2.html`

The page intentionally contains:
- a required text field (`First Name`);
- a checkbox (`Email Updates`);
- a radio group (`Travel Availability`);
- an ARIA combobox (`Schedule`) with exact options `Day`, `Night`, and `Weekend`;
- a `Select Files` button that opens Firefox's native file picker and renders the selected basename plus `Successfully Uploaded!`;
- a `Continue Lab` button that disappears and renders `Lab Continue Verified`.

It makes no network requests. The intended validation sequence is staged:
1. open the local file in Firefox and verify a read-only provider snapshot;
2. test one mutation type at a time with fresh semantic readback;
3. restore the user's original Firefox tab after every stage;
4. only after the disposable lab passes should the same provider operation be considered for a fresh real application.

The lab is not a Workday emulator. It validates Firefox/UIA mechanics and fail-closed targeting without consuming a real application.
