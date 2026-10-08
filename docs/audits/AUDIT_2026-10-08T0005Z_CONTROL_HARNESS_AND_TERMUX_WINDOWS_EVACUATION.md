# Control harness and Termux Windows evacuation audit — 2026-10-08T0005Z

## Canonical destination

All Windows Relay engineering belongs in `monag144/GPT-Windows-Relay`.
The active reconciliation branch is `pce10/reconcile-control-and-rotation`.

## Control-harness proof

Control Harness v3 now requires every engineering turn to read:

- `consumer/control_harness.py`
- `windows-relay/TASKS.md`
- `docs/windows-relay-mission-and-roadmap.md`

It also records:

- canonical Windows repo: `monag144/GPT-Windows-Relay`;
- sandwich formatting is mandatory;
- audit cadence: every five engineering turns/operations;
- harness-hole rule: stale, contradictory, unenforced, or missing controls are repaired/tested before risky mutation.

Harness defects repaired during this audit:

1. incident creation moved from `docs/` to `docs/incidents/`;
2. runtime source validation now recognizes reconciled `run-control.ps1`;
3. operation-budget logic carries the current PCE generation instead of hard-coding PCE9.

The Windows relay result serializer now emits the turn checklist on every result and emits an explicit five-turn audit warning at PCE operation ordinals divisible by five.

## Termux migration proof

Contaminated r29 tip `249e3bb46c6ea57968d9ecf5157d73867a7f918d` contained 87 files under `windows-relay/`.

Path-set proof against the Windows reconciliation branch: **87 / 87 r29 `windows-relay/` file paths are present in GPT-Windows-Relay**.

Historical Windows/job-application documents missing from the Windows repo were copied before cleanup, including:

- overnight relay hardening/sync incident;
- job-application automation defaults;
- job-application historical records;
- relay-rendering incident.

A dry-run Git tree based on the Termux default branch removed the whole `windows-relay/` subtree plus explicitly Windows/job-application historical paths. Result:

- `windows-relay/` remaining: 0;
- matched Windows/job-application cleanup paths remaining: 0;
- Android/Termux source tree remains present.

## Cleanup boundary

The cleanup changes branch tips. Historical commits remain migration provenance unless an explicit destructive history rewrite is separately authorized and audited.

The cleanup must not delete Android Relay, Termux runtime-control, or shared consumer assets merely because they contain the word "relay".
