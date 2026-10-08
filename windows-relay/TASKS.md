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
- [~] Source acceptance remains pending. PCE10.005 never reached Windows execution: browser discovery stalled indefinitely in `relay_packet_discovered` because an unchanged stale pending-settle record had no lease. Harness/content/test repair is committed; PCE10.006 must validate it, deploy the repaired managed Firefox content runtime with rollback, reload via the established Firefox adapter, and prove the browser escapes permanent DISCOVERED.
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
