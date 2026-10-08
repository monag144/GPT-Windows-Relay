# Termux Windows branch-tip cleanup audit — 2026-10-08T0015Z

## Result

Windows Relay assets were migrated to `monag144/GPT-Windows-Relay` and removed from active branch tips in `monag144/GPT-Termux-Relay`.

## Migration proof

- contaminated r29 tip contained 87 files under `windows-relay/`;
- all 87 r29 `windows-relay/` paths exist on the Windows reconciliation branch before deletion;
- missing historical job-application, A6/R29 Firefox/HUD/recovery, PCE8, and PCE9 evidence was copied to the Windows repository before cleanup;
- Android/Termux trees were excluded from the deletion classifier.

## Branch cleanup

Branches changed because they contained Windows assets:

- `development/runtime-control`: `d5254444…` → `ea772ec5…`
- `consumer/one-click-go`: `d5b9db7a…` → `76a280bb…`
- `consumer/r26-control-harness`: `04eae52b…` → `ab16a37c…`
- `consumer/r27-user-test-recovery`: `2589df59…` → `a8a7d65b…`
- `consumer/r28-hud-go-ux`: `d5b9db7a…` → `c66159e6…`
- `consumer/r29-firefox-offline-tray`: `249e3bb4…` → `605269a6…`
- `safety/PCE7.445-pre-hud-state-machine`: `27f1eddd…` → `83261b70…`
- `safety/PCE7.446-pre-canonical-cleanup-87bc5a3`: `87bc5a37…` → `b76ebeeb…`
- `safety/PCE7.447-pre-overnight-source-hardening-4b4f454`: `4b4f4546…` → `6061b848…`

Branches inspected and unchanged because the cleanup classifier found no Windows assets:

- `development/mcp-apk-control-plane-20260916`
- `development/runtime-capability-engine`
- `docs/heavy-engineer-control-harness-20260916`
- `recovery/legacy-apk-0.3.2-feedback-20260920`

## Verification

A direct `windows-relay/README.md` lookup was performed against all 13 active Termux branches after cleanup: **present on 0 / 13**.

Recursive verification on the two critical tips:

- `development/runtime-control@ea772ec517c287ba7f86f163036298e52c65a023`: classified Windows paths remaining = **0**;
- `consumer/r29-firefox-offline-tray@605269a645122818ece711f506e586709f93636d`: classified Windows paths remaining = **0**.

## Historical boundary

This cleans active branch tips. Old commits still contain historical Windows blobs as migration provenance. Removing those from Git object history would require a destructive repository-wide history rewrite and is intentionally outside this bounded cleanup.
