# D&D Bot Windows migration audit — 2026-10-10

## Verified Windows Relay operations 006 through 010

- 006: On local main branch at 3648dbd4feecd01866445a47a38f655af93b6ce0. GitHub Desktop bundled Git located. No local .env or data/*.db. One preexisting untracked cmd.exe.
- 007: Read-only inspection of the untracked executable: size 289792, SHA256 b99d61d874728edc0918ca0eb10eab93d381e7367e377406e65963366c874450. No execution or deletion.
- 008: Confirmed the untracked executable byte-identical to the installed System32 version. Inspected Windows setup/test scripts and encoding-sensitive tests. Some stdout truncated; do not treat unseen lines as proof.
- 009: Created fix/windows-python313-utf8-20261010 on the local D&D repository. Verified backups under ignored backups/windows_portability_20261010_op009. Updated setup_windows.bat, run_tests.bat and tests/test_pr15_5_inline_ui.py, and nothing else.
- 010: Verified backup hashes and git diff --check. Direct tests with PYTHONUTF8=0 passed 205/205 in 25.83 seconds. Updated run_tests.bat under PYTHONUTF8=0 passed 205/205 in 9.01 seconds. Neither .env nor data/*.db was created.

## Safety and next step

No game bot was launched, no live campaign database was touched, and no code was pushed or deployed. All five packets returned OK. Original main and files are recoverable, and untracked executable remains preserved. Source-level and active Client exact-once protections remain separately unresolved; unit tests are not production acceptance. Next: read-only inspect complete local diff and staging before a narrowly scoped local-only commit.

## Relay governance consulted

Repository monag144/GPT-Windows-Relay main: consumer/control_harness.py blob ca2141c45726366abb889db0cb5a794ed8735075, windows-relay/TASKS.md d49999dc29466a04ba2c27cc39f341b9162779e9, dated documentation index bfa29203c03238015cb088d717810d818a980d90, dated roadmap a7b65a643cbcdecd440d6675d1dfb7190300a6fb, mission 86c3e0c3f2d1c44de9cccdc819597f120c8732be, safety 693ad770964352de7de26886ba3b4e295ac0357a, and action sandwich 2b300c59320f144126f8a2a2c0b2dd5dbc349596. Superseded PCE10 road map path is not found on main. This DND task ledger does not advance PCE operation ordinals or replace PCE audits.
