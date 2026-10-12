# Windows Relay workspace consolidation — 2026-10-10

> **2026-10-12 evidence update:** This is a historical consolidation snapshot, **not** a current guarantee of one physical runtime/build. A new local audit found the untracked 3,280-file `windows-relay/runtime/` and multiple competing Prototype/backup copies. The operator has superseded the local-backup-retention preference and directed a GitHub-first **one-runtime/no-local-backups** cleanup. See [multiple-build disk audit](reviews/WINDOWS_RELAY_MULTIBUILD_DISK_AUDIT_2026-10-12.md) and [Codex issue #30](https://github.com/monag144/GPT-Windows-Relay/issues/30). Historical facts below are retained for provenance; they must not override newer measured evidence.


The single Git checkout is `GPT-Windows-Relay-Main-Build`, containing `Prototype/` and `Backup/`. The installed runtime remains deliberately outside the checkout at `GPT/Client/Relay`; it is the sole preserved Client installation and must not be moved during this phase.

Runtime evidence: the backend and HUD launchers reference `GPT/Client/Relay`; the verified persistent Firefox package is staged under the Main-Build `windows-relay/extension-persistent` source and in the WIP snapshot. No live deployment is inferred from disk copies.

Other locations audited: `GPT-Windows-Relay-Consolidation-2026-10-10` (historical consolidation with unique records), `Prototype-Developing` (development artifacts), `GPT/Client/Relay` (installed runtime), and `GPT-Windows-Relay-Main-Build` (Git checkout). Historical rollback/build directories under Client are retained. No occupied or unique directory was moved or deleted.

Unique work and untracked artifacts remain preserved in place or under existing `Prototype/` and `Backup/`. No credentials, state databases, logs, caches, browser profiles, virtual environments, or executables are staged.

Known blocker retained: PCE16.038 native receipt exposed the legacy governance/API compatibility mismatch. This WIP is not a stable release.
