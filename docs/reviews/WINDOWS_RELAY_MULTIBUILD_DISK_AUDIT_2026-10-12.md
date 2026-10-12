# Windows Relay multiple-build disk audit — 2026-10-12 (Pacific)

**Evidence category:** Operator-provided local, read-only Codex inventory, interpreted alongside current tracked GitHub sources. The per-file disk counts/hashes below were supplied by the operator; they have **not** been independently re-enumerated by this GitHub-only assistant. The audit made no disk changes.

## Actual problem: one Git checkout is not one disk installation

The `GPT-Windows-Relay-Main-Build` checkout contains multiple full and partial copies of runtime code, archived candidates, packages, Firefox fixtures, rollback builds and local-only generated state. The fact that only one Git checkout is designated does **not** make the whole directory a single authoritative executable source.

| Filename | Files found on disk | Distinct SHA-256 hashes |
|---|---:|---:|
| `windows_relay.py` | 23 | 13 |
| `hud.py` | 26 | 14 |
| `manifest.json` | 42 | 18 |
| `service_worker.js` | 32 | 12 |
| `content.js` | 113 | 21 |

**Prominent backend candidates:**
- `windows-relay/windows_relay.py` — current Git-tracked canonical root candidate, SHA-256 `662A0EBC718F9C75061032BE8E688BB52DE83C0252AD1487B0393CD46272C877`.
- `windows-relay/runtime/windows_relay.py` — untracked nested runtime candidate, SHA-256 `540F2589EEB4B6980C6947D26381E653F17C0886043514E39721268E998CAB93`.
- `Prototype/release-candidate-20261011-governance/windows_relay.py` — tracked release-candidate/prototype source, **not** automatically authoritative.
- `Prototype/WIP-Windows-Relay-Rebuilt-Resynced-2047-101026/client/windows_relay.py` — tracked prototype/client copy, **not** automatically authoritative.

**HUD source difference:** root `windows-relay/hud.py` SHA-256 `D66609514AE395A6676F90BD0C44C25CB49D5243BC6868A9652E22AB31A2AB2E`; nested `windows-relay/runtime/hud.py` `363C3D55446DF3E850CE53DC1C4DEF6CCAA1FF665126A5A41FF1D93B24CBC44E`. The root and nested persistent Firefox extension files and versions also differ. The Git-tracked `windows-relay/extension-persistent` is GPT Windows Relay v0.3.17; Git-tracked sibling `windows-relay/extension` is *GPT One-Click Go Relay* v1.1.0, a **different product interface**, not interchangeable persistent Firefox release code.

**Untracked second installation:** `windows-relay/runtime/` contains ~3,280 files and zero Git-tracked files. It has backend, HUD, controller/watchdog, launchers, extension trees, `.venv`, binaries/build outputs, logs, state, rollback and backups. Current GitHub cannot recover its unique untracked source or operational state merely by reverting the tracked repository.

**Additional duplicate collections:** `Prototype/` approximately 1,622 local files (profiles, build/release candidates, code, caches and acceptance assets). `STUPID BACKUPS DO NOT USE/` has 27 reported files, with snapshot/repair directories dating to October 10–11 (`20261010T210000Z-pre-consolidation`, `governance-repair-20261010`, `repair-20261010-211713`, `migration-20261011-source-snapshot`). The backup names/timestamps match historical GPT/Codex consolidation and repair work; filesystem metadata alone does not identify an individual author. Those backup directories were not shown to be operating system or Git-created.

**Conflicting untracked root declarations:** `windows-relay/BUILD_MANIFEST.json` and `windows-relay/BUILD_MANIFEST_corrected.json` both claim the authoritative development build but disagree about Git metadata. Neither is currently Git-tracked, so neither is acceptable as a sole source of truth. Hashes and actual process/installer/package references override titles.

## Correlation with prior records

- `docs/MIGRATION_CONSOLIDATION_2026-10-11.md` correctly distinguished the tracked root, historical Client and Prototype, **but its claim of a single development checkout did not establish a single on-disk runnable source**. Its historical recommendation to preserve backups is superseded by the new operator preference below, after verification of restore eligibility.
- `docs/WORKSPACE_CONSOLIDATION_2026-10-10.md` and other documents describe the earlier protected `GPT/Client/Relay` installation. On 2026-10-12 the operator's native identity diagnostic instead found `OLD_CLIENT_PATH_PRESENT=False` and `PORT_8766=NOT_LISTENING`. Treat earlier active-installation claims as historical, not current live proof.
- Tracked scripts still refer to multiple source trees: `windows-relay/install-browser-fix.ps1` loops over both extension trees and defaults to old Client; `windows-relay/sync-live.py` defaults to old Client and **creates a local backup directory**; `windows-relay/safe_live_cutover.py` snapshots/restores from `--backup` and lists both extension trees; consumer `bootstrap.ps1` can choose `consumer/runtime` before `windows-relay/`. Clean-room packaging/launch references must be reconciled before claiming a single runtime.
- User explicitly confirmed the backend and browser extension were shut down for system performance. No listener or Firefox loaded extension is **intentional current operating state**, not by itself an installation failure. Do not start them merely to clean disk.

## New operator cleanup target

**Goal:** one Git-tracked canonical Windows Relay source root `windows-relay/`, with just `extension-persistent/` designated as the Windows Relay Firefox release source, and no duplicate local backups, stale installers, redundant runtime/build/release-candidate source trees or conflicting manifests. Maintain the separately scoped One-Click Go product only insofar as it is actually wanted and reproducibly sourced; do not conflate it with the Windows Relay extension.

**Local backup preference:** **no new on-disk backups, snapshot folders, duplicate builds or rollback copies.** History of tracked/sanitized source should be recoverable in GitHub commits or an explicit remote archival branch. GitHub cannot safely hold session tokens, browser profiles, private user data, or untracked execution state; deletion of those would be **irreversible**, not repaired by `git revert`. Never assert that the existing public repository already protects those bytes.

**Destructive-cleanup rule:** Codex should first produce a complete per-path manifest and hash/reference classification, identify the actual unique and most recent *working candidate* by functionality, commits and dependencies (not directory age alone), prove required publishable content is preserved remotely, update launchers/installers/fixtures/packaging to use the chosen source, and run safe isolated tests. Then remove clearly proven redundant artifacts from disk; for tracked obsolete material, use Git changes so `git pull` does not recreate it. Anything containing untracked unique work, personal data, credentials, pairing, browser profile, active queued actions or unknown state requires a specifically identified operator disposition **before irreversible deletion**. Do **not** relocate into another local backup folder. Do not delete `.git`, active Main-Build, or unrelated user projects.

**Pending:** the local duplicate-count inventory and selection of the only runtime remain to be confirmed and executed by Codex on the user's Windows machine. No deletion, relocation, Firefox change or runtime restart has occurred merely because this record was committed.
