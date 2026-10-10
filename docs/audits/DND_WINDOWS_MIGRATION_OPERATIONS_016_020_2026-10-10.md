# D&D Windows migration checkpoint — operations 016–020 — 2026-10-10

## Scope
User-requested D&D Bot migration via an existing Windows Relay, action IDs DND-WINDOWS-20261010-016 through -020. These are **not PCE engineering ordinals**. No Windows Relay code, Client, extension, automated handoff or PCE governance change has been made. Evidence comes from the user-supplied exact-action Windows results.

| Operation | Status | Concrete result |
| --- | --- | --- |
| 016 ISOLATED-CANDIDATE-SNAPSHOT | OK | 461 archived files from PR15.7 candidate SHA a1b03ae2cd0115a93fd9f5bef28acdfdc6c18112, archive SHA-256 0d0324d3b5fe9526d61285b071b699c4185760a398415c15b4c10aff6a75facc, extracted into backups/pr157_a1b03ae2. Active branch and campaign DB untouched. |
| 017 PR157-FOCUSED-WINDOWS-TESTS | COMMAND_FAILED, nested pytest 2 | Test collection failed on Windows due to unconditional Unix-only fcntl import in app/services/api_credential_service.py. No gameplay test result. Incident file docs/incidents/DND_PR157_WINDOWS_FCNTL_IMPORT_2026-10-10.md records cause and restraint. No rerun of failed packet ID. |
| 018 WINDOWS-CREDENTIAL-LOCK-AUDIT | OK | Windows has msvcrt, icacls, os.chmod, os.fchmod and os.fsync; lacks fcntl and os.O_NOFOLLOW. The candidate source file SHA-256 3ebf1faf7ddac0754d8ce7c03e2296e34194d88148460a7b2dde8a8c29c9eb63. The implementation relies also on Unix permission and directory durability assumptions. |
| 019 WIN32-SECURITY-PRIMITIVES | OK | Disposable temp probes: chmod and fchmod return without error but stat shows file 0o666 and directory 0o777; opening+fsync directory raises PermissionError 13; file fsync works; msvcrt byte-range lock excludes a second file descriptor; lock reacquires after release; os.replace of closed files succeeds. |
| 020 DISPOSABLE-ACL-QUALIFICATION | OK | On a new disposable temp directory icacls inheritance removal and explicit grant to user SID and SYSTEM exited 0; icacls verify exited 0. Directory has no inherited/everyone/users markers, but the string display **did not contain current user SID**, likely account-name translation, so direct per-ACE verification remains open. Child file inherits restrictive parent ACEs and replacement content verified. Temporary files removed. |

## Acceptance state
Neither PR15.7's historic 456 passing Linux tests nor tested D&D main's 205 passing Windows tests establish PR15.7 Windows functionality. The PR15.7 Windows test run is currently **blocked on a platform-specific credential-store import and security design**. Do not shim fcntl silently or weaken protection. Need ascertain exact current-user access control entries in a disposable DACL independent of rendered SID, plus atomic replacement inheritance, ACL validation and safe failure behavior. This checkpoint logs 017 as a real failure, not a gameplay regression. There is no observed duplicate execution or manual side-effect rescue in this range.

Rollback: original archive immutable; local working D&D branch fix/windows-python313-utf8-20261010 at 6bcc567ab75b62c2870c99319dcfc550fdd7823d; origin/main original 3648dbd4feecd01866445a47a38f655af93b6ce0. One preexisting untracked cmd.exe intentionally preserved. No production credentials, real campaign database, live polling, deployment, push or merge touched.

## Canonical controls
Read current GitHub monag144/GPT-Windows-Relay/main: consumer/control_harness.py ca2141c45726366abb889db0cb5a794ed8735075; windows-relay/TASKS.md d49999dc29466a04ba2c27cc39f341b9162779e9; dated index bfa29203c03238015cb088d717810d818a980d90; dated roadmap a7b65a643cbcdecd440d6675d1dfb7190300a6fb; mission 86c3e0c3f2d1c44de9cccdc819597f120c8732be; safety 693ad770964352de7de26886ba3b4e295ac0357a; sandwich 2b300c59320f144126f8a2a2c0b2dd5dbc349596. Historical PCE10 roadmap path no longer exists; dated predecessors supersede. PCE 000..100 ordinals, PCE-specific audit, STOP and script-only user-directed handoff rules remain distinct and respected.

## Next safe step
021: new disposable temp ACL test printing sanitized ACE identity classifications and using whoami name/SID normalization; ideally inspect native DACL or SDDL, not a string substring SID-only check. Keep the actual credentials and campaign database unopened; do not commit anything to D&D until security tests establish a trustworthy Windows implementation.
