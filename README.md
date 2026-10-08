# GPT Windows Relay — Repository Entry Point — 2026-10-08T0650Z

Canonical repository for the Windows relay, Windows consumer/runtime tooling, and reusable job-application automation.

This repository was split from `monag144/GPT-Termux-Relay` on 2026-10-06 so Windows-specific development can evolve independently from the Android/Termux relay.

## Repository scope

- `windows-relay/` — Windows relay runtime, Firefox/Chromium bridge, HUD/control tooling, Windows automation helpers, and job-application engine.
- `consumer/` — packaged Windows consumer application, updater, browser manager, control harness, and recovery supervisor.
- `docs/` — Windows relay engineering history, operational rules, incidents, handoffs, and reusable automation documentation.

User-specific applicant profiles, credentials, and job-application dossiers are intentionally not stored here. Runtime PII belongs in local-only application data.

## Migration provenance

Initial Windows source state is being migrated from:
- relay/consumer line: `GPT-Termux-Relay@consumer/r29-firefox-offline-tray`
- job-application engine line: `GPT-Termux-Relay@development/runtime-control`

The Windows repository is the canonical home for all future Windows relay and job-application automation work.

## Engineering snapshot — 2026-10-08T0650Z

The current working development branch is `pce10/reconcile-control-and-rotation`, not the default `main` baseline. See `docs/index/INDEX_2026-10-08T0650Z_PCE10_SOURCE_MAP.md` before touching runtime or Firefox. The former Termux repository is historical migration provenance, not a Windows development destination.
