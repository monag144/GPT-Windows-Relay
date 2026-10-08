# PCE011 Relay recovery and One-Click GO release queue — 2026-10-08T0852Z

## Mission and precedence
Primary objective: a standalone Windows Relay that survives a full unattended night, then a consumer One-Click GO r28-based build qualified against the **same A–Z tests**. Neither is allowed to inherit PCE9/PCE10's unaccepted live state. Preserve historic source, rollback and exact-once effects. User explicitly prefers GitHub-first change, quick small operations, no routine requests for permission, and Codex CLI after >5 attempts at the same failing approach. Codex model preference is 5.6 or 6 Luna *if available*; do not invent installed model names.

## Before EVERY numbered operation
1. Read `consumer/control_harness.py` **in full**, not only its version or a summary. Read this queue **in full**, the canonical legacy facts and the sandwich procedure. Compute and print exact SHA256/byte counts. Run `engineering_preflight(root, ordinal, series=11)`, which is a read-only governance gate, not live activation approval.
2. Confirm `monag144/GPT-Windows-Relay` remote and exact immutable source SHA; do not commit Windows source to the Termux repository. GitHub edit -> commit -> verify -> Windows `git pull --ff-only`. Stop unsafe mutations on dirty/divergent worktrees.
3. Read evidence from last operation. Distinguish command executed, saved result, result delivered and assistant turn finished. Never replay uncertain IDs. Honor operator STOP and the whole-product safety state.
4. Inspect prior incident/historical proof before probing; never repeat already-settled Firefox or profile archaeology. Record why the current operation makes measurable net-new progress.
5. Keep source/test/docs/restore changes within explicit allowlist and rollback. Do not delete old branches, backups or user files for housekeeping.

## Immediate ordered queue
- **PCE011.001:** GitHub-only harness/queue correction, cite existing PCE10.015–.019 retro-audit `docs/audits/AUDIT_2026-10-08T0316Z_PCE10_OPERATIONS_015_019.md`. Record PCE011 start / operation baseline; repair obsolete PCE10-specific mandatory reads and next-turn prompt. Source/tests first.
- **PCE011.002:** Verify historic Termux *commit objects* `d5b9db7ad785b5cae8dc3b64219303b9fcfa634a` (complete r28 consumer+relay source tree) and `694d47ab89596d5c3801f749caa352b951a2be52` (PCE8 v16 source candidate). Both are earlier than branch-tip Windows migration cleanup. The latter is NOT proof of a complete installed live binary; the recorded v16 content SHA is historical runtime evidence.
- **PCE011.003:** Pull verified PCE011 GitHub tooling to canonical Windows checkout **only if clean/ff-only**; quarantine existing possibly broken `Client/Relay` installation **by local ZIP/manifest copy into its `bin/` folder**; DO NOT move/kill the running listener. Stage separately pinned historic r28 and v16 candidate trees under local `builds/`, each with exact `git rev-parse HEAD` receipt. Preserve the original live runtime to keep relay conversation alive.
- **PCE011.004:** In separate staging folders, run bounded Python/PowerShell/JS syntax, consumer/relay tests; record failures. Do not promote because tests alone do not certify live.
- **PCE011.005:** First five-operation audit of .000-.004, including skipped/failed slots. Reconcile exact SHA/manifest and verify rollback feasibility.
- **PCE011.006+:** Reconstruct exact full PCE8-v16 or PCE7 usable fallback, choose by evidence; stage a **reversible targeted** Relay replacement only after independent STOP, identity, rollback and canary gates. Do not swap code while its own execution is still running; use an independent supervisor and pre-recorded rollback.
- **Subsequent:** A–Z standalone Relay v16 vs PCE7 legacy benchmark; read-only observer plus independent hourly exact-result missions; 12h overnight and 24h qualifying run. Then consumer r28 One-Click GO Chrome/Edge matrix. Promote only proven changes.
- **HUD modernization:** preserve new interface where compatible; add **RETRY** without unsafe replay. User wishes to remove KILL eventually, but STOP and KILL **are not equivalent** until whole-product STOP/browser-quiescence and restart recovery are proven; don't remove emergency KILL before replacement acceptance.
- **Codex CLI:** optional scoped repair after 5 **distinct** failed attempts at an issue, preserving incident and source evidence. Never use to bypass GitHub-first, environment STOP or exact-once semantics.

## Control checkpoints
- **Every 5 numbered operations:** `AUDIT_<UTC>_PCE11_OPERATIONS_NNN_NNN.md` covering previous five slots (first before PCE011.005: .000-.004), with success/failure/blocked, manual rescue count, net-new progress, SHA, rollback, and plan adjustment.
- **Every 20 numbered operations:** `REVIEW_<UTC>_PCE11_OPERATIONS_NNN_NNN.md` summarizing four audits and revising this queue (first before .020).
- **At PCE011.050:** soft checkpoint and user-facing concise findings email *when email access is present and delivery is explicitly executed*. This is not permission to continue unsafe actions while STOP/unknown effects are unresolved. Do not claim mail sent without a Gmail send receipt. Preflight can flag due, but does not itself send email.
- **At PCE011.100:** gate for safe semantic New chat, preserve handoff/owner epoch, create/verify successor `💻PC Engineering 12🔧`; never execute OP101 in same managed session. If remote UI control unavailable, log a block; do not claim rotation occurred.
- User requests uninterrupted unattended work; this requires an actual running external supervisor or scheduled process. ChatGPT alone cannot autonomously generate future messages, send turn-50 email, or run after this response without external triggers.

## Acceptance
`benchmarks/CASES_2026-10-08T0805Z_A_TO_Z.json` is authoritative, alongside `benchmarks/benchmark_runner.py`. Source green is not live accepted; healthy 8766 port is not a functioning browser. All security/replay/STOP gates must pass. Archive locally; transmit redacted concise score and checkpoint proof via Relay.

## Evidence pointers
- `docs/audits/ACCEPTANCE_2026-10-06T2219Z_PCE8_V16_BROWSER_RECOVERY.md`
- `docs/audits/ACCEPTANCE_2026-10-06T2236Z_PCE8_STALE_OWNER_LEASE_DEADMAN.md`
- `docs/INCIDENT_2026-10-06T0953Z_PCE7_445_447_HUD_CONTROL_CUTOVER_CHAIN.md`
- `docs/audits/AUDIT_2026-10-08T0840Z_PCE011_RELAY_BASELINE_BENCHMARK_READINESS.md`
