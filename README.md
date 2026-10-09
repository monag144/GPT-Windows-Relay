# GPT Windows Relay

Canonical repository for the Windows relay, Windows consumer/runtime tooling, and reusable job-application automation.

Windows relay engineering, documentation, testing, issues, and commits belong exclusively in **`monag144/GPT-Windows-Relay`**, branch `main`. Verify that local Git remotes target this repository before changing Windows files.

Local source checkout target: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\GPT-Windows-Relay`. Deployed runtime: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay`. The deployed tree is not a replacement for the source checkout.

Start at [`docs/index/INDEX_2026-10-07T2034Z_WINDOWS_RELAY_SOURCE_OF_TRUTH.md`](docs/index/INDEX_2026-10-07T2034Z_WINDOWS_RELAY_SOURCE_OF_TRUTH.md).

## Repository scope

- `windows-relay/` — Windows relay runtime, Firefox/Chromium bridge, HUD/control tooling, Windows automation helpers, and job-application engine.
- `consumer/` — packaged Windows consumer application, updater, browser manager, control harness, and recovery supervisor.
- `docs/` — Windows relay engineering history, operational rules, incidents, handoffs, and reusable automation documentation.

User-specific applicant profiles, credentials, and job-application dossiers are intentionally not stored here. Runtime PII belongs in local-only application data.

## Historical migration provenance (not an operational dependency)

The Windows repository was separated from the earlier combined Termux/Windows project on 2026-10-06. Its legacy source snapshots are recorded in [`docs/MIGRATION_2026-10-06_WINDOWS_REPOSITORY_SPLIT.md`](docs/MIGRATION_2026-10-06_WINDOWS_REPOSITORY_SPLIT.md). No Windows work should be fetched from, committed to, or otherwise routed through the former Termux repository. Retain archived provenance without reopening that source as an engineering destination.
