# Windows Relay: NO ON-DEVICE BACKUPS — 2026-10-12

**Current operator rule, effective immediately.** Windows Relay engineering, consolidation, deployment, Codex work and tests MUST NOT create, retain as new artifacts, or automatically regenerate local backup copies of source or builds.

**No new local backup folders, ever.** Irreplaceable private runtime data is not magically recoverable from GitHub; handle any existing unique state by explicit user decision, not by making another local safety copy.

The only active Windows Relay source is the Git-tracked `GPT-Windows-Relay-Main-Build/windows-relay/`; its Firefox release source is `extension-persistent/`. One-Click Go's distinct `extension/` remains a separate consumer product, not a duplicate Windows Relay release.

## Required engineering behavior

- **Remote version control for code:** Push validated, non-sensitive source history to `monag144/GPT-Windows-Relay` (WIP branch for active development; a separate pinned remote branch or Git commit for historical versions). Verify the remote commit and file readback **before** removing any covered local copy. Do not create machine-local backup, snapshot, rollback, pre-repair, pre-migration, duplicate source trees, timestamped archives, ZIP backups, or emergency save copies—not even temporarily as a safety measure. Do not rename the folder `quarantine` or `evidence` and call it an exception.
- **No backup-generating scripts:** Retire or rewrite deployment/sync tools that make a `backups/` copy before changing files. Unreviewed old live-sync/cutover logic must fail closed, not silently create another local runtime or backup. Do not recreate `STUPID BACKUPS DO NOT USE` or `windows-relay/runtime` as a duplicate source tree.
- **Single source of code truth:** `windows-relay/windows_relay.py`, `hud.py`, controller, watchdog and launcher are source files in the canonical checkout; `windows-relay/extension-persistent/` is the Firefox release source. The consumer `extension/` is intentionally separate and remains governed by its own product boundaries. Historical copies are retrievable from GitHub history and explicit remote archive branches, not by keeping a second local build.
- **Allowed files are not backups:** One actual active build, dependency environment necessary to run it, live state required for STOP/pairing/action results, logs necessary for current operation, and transient atomic-write files that are removed as part of a successful write. Tests may use temporary files/isolated disposable fixtures in OS temporary locations and must clean them up afterward; those are *test execution data*, not persistent rollback copies.
- **Deletion safety:** GitHub **does not** recover unique untracked work, browser profiles, tokens, secrets, execution queues, local databases, private user data or other unpushed operational state. Identify these individually and get the operator's decision before irreversible destruction; do not upload them to this PUBLIC repository as a workaround. No local backup is created while waiting for that decision. Do not delete `.git`, the canonical checkout, or unrelated directories.
- **Clean checkout behavior:** Historical backup files must not be tracked on the active WIP branch; otherwise `git pull` restores them. They may reside on the pinned `archive/preconsolidation-source-2026-10-12` branch or in earlier commits, and not in the current working tree.
- **Operational boundaries:** The relay backend and Firefox extension remain intentionally off until separately authorized. No code cleanup, local Git pull, test or policy document may launch/restart them, alter pairing, bypass STOP/owner/issuance/deduplication or silently perform a runtime cutover.
- **Authority:** This operator directive supersedes dated rollback-to-local-folder recommendations in older migration, preflight, cutover, release-candidate, incident, and governance documents. It is a developer WORKFLOW rule, **not** a backend command-admission gate or engineering audit checkpoint.

## GitHub archive receipt

- Commit `40445329f20c77774657a9ec27b7a49835749317` published all 27 files previously found in `STUPID BACKUPS DO NOT USE/`.
- Dedicated remote archive branch `archive/preconsolidation-source-2026-10-12` is pinned to that exact commit.
- Active WIP branch commit `5740f636624732173e195bcf98f38fd5ddf1b552` removes those 27 Git-tracked backup artifacts from current checkout history, while leaving the remote archive accessible.
- A `git pull --ff-only` from WIP removes tracked backup files on disk **if the local checkout has no conflicting modifications**; pre-existing untracked or locked files may remain and must be resolved separately.

## Delivery contract

ChatGPT leads routine source engineering in GitHub and gives one non-destructive pull command after verifying the push. Codex handles major local engineering/cleanup when asked. Both follow this policy, including when old scripts, manuals, comments or tests recommend making local safety copies. Do not claim disk cleanup completed until the operator or Codex reports actual post-pull filesystem results.
