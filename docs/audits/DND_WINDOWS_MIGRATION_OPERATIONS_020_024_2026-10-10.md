# D&D Windows migration audit — operations 020–024 — 2026-10-10

## Scope and provenance
User-reported Windows Relay results for task-scoped `DND-WINDOWS` actions 020–024, not PCE engineering ordinals. This five-action checkpoint is written/read back on canonical `monag144/GPT-Windows-Relay` main before action 025. No code in the Relay repository or its Client was changed.

## Results
| Operation | Status | Finding |
| --- | --- | --- |
| 020 DISPOSABLE-ACL-QUALIFICATION | OK | Temporary-only icacls hardened a directory successfully; verification succeeded. Inheritance removed from parent; child file and replacement inherited permissions. Textual ACL output did not show user SID (ambiguous display). No protected secrets or campaign DB touched. |
| 021 ACL-IDENTITY-VERIFICATION | COMMAND_FAILED | Hardened temporary directory and exported its security descriptor, but diagnostic parser attempted to read `fields[1]` from split fragment `(A` and raised IndexError before evaluating any ACL. See `docs/incidents/DND_WINDOWS_ACL_DIAGNOSTIC_PARSER_2026-10-10.md`. No source/credential data mutation. Action ID not repeated. |
| 022 CORRECTED-ACL-VERIFICATION | OK | Self-tested SDDL parsing, resolved current user SID, created disposable directory ACL; directory, new file and replaced file each had exactly two full-access allow trustees USER and SYSTEM with no malformed entries. Verification PASS. No actual credentials accessed. |
| 023 ISOLATED-WINDOWS-SECURITY-HELPER | OK | Created only isolated `backups/pr157_a1b03ae2/app/services/windows_credential_security.py` (SHA256 `aabbdd834adcddc983ef8471b24a53dba42c61eb372ec08b7e900dbea1a71b49`). Synthetic test: competing handle blocked, lock reacquired, private ACL survived replace. Original immutable PR15.7 source archive unchanged; active D&D worktree unchanged. |
| 024 ADVERSARIAL-ACL-AND-LOCK-TESTS | OK | Synthetic negative checks rejected Everyone read ACE, multiple hard links, inherited public ACL and missing file; secure ACL restored. Symlink creation unavailable on this Windows account, so symlink behavior untested. Helper SHA unchanged. Original checkout/real credentials/DB unmodified. |

## Security acceptance caveats
Helper is a test-isolated prototype, **not deployed credential security**. Windows DACL and exclusive byte-range-lock positive tests and several negative tests passed; the helper has not yet been integrated into `ApiCredentialStore`. Tests of actual read/write/replace, concurrency, process-level contention, failure rollback, restart, and ACL-on-created-temp-file are outstanding. Symlink/reparse-point creation could not be tested; absence of ability to create a symlink is not validation. Windows POSIX modes (`os.chmod`, `os.fchmod`) have no privacy meaning on tested host and directory fsync fails. No Windows BYOK readiness claim.

## Main checkout/rollback
D&D local fix branch `fix/windows-python313-utf8-20261010`, local commit `6bcc567ab75b62c2870c99319dcfc550fdd7823d`; only existing untracked `cmd.exe`. Isolated candidate SHA `a1b03ae2cd0115a93fd9f5bef28acdfdc6c18112`, immutable archived source SHA256 `0d0324d3b5fe9526d61285b071b699c4185760a398415c15b4c10aff6a75facc`. No bot launch, external credential use, live DB migration, push or merge.

## Next operation
025: make an exact-change, rollback-backed Windows-only adaptation to the **snapshot** credential store, preserving POSIX behavior and refusing unsafe DACLs; compile/smoke test without exposing secrets. Afterwards run focused candidate suite plus credential safety tests against disposable stores. Failure warrants incident and investigation, not a permissive fcntl shim.

## Canonical relay controls
Read `consumer/control_harness.py` SHA ca2141c45726366abb889db0cb5a794ed8735075; `windows-relay/TASKS.md` SHA d49999dc29466a04ba2c27cc39f341b9162779e9; `docs/index/WINDOWS_RELAY_DOCUMENTATION_INDEX_2026-10-09.md` SHA bfa29203c03238015cb088d717810d818a980d90; maintained backlog a7b65a643cbcdecd440d6675d1dfb7190300a6fb; mission 86c3e0c3f2d1c44de9cccdc819597f120c8732be; operating safety 693ad770964352de7de26886ba3b4e295ac0357a; sandwich 2b300c59320f144126f8a2a2c0b2dd5dbc349596. Old referenced `docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md` is NOT_FOUND and replaced by dated documents. Exact-once production not established. No automatic ChatGPT agent handoff authorized.
