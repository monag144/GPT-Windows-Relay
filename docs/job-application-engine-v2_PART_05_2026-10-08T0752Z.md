# Archived source fragment 5/6 — 2026-10-08T0752Z

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
