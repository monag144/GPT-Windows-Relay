# PCE11.016 — stale canonical checkout base in standalone v16 preflight

**Status:** OPEN, awaiting unique PCE11.017 recovery acceptance. **Severity:** source preflight blocker; no deployed process impact.

## Observed
On 2026-10-08 at 09:59:19–09:59:21 UTC, unique Windows Relay action `PCE11.016-full-source-acceptance-and-v16-canary-preflight` returned `COMMAND_FAILED` exit 2:
`PCE11_V16_CANARY_BLOCKED=RuntimeError: unexpected source base before .016`.

The last delivered successful numbered `PCE11.015-static-suspended-start-containment-regression` had clean fast-forwarded the canonical source checkout to GitHub commit `7f894e2e90e5f35156558957ed3b148d49be50e6`; its 18 static tests passed. But `windows-relay/tools/pce11_016_v16_health_canary.py` incorrectly pinned `BASE_SHA="2b02b506d8850882d806f8461c25b0a7f03140fd"` — an earlier intermediate TASKS commit. The guard correctly refused to pull or test against an unexpected base. Original source pin of script commit `ce0d211959760026e241afaf2f8edfe91b791f42` had been verified before dispatch.

## Impact and limits
The failure occurred **before git pull, source test, process launch, /status request, STOP, browser interaction, or queue mutation**. No sidecar process started and no live Relay service was replaced. Do not replay this executed `.016` packet or renumber it as a pass.

## Corrective procedure
Fix exact previous HEAD pin to `7f894e2e90e5f35156558957ed3b148d49be50e6`, and move static acceptance to new unique ordinal **PCE11.017**. Inspect source-code/tests for other readiness defects (including unittest mock URL response context and JS syntax gating) and add regression coverage. Record .016 as failed. The actual isolated live canary must be a separate **.018 or later**, only after .017 success, full source acceptance, and confirmed fail-closed containment. Continue to preserve port 8766, original ZIP and queued missions.

## Audit
Include this failed attempted slot in mandatory PCE11.015–.019 audit before .020.