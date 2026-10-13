# PC Engineer 17 → PC Engineer 18 — 2026-10-12

**Handoff date:** October 12, 2026, Pacific (some repository commits and relay receipts have October 13 UTC timestamps).

**Mission:** Keep the single GPT Windows Relay build working end to end, make the entire tracked project test-clean, preserve STOP/ownership/exact-once safety, and retire genuinely redundant disk trees without creating any new local backups. Do not allow filenames such as `active`, `current`, `main`, `latest`, or self-declared manifests to override measured Git commits and dated acceptance evidence. Date-stamped documents record their observation windows; they are not timeless installation instructions.

## The only canonical Windows Relay

- GitHub: `monag144/GPT-Windows-Relay`.
- Engineering branch: `wip/windows-relay-rebuilt-resynced-2047-101026` (**not** default `main`).
- User's actual Git checkout: `%USERPROFILE%\Downloads\Dev\GPT-Windows-Relay-Main-Build`.
- Exactly one Windows Relay source: `windows-relay/` within that checkout. Backend `windows_relay.py`, HUD `hud.py`, `relay-control.ps1`, `relay-watchdog-loop.ps1`, `run.ps1` and `START-GPT-WINDOWS-RELAY.bat`. Default localhost endpoint `127.0.0.1:8766`.
- The **one** Windows Relay Firefox add-on: `windows-relay/extension-persistent/manifest.json`, **GPT Windows Relay v0.3.18**, Firefox extension ID `gpt-windows-relay@local`. The user explicitly confirmed this version in Firefox's `about:debugging#/runtime/this-firefox`. Do not load another copy or replace the user's Firefox profile.
- `windows-relay/extension/` is the **separate One-Click Go consumer product**, not a second GPT Windows Relay. Do not delete it just because its service worker differs.
- Pairing token remains private in the operator's `%APPDATA%\GPTWindowsRelay\bridge.json`. Never print, paste into the chat, upload, regenerate unnecessarily, or write it into the consumer extension.

## The known-working build (important evidence boundary)

