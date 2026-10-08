# Archived source fragment 4/6 — 2026-10-08T0752Z

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
