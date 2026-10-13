# Windows Relay legacy browser installer retirement — 2026-10-12

**Operator safety correction following the verified v0.3.18 release.** The tracked `windows-relay/README.txt` begins `GPT Windows Relay browser-side repair — 2026-10-01`, recommends `install-browser-fix.ps1`, and promises local backup copies of the two extension trees. That is obsolete instructions, **not** the October 12 operational workflow.

- `windows-relay/install-browser-fix.ps1` **fails closed** with `RETIRED_NO_LOCAL_BACKUPS` before any file mutation; it must not be revived or used for the October 12 canonical Firefox extension.
- `windows-relay/sync-live.py`, `safe_live_cutover.py`, the historical PCE7 cutovers and local backup paths are likewise not an approved deployment method. Keep the one known verified source `GPT-Windows-Relay-Main-Build/windows-relay/`.
- The verified Firefox extension resides at `windows-relay/extension-persistent/manifest.json`, name `GPT Windows Relay`, ID `gpt-windows-relay@local`, **v0.3.18**. Load or reload **only that** source in the same Firefox profile.
- The source and installed runtime were confirmed through a real authenticated PowerShell canary. See [dated October 12 acceptance](../releases/WINDOWS_RELAY_LIVE_EXECUTION_CHECKPOINT_2026-10-12.md). Job-application features, restart recovery and project-wide tests still require separate testing.
- **Do not create new local backups.** For tracked source revert using Git commits and the pinned remote release tag; never push secrets or irreversible private browser/pairing/action state to the public repository.

**Unmodified compatibility file caveat:** The operator's October 12 disk-cleanup report explicitly preserved an existing uncommitted local edit to `windows-relay/README.txt`. Changing that tracked path in GitHub without the local diff could cause a non-fast-forward/overwrite conflict and lose operator work. Accordingly, this dated safety supersession was added **without modifying** the historical `README.txt`; reconcile or replace that file only after reviewing its local delta. Do not infer a different runtime or new active installer from the old document's heading.
