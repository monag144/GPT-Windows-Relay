# PCE14 GitHub Actions pre-step failure — 2026-10-09T2231Z

## Observed evidence
- GitHub Actions workflow `.github/workflows/pce14-relay-behavioral.yml`, draft PR #10, revision `6a2507ecf60348757a0a6afe6bc36f981d777e63`.
- Workflow run [37999190794](https://github.com/monag144/GPT-Windows-Relay/actions/runs/37999190794), event `pull_request`, created 2026-10-09T22:26:06Z, updated 22:26:08Z, `status=completed`, `conclusion=failure`.
- Job `trace-contracts`, id `114052814923`, `conclusion=failure`, `steps=null`; job steps endpoint returned empty `[]`. GitHub Actions redirected job logs previously returned 404 BlobNotFound. This **does not demonstrate a failed unit-test assertion**. Underlying reason remains **UNKNOWN**, possibly runner/workflow/platform/account gating; do not infer a particular cause.
- Independent **real Windows** operation `PCE14.011-targeting-guard-regression-acceptance` executed exact pinned feature revision in a temporary directory and ran `python -B -m unittest discover -s benchmarks/tests -p test_*.py -v`: **44/44 PASS**, `exit_code=0`, reported 0.156 seconds. `PCE14.007` at prior revision separately ran 33/33 PASS.
- Neither result is live Firefox acceptance. Production/source checkout and protected PCE12 evidence were unchanged.

## Failure classification and next steps
**Status: CI RED / TESTS LOCAL GREEN / CAUSE UNKNOWN.** Inspect GitHub job-run page and account runner restrictions/billing if available. Do not claim CI green or weaken the behavioral assertions merely to change CI status. Add a read-only Windows UI Automation feasibility probe and vetted independent observer before claiming live acceptance. The R01–R20 live cases and 12h/24h windows remain **NOT RUN**.

## Safety
No production install, Firefox reset, message send, duplicate replay, release promotion, or tampering with protected evidence is justified by the pre-step failure.
