# Downloads Dev migration inventory — original evidence saved — 2026-10-11 (PDT)

**Repository:** `monag144/GPT-Windows-Relay`, branch `main`. **Visibility:** public repository. **Status:** BOTH USER-UPLOADED SOURCE FILES COMMITTED, INDEPENDENTLY READ BACK AND BYTE-IDENTICAL. This is a provenance/evidence record, **not** a completed migration certification.

## Source provenance
User provided two original inventory files produced at `2026-10-11 20:08:19 -07:00`, by a read-only one-click Windows Dev inventory. The user then reported moving the same files from `C:\Users\Craig Morgan\AppData\Local\GPTWindowsRelayAnalyses\OneClick-Dev-Inventory-20261011-200819` into `C:\Users\Craig Morgan\Downloads\Dev\GPT-Windows-Relay-Main-Build\`; user said SHA-256 remained unchanged. This local move is **user-reported, not independently witnessed**.

1. `DEV_INVENTORY.md`: original SHA-256 `B8C30AE49BD98BEA6BE092F0EAAA7A77C58EB06774FD3C70E96EA56E2EA5E29C`. GitHub committed at [`docs/inventories/DEV_INVENTORY_2026-10-11.md`](../inventories/DEV_INVENTORY_2026-10-11.md), original Git blob SHA-1 `a27f9facfe4a64ed5ae0ee14011fe9bc046a2b6d`; commit `15641767c81d6241de7db50aa31bcc0cfe05b60f`. Exact blob re-fetched from `main` and verified equal to original, preserving BOM/CRLF.
2. `file-metadata.csv`: original SHA-256 `8E2A52CC0999796EF91E67B921F3A05E834914FF044044FFC94CFA1CE15EF810`. GitHub committed at [`docs/inventories/file-metadata_2026-10-11.csv`](../inventories/file-metadata_2026-10-11.csv), original Git blob SHA-1 `6a99bddaf72be0343810b6e4ac06ee92f8fa0e5c`; commit `82c84de777c5d69b9d2d362b425c5d67397d8a55`. Exact blob re-fetched from `main` and verified equal to original, preserving BOM/CRLF; 5,289 CSV data rows.

## Source-grounded inventory snapshot
- Root inventoried: `C:\Users\Craig Morgan\Downloads\Dev`. Observed top-level directories: `bug-bounties`, `GPT`, `GPT-Windows-Relay-Main-Build`, `Legacy`, `Prototype-Developing`.
- Indexed non-private file counts: `GPT` = 1,235; `GPT-Windows-Relay-Main-Build` = 1,584; `Legacy` = 2,470; `Prototype-Developing` = 0. Total = 5,289 indexed rows.
- Inventory excluded 1,658 generated/cache/backup directories and redacted sensitive-looking file paths. This inventory does **not** prove the old `GPT` contents were fully migrated into the main build. It does establish `GPT` still existed separately at inventory time.
- Canonical development build required files were present at inventory time: `windows-relay/windows_relay.py`, `hud.py`, `relay-control.ps1`, `relay-watchdog-loop.ps1`, `START-GPT-WINDOWS-RELAY.bat`, `extension-persistent/manifest.json`, and `consumer/control_harness.py`.
- Inventory script declared **no Dev source modification**. Codex was **not** launched by this inventory: its guard saw three existing related workers and skipped Codex. The file metadata inventory gives paths, sizes and local modification times, but **no cryptographic content hashes per indexed source file**, so duplicate-by-content and migration completeness require a separate comparison.

## Preservation and privacy
- Files are stored in this **public GitHub repository**, so filenames, relative paths, file sizes and local modification timestamps recorded in the CSV are visible to the public. The CSV is metadata, **not the underlying source-file contents**; this log does not disclose auth token values.
- Do not delete, move, overwrite, reclassify or synchronize the user's local `GPT`, `Legacy` or `Prototype-Developing` folders based on this inventory alone. Do not assume `Prototype-Developing` is empty merely because 0 files were indexed.
- User request fulfilled: preserve these exact two uploaded artifacts and log their provenance to GitHub. Further file-by-file migration verification is a separate work item; any resulting changes require independently proven scope, tests, rollback and operator authorization.
