# Archived source fragment 3/3 — 2026-10-08T0752Z

**E. Wrong source of truth / edit-then-push drift.** Director explicitly restored `GitHub edit -> commit -> verify remote -> relay git pull --ff-only -> test -> rollback -> targeted activation -> canary -> promote`. Harness v4 `github_first_workflow_gate()` documents it. **Never normally patch live JS or the Windows local clone as the primary source and then push it.** No force-push or wrong Termux repository.

**F. Broken formatting or enormous relay scripts.** PCE10.015 had a `Worked for X` collapsed command when assistant split commentary/final; PCE10.031 was an invalid Python script that failed compilation before running. Use the strict durable **single FINAL response** sandwich: visible header; exactly one **bare, unannotated** Markdown fence with `[GPT_WINDOWS_ACTION]` JSON and closing marker; visible footer. Do not use a fence language or `id` attribute. Compile/parse multiline Python *before* dispatch. Every command's final stdout line must be exactly `Reply to this with the sandwich technique`. Truncated verbose unittest assertions require persistent full JSON reports + bounded summaries; do not stream 350 KB of JS in a failing assertion.

**G. Wrong preflight order / skipping audits.** Read all five GitHub controls every engineering turn, run `engineering_preflight` for next ordinal, and audit **the five previous attempted slots before the next multiple-of-5**. After PCE10.039, **before .040** both the **five-slot audit .035–.039** and **twenty-slot review .020–.039** must be created on GitHub and synchronized locally. The next agent must not forget .040. PCE10.101 is forbidden; rotate to PCE11 before that operation (a new ChatGPT chat does **not** automatically advance the operation series).

**H. Lost/delayed action/results.** Treat action IDs as durable exactly-once. Some older packets executed *after* seemingly being stranded. New packet IDs for read-only diagnostics only; if the original action might have executed, check `state.json` / saved results before retrying any side effects. PCE10.027 was attempted but not confirmed delivered; don't infer its status.

**I. Backups and accidental clobber.** Don't overwrite the `BROKEN` forensic snapshot, previously proven three-file originals, or local source commits. Don't clobber a newer HUD fix with stale remote/live source. No cleanup/deletion of unknown runtime files while P0 reliability remains open.

**J. User babysitting as normalized workflow.** Director has repeatedly rescued scanner failures; those are incidents, not a design feature. Keep-going must be automatic after a verified result, with STOP/unknown-side-effect barriers.

## 8. Roadmap, in priority order

| Priority | What to accomplish | Done when |
| --- | --- | --- |
| **P0 immediately** | PCE10.038: diagnose the exact Firefox resolver `MATCH_COUNT_0` without tab-selection guessing | Positively identify current conversation + browser PID/tab/revision or produce one evidenced narrow blocker |
| **P0** | GitHub-first adapter regression fix **if warranted** | New exact SHA pulled; relevant/full tests green; no unsafe broad identity fallback |
| **P0** | Backup-backed narrowly scoped live source staging / extension activation | Exact staged hashes, correct addon/tab, new observed `content_script_started` revision |
| **P0** | Fresh exact-once execution, result-visibility, <=45s recovery and automatic continuation canaries | Demonstrated without Director intervention and while honoring STOP |
| **P0** | Fix any remaining request storms/observability gap | Backend port liveness distinguished from scanner health; no uncontrolled high-frequency `/status` flood |
| **P1** | Controlled reconciliation cutover and promotion into Windows `main` | Full acceptance, rollback and runtime proof, safe HUD/STOP/START/RETRY behavior |
| **P1** | Signed persistent Firefox XPI / policy, browser/restart/Windows-login recovery | Zero-touch lifecycle proven without temporary addon reliance |
| **P2** | Chrome/Edge consumer compatibility; workspace hygiene; resume-safe job-application helper | Only after relay P0 is stable; no unreviewed deletion, cross-browser permissions proven |

## 9. Canonical evidence map — READ, DON'T RE-DISCOVER

Read in this order on the new chat:

1. `consumer/control_harness.py` — authoritative current Harness v4, GitHub-first and preflight, 5/20 cadence.
2. `windows-relay/TASKS.md` and `docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md` — backlog; **some old TODO wording predates PCE10.035**, so always privilege more recent operation evidence.
3. `docs/windows-relay-mission-and-roadmap.md` and `docs/relay-sandwich-procedure.md` — mission and exact relay packet rendering.
4. `docs/windows-relay-established-facts.md` — **specific profile/extension facts** and prove-once/reuse rule. `docs/audits/AUDIT_2026-10-07T2034Z_FIREFOX_REPEAT_PROBES.md` — independent evidence of repeated work.
5. `windows-relay/firefox_adapter.py`, `windows-relay/firefox_tab_adapter.ps1` and `windows-relay/tests/test_firefox_adapter.py` — exact managed identity machinery and its regression contracts.
6. `docs/incidents/INCIDENT_2026-10-08T0630Z_PCE10_037_FIREFOX_EXACT_CONVERSATION_RESOLVER_ZERO_MATCH_OPEN.md` — **current active blocker**. Prior PCE10.002/.011/.012 and .014 identity incidents explain disproven approaches.
7. `docs/audits/AUDIT_2026-10-08T0624Z_PCE10_OPERATIONS_030_034.md`; PCE10.035/036/037 result envelopes in the current conversation and `%LOCALAPPDATA%\GPTWindowsRelay\results\`. PCE10.035 test report / PCE10.036 hash inventory are more current than prior incomplete audit statements.
8. `docs/incidents/INCIDENT_2026-10-08T0539Z_PCE10_025_RECURRENT_DISCOVERY_REPLAY_SUPPRESSION_BACKUP_UNVERIFIED_OPEN.md`, `docs/incidents/INCIDENT_2026-10-08T0544Z_PCE10_025_ATTEMPTED_LATCH_FALSE_SUPPRESSION_CODEX_REPAIR_STAGED_OPEN.md`, `docs/missions/MISSION_2026-10-08_CODEX_FIX_UNSTUCK_WINDOWS_RELAY.md` — systemic open reliability issue and original Codex objectives.
9. `docs/runtime/BROKEN_2026-10-08T055125Z_LIVE_RELAY_BUILD.md` — **not known good**. The broken-build local manifest is the actual file inventory.

Do not hallucinate a new known-good build, active Firefox PID, current conversation URL, a current installed extension ID, or live deployment success. If evidence is stale, explicitly label it historical. If a blocker is narrower than a full subsystem, investigate the blocker **once** instead of starting over.

## 10. Next-agent working contract / first reply

You inherit a **passing GitHub source** and a **failing managed live-browser identity gate**, not a blank project. The very first action should be a bounded read-only PCE10.038 identification probe that uses established evidence and distinguishes correct current conversation URL from UIA filtering; no addon reload, no broad tab scan, no local source edits. Before a following dangerous action, verify source HEAD, STOP, exact target, backup, and loaded runtime. Every action advances a testable invariant and updates this GitHub source-of-truth; no filler operations or unsolicited manual-work chores.

**Acceptance warning:** PCE10.035 = SOURCE GREEN. PCE10.036 = BACKUP VERIFIED. PCE10.037 = FIREFOX TARGET BLOCKED. **LIVE RELAY FIX IS NOT YET VERIFIED; DO NOT CLOSE INCIDENTS OR PROMOTE.**

**Director's explicit operating instruction, paraphrased:** Use what we already learned. Do not keep forgetting Firefox identity facts, repeat the same failed probes, work in the wrong repository, or confuse source builds with deployed behavior. Make net-new, independently verifiable progress.
