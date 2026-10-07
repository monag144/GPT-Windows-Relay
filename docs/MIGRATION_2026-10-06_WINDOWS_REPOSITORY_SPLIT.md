# Windows Relay repository split — 2026-10-06

## Canonical destination

Windows relay development, the Windows consumer/control plane, job-application automation, and associated Windows relay projects now live in:

`monag144/GPT-Windows-Relay`

The old `monag144/GPT-Termux-Relay` repository remains the Android/Termux project and migration provenance source. It is no longer the canonical destination for Windows relay work.

## Source snapshots used

The migration intentionally merged two previously divergent Windows source lines from the old repository:

- `consumer/r29-firefox-offline-tray` at `d69666da530390146ba093dc1138dc794541b861`
  - freshest PCE7/HUD/recovery/consumer state
- `development/runtime-control` at `d52544440a366ec12c22d0a39d28d11d64011fc5`
  - newer Job Application Engine v2 modules/tests that had not all reached r29

## Ported scope

The clean migration contains 124 intended source/history files plus repository metadata, including:

- `consumer/` — One-Click consumer, updater, browser manager, control harness, recovery supervisor, tests
- `windows-relay/` — executor, browser bridge, Firefox/Chromium integration, HUD/control plane, watchdogs, UIA tools, workflow helpers
- Job Application Engine v2, Workday provider code, reasoning broker, intake/discovery/preview/rehearsal/runner/session layers, tests
- PCE7.445/PCE7.446/PCE7.447 source/cutover helpers
- PCE6→PCE7 handoffs, PCE7 incident chain, rollback index, operational rules, established facts, mission/roadmap, engineering log

## Explicitly excluded from the public destination

The destination repository is public, so user-specific application dossiers and private applicant defaults were intentionally not copied, including:

- `docs/job-application-automation-defaults.md`
- `docs/job-applications/`
- local applicant profile data
- credentials, pairing tokens, generated secrets, browser-local configuration
- runtime evidence/log/rollback artifacts

Applicant data remains local-only under the existing runtime profile model.

## Canonicality changes made during port

- `consumer/release.json` now targets `monag144/GPT-Windows-Relay` / `main`.
- Recovery-supervisor GitHub guidance now targets the Windows repository.
- User-specific absolute paths were converted to self-relative or environment-derived paths.
- PCE7 tools were retargeted to the new repository layout.
- PCE7.446's old-repository commit ancestry gate was replaced with a new-repository migration baseline anchor.
- Test applicant identity fixtures were generalized.
- Historical engineering documents were sanitized for public-repository path privacy while preserving technical evidence.

## History hygiene

The migration was assembled on a temporary cutover branch, audited, and then published as a clean squashed snapshot from the repository's initial root. The temporary branch is repointed to the same clean snapshot so the normal visible branch history does not retain the intermediate PII-bearing copy commits.

## Live-runtime boundary

This repository migration does **not** by itself prove or change the currently running Windows relay installation. Live cutover remains a separate, explicit operation with rollback and acceptance proof.
