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
- Historical screenshots, including PCE10.025, recorded specific ChatGPT conversation URLs, but **do not hard-code those old IDs as the current engineering chat**. The next agent must derive and positively verify the *present* conversation identity; chat rotation can change the URL.
- These profile/extension facts were **proven historically**, not freshly read at PCE10.037. Do **not** pretend the old addon ID, tab title, internal UUID, process PID, or URL is necessarily today's active instance. The current Firefox PID and exact tab URL are explicitly **UNVERIFIED**.

**The current diagnosis is NOT "we don't know how to use Firefox."** It is: approved source built green; existing adapter `resolve-conversation-tab` returned zero on a named live-identity gate. We know exactly where the filter and comparison are and how to test it; do not start from browser installation, deep profile database inspection, stale title matching, or another random window enumeration.

## 4. Next safe engineering operation: PCE10.038

**Goal:** discriminating, genuinely observational Firefox identity inventory that explains PCE10.037's zero-match before any live mutation. It must remain a fresh unique `PCE10.038`, not a repeat of a potentially executed earlier packet.

1. Read all five governance controls; run `engineering_preflight(repo,38,10)`. The .030–.034 audit exists at `docs/audits/AUDIT_2026-10-08T0624Z_PCE10_OPERATIONS_030_034.md`, synchronized and accepted by `GOV-AUDIT-030-034-SYNC`. Inspect current branch/head/clean checkout. Do not preemptively modify the runtime.
2. Collect **bounded** newest backend browser events and state (e.g., `content_script_started`, `content_port_connected`, `relay_packet_discovered`, tab/conversation metadata and actual loaded runtime version if emitted). Correlate to the **current** chat owner, not an earlier conversation's UUID. Avoid dumping full logs or unrelated tab URLs.
3. Query Firefox process/tree, visible windows, **currently selected** accessible tab and its URL readback without switching tabs. If profile/process binding is required, use the established managed adapter and prior evidence; don't spawn broad new desktop scrapers. Check whether the .037 caller supplied a stale/wrong `--conversation-url` and whether the specific `IsOffscreen`/parent filter hid a valid tab.
4. Distinguish and report **one** root-cause class with evidence: wrong URL, visibility/filter defect, tab accessibility absent, stale process/profile binding, or current target actually missing. If evidence remains ambiguous, say `IDENTITY_UNVERIFIED` and **stop**, rather than loading the addon into an uncertain browser.
5. When the resolver code is defective, fix it on GitHub first (not in Windows live), add a focused regression, verify remote SHA, have Windows `git pull --ff-only`, and rerun relevant/full test gates. Prefer read-only identity collection and exact tab-ID verification to repeatedly selecting every tab just to inspect URL. No hidden tab focus/selection side effects advertised as purely read-only.
6. If the target can be proven with existing source and no code change, proceed **in a subsequent operation**, after explicit operator/backup checks, to a **controlled, narrowly scoped, reversible activation**. Never treat "identity found" as automatic permission to stage and reload everything.

**Forbidden approaches right now:** rerun the same `resolve-conversation-tab` with the same guessed URL; an unscoped `list-tabs`; rebuild every PID/profiles fact; paste giant UIA scripts into the relay; terminate all Firefox processes; automatically refresh or reload the addon before exact target proof; replay PCE10.018/.021/.025; conclude `no Firefox` from `MATCH_COUNT_0`.

## 5. Safe deployment once and ONLY once identity is proven

