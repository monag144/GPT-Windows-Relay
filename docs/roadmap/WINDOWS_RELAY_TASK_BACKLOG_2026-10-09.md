# Windows Relay task backlog — 2026-10-09

**Scope:** `monag144/GPT-Windows-Relay`, Pacific-local date snapshot. This is a short prioritized backlog based on known PCE15 results, not an active-operation allocation to a running agent.

## Open verification work

- [ ] Correct the non-atomic lookup → reserve claim race revealed in isolated PCE15.043 tests, under an explicitly authorized source-change gate, and prove concurrency across thread/process boundaries.
- [ ] Prevent processed-ID cache eviction from permitting post-execution replay. Make identity retention durable, bounded safely and fail closed across restart, including SUBMITTED and SUBMIT_UNCERTAIN outbound states. The PCE15.049 ledger prototype was memory-only.
- [ ] Identify the **actually loaded** Firefox extension and preserve conversation ownership. Close G16 with live evidence.
- [ ] Verify G26 independent exact-result sends (last verified 0/60), and G27 endurance runs (last verified 0/2). Do not count mock execution or static code scans.
- [ ] Reconcile signed XPI, source/Client build provenance, release packaging and Firefox/Windows lifecycle acceptance.
- [ ] Respect the GitHub-first five-operation checkpoint and twenty-operation review; no unverified audit credit. The last observed governance sync accepted PCE15 audit [45,49] and saw PCE15.050 unconsumed, but another agent may have progressed since then; inspect actual receipts before using an ordinal.

## On hold by direct user instruction

- [ ] **PAUSED, do not execute or develop:** automatic new-agent / new-conversation rotation, watcher-driven switching, experimental replacement switching mechanism, and fallback agent handoff automation. A manual user-requested one-shot `Run-Copy-Contents.cmd` transfer is the only approved handoff for now.

## Evidence/reference

Historic `windows-relay/TASKS.md` at commit `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8` contains extensive prior PCE8/PCE9 task chronology, old statuses and rotation items. That archived state should not be relabeled 'current'. Open release blocker incidents: `docs/incidents/INCIDENT_2026-10-10T0250Z_PCE15_NONATOMIC_ACTION_CLAIM_AND_OWNER_GUARD_GAPS.md` and `docs/incidents/INCIDENT_2026-10-10T0304Z_PCE15_DEDUP_RETENTION_POST_EVICTION_REPLAY.md`.

Before editing or executing, inspect the actual installed governance files and any more recent engineering actions. Do not replace a current in-progress agent's backlog merely because this document was published.
