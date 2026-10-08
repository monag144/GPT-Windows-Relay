# Archived source fragment 3/6 — 2026-10-08T0752Z

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
