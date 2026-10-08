# Archived source fragment 2/2 — 2026-10-08T0752Z

- [ ] Redesign canary so it owns its fresh discovery/execution/result proof instead of waiting for an unissued future packet.
- [ ] Browser acceptance must verify the exact expected conversation in addition to runtime identity.
- [ ] Do not deploy v15 until the three browser-session requirements above have regression coverage and source validation.
- [ ] Whole-product STOP/quiescence remains open.

## Reliability recovery checkpoint — 2026-10-06T2126Z

- [x] Reproduce the Director-observed sustained-forward-progress failure on protected live v11.
- [x] Prove PCE8.61 completed before stale draft recovery reacquired its packet ID.
- [x] Prove failed draft recovery leaked `activeRelayOperationId` and blocked PCE8.62 for multiple minutes.
- [x] Fix the general draft-recovery owner-release invariant in source runtime v16 (`694d47ab89596d5c3801f749caa352b951a2be52`).
- [x] Regression validation: 55 browser-contract tests, 273 Windows-relay tests, 99 consumer tests PASS under canonical suite environments.
- [ ] Guarded live v16 activation on the exact persisted engineering conversation.
- [ ] Fresh v16 exact roundtrip with exact-route proof and no duplicate Windows execution.
- [ ] Explicitly exercise a failed/deferred draft-recovery attempt and prove the next packet is not stranded behind stale ownership.
- [ ] Sustained multi-operation v16 soak with intervention count recorded.
- [ ] Promote v16 to protected live baseline only after the above runtime gates pass.
- [ ] Restore/reconcile the modern HUD only after the browser reliability baseline is stable; live HUD remains the rollback-era implementation.
- [ ] Close whole-product STOP so browser timers, result delivery, recovery refresh, deferred drains and watchdog resurrection all quiesce while stopped.

**Priority note:** R0 sustained relay forward progress remains ahead of the signed-XPI / restart-validation P2 external gate. P2 is still required, but it is not the next engineering action while browser forward progress is not yet accepted.

## PCE8 v16 acceptance status — 2026-10-06T22:19Z

- [x] Guarded v16 live Firefox canary.
- [x] Failed-draft owner-release path live proven.
- [x] Post-release exact-once forward progress proven.
- [x] Five-operation sustained soak proven with zero active-operation starvation.
- [ ] General stale-owner lease/deadman acceptance.
- [ ] Whole-product STOP semantics.
- [ ] Restart/signing/browser-matrix acceptance.
- [ ] Safe managed-conversation rotation.
- [ ] Separately guarded modern-HUD recovery.
- [ ] Audit local/remote divergence before any push.

## PCE8 ownership recovery closure — 2026-10-06T22:36Z

- [x] Failed-draft owner release live proven.
- [x] General five-minute stale-owner lease/deadman live proven.
- [x] Pre-expiry owner retention live proven.
- [x] Exact-replay and exact-visible stale-owner release branches live proven.
- [ ] Whole-product STOP semantics.
- [ ] Restart/signing/browser-matrix acceptance.
- [ ] Safe managed-conversation rotation.
- [ ] Separately guarded modern-HUD recovery.
- [ ] Audit local/remote divergence before any push.

## PCE9 reconciliation checkpoint — 2026-10-07
- [x] Result-confirmation selector/role-gate defect live-proven fixed with exact-once delivery canaries.
- [x] Browser stop-generation/quiescence protocol live-proven; STOP -> START acceptance returned with verified browser quiescence.
- [x] Rich HUD control surface restored live with START/STOP/RESTART/OFF/KILL/MINIMIZE.
- [x] Dual-runtime ownership diagnosed: 8766 control plane and isolated 8767 consumer runtime are intentional.
- [x] Dedicated 8766 control-launcher split implemented and deployed to the current live tree.
- [ ] Reconcile the richer HUD with canonical RETRY support; RETRY exists in Windows-repo source but is absent from the current richer live HUD.
- [ ] Port/reconcile all valid PCE9 Windows changes from the old Termux repository into `monag144/GPT-Windows-Relay`; do not continue Windows development in the old repository.
- [ ] Complete canonical STOP -> START ancestry acceptance proving restarted 8766 is owned by `run-control.ps1`; the pending attempt was interrupted during harness repair.
- [ ] Enforce operation-series rollover so no future managed series can emit OP101.
- [ ] Signed persistent Firefox XPI/policy and full Firefox + Windows/login restart acceptance remain open.
- [ ] Chrome and Edge clean-consumer browser-matrix acceptance remain open.
