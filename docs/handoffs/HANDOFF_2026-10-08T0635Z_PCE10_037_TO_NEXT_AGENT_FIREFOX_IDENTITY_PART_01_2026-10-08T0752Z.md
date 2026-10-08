# Archived source fragment 1/3 — 2026-10-08T0752Z

# PCE10 next-agent engineering handoff — 2026-10-08T06:35Z

**DIRECTOR HANDOFF. READ BEFORE TOUCHING SOURCE, WINDOWS, FIREFOX OR THE RELAY.**

**Mission status:** GitHub source acceptance **GREEN**; the actual live Firefox/relay deployment **NOT ACCEPTED**; the current blocker is **exact Firefox conversation identity** (PCE10.037 returned `FIREFOX_CONVERSATION_MATCH_COUNT_0`). Prior broken build is verified backed up and quarantined. No one has yet proved that the approved scanner is running inside Firefox. **NEXT UNIQUE OPERATION: PCE10.038**, not a repeat of .037.

**Primary rule: do not burn another 25 operations repeatedly proving things the repository already knows.** Read the established proof, identify the exact new unknown, perform one bounded discriminating diagnostic, and make the smallest justified change. When a test/assumption fails, do not repeatedly rerun the same command expecting a different answer. Every agent must deliver measurable forward progress, not a new history of the same problem.

## 1. Entire mission

Make GPT Windows Relay a *real* reliable autonomous Windows↔ChatGPT bridge: source-controlled, exactly-once for Windows side effects, once-only result injection, safe operator STOP/OFF/KILL, observable HUD, deterministic state-based stalled-scanner recovery, rollback after unsafe deployment, and automatic continuation without routine user rescue. The eventual product survives browser and Windows restart with a signed persistent Firefox extension and a supervised backend; no job/application or other automation may outrank operator STOP.

The Director does **not** want to reload Firefox manually, click RETRY, re-paste stranded results, explain prior discoveries repeatedly, or routinely send `continue` after each operation. An unexpected user rescue is an **incident**.

Canonical GitHub repo: **`monag144/GPT-Windows-Relay`**, working branch **`pce10/reconcile-control-and-rotation`**. Absolutely **NOT** `GPT-Termux-Relay`: migration to Windows repo already completed.

