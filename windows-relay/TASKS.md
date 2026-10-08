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
- [~] **P0 render-collapse user rescue:** PCE10.015 command collapsed after a commentary/final split. PCE10.016/017 final-channel probes succeeded; PCE10.015 has no saved result and must not be replayed. Source-side engineering collapse detection (without consumer mission), HUD RENDER COLLAPSED state, mirror sync, and regression tests are committed but not yet live. PCE10.018 must run full source acceptance first. Incident: `docs/incidents/INCIDENT_2026-10-08T0200Z_PCE10_015_USER_RESCUE_COLLAPSED_COMMENTARY_COMMAND.md`.
- [~] **P0 recurring discovery stall:** User screenshot shows `DISCOVERED PCE10.018` aged 3774s, relay online/armed, Firefox browser visibly on the expected exact ChatGPT conversation URL. No execution result provided; **do not replay PCE10.018**. The 5s browser settle lease is in canonical source but not proven live. HUD now marks DISCOVERED older than 45s STALLED; harness requires live revision/rollback/canary evidence. Incident `docs/incidents/INCIDENT_2026-10-08T0309Z_PCE10_018_DISCOVERED_STALL_USER_INTERVENTION.md`. One ordinary Firefox page refresh is an authorized rescue bootstrap if no controlled browser path is available; inspect PCE10.018 durable state immediately afterward.
- [~] **Firefox canary still blocked:** PCE10.014 visible URL probe found no visible ChatGPT conversation URL. This negative UIA result does not establish that the browser is closed. Do not hard-code the old conversation URL; secure positive managed-target evidence before any live extension reload/cutover.
- [~] **PCE10.019 source acceptance and live drift:** Source acceptance completed (verify saved exact final text in PCE10.020). All three content scripts and HUD differ from the live runtime by SHA256. PCE10.018 has no backend result/processed entry, and browser events show discovery followed by replay suppression—not execution. Audit PCE10.015–.019: `docs/audits/AUDIT_2026-10-08T0316Z_PCE10_OPERATIONS_015_019.md`. PCE10.020 must establish browser reload path and rollback backup plan before any live mutation.
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
