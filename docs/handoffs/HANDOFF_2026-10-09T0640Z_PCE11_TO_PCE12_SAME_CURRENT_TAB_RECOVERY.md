# HANDOFF — PC Engineering 11 → PC Engineering 12
**UTC:** 2026-10-09, after PCE11.088. **Status:** PCE12 browser handoff NOT delivered. **Priority:** Resume governance and restore robust current-tab recovery without repeating failed operations.

## Your identity and first command
You are **💻 PC Engineering 12🔧**. Your relay session is **`pce12.1`**, first engineering ordinal **`PCE12.000`**. Start a new PCE12 operation series; do not resume PCE11 ordinal .089 as your own. Read this handoff, the canonical controls and current Git history before acting. The human has brought this handoff here because the browser-assisted rotation **failed**; that is not proof of a successful live cutover.

## Non-negotiable user intent — SAME CURRENT CHATGPT TAB
The user explicitly corrected us: clicking **New chat** means ChatGPT navigates to a new conversation **inside the tab the user is presently using**. It does not mean a new Firefox window, another tab, or the other preexisting Firefox window. Never identify the destination by an assumed 11-tab window, tab-count heuristic, or foreground-only heuristic. Positively identify the actual originating ChatGPT conversation and selected tab from current relay message/result provenance before any live action. Keep the same tab and HWND when invoking its unique semantic New chat control. Preserve any unsent draft. Once on a verified empty new-chat composer in *that tab*, paste once and Send once under an exclusive durable no-retry receipt. Confirm a user-role message in the new `/c/...` conversation; launching a worker or opening a blank composer is **not** delivery. STOP, operator pause, uncertain side effects and ambiguous identity override autonomy.

The active canonical override is `docs/architecture/CONTRACT_2026-10-09T0636Z_AGENT011_CURRENT_TAB_SEMANTIC_ROTATION.md` and `docs/relay-sandwich-procedure.md`. Historical `docs/handoffs/HANDOFF_2026-10-09T0147Z_AGENT011_PCE11_TO_PCE12_ATOMIC_SEPARATE_WINDOW.md` is **obsolete as operational instructions**; read it only for historical context. Do not rerun separate-window workers or the failed .074/.076/.083 operations. The user's request to create this handoff replaces any assumption that the automation already switched conversations.

## Last observed results — distinguish source, tests, and browser
- **PCE11.076:** one semantic New Chat occurred during earlier rotation attempts; its paste/Send were false. Do not infer that the current browser tab remains unchanged since that old receipt.
- **PCE11.079:** 8,642-character combined handoff clipboard proof passed; clipboard-only, no Send.
- **PCE11.080:** governance checkpoint missing until fast-forward audit/review sync. Follow-on launcher failed `NameError: worker_file`; no worker launch.
- **PCE11.081:** wrong hardcoded SHA for established-facts doc, stopped before worker.
- **PCE11.082:** missing presumed payload file, stopped before worker.
- **PCE11.083:** a detached worker *did* launch (PID 11900) but stopped at `FIREFOX_NOT_ON_NEW_CHAT`; unique receipt `PCE11_083_ONCE.json` says `HALT_UNCERTAIN_NO_RETRY`, `composer_click_attempted=false`, `paste_attempted=false`, `send_invoked=false`, `user_turn_verified=false`. The worker incorrectly required every Firefox window to be at ChatGPT home. Do not replay.
- **PCE11.084:** read-only receipt verification confirmed **no PCE12 user message**.
- **PCE11.085:** governance sync for .080–.084 audit and incident passed. A subsequent read-only two-window diagnostic packet was superseded by the user's explicit correction; no result for it was supplied, so do not treat it as executed.
- **PCE11.086:** new current-tab source files synced to Windows; 1/8 regression tests failed due test wording, **no worker launched**.
- **PCE11.087:** after fixing assertion, current-tab contract **8/8 PASS**; consumer runner lacked `PYTHONPATH`, yielding `ModuleNotFoundError: browser_manager`; **no worker launched**.
- **PCE11.088 (last Windows result):** current-tab **8/8 PASS**, consumer **123/123 PASS**; Windows full suite FAILED for two reasons: (1) obsolete two-window test demanded exactly 17 `$destination` occurrences while script has 18; (2) `docs/relay-sandwich-procedure.md` grew past the 10,240-byte documentation limit when the current-tab contract was appended. Test gate stopped before any new worker launch, New Chat, paste, or Send. No full Windows-suite PASS or live PCE12 delivered-user-turn evidence.

