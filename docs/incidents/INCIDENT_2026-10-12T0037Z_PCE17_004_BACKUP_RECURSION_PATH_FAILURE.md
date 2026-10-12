# PCE17.004 backup recursion/path failure — 2026-10-11

**Repository:** `monag144/GPT-Windows-Relay` (Windows only). **Observed:** 2026-10-11 17:36–17:37 PDT / 2026-10-12 00:36:59–00:37:12 UTC.

## Exact attempted operation and receipt
- Issued action `PCE17.004-final-cutover-readiness-and-rollback-backup`, session `pce17.1`, via authenticated Windows Relay.
- Native status: `COMMAND_FAILED`, exit code 1. This ordinal is consumed and MUST NOT be replayed.
- Six approved canonical artifacts passed SHA-256 verification: backend, five-button HUD, controller, watchdog, launcher, persistent-extension worker.
- After checks, a unique backup folder was created under `LOCALAPPDATA/GPTWindowsRelayDeployBackups/`. AppData configuration copy was attempted; recursive copy of the entire `LOCALAPPDATA/GPTWindowsRelay` folder failed when it encountered a historical nested backup containing `live/.venv/Lib/site-packages/...` and a deep Python package path.
- Reported PowerShell error: `Copy-Item DirectoryNotFoundException` for nested legacy `backups/BROKEN-PCE10.026-.../live/.venv/.../emscripten_fetch_worker.js`.
- Backup completion marker, post-copy validation and listener identity check were NOT reached. Files already copied may constitute a partial/unverified backup.

## Cause and impact
The backup method was over-broad: it recursively copied historical backups, development virtual environments and other nonessential archival artifacts alongside current operational data. This exceeded practical path/copy reliability. The receipt does not establish a source-state mutation or a completed rollback set.

**No cutover was attempted:** no STOP, process termination, Firefox reload, source replacement or live deployment was requested or observed. Do not treat the partial backup as trusted rollback evidence, and do not assume it is disposable without a separate inventory and approval.

## Corrective next step
1. Preserve and identify the incomplete `.004` backup without automatically deleting or overwriting it.
2. Inventory essential *live* config/state, outstanding missions, action/results and delivery journals, and required browser pairing data **without reading out or publishing secrets/content**. Exclude `backups/`, `.venv/`, historic source trees, caches and transient logs unless needed for a specific rollback dependency.
3. Prepare a distinct, exclusive-create, allowlisted rollback snapshot; copy only verified necessary paths and protect against recursive traversal/junctions. Verify file counts, lengths, and hashes before calling it complete.
4. Check active listener and Firefox ownership before any service transition. Preserve the old runtime, HUD and browser extension as rollback sources. Live cutover must be separately staged with a fail-closed handoff and no uncertain action replay.
5. Before issuing PCE17.005, commit and read back the PCE17.000–.004 five-operation audit from canonical GitHub `main`.

## References
- Canonical control: `consumer/control_harness.py`.
- Dated priorities: `docs/roadmap/WINDOWS_RELAY_MISSION_AND_PRIORITIES_2026-10-09.md`.
- Native results supplied by operator for PCE17.000–PCE17.004.
- WIP build identity as of incident: `a35d325ce9a666a372e2a88bc7b60704bdf785f9`; do not confuse this source commit with a deployed runtime.
