# PCE11.032 — source acceptance blocked by incorrect prior native proof revision

**STATUS: OPEN pending distinct PCE11.033 source-only retest. No v16 server started or production cutover.**

## Observed .032 failure

Packet `PCE11.032-corrected-private-http-host-full-source-acceptance` returned COMMAND_FAILED, exit 2, 2026-10-08 11:00:18 UTC. Stderr: `PCE11_032_BLOCKED=RuntimeError: native launcher/host exact Job containment proof not accepted`. It emitted no numbered source-suite marker, so no targeted/full suite, JS, original ZIP or historical-source acceptance occurred under .032. This was **not evidence that the live containment proof failed**; a runner provenance condition rejected it before suites.

## Reconciled root cause in pinned GitHub source

`windows-relay/tools/pce11_032_verified_host_source_acceptance.py` sets `PREVIOUS="a2546f1f28017032dc46a336bcbfe5803bde9322"`, the completed PCE11.031 source revision. The code loads the **PCE11.030** native lineage report at `%LOCALAPPDATA%/GPTWindowsRelay/ops/PCE11_030_LINEAGE_20261008T105116Z/lineage-report.json` and incorrectly asserts `d["source_sha"]==PREVIOUS`. The report was created at the **PCE11.030** source revision `8db22edb17697805beb528f8491f9b4f60572533`, making the equality impossible even for an authentic, successful proof. The PCE11.030 Windows result directly attests to launcher PID 1360, direct Python child 12844, both in the same private Job, Job termination and actual host exit, main preserved, 8768 free.

**Correct fix:** separate the current checkout's `PREVIOUS` pin from an immutable `NATIVE_PROOF_SOURCE` pin `8db22edb17697805beb528f8491f9b4f60572533`. Continue requiring **all** safety invariants and the exact original report path, schema and identity, not merely a pass flag. Never manufacture or modify the native report and do not weaken Job/parent membership.

## Follow-up

Publish new `PCE11.033` source-only acceptance runner, anchored to the actual canonical local checkout at the .032 attempt's remote commit `ab965d7343f947d2496027063952d6ece9fe6afe`. It must validate the actual .030 report's original source revision independently, the prior .031 failed suite evidence, the repaired malformed-PID regression, all host/Win32 security suites and full Windows/consumer suites, four JS syntax gates, archive, historical Git source. Save all stderr for exact diagnosis. No service launch, Firefox, STOP, PID kill or production deployment. Do not replay .032.

The full series remains governed by five-control reads, .030 checkpoint and audit cadence before .035.