## Newer GitHub changes — NOT YET TESTED ON WINDOWS
The canonical branch advanced independently after the PCE11.088 result:
- Previous Windows HEAD observed: `03c7779268aed2984b8b5f3cea6ff3dbff0f66df`.
- Next GitHub ancestor: `94c22fe73802066ac8bc6b090d0cddb353b26ac5`, four new commits:
  1. New dated contract `docs/architecture/CONTRACT_2026-10-09T0636Z_AGENT011_CURRENT_TAB_SEMANTIC_ROTATION.md`.
  2. Shortened compatibility `docs/relay-sandwich-procedure.md` to below 10 KiB, with pointer to dated contract.
  3. Aligned current-tab documentation regression test with dated contract.
  4. Replaced deprecated separate-window test's brittle exact `$destination` variable occurrence count with a lower bound (>=17).
These are **source edits, not evidence of passing tests**. Recheck actual remote HEAD before synchronizing. This newly added handoff creates a later GitHub commit too, so never hardcode `94c22...` as the latest HEAD.

## Canonical repo and source
- Repository: **`monag144/GPT-Windows-Relay`**.
- Branch at handoff: **`pce11/one-click-go-recovery-and-doc-hygiene`**.
- Windows root: `%USERPROFILE%\Downloads\Dev\GPT\GPT-Windows-Relay`.
- Current-tab worker (not yet accepted live): `windows-relay/agent011_current_tab_new_chat.ps1`.
- Current-tab tests: `windows-relay/tests/test_agent011_current_tab_rotation_contract.py`.
- Actual user-turn proof helper: `windows-relay/agent011_user_turn_proof.ps1`.
- PCE11.080–.084 audit: `docs/audits/AUDIT_2026-10-09T0618Z_AGENT011_PCE11_OPERATIONS_080_084.md`.
- Current incident: `docs/incidents/INCIDENT_2026-10-09T0619Z_AGENT011_PCE11_080_084_HANDOFF_LAUNCHER_AND_WINDOW_SCOPE.md`.

## Mandatory governance before PCE12.000
Read the full canonical source-of-truth index, `consumer/control_harness.py`, `windows-relay/TASKS.md`, `docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md`, `docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md`, `docs/windows-relay-mission-and-roadmap.md`, `docs/windows-relay-established-facts.md`, `docs/relay-sandwich-procedure.md`, the current-tab contract, latest audits/reviews/handoffs/incidents. Record actual SHA256s (some changed). Verify correct remote, branch and clean working tree. Run `engineering_preflight(ROOT,0,series=12)`; accept its real result. Preserve the 000–100 series budget, five-operation audit cadence, twenty-operation reviews, no retries after uncertain browser mutation, STOP/ARMED/owner checks, exact-command unique receipts and rollback. Keep relay packets in a **single plain fenced [GPT_WINDOWS_ACTION] sandwich** with visible header and footer `Reply to this with the sandwich technique`.

## Safe next steps
1. **PCE12.000 read-only recovery and reconciliation:** fetch current GitHub HEAD; inspect source changes and the three relevant failure/launch receipts; check current Firefox/tab provenance without clicking or changing focus. Confirm whether any PCE11.088 worker was launched (result says no). Verify actual relay state and STOP epoch; do not assume stale PID 5440 or pending-missions count 2 are still valid.
2. **Source acceptance:** fast-forward only on clean canonical checkout; ensure `PYTHONPATH` includes `consumer` and `windows-relay` for the right test subprocesses. Rerun **all Windows tests**, consumer tests and current-tab tests. Investigate any remaining failures instead of weakening unrelated checks. Compare results with PCE11.088 (8/8, 123/123, Windows FAIL).
3. **Design/live proof:** ensure the worker can actually observe the *originating* relay turn in the exact selected tab, survive asynchronous result rendering, and preserve the sender draft. Do read-only UIA diagnosis first, then one newly authorized no-replay live same-tab attempt only if identity and tests are green. A blank/new chat page alone proves nothing. No separate-window fallback.
4. **After rotation acceptance:** resume the broader mission: reliable unattended GPT↔Windows relay, exact current-tab error recovery, One-Click GO r28 Chrome/Edge and Firefox consumer paths, STOP safety and rolling audits. The 12-hour endurance canary and 24-hour qualification have **NOT** passed; do not claim otherwise. Preserve the 2,532-file broken-state backup and staged r28/v16 rollback assets.

## Success criteria and accountability
Success is **verified semantic current-tab New Chat → exact PCE12 handoff composer → exactly one Send → actual unique user-message proof in new conversation**, with no other Firefox tab/window touched, all safety gates accepted and no existing unsent text lost. Until then report **handoff pending/failed**, not success. Agent 12 owns the recovery from this handoff. Do not ask the user to manually paste/send relay operations unless they explicitly choose to; they have asked for autonomous relay operation, but must retain STOP control.
