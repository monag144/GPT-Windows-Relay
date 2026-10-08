# GPT Windows Relay — Current TODO

Snapshot: `2026-10-08T0020Z`

**Read this file every engineering turn.**

Canonical repository: `monag144/GPT-Windows-Relay`.

Current roadmap: `../docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md`.

## P0 now

- [x] Control Harness v3 and per-turn discipline.
- [x] Five-turn audit cadence encoded in harness and relay-result source; PCE10.000-.004 audit completed and promotion blocked pending green source acceptance.
- [x] Windows Relay source/test/evidence migration out of Termux.
- [x] Active Termux branch tips cleaned of classified Windows Relay assets.
- [~] Source behavior and migration/scoped-diff gates are green. PCE10.012 then failed read-only at exact `resolve-conversation-tab` before any live staging. The compact visible result omitted the nested adapter error. Incident `INCIDENT_2026-10-08T0123Z_PCE10_012_EXACT_CONVERSATION_RESOLVER_FAILURE.md` is open. PCE10.013 is diagnostic-only: extract the saved exact resolver error, rerun the semantic resolver, and collect bounded Firefox process/window telemetry before any mutation.
- [ ] Deploy the relay reminder change with rollback; restart and positively prove it in a fresh result.
- [ ] Complete control-plane reconciliation acceptance and guarded live cutover.
- [ ] Merge accepted reconciliation into Windows `main`.

## Next external/product gates

- [ ] Signed persistent Firefox XPI/policy installation.
- [ ] Full Firefox restart and Windows/login restart zero-touch acceptance.
- [ ] Chrome/Edge clean-consumer matrix.

## Deferred

- Scroll/conversation-follow UX remains deferred unless the Director reopens it or new evidence materially changes the failure.

Historical pre-PCE10 backlog: `../docs/history/TASKS_2026-10-08T0020Z_LEGACY_WINDOWS_RELAY_BACKLOG.md`.
