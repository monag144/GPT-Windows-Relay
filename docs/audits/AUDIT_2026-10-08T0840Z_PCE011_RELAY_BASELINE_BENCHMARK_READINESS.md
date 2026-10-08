# PCE011 Relay baseline selection and benchmark readiness — 2026-10-08T0840Z

## Grounded candidate ranking (NOT a production certification)
1. PCE8 v16: strongest *specific* documented live Firefox recovery evidence. PCE8.101–106 completed successive exact-once operations; v16 draft-owner and deadman regressions were tested live. Original source fix `694d47ab89596d5c3801f749caa352b951a2be52`, documented v16 live content SHA-256 `9541A890A80A8200F949E6D7DA7132C10335BFABD487E0B89047919C6B1B899E`. Exact complete installable v16 snapshot is NOT currently verified. Whole-product correlated STOP acceptance remained source-only.
2. PCE7 prior legacy live Relay/HUD: restored and described as usable after PCE7.446 START failure and rollback. Exact files/hash of the returned legacy runtime must be recovered before fair replay. Do not misidentify the PCE7.447 safety branch as that installed state.
3. PCE8 v17: interesting candidate, new logic, but not a proven night.
4. PCE9/PCE10: operational failed attempts; source remains salvageable but must not be treated as accepted reliability baselines.
5. One-Click GO consumer r28: separate consumer competitor, not a standalone Relay build, and not a Firefox production solution.

## Newly committed GitHub benchmark assets
- `benchmarks/CASES_2026-10-08T0805Z_A_TO_Z.json`: all 26 cases and mandatory 12/24h criteria.
- `benchmarks/BENCHMARK_2026-10-08T0805Z_A_TO_Z_RELAY_ONE_CLICK_GO.md`: human-readable full A–Z test plan.
- `benchmarks/benchmark_runner.py`: version-pinned run manifests, hashed local evidence, safety hard gates, scoring, same-product comparisons.
- `benchmarks/overnight_observer.py`: independent, strictly read-only local TCP port liveness observer, not secret/API access and not a browser completion proof.
- `benchmarks/tests/test_benchmark_runner.py`: regression assertions for no-evidence, short night, mutated proof, omitted hourly receipts and scope.
- `.github/workflows/pce011-source-benchmark.yml`: Windows GitHub Actions unit, scanner JS parsing and PowerShell parse gates; these do NOT substitute for live or overnight testing.

## Status / limitations
- Connected GitHub confirms asset commits in PCE11 development branch, but Windows test suite, consumer full suite, live browser identity, STOP, cold reboot and overnight benchmark have NOT been performed here.
- GitHub Actions run 37751315240 and later runs 37751465312 / 37751488660 reported FAILURE with zero available step summaries; exact cause is unverified (logs inaccessible at inspection). Do not pretend a green CI check or infer a specific source failure.
- The A–Z documentation's structured-evidence paragraph currently says `observer_summary`, while the stricter updated scorer requires `observer_log: {"path": "local heartbeat JSONL", "sha256": "exact digest"}`. Treat the **scorer's raw-observer requirement as controlling**; fix documentation text in a future documentation-only commit after normal review. No pass can arise merely from a claimed summary.
- The monitor records listener availability only; actual end-to-end successes require separately collected 12/24 hourly result receipts. Evidence requires independent review. The Relay is never the sole collector.
- Old versions are not yet packaged as hash-verified, identical test installations; baseline selection remains provisional pending this evidence.

## Next execution on isolated Windows test system
1. Investigate Actions failure and obtain runnable source suites; require passing reports before promoting.
2. Recover exact PCE8-v16 and restored PCE7-legacy live file manifests/commits (without altering current runtime). Pin digests.
3. Run offline/unit gates on both, then isolated targeted browser/STOP exact-once tests.
4. Launch external supervised passive observer for >=12h, with a safe hourly end-to-end driver and independent rescue/duplicate-effects accounting; repeat for >=24h qualification.
5. Produce `score.json` per build; compare only same product/browser. Archive reports locally and send the compact scores to ChatGPT after the Relay has recovered. Use Codex CLI for scoped test-backed repairs, never for a blind live install.
6. Continue One-Click GO r28 Chrome/Edge consumer acceptance separately.

**Current winner:** PCE8 v16 is a *leading recovery subsystem candidate*, restored PCE7 is a *usable legacy fallback*, and no Relay has a certified overnight result.