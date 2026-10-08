# PCE11.031 — Host identity source acceptance blocked by outdated string-PID assertion

**Incident status:** OPEN until full .032 acceptance; no isolated server launch, browser action or production cutover.

## Observed from numbered Windows result

`PCE11.031-private-http-host-job-ancestry-and-exit-source-acceptance` returned `COMMAND_FAILED`, exit code 2, at 2026-10-08T10:57:19Z. Canonical GitHub source commit `a2546f1f28017032dc46a336bcbfe5803bde9322`; report `Client/Relay/bin/SOURCE_HOST_IDENTITY_ACCEPTANCE_2026-10-08T105718Z/acceptance.json`. Eleven new host-identity/static guards reported true, but first `target_v16` test suite ran 12 tests and reported one failure: `test_missing_or_string_pid_is_rejected_and_recorded`. Subsequent targeted host membership and containment suites, complete Windows and consumer suites, JavaScript checks, archive and historical source were NOT run. Runtime v16 launched=false; production replaced=false; promotion blocked.

## Cause from pinned GitHub source review

The newly hardened `windows-relay/tools/pce11_016_v16_health_canary.py` explicitly rejects a /status PID of type string with `RuntimeError("isolated sidecar status PID malformed")` **before** querying listener PID or opening the private host handle. This is the correct fail-closed security behavior. The prior regression `test_missing_or_string_pid_is_rejected_and_recorded` still expected the older text `"status PID mismatch"`. The wrong expectation explains the failing test; complete stderr is available in the saved `target_v16.stderr.txt` if future verification contradicts this diagnosis.

## Minimal remediation and acceptance

GitHub-first test-only fix: assert `"isolated sidecar status PID malformed"` and that no listener identity or host attestation was reached. Do not relax the typed PID requirement, parent/Job owner checks, private credentials or cleanup. Re-run distinct numbered .032 full source acceptance from pinned .031 base, including 12 v16 tests, 9 mocked private-host identity tests, 12 containment tests, complete Windows and consumer suites, four JS files, exact archive and historic v16 source. Save full suite stderr and new acceptance report. No live sidecar during .032.

## Current protection

PCE11.030 independent inert-native test proved venv launcher PID 1360 spawning direct Python child PID 12844, both in exact private Job, actual host exit observed after Job termination. This proof does not by itself authorize v16 production or substitute for an actual new private v16 service health check. Previous main production PID 18632 and sidecar port 8768 are last verified at .030; always verify fresh before any later runtime test.
