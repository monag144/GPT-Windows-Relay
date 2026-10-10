# PCE16 local audit-gate compatibility acceptance — 2026-10-09

## Verified result
Windows relay operation `PCE16.008-corrected-legacy-audit-compatibility` returned **OK / exit 0** at 2026-10-10 06:32:01 UTC (October 9 Pacific), duration 965 ms. This succeeds the blocked `.005` and failed-and-rolled-back `.007` attempts. `.005`, `.007` and `.008` are all issued/consumed; next operation `PCE16.009`.

The installed local legacy validator `engineering_preflight(repo,5,series=16)` returned `ok=True`. It accepted a **compatibility-named copy**:
`docs/audits/AUDIT_2026-10-10T0623Z_PCE16_OPERATIONS_000_004.md`.
Returned `window=[0,4]`, exact selected local path and SHA256 `b0ec7d0bbc761e2e14f965cf42e1e611221e0446d063654e62c2b5434dc81898`.

## Authenticity, provenance and what changed
- Immutable upstream audit `monag144/GPT-Windows-Relay/main` at Git commit `13a4a5419248e10ac65b786fe4ae2b42d2146465`, canonical file `docs/audits/AUDIT_2026-10-10T0623Z_PCE16_000_004_CHECKPOINT.md`, Git blob `8e51a4a1ee49779e62e1bca62b82d3938c3c936c`.
- Native .008 downloaded **6,369 bytes**, verified Git blob and exact SHA256. Created the local filename with exclusive `xb` (no overwriting existing files); verified local byte readback.
- Before writing, verified legacy harness SHA256 `76d13b46ddc0289291a7bc155785c0b160d55751c4d1b515ea44db3f4bc6d883`, exact legacy API signature, `due_engineering_checkpoints(5,16).audit_window==(0,4)`, and read-only `engineering_preflight(repo,8,series=16).ok==True`.
- Legacy mandatory control reads remained unchanged: `consumer/control_harness.py`, `windows-relay/TASKS.md`, dated PCE11 overnight roadmap, `docs/windows-relay-established-facts.md`, and `docs/relay-sandwich-procedure.md`. Their hashes are in the native PCE16.008 saved result.
- **No Client backend/HUD or extension source updates**, no relay restart, no browser navigation, no resend/duplicate shell command, and no execution/acknowledgment of two dormant Chrome missions. Only a new compatibility-named audit file in the development checkout was created.
- This confirms the local legacy gate can accept the *previous* `.000–.004` audit. It does **not** attest loaded Firefox code or eliminate the source/Client split.

## Future gate boundaries
Before `PCE16.010`, create and GitHub-readback the audit for **PCE16.005–.009**, including:
- .005 **GOVERNANCE_BLOCKED**, no action reserved/executed.
- .006 **OK**, legacy validator/source inspection.
- .007 **COMMAND_FAILED / exit 2**, audit bytes verified but erroneously tested ordinal .010; created compatibility file rolled back.
- .008 **OK**, exact-source compatibility file committed locally and legacy validation accepted.
- .009: record actual native outcome when received; do not pre-credit.

The **local legacy** validator for `.010` expects a different filename ending in `_PCE16_OPERATIONS_005_009.md`; synchronize verified bytes only after that GitHub audit is committed. Never fabricate an audit or disable the checkpoint. GitHub canonical `engineering_preflight(series,10,github_audit_receipt=...)` and legacy `engineering_preflight(repo,10,series=16)` are different APIs; treat them as distinct until governed migration.

Related incident: `docs/incidents/PCE16_LOCAL_AUDIT_GATE_DESYNC_2026-10-09.md`.
