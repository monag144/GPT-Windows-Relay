# GPT Windows Relay

Canonical repository for the Windows relay, Windows consumer/runtime tooling, and reusable job-application automation.

Windows Relay engineering belongs exclusively in **`monag144/GPT-Windows-Relay`**. The **active integrated development branch** is `wip/windows-relay-rebuilt-resynced-2047-101026`; `main` is the separate stable/reviewed baseline and is not the default delivery target for the current Main-Build work. Verify the remote and branch rather than switching/resetting a dirty checkout.

**October 12 verified installation:** the operator loaded and successfully executed from `GPT-Windows-Relay-Main-Build/windows-relay/` using that directory's `extension-persistent/` Firefox add-on v0.3.18. No legacy Client tree is the verified deployed source. See the [dated live execution checkpoint](docs/releases/WINDOWS_RELAY_LIVE_EXECUTION_CHECKPOINT_2026-10-12.md). Historical Client paths are not installation instructions.

**No local backups:** [2026-10-12 operator policy](docs/policy/WINDOWS_RELAY_NO_ON_DEVICE_BACKUPS_2026-10-12.md) forbids on-device source snapshots and rollback folders. GitHub remote source history is the approved recovery method. A pinned [preconsolidation archive branch](https://github.com/monag144/GPT-Windows-Relay/tree/archive/preconsolidation-source-2026-10-12) preserves previously published legacy files without rechecking them out in Main-Build.

**Working engineer:** [ChatGPT source ownership and push-before-pull delivery — 2026-10-11](docs/policy/WINDOWS_RELAY_ENGINEERING_OWNER_AND_DELIVERY_2026-10-11.md). Routine source engineering is done in GitHub first, then a safe relay pull is supplied. Codex is for heavy repair. [Read-only runtime identity diagnostic](windows-relay/tools/Inspect-Relay-Runtime-Identity.ps1) checks old Client versus Main-Build startup references without touching the runtime.

**Execution policy:** [No relay governance or audit preflight](docs/policy/WINDOWS_RELAY_EXECUTION_WITHOUT_GOVERNANCE_2026-10-11.md). Tests, benchmarks and reviews are separate from authorized command admission; STOP, token and owner safeguards remain mandatory.

**Verified build record:** [Windows Relay live execution checkpoint — 2026-10-12](docs/releases/WINDOWS_RELAY_LIVE_EXECUTION_CHECKPOINT_2026-10-12.md) pins the approved source tag. It is not a certification of the entire test suite.

**Documentation:** [Windows Relay documentation index — 2026-10-09](docs/index/WINDOWS_RELAY_DOCUMENTATION_INDEX_2026-10-09.md). This is the newer date-only reading directory; earlier timestamped indexes remain historical evidence. Root `README.md` stays as a conventional GitHub navigation alias.

## Repository scope

- `windows-relay/` — Windows relay runtime, Firefox/Chromium bridge, HUD/control tooling, Windows automation helpers, and job-application engine.
- `consumer/` — packaged Windows consumer application, updater, browser manager, control harness, and recovery supervisor.
- `docs/` — Windows relay engineering history, operational rules, incidents, handoffs, and reusable automation documentation.

User-specific applicant profiles, credentials, and job-application dossiers are intentionally not stored here. Runtime PII belongs in local-only application data.

## Historical migration provenance (not an operational dependency)

The Windows repository was separated from the earlier combined Termux/Windows project on 2026-10-06. Its legacy source snapshots are recorded in [`docs/MIGRATION_2026-10-06_WINDOWS_REPOSITORY_SPLIT.md`](docs/MIGRATION_2026-10-06_WINDOWS_REPOSITORY_SPLIT.md). No Windows work should be fetched from, committed to, or otherwise routed through the former Termux repository. Retain archived provenance without reopening that source as an engineering destination.
