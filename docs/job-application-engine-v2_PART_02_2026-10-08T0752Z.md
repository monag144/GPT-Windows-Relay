# Archived source fragment 2/6 — 2026-10-08T0752Z

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


