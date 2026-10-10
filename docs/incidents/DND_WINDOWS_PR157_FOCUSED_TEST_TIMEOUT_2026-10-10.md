# D&D Bot PR15.7 Windows focused qualification timeout — 2026-10-10

## Observed failure
User-supplied Windows Relay receipt for `DND-WINDOWS-20261010-031-PR157-WINDOWS-FOCUSED-QUALIFICATION`: COMMAND_FAILED / exit 1, 2026-10-10 20:52:40Z–20:55:36Z (~175.6 seconds). Outer Python wrapper passed preflight, printed `OPERATION=031_PR157_FOCUSED_WINDOWS_QUALIFICATION` and `TEST_MODULES=5`, then `subprocess.run(..., timeout=175)` running pytest on five focused modules raised `subprocess.TimeoutExpired`. No intermediate `PYTEST_EXIT` or pytest output was emitted because stdout/stderr were captured until process exit. This is **not evidence that the 5 modules passed, failed any test assertion, or hung at a specific test**. On Windows, subprocess.run kills its direct subprocess after timeout and waits; evidence for descendants' status is missing. Python with TemporaryDirectory exits context via exception cleanup but cleanliness was not asserted in this receipt.

## Previously verified baseline
Operation 030 PASSED: isolated Windows ApiCredentialStore using temporary fake credentials: created store and private ACLs, opened again, separate owners, preserved 12 concurrent records, model update, delete with wrong-owner denial, injected Everyone ACE rejected, cleaned temporary data. Snapshot-only patched `api_credential_service.py` SHA256 `93ab3c55bf61f98870ec15b2c386b84cb44c2dd2fce1426dada53478e2d20fba`; isolated Win32 security helper `windows_credential_security.py` SHA256 `aabbdd834adcddc983ef8471b24a53dba42c61eb372ec08b7e900dbea1a71b49`. Source archive zip SHA256 `0d0324d3b5fe9526d61285b071b699c4185760a398415c15b4c10aff6a75facc`. Local active D&D checkout fix branch at `6bcc567ab75b62c2870c99319dcfc550fdd7823d`, with only previously known `?? cmd.exe`. No real secrets or production campaign database used.

## Required diagnostic and recovery
Do not repeat action ID 031 or another blind 175-second `pytest -q` run. New DND action 032 should:
1. Verify Git/source SHA, absence of real env/database and intact original archive.
2. Inspect whether an orphaned child process from operation 031 can be identified without touching unrelated processes.
3. Run a quick separate pytest collection check with a short timeout and show its exit status and concise output.
4. Run **one focused module** bounded, with verbose progress and Python faulthandler timeout stack traces captured to a disposable file and returned even on timeout; do not leak credentials or use external services.
5. Limit execution time and terminate only the test process it starts, including descendants if safely identified; preserve active checkout and archives.
6. Attribute any stall to a concrete test only after receipt evidence, then make isolated minimal repair or narrower focused tests. Do not claim PR15.7 Windows qualification until completed.

## Governance
This DND migration incident is logged in canonical `monag144/GPT-Windows-Relay/main`, with no Relay runtime/source changes and no automatic agent switching. PCE ordinal budget/cadence is separate from task-scoped DND operations. The old PCE10 roadmap path named by canned relay footer is NOT_FOUND and superseded by dated relay docs.