Windows checkout: `C:\Users\Craig Morgan\Downloads\Dev\GPT\GPT-Windows-Relay`.
Live runtime tree: `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay`.
Durable runtime: `%LOCALAPPDATA%\GPTWindowsRelay\state.json`, `browser-events.jsonl`, `results\`, `ops\`; pairing/config: `%APPDATA%\GPTWindowsRelay\bridge.json`. **Do not print or commit any pairing secrets.**

## 2. Exact current checkpoint — what is proven, and what is not

| Evidence | Actual result | Interpretation |
| --- | --- | --- |
| **PCE10.035**, source HEAD `afa5feb5c858573c5012dc64288b5bf7667a9ac8` | Three scanner mirrors identical; **five** JS `node --check` green; **five** replay regressions green; **443/443 Windows** tests green; **116/116 consumer** tests green; `git diff --check` green. Saved report: `%LOCALAPPDATA%\GPTWindowsRelay\ops\PCE10.035-source-acceptance.json`. | **SOURCE ACCEPTANCE GREEN**, not live acceptance. Stop re-running these suites as a substitute for identifying Firefox. Re-run after source changes / promotion gate, not to rediscover history. |
| **PCE10.036** | GitHub HEAD clean; **658 backup files SHA-256 verified, 0 mismatches**; Git source bundle present; historical PCE10.020 three-file rollback also verified, 0 mismatches. Found **19 source/live differences, 19 matches, 0 missing** in compared set. | Rollback evidence exists but some backups capture **BROKEN** runtime, not a known-good release. The live tree is *different from* the tested source. |
| **PCE10.037**, 2026-10-08T06:30Z | Existing backend recorded ARMED, zero blocking flags; source HEAD `afa5feb5…`; live all three content scripts differ from approved source, and both worker scripts differ. Managed `resolve-conversation-tab` subprocess exit **1** with `FIREFOX_CONVERSATION_MATCH_COUNT_0` at `firefox_tab_adapter.ps1:169`; outer relay action `status=OK` because it intentionally collected diagnostic result. | **EXACT_TARGET=BLOCKED**, no Firefox activation, no live browser canary. An outer `OK` does **not** mean the nested resolver passed. |
| GitHub HEAD after .037 | `76d72e3441fd51bf0db99a9073cac6fc61d2cc61` as checked for this handoff, one commit after `afa5feb5…`. Diff is **only** the PCE10.037 incident document. This handoff/index commits will advance HEAD again. | Source passing tests is still the same as `afa5feb5…`; verify GitHub's *current* exact HEAD before next pull. |
| PCE10.018/.021/.025 | `DISCOVERED` stalls of ~3774 s/~784 s/~326 s; .025 produced `relay_packet_discovered` then same-second `relay_result_replay_suppressed` while backend showed no durable action at Codex inspection. | These are *open incidents*. **NEVER blind-replay them or invent completion.** |
| Current result-delivery path | PCE10.035–.037 relay command results returned through ChatGPT; PCE10.037 delivery succeeded even though browser target resolver inside its command failed. | Backend/transport success can coexist with a broken scanner or target resolver. |

PCE10.037 source/live content SHA-256 prefixes printed: all three source content scripts `99678c0d8a0884d1…` versus live `34500934b214423a…`; temporary worker source `24bfdaac540f21d0…` versus live `dd43c9f50ab3a173…`; persistent worker source `916a8859de442603…` versus live `02b9ca12d964ced9…`. Short prefixes are **comparisons**, not a complete loaded-runtime identity or proof of deployed code.

### Source repairs that have ALREADY been implemented and passed unit tests

Codex commits `7c38e90`, `d5df0b3`, `b0a01ee` were reconciled into GitHub in PCE10.026. Subsequent GitHub-first fixes removed the ID-only result-acknowledgment fallback in `userTurnContainsPacketId()`, removed deferred queue/drain shortcuts that bypass backend checks, made attempted-history rearming require authenticated `NO_EXECUTION`, made unknown packet status fail closed, prevented false UI replay suppression from clearing the worker's recovery watchdog, and synchronized three `content.js` mirrors. Harness v4 codifies GitHub-first source work. Tests were updated for real changed semantics instead of preserving unsafe legacy selectors/250-ms polling requirements. The running Firefox addon **may still have the old behavior** because no post-fix loaded-content-script proof exists. Do not declare the core incident resolved on the strength of passing unit tests.

## 3. Firefox identity: concrete established facts, and the exact current gap

**READ `docs/windows-relay-established-facts.md` BEFORE running Firefox probes.** It already records *real* October 2–3 UI Automation/about:debugging verification:

- Previously observed Firefox profile: `3awtt83g.default-release`.
- Temporary relay extension ID that was **installed=True during that observation**: `55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon`. Three other recorded older temporary IDs had `installed=False`; do **not** equate profile history with multiple live addons.
- Previously observed extension internal UUID: `2583b6b1-f194-48c9-a8ab-cc1add6602ec`.
- Verified temporary addon count at that time: **one**; background worker **Running**; actual addon source path `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay\extension\`.
- Verified UI: `about:debugging#/runtime/this-firefox`. After a **full** Firefox exit, a temporary addon is removed. Permanent zero-touch Firefox restart requires a signed persistent XPI/policy installation; this remains an **external product gate**.
- The canonical managed adapter is `windows-relay/firefox_adapter.py` calling `firefox_tab_adapter.ps1`. Do **not** create yet another generic UIAutomation top-level `MozillaWindowClass` scanner. That **already failed** in PCE10.002. Do not call unscoped `list-tabs` across multiple windows; that failed in PCE10.011.
- The `resolve-conversation-tab` method requires a precise `https://chatgpt.com/c/<conversation-id>` URL and exactly one match. PowerShell currently enumerates UIA `TabItem` descendants, rejects `IsOffscreen`/disabled tabs, requires immediate Tab parent `AutomationId=tabbrowser-tabs`, **selects** candidate tabs to read `urlbar-input`, and restores prior selection. It can return zero for accessibility/selection/visibility limitations, an obsolete URL, or a real missing target. The current cause has **NOT** been identified.
- Prior URL/UIA false negatives PCE10.002, .012, .014 occurred even when Firefox was visibly at the right ChatGPT conversation. A zero count **does not prove Firefox closed, extension missing, or chat absent**.
