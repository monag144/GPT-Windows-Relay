# PCE11.024 — First contained historical v16 canary runtime failure

**OPEN — runtime acceptance BLOCKED; cleanup and production identity not independently established after the failure.**

## Directly observed

At 2026-10-08T10:29:11–10:29:37Z, unique packet `PCE11.024-first-isolated-v16-health-private-job-canary` returned `COMMAND_FAILED`, exit code 2. Standard error:

`PCE11_024_CANARY_FAILURE=RuntimeError: isolated v16 canary failed; forensic evidence .../PCE11_ISOLATED_V16_CANARY_20261008T102936Z_2a7894efa7d3/health-report.json`

The runtime code reached the independent `health.run_health_canary` invocation, so this was **not merely a source preflight rejection**. Exact cause and sidecar PID/status/cleanup flags are in local evidence, **not supplied by the result**. The failed result did not contain the final PCE11_024_V16_HEALTH acceptance marker. Consequently no health acceptance, no proof of termination, no source promotion, no production cutover or overnight qualification. Do not assume that the prior native sleeper smoke proves this sidecar exited.

## Earlier positive evidence (not current-time claim)

PCE11.022 source acceptance passed 50 protocol, 476 Windows, 119 consumer (including governance/migration) and 4 JS syntax checks; original ZIP and v16 historical Git source verified. PCE11.023 real isolated child PID 1052 was job-contained and killed successfully, with 12 containment, 479 Windows, 119 consumer test passes, production PID preserved and port 8768 free **before** PCE11.024. Production listener previously PID 18632 on port 8766, two pending missions and one visible HUD. These are historic observations, not proof of state after the .024 failure.

## Next safe operation

After publishing mandatory audit PCE11.020–.024 and performing **unnumbered governance sync before ordinal .025**, use unique PCE11.025 to read the exact JSON forensic report from `%LOCALAPPDATA%/GPTWindowsRelay/pce11-isolated/PCE11_ISOLATED_V16_CANARY_20261008T102936Z_2a7894efa7d3/health-report.json`. Read only necessary state fields, never the private token; check current listener PID ownership on 8766 and 8768 and authenticated production GET /status without modifying ARMED/STOP/queue. Read-only tasklist identity of any recorded child if useful. Save one bounded report with complete unsanitized raw source report referenced locally (but no token), present bounded summary. If sidecar or production identity is uncertain, classify BLOCKED and do not kill by PID, replay packet or launch another canary.

## Remediation discipline

Inspect whether failure is child early exit, wrong launch path, GET auth/status mismatch, or cleanup failure **from evidence first**, then smallest GitHub-first source/test repair, fresh full source acceptance and a separately authorized new unique ID. Do not use stale PCE11.017/.018 canary modes (they were consumed and original Popen-before-Job attach path is disabled). Include this incident in .020–.024 audit.