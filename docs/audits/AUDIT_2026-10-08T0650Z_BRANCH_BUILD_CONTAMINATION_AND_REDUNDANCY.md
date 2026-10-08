# PCE10 source, build and contamination audit — 2026-10-08T0650Z

**Boundary:** GitHub remote branches and tracked blobs, not all untracked Windows disk builds, local rollback folders, loaded browser code, or local secrets. `build` must not be equated with Git commit.

## Exact GitHub counts at observed commit
- `main@94de291`: 62 commits along its history; 171 tracked files +13 directories (184 tree entries); 1,795,303 tracked bytes.
- `pce10/reconcile-control-and-rotation@5dac27c`: 311 commits along its history, of which 249 are ahead of `main`; 274 tracked files +21 directories (295 tree entries); 2,338,904 tracked bytes.
- 12 branch references checked. Other named `safety/pce8-*` branches are historical checkpoints, not separate distributable product builds.
- GitHub releases: **0**; tags: **0**; tracked packaged `.exe`, `.xpi`, `.zip`, `.msi`, `.whl`: **0**. GitHub therefore cannot establish an exact count of local compiled/installable builds.
- Packaging scripts exist for a consumer ZIP (`consumer/build-package.ps1`), Windows EXE (`windows-relay/build-exe.ps1`) and persistent Firefox XPI (`windows-relay/build-extension-xpi.ps1`). `consumer/release.json` declares product **1.1.0 revision 29**; this is metadata, not 29 distributable files.

## Contamination, bounded by evidence
- Former Termux r29 post-split Windows drift: 35 commits / 63 changed files (32 Windows relay, 5 consumer, 26 docs), 4,779 additions and 354 deletions. Earlier audit compared these to Windows `main`: 10 byte-identical, 24 divergent, 29 absent at that time.
- Later PCE10 migration confirmed all **87 of 87** Windows Relay file paths from the contaminated r29 tip existed on the Windows reconciliation branch before removing Windows paths from active Termux tips; sampled 13 active tips no longer exposed `windows-relay/README.md`. Preserve historical Git commits as provenance.
- PCE10.025 was stuck at DISCOVERED and generated false replay-suppression without durable backend execution evidence. PCE10.018 (~3,774s) and .021 (~784s) were separate stalled/unknown incidents; never reissue them blindly.
- Live broken-state backup `BROKEN-PCE10.026-2026-10-08T055125Z`: PCE10.036 reported **658 of 658** files rehashed with zero mismatches. These are local backup files, NOT GitHub-tracked 658 builds, and some capture a broken state.
- PCE10.036 compared 38 source/live files: 19 mismatches, 19 matches, 0 absent. PCE10.037 found all three live scanner copies plus two extension workers differed from approved source; loaded runtime hash/unambiguous Firefox target NOT verified.
- Source-only PCE10.035: 443/443 Windows, 116/116 consumer tests, 5/5 focused replay regressions, 5 JS syntax checks, and scanner-mirror equality reportedly passed. This does NOT constitute live canary success.

## Redundancy classification
- `windows-relay/content.js`, `windows-relay/extension/content.js`, `windows-relay/extension-persistent/content.js`: exactly the SAME Git blob SHA in current PCE10 HEAD. Intentional synchronized build/staging mirrors — KEEP.
- `windows-relay/extension/` versus `extension-persistent/`: distinct temporary/signed-persistent delivery variants — KEEP until a validated replacement exists.
- Safety branches, `docs/history/` snapshots, live rollback backups, saved exact result artifacts: intentional recoverability/evidence — KEEP.
- `windows-relay/README.txt`: obsolete Oct 1 single-fix instructions claiming HUD absent and prescribing manual refresh; removed as misleading.
- `docs/DOCUMENT_SIZE_AUDIT_2026-10-07.md`: 46-document baseline superseded by timestamped size/title audit and this full branch inventory; removed as stale duplicate.

## Unclosed damage, release verdict
**Source branch accepted in PCE10.035; active/live build remains UNACCEPTED.** The immediate blocker is `FIREFOX_CONVERSATION_MATCH_COUNT_0` from `firefox_tab_adapter.ps1` during PCE10.037 exact target check. The old overnight automation path exists; current failure is execution/activation/identity divergence and false-result suppression, not proven absence of all recovery functions.

Do not promote, roll back over existing evidence, reset branches, force-push, terminate Firefox broadly, or stage automatically from this documentation audit. Live identity and STOP canary are still required.
