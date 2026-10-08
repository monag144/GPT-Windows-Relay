# PCE10 controlled reconciliation roadmap — 2026-10-08T0020Z

Canonical repository: `monag144/GPT-Windows-Relay`.

## Per-turn control contract

Before every engineering turn:
1. read `consumer/control_harness.py`;
2. read `windows-relay/TASKS.md`;
3. read this roadmap;
4. read `docs/windows-relay-mission-and-roadmap.md`;
5. use sandwich formatting for relay actions;
6. repair/test any harness hole before risky mutation;
7. audit the preceding five engineering turns at least every fifth turn/operation.

## Immediate P0 sequence

- [x] Control Harness v3: per-turn reads, canonical Windows repo, harness-hole rule, five-turn audit cadence.
- [x] Relay result serializer source: explicit per-turn checklist + five-turn audit reminder.
- [x] Termux r29 source/test migration proof: all 87 `windows-relay/` paths represented in Windows repo.
- [x] Missing A6/R29/PCE8/PCE9/job-application evidence migrated.
- [x] Windows-specific assets removed from all active Termux branch tips that contained them; 0/13 active branches expose `windows-relay/README.md`.
- [ ] Run local source acceptance from a canonical `GPT-Windows-Relay` clone.
- [ ] Promote the reminder change to the live relay with rollback and restart proof.
- [ ] Verify a fresh relay result contains the mandatory checklist.
- [ ] Complete reconciled control-plane full-suite acceptance.
- [ ] Guarded live control-plane deployment with detached STOP→START/8766 ancestry proof.
- [ ] Merge/promote the reconciliation branch to Windows `main`.
- [ ] Close the signed persistent Firefox XPI/policy external gate, then full Firefox + Windows/login restart acceptance.
- [ ] Run Chrome/Edge clean-consumer acceptance matrix.

## Reliability invariants

- Backend exact-once and submit-once browser delivery remain independent.
- Operator STOP must quiesce browser autonomy; operator intent outranks self-healing.
- Rollback snapshot precedes every live mutation.
- No Windows source mutation belongs in GPT-Termux-Relay.
- PCE10.101 is forbidden; rotate to PCE11 before that operation.
- Established Firefox lifecycle facts are reused unless browser state changed or an acceptance gate explicitly requires re-proof.
