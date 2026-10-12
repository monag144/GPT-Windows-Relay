# PCE17.017 — Python -c argument quoting failure and READY journal interpretation — 2026-10-11 (Pacific)

## Native receipt
- PCE17.017-delivery-journal-and-python-runtime-inspection, 2026-10-12 01:53:17–01:53:19 UTC.
- `COMMAND_FAILED`, exit_code 1. Execution progressed through PowerShell read-only state inspection, then Python `-c` string was altered by Windows/Powershell quoting: Python traceback represented `names=[windows_relay.py,hud.py]` rather than string literals, raising `NameError: name 'windows_relay' is not defined`.
- No server, HUD, Firefox or persistent state mutations were requested. No Python runtime compatibility result was established by this failed attempt. Ordinal .017 consumed. Next .018 must avoid quoted string literals nested inside Python -c, or run Python by script/file path.

## Read-only observations
- 519 `outbound_deliveries` records, all phase `READY`; no attachments. 520 processed records including 418 OK, 99 COMMAND_FAILED, 1 EXEC_ERROR, 1 TIMEOUT, and current .017 INFLIGHT. State armed true, owner `browser`, no pending missions. INFLIGHT was the currently executing .017, not proved to be orphaned.
- Python and Pythonw system command resolution point at the user-installed Python 3.13 executables (no canonical `.venv`). Presence is not equivalent to successful Tkinter and canonical AST checks.

## Interpretation from canonical staged WIP source (not yet running)
- The source at WIP commit a35d325ce9a666a372e2a88bc7b60704bdf785f9, `windows-relay/windows_relay.py` State.mark lines ~260–272 records each execution's saved result as outbound phase READY.
- The Windows outbound worker only claims READY/PRE_SUBMIT_FAILED if `outbound_owner == windows`; source `list_claimable_outbound_ids` enforces this. Current observed owner is `browser`. `windows-relay/windows_outbound_worker.py` explicitly marks sender dormant.
- Therefore 519 READY entries do **not prove** 519 unsent ChatGPT replies. Delivery in browser is separately evidenced by browser events and visible turns. State growth and retention still need investigation; never bulk-send, flush, clear, or acknowledge journal based only on READY count. Actual installed nested runtime behavior must be inspected independently before asserting identity with candidate code.

## Safety and next action
- No cutover at .017. Last observed legacy active backend PID 13344 and legacy watchdog/HUD. Independent Task Scheduler helper success was established by .014.
- Next .018 should inspect actual legacy source handling READY, verify Python/AST and Tkinter using `-c` source **without embedded Python quoted literals**, reconfirm no old/new process identity changes, and preserve backup.
- Preserve one integrated development build plus future re-release; do not alter old running backend until a bounded independent helper and rollback are ready. No automatic chat rotation.
