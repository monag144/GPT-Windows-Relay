# Agent switching retirement — 2026-10-09

## Decision and scope
**Director decision (Pacific local date 2026-10-09): permanently retire the experimental agent/conversation switching architectures.** Do not resume their roadmap, unattended rotation, browser-resident agent handoffs, operation-count triggers, window/tab switching experiments, or a replacement switching project. This is deliberate scope reduction, not an assertion that every historical failure has one root cause.

The **only approved agent-to-agent handoff transport** is the existing, user-requested one-shot Windows launcher at `Client/Relay/test/Run-Copy-Contents.cmd` with `Copy-Contents-To-ChatGPT.ps1` and staged `Copy Contents.txt`. The engineer, not the launcher, derives its successor by adding 1 to the current verified PCE series: PCE16 -> PCE17 -> PCE18, etc. Never hardcode PCE9 or another successor into scripts or policy. The text is staged and verified; launcher runs once on explicit request; success is a visible submitted user turn in the *new* chat, not a new tab, button click, child PID, URL, or keyboard event alone. Do not replay uncertain sends.

## Retired approaches and observed limits
| Approach | Former code/evidence | Reason for retirement |
| --- | --- | --- |
| 100-operation autonomous rotation | `extension/service_worker.js`, `CHAT_ROTATION_EVERY`, `noteDeliveredOperation` | Unrequested/late navigation and complex ownership timing; no accepted end-to-end agent handoff |
| Extension-managed handoff, rename and resume | `extension/content.js` / both content mirrors, `resumeEngineeringRotation` | Hardcoded PCE9, DOM/composer dependency and unverified paste/send; fragile across ChatGPT UI changes |
| One-off semantic New Chat / mouse click | `tools/CLICK-NEW-CHAT.bat`, PCE12.006 evidence | Can navigate but cannot alone prove paste/Enter delivery |
| Out-of-band PowerShell/UI Automation agent switching | `firefox_tab_adapter.ps1`, `firefox_adapter.py`, consumer recovery controllers | Tab/composer focus and accessibility uncertainties; old methods often stopped before submission |
| Disposable headless browser fixture/rotation tests | PCE14 / PCE15 audits | Static markers or headless readiness cannot substitute for a real confirmed user turn |
| Experimental replacement / watcher-driven switching | historic roadmap and policy | No independently accepted full transfer; repeated large maintenance burden |

Supporting incidents: `docs/HANDOFF_2026-10-06T0246Z_PC_ENGINEERING_6_TO_7_FAILED_ROTATION.md`; `docs/INCIDENT_2026-10-06T0309Z_PCE7_SESSION_ESCAPE_AND_UNNAMED_ROTATION.md`; `docs/INCIDENT_2026-10-07T083038Z_OP100_SEMANTIC_NEW_CHAT_FALLBACK_NOT_PROVEN.md`; `docs/incidents/INCIDENT_2026-10-09T0756Z_PCE12_007_008_NEW_CHAT_FALSE_NEGATIVES.md`; `docs/handoffs/HANDOFF_2026-10-10T0331Z_ONE_SHOT_WINDOWS_SCRIPT_AGENT_TRANSFER.md`.

## Archived source and retained components
Historical executable rotation source remains available **in Git history at commit `77bee0a6b24e9bc7360f4a09505da4d6d1e8047c`**:
- `windows-relay/extension/service_worker.js` (old rotation counter, PCE9 target and handoff)
- `windows-relay/extension/content.js` and mirrors (old navigate/insert/send/rename/resume)
- `consumer/control_harness.py` (old automatic-rotation budget and clipboard/UIA capture guidance)
- Original positive-only tests copied verbatim into this bin as `legacy_rotation_trigger_test_2026-10-09.py.txt` and `legacy_rotation_handler_test_2026-10-09.py.txt`.
- Obsolete runnable `tools/CLICK-NEW-CHAT.bat` removed from `tools/` and preserved verbatim in this bin as `legacy_CLICK-NEW-CHAT_2026-10-09.bat.txt`. **This is not the working** `Client/Relay/test/Run-Copy-Contents.cmd`; do not confuse the two.
- Ordinary `relay_handoff_scroll` and `HANDOFF_SESSION_KEY` names in the content script refer to *scrolling after result delivery*, **not conversation/agent switching**; those remain essential and must not be removed for their names alone.

**Temporarily suspended for agent switching only:** existing UI Automation, clipboard fallback, tab/window discovery, out-of-band prompt sending, screenshot/navigation recovery, and browser supervisory machinery. Do not use these to open a successor chat, rewrite a handoff, or transfer agent ownership. Their implementations are **not deleted or globally disabled**, because they are shared by unrelated normal Windows Relay command delivery, security/STOP, recovery, or user-requested non-handoff workflows. Reusing them for agent-switching is prohibited unless the Director issues a new explicit decision; this retirement is intended to be permanent.

**Keep in normal service:** packet detection, bridge authentication, normal same-chat reply delivery, STOP/ARM, exact-once protections (known defective; see incidents), incident capture, necessary same-chat recovery, and GitHub-first audits. Removal of agent switching must not disable these controls.

## Readiness and deployment boundaries
At last PCE15 grade: **F / RELEASE BLOCKED, 11/28**, G16 actually loaded Firefox extension unknown, G26 0/60 independent send traces, G27 0/2 endurance periods. PCE15.043 and .047 isolated tests show atomic claim and post-eviction replay defects; PCE15.049 was only an in-memory design sketch. These remain open.

The `PCE15.050-read-only-saved-result-overwrite-order-audit` packet later produced `ACTION_FAILED: relay_owner_same_session_different_conversation` in the new chat; it is consumed, not retried. That protective guard does **not** verify the precise loaded Firefox extension or establish a backend execution receipt.

**GitHub source change is not live Client deployment.** Before claiming retirement operative on a machine, verify installed Client binaries, selected Firefox profile/loaded add-on, and process code, then use a separately authorized rollback-backed deployment and tests. Do not silently restart Firefox or relay during archival work.

## Remaining engineering mission
Reliable ChatGPT <-> Windows commands and results without duplicate side effects; prove exact-once durable reservation; attest real loaded extension/code; reconcile build/release provenance; perform independent real user-role send tests, 12h/24h endurance, restart/recovery and Windows/browser support; preserve STOP/ARM and useful consumer HUD/workflows. See `docs/roadmap/WINDOWS_RELAY_TASK_BACKLOG_2026-10-09.md`.

*Archival means no future switching feature development by default. Git history remains the rollback and evidence trail; this folder is for intentionally retired feature records, not live instructions.*