**Operator-pushed immutable annotated Git tag:** [`windows-relay-v0.3.18-live-verified-20261012`](https://github.com/monag144/GPT-Windows-Relay/tree/windows-relay-v0.3.18-live-verified-20261012). Tag target **`f00307494a83338d29b4c35dd6264e71fa142dbd`**, verified with GitHub tag object. The tag is intentionally separate from ongoing WIP repairs; never move or overwrite it.

Native operator evidence on Windows for that release:
- `test_authenticated_transport.py`: **8/8**.
- `test_operator_owner_http.py`: **4/4**.
- `test_browser_transport_node.py`: **1/1**. Thus **13/13 focused tests passed**.
- Real action `PCE17-CANARY-20261012-002` returned **`[GPT_WINDOWS_RESULT]`**, session `pce17.1`, `status=OK`, `exit_code=0`, duration **1680 ms**, empty stderr, no output truncation, stdout starting `GPT_WINDOWS_RELAY_CANARY_002_OK`, native PowerShell **5.1.19041.2364**, ending in the required sandwich reminder. This proves one successful ChatGPT → persistent Firefox bridge → authenticated Main-Build backend → Windows PowerShell → ChatGPT result cycle. The receipt did **not** separately establish whether the interactive operator YES/NO dialog appeared.
- One positive real canary does **not** certify full-project tests, browser/refresh endurance, exact-once crash recovery or all negative STOP/cross-tab behavior.

Earlier failure `RELAY-CANARY-20261012-1656-001` emitted `RELAY_DIAGNOSTIC ACTION_FAILED detail=RelayError`. Source review established browser `{packet}` vs backend `{packet,issuance,owner}` mismatch. The v0.3.18 bridge now hashes exact packet bytes, supplies issuance and operator-bound conversation/session/tab, asks native Windows YES/NO before binding a previously unauthorized owner, fails closed on extension storage errors, and improves rejection reporting. Never rerun an uncertain action with the old ID.

## Full tracked-project health sweep: real native result

User executed `PCE17-HEALTH-SWEEP-20261012-001` on 2026-10-12 Pacific / 2026-10-13 UTC. It fast-forwarded the Windows checkout **`9cf9d66 → d1330ffc`**. The Windows host reported:
- Git WIP and origin correct; pinned tag points to `f003074...`.
- **322 Git-tracked files**; **87 Python sources parsed**, **9 JavaScript files passed Node syntax**, **5 JSON documents parsed**, **178 Markdown documents with 0 unresolved local links**.
- **23 PowerShell files AST checked; one failed**: obsolete `install-browser-fix.ps1` at line 84, `IncompleteDollarSubexpressionReference` and `TerminatorExpectedAtEndOfString`.
- **434 Windows Relay unit tests: 9 FAIL, 4 ERROR.** **123 consumer tests: all 123 PASS.** The operation rightly returned `COMMAND_FAILED` / exit 1. Do not relabel this as an overall pass.
- **6 dirty/untracked Git status entries** and two still existing ignored/untracked paths: `STUPID BACKUPS DO NOT USE/` and `windows-relay/runtime/`. The reported earlier nested runtime contains ~3,280 files and unique untracked source/state. Existence is measured; deletion has not been demonstrated.
- The original failure output included giant diff/traceback tails and the new `relay_project_test_sweep.py` now prints concise per-test exception types/names.

## Source fixes pushed AFTER the native sweep (not yet re-tested on Windows)

**Last remote HEAD verified at handoff preparation: `445eaf352a067c588104668b53fde57363acd933`.** This is the *newest development source*, **NOT** the tested/tagged release and **NOT** the last confirmed local HEAD (`d1330ffc`).

The commits between `d1330ffc` and `445eaf35` address:
1. Replaced retired `install-browser-fix.ps1` with a **9-line, parseable, fail-closed stub** (no backup/Firefox mutation); updated its test to require no destructive code.
2. Synchronized exactly one outdated `recommended_action` diagnostic line across shared `windows-relay/content.js`, consumer `extension/content.js`, and canonical persistent `extension-persistent/content.js`. Kept One-Click Go **service worker** separate.
3. Updated browser contract tests to allow the persistent worker's `callAction(m.packet,ownerDecision.owner)` while consumer still uses legacy `callAction(m.packet)`, preserving mandatory authenticated issuance/ownership rather than downgrading production.
4. Corrected mocked protocol result assertions to require the **sandwich reminder only**, not retired extra governance text; positively armed test-only outbound sender fixtures before claiming work. Production STOP remains unchanged.
5. Aligned HUD tests with the actual **START / STOP / RESTART / OFF / KILL** controls and delegated launcher; do **not** add a sixth RETRY button solely to please an obsolete test.
6. Updated dated health review with the exact native failures and limitations and amended test-sweep reporting to show bounded exception summaries instead of huge source diffs.

An earlier source pass also fixed `install.ps1` leaking the pairing token to the One-Click Go extension and misleadingly claiming startup ARMED; `build-extension-xpi.ps1` hardcoding v0.3.17; `tools/Launch-Codex-CLI.bat` launching on a mismatched checkout; legacy protocol tests omitting issuance; and old documentation falsely asserting Client/Prototype authority. The tag is still at the earlier proven `f003074`.

**Crucial:** none of the post-`d1330ffc` changes have yet been validated by another native whole-project sweep. Some fixes are inferred from source versus the test failure list; follow actual next run output. Do not restart or reload the known-working live relay merely because source changed on GitHub.

## Absolute operator rules and constraints

- **NO ON-DEVICE BACKUPS.** No local backup folders, ZIPs, date-stamped snapshots, rollback source clones, staging archives masquerading as backups, or duplicate runtime installs. Use GitHub version history or remote archival branches for nonsecret code. The former 27-file `STUPID BACKUPS DO NOT USE` archive is verified remotely at `archive/preconsolidation-source-2026-10-12`, but untracked private leftovers are not inherently Git recoverable.
- **Do not delete private/unique state without specific operator disposition.** This includes pairing secrets, browser profiles, pending action/result journals, local databases, and unpushed code inside `windows-relay/runtime/`. No local backup created in the meantime.
- **No execution-governance gates.** Older PCE8/PCE9 requirements about five-operation GitHub audits, compulsory document reads before every action, 20-turn reviews, mandatory receipts, or obsolete rollback recommendations are historical; they MUST NOT block commands. The distinction: real runtime security **does** remain mandatory (localhost token, operator authorization, conversation/session/tab binding, STOP/OFF/KILL, issuance, durable deduplication).
- **GitHub-first:** assistant engineers and commits on WIP, operator fast-forwards the canonical Windows checkout. Codex may do large disk work when invoked/authorized, but do not allow old Codex scripts to select the Client or Termux tree.
- **No destructive Git cleanup:** operator already had uncommitted `windows-relay/README.txt` modifications; it was deliberately not overwritten. Preserve all remaining dirty files. Do not run `git clean -fdx`, `reset --hard`, force-push, automatically purge Firefox profile, or retag `windows-relay-v0.3.18-live-verified-20261012`.
- **Relay sandwich:** visible operation header; fenced `[GPT_WINDOWS_ACTION]` envelope with unique action ID, correct live session/owner and explicit command; visible follow-up footer. Native results include the exact reminder `Reply to this with the sandwich technique`. Never fabricate `[GPT_WINDOWS_RESULT]` or assume code was deployed because a GitHub commit succeeded.

## PCE18 first mission: rerun before changing anything else

1. Confirm the pinned tag, WIP HEAD and the known-good runtime status. Review these dated records, not stale `active/current/main` filenames: [release checkpoint](../releases/WINDOWS_RELAY_LIVE_EXECUTION_CHECKPOINT_2026-10-12.md), [health sweep](../reviews/WINDOWS_RELAY_RELEASE_AND_PROJECT_HEALTH_SWEEP_2026-10-12.md), [execution-no-governance policy](../policy/WINDOWS_RELAY_EXECUTION_WITHOUT_GOVERNANCE_2026-10-11.md), [no-local-backups policy](../policy/WINDOWS_RELAY_NO_ON_DEVICE_BACKUPS_2026-10-12.md), and [prior incident](../incidents/WINDOWS_RELAY_CANARY_001_OWNER_ISSUANCE_REJECTION_2026-10-12.md).
2. Ask the operator to **fast-forward only** `%USERPROFILE%\Downloads\Dev\GPT-Windows-Relay-Main-Build` to WIP HEAD, preserving dirty files. Then run:
   - `python -B "%USERPROFILE%\Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay\tools\relay_project_health_sweep.py"`
   - `python -B "%USERPROFILE%\Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay\tools\relay_project_test_sweep.py"`
   The first checks full tracked source Python/JS/JSON/Markdown/PowerShell plus Git identity and reported obsolete folder presence; the second runs two suites independently. These are not live browser or backend changes.
3. Use **new unique PCE18 action IDs** and the actual authorized relay session if executing through the live bridge. Remember that a new ChatGPT conversation/tab may require fresh affirmative owner binding; don't bypass it or claim session ownership with a packet field. Do not reuse the failed or successful PCE17 IDs.
4. Repair **only observed failures**. Beware that legacy tests may still contain obsolete assumptions; prefer matching tests to explicit operator-approved runtime semantics over weakening auth/STOP, copying an incompatible One-Click Go worker into the persistent add-on, or adding throwaway runtime trees. Commit focused fixes to WIP with dated source evidence.
5. Report exact before/after native test numbers, PowerShell parsing, any remaining physical duplicate/private-data blockers, and what is still unverified. Once all tracked-project tests pass, consider operator-approved non-destructive repeat/STOP/replay/refresh endurance canaries. Do not redefine the pinned October 12 baseline without explicit acceptance.

**Priority order:** preserve known-working v0.3.18 → make broad source/tests green → diagnose remaining unique untracked disk material with operator consent → prove long-run browser/STOP/exact-once durability. Never destroy a verified system to satisfy outdated labels.

## Where progress is logged

- [Release acceptance — 2026-10-12](../releases/WINDOWS_RELAY_LIVE_EXECUTION_CHECKPOINT_2026-10-12.md).
- [Git-tracked build and repository health sweep — 2026-10-12](../reviews/WINDOWS_RELAY_RELEASE_AND_PROJECT_HEALTH_SWEEP_2026-10-12.md).
- GitHub [issue #27](https://github.com/monag144/GPT-Windows-Relay/issues/27): source/auth/Firefox/runtime acceptance.
- GitHub [issue #30](https://github.com/monag144/GPT-Windows-Relay/issues/30): true single build on disk and cleanup of verified duplicates.
- This handoff: dated, source-based, and intentionally does **not** claim a clean native sweep after the latest fixes.