1. Verify current repository HEAD is GitHub-committed, Windows checkout fast-forwarded to exact SHA, full tests still green for **that source**, and live staging paths explicitly enumerated. **Do not use an older stale live copy of `sync-live.py` for an unreviewed broad sync.**
2. Prove operator STOP/ARM/stop-generation state at the time of activation. PCE10.036/.037 recorded `armed=True` and `stop_generation=7`, but these can change. A prior ARMED screenshot/result is not fresh authorization for risky mutation.
3. Preserve every existing backup. Make a new timestamped, exact-byte, SHA-256 verified backup of **each file to be changed** plus a machine-actionable restore manifest. Do not overwrite the PCE10.026 forensic snapshot or the PCE10.020 original-content backup.
4. Stage only vetted files through a helper with rollback, prove exact source/live hashes and path scope, activate/reload the **identified** addon and specific ChatGPT tab without affecting unrelated profiles/tabs, and prove a fresh `content_script_started` after reload with version identity. Disk SHA matching alone is insufficient.
5. One harmless *fresh unique ID* end-to-end canary must traverse `DISCOVERED -> authenticated backend reservation/action -> saved result -> visible correctly parsed user result`. Separately verify the 5s settling lease and independent <=45s STOP-aware scanner recovery, including no duplicate action, no accidental clearing on false replay suppression, and **visible** continuation.
6. On failure, hold and restore from an independently verified rollback. Do not promote a candidate unless source acceptance, identity, STOP, runtime revision, both canaries and performance/latency are evidenced.
7. Only then close the composite discovery incident, reduce excess `GET /status` traffic if still measured, and consider `main` merge and product lifecycle gates.

## 6. Backups: what they are, and what they are NOT

**PCE10.026 forensic snapshot:** `%LOCALAPPDATA%\GPTWindowsRelay\backups\BROKEN-PCE10.026-2026-10-08T055125Z`. All **658 files** were re-hashed successfully in PCE10.036. It includes program files, source bundle, and best-effort state/config captures. Manifest SHA256 `5d67ffb068e12cabfab7c2c2b58ebd4a3c9236aaf856fb37da1137d874650563`. **Label: BROKEN — DO NOT PROMOTE.** It is a recoverable forensic snapshot, not an established working production release; it excludes historical backup/log/cache directories.

**PCE10.020 pre-stage originals:** `%LOCALAPPDATA%\GPTWindowsRelay\backups\PCE10.020-20261008T031613Z\manifest.json`. Three original content files; PCE10.036 confirmed three and 0 hash failures. This is a **partial rollback**, not a full prior working installation.

**Codex-reported stage backup:** `Client\Relay\backups\pce10-replay-suppression-repair-20261007-224256`. Existence/restore coverage was separately reported but **not independently certified** in the PCE10.036 proof. Do not silently treat it as a complete rollback.

**Critical:** No confirmed **known-good complete previous live build** exists in the provided acceptance results. "We have a backup" is not the same as "we have a working known-good version." Treat any rollback as a decision based on exact manifest and current runtime state.

## 7. Failure patterns and expensive repetitions — DO NOT REPEAT

**A. Endless Firefox identity archaeology.** The earlier PCE9 audit found **at least 25** operation slots revisiting Firefox restart/continuity/no-reload facts. Facts remain valid until a state-changing event contradicts them. Re-probe only when (i) browser state actually changed, (ii) contradictory evidence appeared, or (iii) a named acceptance requires it. Right now .037 supplies a **specific contradictory resolver result** permitting a *bounded, targeted identity diagnostic*—not a restart of all past investigations.

**B. Treating "ONLINE/ARMED/heartbeat" as command execution.** Server can respond HTTP 200 while `DISCOVERED` is stuck for thousands of seconds; prior watchdog stopped scanning when port 8766 listened. Require packet-specific state and fresh actual browser runtime.

**C. False result acknowledgement from an ID mention.** Original code accepted `elementText(...).includes(packetId)` on generic user-message wrappers. Session `attempted` history preserved false suppression. Older workers cleared watchdog on `relay_result_replay_suppressed` as if success. Source changes address these, but live proof remains absent. No speculative replay.

**D. Rewriting tests to pass without examining safety semantics.** We found stale selectors, old poll intervals, forbidden alarm assertions, and literal-adjacency tests; modified them in GitHub only where implementation evidence justified it. Full green tests at PCE10.035 matter, but aren't a deployed-system result.

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
