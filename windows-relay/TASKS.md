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
- [~] Source behavior and migration/scoped-diff gates are green. PCE10.013 isolated `FIREFOX_CONVERSATION_MATCH_COUNT_0`; PCE10.014 then completed a read-only visible URL/PID diagnostic, but the compact result truncated its final verdict. The PCE10.010-.014 audit is complete at `docs/audits/AUDIT_2026-10-08T0128Z_PCE10_OPERATIONS_010_014.md`. PCE10.015 must extract the saved PCE10.014 verdict and positively establish the current visible ChatGPT conversation URL/PID before any identity repair or live canary.
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
