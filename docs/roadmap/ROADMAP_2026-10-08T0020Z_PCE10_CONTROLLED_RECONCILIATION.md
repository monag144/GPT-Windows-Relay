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
- [~] PCE10.015 experienced a repeated user-reported `Worked for X` rendering collapse because its packet was emitted in commentary followed by an empty final. PCE10.016/017 final-message probes succeeded; PCE10.015 has no saved result. Harness v3 now requires final-only sandwiches. Source includes a mission-independent PCE collapse observer (three identical content scripts), RENDER COLLAPSED HUD state, and regression tests; PCE10.018 must execute targeted/full tests and JS syntax verification. Browser/live promotion remains blocked.
- [~] PCE10.014's visible URL probe reported zero visible ChatGPT conversation URLs, despite an armed/online relay. The UIA observation does not prove Firefox closure or target identity. Do not reload the add-on or assume the old URL until a managed conversation identity is positively established.
- [ ] Promote the reminder change to the live relay with rollback and restart proof.
- [ ] Verify a fresh relay result contains the mandatory checklist.
- [ ] Complete reconciled control-plane full-suite acceptance.
- [ ] Guarded live control-plane deployment with detached STOP→START/8766 ancestry proof.
- [ ] Merge/promote the reconciliation branch to Windows `main`.
- [ ] Close the signed persistent Firefox XPI/policy external gate, then full Firefox + Windows/login restart acceptance.
- [ ] Run Chrome/Edge clean-consumer acceptance matrix.

## Five-operation audit status

PCE10.000-.004 audit: `docs/audits/AUDIT_2026-10-08T0024Z_PCE10_OPERATIONS_000_004.md`.

PCE10.005-.009 audit: `docs/audits/AUDIT_2026-10-08T0108Z_PCE10_OPERATIONS_005_009.md`.

PCE10.010-.014 audit: `docs/audits/AUDIT_2026-10-08T0128Z_PCE10_OPERATIONS_010_014.md`.

Promotion verdict: **BLOCKED** until the scoped diff gate and Firefox live canary are green.

## Reliability invariants

- Backend exact-once and submit-once browser delivery remain independent.
- Operator STOP must quiesce browser autonomy; operator intent outranks self-healing.
- Rollback snapshot precedes every live mutation.
- No Windows source mutation belongs in GPT-Termux-Relay.
- PCE10.101 is forbidden; rotate to PCE11 before that operation.
- Established Firefox lifecycle facts are reused unless browser state changed or an acceptance gate explicitly requires re-proof.
