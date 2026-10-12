# PCE17.005–.009 Five-Operation Audit — 2026-10-11 (PDT)

Canonical source: monag144/GPT-Windows-Relay, branch main. Assistant engineering governance only; no relay-runtime enforcement.

## Source controls read (GitHub main blobs)
- consumer/control_harness.py: ca2141c45726366abb889db0cb5a794ed8735075
- windows-relay/TASKS.md: d49999dc29466a04ba2c27cc39f341b9162779e9
- dated documentation index: c10b5ef2e1b33d87f77cc689f041110ffab127f9
- dated mission/roadmap: 86c3e0c3f2d1c44de9cccdc819597f120c8732be
- dated task backlog: 9a59e77967dc384962a777869c1964f9bda60e29
- established safety: 693ad770964352de7de26886ba3b4e295ac0357a
- previous .000–.004 audit: 1a7015838836f33386a241e004fe75deb108c8af
- incidents: docs/incidents/INCIDENT_2026-10-12T0037Z_PCE17_004_BACKUP_RECURSION_PATH_FAILURE.md and docs/incidents/PCE17_005_LEGACY_RUNTIME_AUDIT_GATE_2026-10-11.md.

## Issued ordinal evidence (native receipts, UTC)
- PCE17.005-allowlisted-verified-operational-backup: GOVERNANCE_BLOCKED 2026-10-12 00:40:57, no reservation/execution; old runtime wrongly reported github_checkpoint_audit_missing despite committed/read-back .000–.004 audit. .005 consumed. No backup from .005.
- PCE17.006-targeted-rollback-snapshot: OK 00:43:27–00:46:04; verified SHA256 copy of 2,628 allowlisted files, excluding historical backups and virtualenv. Backup marker and manifest at LOCALAPPDATA/GPTWindowsRelayDeployBackups/PCE17-006-20261011-174328-5118e464.
- PCE17.007-pre-switch-shutdown-and-runtime-check: OK 00:47:31–00:47:34; confirmed old runtime PID 7464 on port 8766, authenticated armed=true, pending_missions=2; backup marker and manifest present. Read-only.
- PCE17.008-legacy-off-control-safety-inspection: OK 00:48:54–00:48:55; read old controller SHA256 79264E06AE53F54BFE5F43CAC6664F967C32244FFC1201F46F280A4D6E9850FC, verified OFF path and old watchdog OFF latch; active_action observed while current command executing, no external stuck action inferred. Read-only.
- PCE17.009-cancel-two-stale-chrome-missions: OK 00:52:10–00:52:14; operator explicitly authorized cleanup. Verified exactly two October-4 Chrome-target missions consumer-20261004T052926Z-293c16e0 and consumer-20261004T052951Z-afbbaf68. Created pre-cancel state SHA256 snapshot, acknowledged via authenticated /mission-ack individually, verified PENDING_AFTER=0. Cancellation backup LOCALAPPDATA/GPTWindowsRelayDeployBackups/PCE17-009-Mission-Cancellation-20261011-175213-c4e44cc5. No mission executed by cleanup.

## Audit findings
- Ordinal continuity: .005,.006,.007,.008,.009 were each issued once, no replay. Next .010 requires this audit committed+read back on GitHub main; .020 is next 20-operation review.
- Net-new progress: successful allowlisted rollback after .004 over-broad recursive copy failure, verified legacy shutdown code, and explicit clearing of two orphaned Chrome-target queue entries under operator direction.
- Rollback/side effects: .006 created backup; .009 mutated mission queue and ACK journal, preserving original snapshot. .007/.008 read-only. No stop, off, kill, restart, Firefox reload, new HUD activation, or live cutover occurred.
- Failure/incident: .005 stale runtime governance gate blocked before execution; GitHub audit was actually present. Incident previously committed+read back. Do not bypass STOP/authentication or replay blocked .005. Do not repeat broad recursive backup.
- Current loaded runtime remains legacy nested windows-relay/runtime source; latest approved WIP source commit a35d325ce9a666a372e2a88bc7b60704bdf785f9 is not deployment proof.
- Before live cutover: verify exact legacy backend/watchdog/HUD identities, respect HUD global mutex; stop legacy service using independent local operator console (not a relay command that kills its own return path); verify listener and legacy HUD exit before canonical launch. Maintain rollback and do not replay uncertain commands.
- No automatic agent/chat switching. Assistant governs engineering, relay is transport. No unsupported claim of production acceptance, signed extension, real e2e reliability or endurance.
