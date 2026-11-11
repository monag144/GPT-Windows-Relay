# PCE14 relay behavioral capability benchmark — 2026-10-09T2200Z

## Objective

Turn the 26-case A–Z release checklist into **measurable behavior** rather than treating a green source suite as live success. Inspired by the *measurement method* of `monag144/ClosedCode`'s `packages/app/e2e/performance/benchmark.ts` and timeline fixtures: deterministic adversarial scenarios, explicit latency metrics, machine-readable reports, no silently missing results, repeatability, and a separate observer. The applications and case assertions are intentionally different.

**This layer is an evaluator, not a Firefox automation driver.** It does not click, paste, send, read credentials, reconnect, restart, or invoke a relay packet. The 20 scenarios become genuinely measurable **only when a vetted independent desktop observer and an authorized isolated-profile relay driver supply event traces**. The included unit tests use synthetic fixture traces and are **not** production acceptance. Do not label synthetic results as relay successes.

## Cases (three independent trials each)

| Category | Cases | What is demonstrated |
|---|---|---|
| File and routing | R01–R03 | Exact file hash, originating tab, same-tab New Chat |
| Composer and Send | R04–R07 | Unicode/multiline, >=12,000-byte input, one Send, real exact user-role message |
| Receipt and negative safety | R08–R14 | Correlated result acknowledgment; draft, wrong tab, STOP, duplicate effects, dropped HTTP response, assistant quote rejection |
| Recovery and provenance | R15–R18 | Delayed Send, scoped refresh, positively attested loaded script, no secret content in benchmark evidence |
| Complete transactions | R19–R20 | Autonomous round-trip and successor handoff, each in the originating tab |

The existing A–Z scorer and 12-hour/24-hour observer remain mandatory *separate* release qualifications. A real dry-run lasting 15 seconds cannot substitute for case U or Z.

## Immediate real-host read-only smoke test

Even before a live desktop trial is authorized, the independent surface probe can answer which parts of the current Windows installation are alive and which source copies differ:

~~~powershell
python -B benchmarks/relay_readonly_surface.py --output "$env:LOCALAPPDATA\GPTWindowsRelay\ops\surface-pce14-001.json"
~~~

It checks a TCP listener, records the exact unauthenticated HTTP status (401 is a healthy **authorization denial**, not listener failure), obtains the native listener PID on Windows when uniquely resolvable, and hashes the three canonical and three Client content-script copies. It never accesses the bridge token. It explicitly marks the executing Firefox JS hash and real New Chat/paste/Send **NOT_RUN**; file hashes do not establish Firefox loaded-source provenance. This smoke test is safe to run in read-only mode against the existing installation and is not a substitute for a real browser send canary.

## Trace contract

One JSON object per line. All traces use monotonic elapsed milliseconds, never wall-clock-relative guesses. Every line includes `case_id`, `trial_id`, `source` (`relay` or `observer`), `event`, `at_ms`, `operation_id`, `tab_id`, and `payload_sha256`. Observer events also require an `observer_id` matching the manifest. The final line of **each trial** must be `observer:trial_complete`. A missing terminal observation yields BLOCKED, not PASS.

All events must agree on the operation ID, tab identity, payload digest, and trial ID. The observer's `user_turn_verified` must carry `role="user"`, a matching operation/payload hash, and the new `conversation_id`. A blank composer is **not** evidence of delivery. `composer_exact` must carry `readback_sha256`, `payload_bytes`, and `readback_bytes` with exact equivalence; R04 requires `unicode_seen=true` and `multiline_seen=true`, and R05 requires at least 12,000 readback bytes. `loaded_runtime_attested` must report the executing script's SHA, not infer it from a disk copy. Counted `send_invoked` and `effect_committed` events must match the case's expected number exactly.

The harness rejects raw message text, secrets, tokens, and unknown keys. Capture these sensitive items only in separately protected local evidence if needed, never in the benchmark JSONL or scores.

A manifest has this structure (replace with real pinned values; this is only a shape example):

~~~json
{
  "schema": "pce14-relay-run-v1",
  "run_id": "isolated-relay-trial-001",
  "mode": "live",
  "source_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "loaded_runtime_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "catalog_sha256": "<actual SHA256 of CASES_2026-10-09T2200Z_RELAY_BEHAVIORAL.json>",
  "observer_id": "independent-observer-01",
  "observer_independent": true,
  "isolated_profile": true
}
~~~

**Fixture-only manifest:** set `mode` to `fixture`, `observer_independent` to `false`, `isolated_profile` to `false`, and omit the runtime hash. Fixture results are reported as `FIXTURE_PASS` and `release_qualified=false`.

## Execute the evaluator (no live side effects)

~~~powershell
python -B -m unittest discover -s benchmarks/tests -p "test_*.py" -v
python -B benchmarks/relay_behavioral.py --manifest <run.json> --trace <events.jsonl> --output <new-score.json>
~~~

The report begins with `RELAY_BENCHMARK` and includes per-case TRACE_PASS (trace-claimed live), FIXTURE_PASS, FAIL, BLOCKED, or NOT_RUN, median and p95 elapsed milliseconds, evidence hashes, and specific failure reasons. The evaluator requires **three complete trials for each of the 20 cases** (60 total) before a matrix can show full trace coverage. Scores are written **once**, never overwritten, and the source tree need not be modified to evaluate local logs.

A live mode's **TRACE_PASS is trace-level acceptance only**, not proof that an observer implementation is truly independent. Both a vetted separate observer and actual runtime identity are needed before trusting its claims. The runner always sets `full_behavioral_gate=false` and `release_qualified=false` because live source/environment verification, STOP/replay certification, 12-hour endurance, and 24-hour release qualification are outside its scope.

## Implementation stages and safety

1. Commit and test this trace evaluator and its attack fixtures. No live browser action is involved.
2. Instrument the existing working Windows file-copy / Firefox New Chat / paste / Send script so it emits phase receipts with hashes but *never* raw user text. Put it behind a uniquely numbered, STOP-aware, tab-bound adapter. Preserve its working keyboard/clipboard method.
3. Add a **separate, out-of-band, read-only observer** of the exact invoking tab's URL, composer state, user-role turn, and loaded extension. Do not let the sender self-certify its own final delivery.
4. In an isolated test profile with explicit approval, execute three repetitions of each scenario. Inject wrong tab, pre-existing draft, STOP, lost HTTP reply, refresh, duplicate delivery, stale receipt, and delayed Send. Never fault-inject against the live user's Firefox or active relay.
5. Compare source SHA/runtime SHA, per-case failure rates and latencies across versions. Map R-cases into existing A–Z evidence. Only after live checks pass, perform genuine 12-hour and 24-hour qualification.

**Current status:** executable scoring and adversarial offline tests authored on a feature branch; live driver/observer integration and all real end-to-end PASS claims remain **NOT RUN**. The previous 569/569 source tests cannot change that status.
