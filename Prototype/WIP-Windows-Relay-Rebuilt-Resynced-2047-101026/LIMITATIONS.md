# Windows Relay — Rebuilt and Resynced — 2047 101026

WIP snapshot only; not a proven stable production release and not deployed.

This snapshot records the installed Client source that remains in service, including the five-button HUD, lifecycle launchers, supervisor/watchdog, Firefox adapters, and the verified GPT Windows Relay v0.3.17 persistent extension.

Excluded: credentials, tokens, state databases, logs, caches, personal data, virtual environments, generated executables, and runtime artifacts.

Known limitations: disk hashes do not prove in-memory identity; backend/browser integration remains unverified; PCE16.035 and PCE16.036 were not replayed.

## October 10 paired-relay checkpoint

**Status: WIP — saved for later development.** The source snapshot is preserved on the dedicated WIP branch; it has not been deployed as a unified replacement backend. The installed Client backend/HUD continues to run separately from the manually loaded Firefox-persistent extension.

- Client controller was restarted by Codex after observing stale server processes with no TCP listener. Codex reported one listener on 127.0.0.1:8766, HTTP 401 for unauthenticated /status, preserved five-button HUD, a SHA-256 backup at `Backup/repair-20261010-211713/`, and **403 passing offline tests**. See `REPAIR-REPORT.md`. These observations do not prove exact-once side effects or a fully stable release.
- Firefox `GPT Windows Relay` v0.3.17, Gecko ID `gpt-windows-relay@local`, was visibly the sole temporary relay add-on after manual removal of the two One-Click Go instances.
- The persistent Firefox extension popup initially showed **NOT PAIRED**. The operator paired it manually; no pairing secret is included in this repository.
- **PCE16.038-paired-relay-smoke-test** yielded the first observed native `[GPT_WINDOWS_RESULT]` over the newly paired path. Result: `GOVERNANCE_BLOCKED`, `exit_code:null`, stderr `GOVERNANCE_CANONICAL_HARNESS_UNAVAILABLE; no action reserved or executed`. This confirms a browser→backend→ChatGPT **governance-response round trip**, **not a successful command execution or file-read test**. Issued ID .038 is consumed and must not be replayed.
- The preserved Client `windows_relay.py` points its engineering governance check at `Downloads/Dev/GPT/GPT-Windows-Relay` rather than `Downloads/Dev/GPT-Windows-Relay-Main-Build`. It also invokes an older `engineering_preflight(root,ordinal,series)` API incompatible with canonical GitHub's newer function signature and return contract. A path-only edit would not resolve both defects. See `docs/incidents/PCE16_038_PAIRED_RELAY_GOVERNANCE_ROOT_DRIFT_2026-10-10.md`.
- Earlier PCE16.035–.037 have no confirmed native execution receipts; preserve their consumed IDs, do not replay them, and reconcile records before any recovery. PCE16.038 is governance-blocked, not executed.
- The backend STOP/owner/durable replay gaps documented in earlier PCE16 isolated work remain **unresolved in the installed Client**. Do not call this a stable, complete production release.

**Later engineering:** stage a tested, fail-closed governance compatibility adapter against the actual Main-Build harness and a genuine audit/attempt ledger. Preserve STOP, conversation ownership, the Client's five HUD controls, rollback and exactly-once safeguards. Validate offline first, obtain operator approval before live deployment/restart, and run a **new unique** read-only operation to prove a real executed-and-confirmed file-read round trip. Do not rewrite or move the live Client merely because its folder is held open.

**Snapshot label remains:** Windows Relay — Rebuilt and Resynced — 2047 101026. No stable/release promotion.

