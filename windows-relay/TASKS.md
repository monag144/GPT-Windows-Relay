# PCE011 Relay & One-Click GO — Mandatory Daily Task Queue — 2026-10-08T0852Z

## Read THIS ENTIRE FILE and the ENTIRE control harness before EVERY operation
Read `consumer/control_harness.py` completely, this queue completely, `docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md`, established facts and relay sandwich procedure. Run `engineering_preflight(root, ordinal, series=11)` and log SHA256s. The full source is authoritative; a previous model summary is not a replacement.

## Director override: PCE12 transition MUST stay in THIS CURRENT CHATGPT TAB (2026-10-09)
- [ ] **P0 — Same-current-tab rotation**: supersede the distinct-window approach. Identify the currently selected tab that actually contains this relay action/result exchange; pin its current conversation URL, tab automation element, HWND and PID. Click its own **New chat** control, NOT one in another window. Do not launch a new Firefox window/tab, use the old separate-window worker, or assume that the 11-tab window is the invoking tab.
- [ ] **P0 — Current-tab-only end-to-end canary**: after a unique semantic New Chat on the bound current tab (or skip if this very tab is already on blank home), paste pinned PCE12 prompt in that *same tab*, verify exact editor content, Send exactly once with durable no-replay receipt, and verify unique user-role message on the new conversation. Preserve existing unsent draft or stop for explicit resolution. STOP/armed/owner and preflight gates remain mandatory.
- [ ] **P0 — Incident resolution**: PCE11.083 stopped `FIREFOX_NOT_ON_NEW_CHAT` with all click/paste/Send fields false; the worker incorrectly required every Firefox window to display New Chat. PCE11.084 confirmed. PCE11.085 window-by-window analysis, if already transmitted, is READ-ONLY; it does not authorize targeting any other window. User has explicitly vetoed separate-window selection. Do not replay legacy attempts. Latest user directive supersedes historical pinned separate-window handoff.

## ACTIVE ORDER (no speculative detours)
- [x] GitHub verified legacy source references: historic full-tree One-Click GO r28 `d5b9db7ad785b5cae8dc3b64219303b9fcfa634a`; PCE8 v16 source `694d47ab89596d5c3801f749caa352b951a2be52`. Both original Git objects exist in Termux history; Termux branch tips have no `windows-relay/` folder.
- [x] A–Z Relay and consumer benchmark criteria committed; no overnight pass is yet claimed.
- [x] Corrected PCE011 harness scheduled reads/audit-reviews and created dated PCE011 queue on canonical Windows GitHub branch.
- [x] PCE11.004 source acceptance: backup integrity and staged SHA checks, **19/19 jobs PASS, 697 tests counted**, report `Client/Relay/bin/SOURCE_GATES_2026-10-08T091457Z/source-gates.json`; live activation and overnight qualification remain untested.
- [x] PCE11.001: exact PCE011 SHA pulled by fast-forward on clean canonical checkout; 5-control governance receipt returned. Preserve Codex-mapped paths and do not overwrite dirty future changes.
- [x] PCE11.001: 2532-file current Relay ZIP and SHA256 manifest saved non-destructively at `Client/Relay/bin/BROKEN_2026-10-08T090413Z.zip`; running listener left untouched.
- [x] PCE11.001: immutable historical v16 `694d47ab` and r28 `d5b9db7` staged in separate `Client/Relay/builds/` checkout trees; exact source HEAD verified. Live deployment NOT performed.
- [ ] Test both independently using pinned benchmark catalog: offline syntax/unit tests -> read-only identity -> STOP+rollback acceptance -> exactly-once canary -> 12h night -> 24h release gate.
- [ ] Recover exact PCE7 legacy rollback as independent standalone Relay challenger, not guessed from PCE7.447 branch.
- [ ] Qualify One-Click GO r28 Chrome and Edge consumer flows. Temporary Firefox development add-on is NOT signed persistent consumer Firefox support.
- [ ] Reintroduce newer HUD UI cautiously with **RETRY**; make STOP fully quiescent. Do not remove emergency KILL unless safety behavior of STOP is proven equivalent and recoverability retained.
- [ ] After five distinct repeated failures, optional Codex CLI scoped repair, preferred 5.6 or 6 Luna **if installed**, with GitHub-first commit and rollback.
- [ ] At PCE011.050 compile finding and send via connected mail only when an actual sender action is available; report send receipt, don't fake delivery.
- [ ] At PCE011.100 hand off/rotate to verified `💻PC Engineering 12🔧`, not OP101.

## Completed engineering history and current blockers
Complete pre-compaction task history is preserved by the original Git blob at commit c04d98e5f8b6709a0ec9e5262d6533b9b008ff6c and will be copied without changes to docs/archives/TASKS_2026-10-09T1951Z_PCE13_PRE040_FULL_SNAPSHOT.txt. Prior dated audits and the existing pre020 snapshot remain authoritative for historical operations.

- [ ] PCE11.034 private v16 canary remains unaccepted; require native host/Job verification, private port, backup, STOP and rollback gates before launch. No production cutover.
- [ ] User connection interruption incident remains open. Never blindly replay uncertain results, change a different ChatGPT tab, or overwrite an unsent draft.
- [ ] PCE13.039 full Windows suite 568/569; sole failure was this task file exceeding the 10,240-byte documentation limit. Repair documentation, rerun regression, and preserve active source and runtime separation.

## Full original queue preserved
[Complete 2026-10-08T1011Z snapshot](TASKS_2026-10-08T1011Z_PCE11_PRE020_FULL_SNAPSHOT.md).

## CHECKPOINTS
- Five-operation audit every .005/.010/... covering preceding five attempted IDs, including 0 baseline slot, failures and missing results. **Historical audit PCE10.015-.019 already recorded:** `docs/audits/AUDIT_2026-10-08T0316Z_PCE10_OPERATIONS_015_019.md`.
- Twenty-operation review every .020/.040/.060/.080/.100.
- Soft reporting/email checkpoint .050; mandatory safe rotation .100.
- Human STOP, uncertain side effects, ambiguous tab identity, failed rollback or dirty checkout always prohibit unsafe unattended mutation; reporting and read-only diagnosis may continue.

## Historical task archives
Full prior task details in [pre020 snapshot](TASKS_2026-10-08T1011Z_PCE11_PRE020_FULL_SNAPSHOT.md). Prior series evidence preserved in GitHub audits and incidents.
