# Incident — PCE10.037 exact Firefox conversation resolver matched zero tabs

**Status: OPEN / LIVE ACTIVATION BLOCKED.** PCE10.037 returned `OK` as a diagnostic operation but the nested Firefox resolver subprocess exited 1 with `RuntimeError: FIREFOX_CONVERSATION_MATCH_COUNT_0` from `windows-relay/firefox_tab_adapter.ps1:169`. The operation printed `EXACT_TARGET=BLOCKED`. This is not proof that Firefox was closed, the target chat missing, or the extension absent; it is a failure of the available resolver to prove a unique exact browser target.

## Evidence and stable facts

- Canonical source branch `pce10/reconcile-control-and-rotation`, source HEAD `afa5feb5c858573c5012dc64288b5bf7667a9ac8`. PCE10.035 passed five Node syntax checks, 5 targeted replay tests, 443 Windows tests, 116 consumer tests, content mirror equality and diff check. Source acceptance **GREEN**, without live promotion.
- PCE10.036 reported `BROKEN_BACKUP_VERIFIED=True` with all 658 files and zero hash failures; PCE10.020 three-file rollback also verified with zero hash failures. The program source/live comparison found 19 differing files and zero missing.
- PCE10.037 identified current three live browser scripts as different SHA256 from repository source; extension workers also differ. Backend `armed=True`, no four blocking operator flags, known broken snapshot preserved. Exact resolver returned zero and activation must stay blocked.
- Existing source `firefox_tab_adapter.ps1` `resolve-conversation-tab` enumerates UIAutomation `TabItem` descendants; filters out `IsOffscreen`/disabled tabs, demands a parent Tab with `AutomationId='tabbrowser-tabs'`, programmatically *selects each qualifying tab* to inspect the current `urlbar-input`, then restores original selection; on !=1 matching conversation, fails closed. Zero matches could be incorrect target URL, UIA's tab filtering, visibility/selection/accessibility limits, or browser state. None is yet proved.
- Historical evidence `docs/windows-relay-established-facts.md` had earlier false-negative Firefox UIA conversation URL discovery; do not repeat speculative full-profile archaeology or assume an old conversation ID matches the current chat.

## Next investigation and safety contract

1. Use a **unique read-only PCE10.038** to inspect bounded recent browser events (`content_script_started`, `relay_packet_discovered`, `content_port_connected`) for current `href`, tab and conversation identity and inspect visible Firefox process/windows and the **currently selected** tab without programmatically switching tabs.
2. Correlate events with current ChatGPT conversation and exact Firefox PID. Refuse a guessed, stale, ambiguous or mismatched identity; do not disclose unrelated browser tab URLs in logs.
3. If resolver has an implementation defect, **fix and commit in GitHub first**, update targeted tests, have relay `git pull --ff-only` exact SHA, run both full suites and syntax. Never patch live source directly.
4. Once positively matched, verify STOP/exact-once/backup, stage exact browser files with a new SHA-256 snapshot, activate controlled Firefox content and verify a fresh `content_script_started` runtime identity and then delivery + 45-second recovery canary.
5. Existing `BROKEN-PCE10.026-2026-10-08T055125Z` backup must stay untouched; no automatic replay of PCE10.018/.021/.025.

**Live activation: BLOCKED.** Target diagnosis, not another blind resolver re-run, is next.
