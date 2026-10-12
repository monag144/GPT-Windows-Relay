# Codex migration and deduplication prepared — 2026-10-11 (PDT)

**Status:** Package authored and verified, **not yet executed on the user's Windows machine**. Operator needs to run `Run-Codex-Migration.cmd` once locally because the Firefox relay action bridge recently returned `RelayError` on two attempted commands. Never claim a live Codex run or filesystem migration without its native output.

**Authoritative task:** `docs/tasks/WINDOWS_RELAY_CODEX_DEV_MIGRATION_AND_DEDUPLICATION_2026-10-11.md`, GitHub main blob `2888c4d7edd6f5b7add566d14a0f299c80570459`, committed and read back.

**Evidence preserved:** `docs/inventories/DEV_INVENTORY_2026-10-11.md`, `docs/inventories/file-metadata_2026-10-11.csv`, provenance `docs/logs/DEV_MIGRATION_INVENTORY_SAVED_2026-10-11.md`; original SHA-256 both verified.

**Independent CSV analysis:** `GPT\Client\Relay` has 1,235 indexed nonprivate file paths; nested `GPT-Windows-Relay-Main-Build\windows-relay\runtime` has 1,234. Of these, 1,233 relative paths match exactly. Old-only .relay-kill/.relay-kill-hud and nested-runtime-only .relay-off are control marker files; **do not migrate them**. Seven matched paths have size differences; file contents have **not** been hash-compared by this analysis, so a true duplication or complete migration verdict remains unproved.

**Prepared package:** `Windows-Relay-Codex-Migration-OneClick.zip` contains `Run-Codex-Migration.cmd`, `Run-Codex-Migration.ps1`, `Codex-Migration-Task.md`, both untouched original inventory files, and `README.txt`. Package ZIP CRCs passed and the inventories' exact original SHA-256 hashes matched. ZIP content SHA-256 at packaging time: `642D72AEFBCCF4E831CECB237FFD915F517E1F382877E1F812C9C501E0E82A28`. The package is a conversation artifact, **not a GitHub release**.

**Behavior:** When operator double-clicks launcher outside Dev, it validates originals and local main build, detects Codex CLI, takes a hash-verified bounded independent source snapshot outside Dev, guards against duplicate migration via named mutex and another worker explicitly targeting the same build, then invokes noninteractive Codex CLI `exec` with `workspace-write` sandbox. No host-wide bypass, no forced process termination. Codex tasked to compare hashes, finish proven missing feature/docs/tests migration, dedupe verified active source, optionally archive `GPT` to versioned Legacy only after proving no live references, test and produce reports. Preserve historical and private data, no blind deletion or remote push.

**Expected verification artifacts** under `GPT-Windows-Relay-Main-Build\migration-reports`: `MIGRATION_REPORT_2026-10-11.md`, `MIGRATION_MANIFEST_2026-10-11.csv`, `ROLLBACK_INSTRUCTIONS_2026-10-11.md`; launcher output under `%LOCALAPPDATA%\GPTWindowsRelayAnalyses\CodexDevMigration-*`.

**Acceptance pending:** native Codex process result, rollback verification, before/after file hashes, tests, code review of any changes, manual confirmation of live loaded backend/extension identity. Do not retire `GPT` source or remove other directories on metadata alone.
