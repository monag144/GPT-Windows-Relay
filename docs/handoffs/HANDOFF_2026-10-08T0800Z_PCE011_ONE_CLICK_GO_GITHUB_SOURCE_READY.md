# PCE011 GitHub-first source handoff and release discipline — 2026-10-08T0800Z

## Current exact GitHub checkpoint
Branch `pce11/one-click-go-recovery-and-doc-hygiene`, previous parent `c1584b8229e527cd562f75426663b1d69a089a18`. This handoff is itself a documentation-only additional Git commit after that SHA. No merge into `main`, no local Windows relay source sync, no Firefox addon refresh, no live canary.

## Mission
Consumer-facing **One-Click GO** is the principal product target. Frozen r28 `consumer/one-click-go` in Termux is the recommended consumer reference; current r29 Windows source is a developer candidate with unaccepted temporary Firefox lifecycle. PCE9/PCE10 are marked operational failures; preserve vetted PCE6–8 capabilities and reject blind backwards regressions.

## Completed on GitHub
- Termux all 13 branch tips: 0 paths under `windows-relay/`. Historic consumer branches/safety commits deliberately retained. See `docs/audits/AUDIT_2026-10-08T0735Z_TERMUX_WINDOWS_RELAY_BRANCH_TIPS_CLEAN.md`.
- Firefox PCE10.037 zero-match code candidate corrected in commit `07ed26e0`: stop rejecting offscreen TabItems, traverse bounded ControlView/RawView tab ancestors, preserve selected-tab restoration and fail-closed exact URL while exposing safe diagnostic counts. New focused contract test present. **Live root cause still unproved**: could be stale URL, process/window binding, accessibility absence.
- Source/README corrected to distinguish frozen r28 Firefox-disabled release from experimental r29 temporary addon support.
- Timestamped canonical copies for **53 old document content entries**, including 40 legacy-history migrations and 13 stable source/UX entrypoints. 40 old filenames are marked redirect pointers; 13 protected paths remain operative; dependency manifest name remains `requirements.txt`.
- 13 oversized documents indexed into 60 dated archive fragments. Current GitHub tree has **zero .md/.txt blobs above 10 KiB**. Complete archived texts available via original Git blob SHA and fragments. All 40 redirect alias targets independently checked successfully by connected GitHub. New documentation contract test added.
- PCE10 old roadmap/index now explicitly link to PCE011 One-Click GO release mission.

## Explicitly NOT done
- No PowerShell AST parse, Windows Python/consumer full suite, or live Firefox target validation. No GitHub Action jobs/CI statuses were found for pre-handoff HEAD.
- No relay pull, source-to-live hash match, exact browser PID/tab binding, backed-up narrow addon staging, operator STOP proof, full restart or one-click consumer acceptance. No verified signed Firefox XPI.
- No deletion/reset of r28 stable branch, historical Git blobs, rollback backups or safety branches.
- No claim that all physical legacy filenames were deleted; redirects and fixed-purpose paths remain intentionally.

## Next safe sequence
1. Begin PCE011 ordinal sequence with `engineering_preflight(...,series=11)` (not default PCE10), read `docs/roadmap/ROADMAP_2026-10-08T0735Z_PCE11_ONE_CLICK_GO_RECOVERY.md`, canonical controls, this handoff, and prior Firefox established facts/archival parts.
2. Verify remote SHA and Windows git worktree cleanliness, then **explicitly** fast-forward fetch/checkout the PCE011 branch; do NOT overwrite dirty local Windows changes, staged live files or known good backups.
3. Run PowerShell AST validation of `firefox_tab_adapter.ps1`, focused adapter/docs regression, full Windows and consumer tests. Stop if failed; fix source on GitHub and rerun.
4. Collect one bounded read-only exact Firefox current selected conversation identity/PID/profile observation. Read safely; do not guess an old ChatGPT URL or rerun generic profile archaeology. If root-cause class remains unclear, do NOT activate.
5. Once unique exact tab and STOP/armed gates pass, back up existing live files with SHA-256 manifest and clean rollback test, then stage only intended files, confirm source/live hash equality, reload only matched addon/tab and test a NEW harmless exactly-once ID/visible result. Restore on failure. No old replay of .018/.021/.025.
6. Return to **r28-based One-Click GO Chrome/Edge user acceptance matrix** and only selectively integrate tested r29/Firefox capabilities after signed persistent add-on acceptance. Full consumer release—not autonomous engineering-chat rotation—is primary success measure.

## GitHub source links
- `docs/audits/CLEANUP_2026-10-08T0756Z_PCE11_DOCUMENT_TIMESTAMP_SIZE_MIGRATION_LOG.md`
- `docs/audits/AUDIT_2026-10-08T0735Z_FIREFOX_RESOLVER_GITHUB_SOURCE_REVIEW.md`
- `docs/roadmap/ROADMAP_2026-10-08T0735Z_PCE11_ONE_CLICK_GO_RECOVERY.md`
