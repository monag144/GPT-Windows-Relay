# Incident — A6.399ar JavaScript replacement-string recurrence — 2026-10-06T0213Z

**Class:** SOURCE-GENERATION / VALIDATION INCIDENT  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Operation:** `PCENG-A6.399ar-firefox-oob-submit-fix-gate-and-stage`

## Observation

A6.399ar fast-forwarded Windows to `d92e843` and immediately failed the mandatory PowerShell AST gate. The changed `firefox_tab_adapter.ps1` had grown to 35,910 characters / 542 lines, with three `list-tabs` blocks and three debug-tail blocks. No live adapter staging occurred.

## Root cause

This is the same source-generation class previously recorded at 2026-10-06T0050Z.

The intended replacement block contains the PowerShell regex:

`(?i)^Send(?: prompt| message)?$`

followed by a single quote. When passed as the replacement **string** to JavaScript `String.replace`, the sequence `$'` is interpreted by JavaScript replacement-string semantics as “insert the suffix after the match.” That spliced the remainder of the PowerShell source into the replacement and duplicated the tail.

## Containment

The Windows AST parse gate detected the malformed blob before Python tests, staging, or live execution. The active dev adapter remained the previous known-good file.

## Repair

The adapter was reconstructed from the preserved known-good pre-patch blob and the same logical patch was applied with a JavaScript function replacer, which treats the replacement as literal data. Before commit the rebuilt source was structurally gated:

- `list-tabs` block count = 1;
- OOB prompt marker count = 1;
- clipboard fallback marker count = 1;
- debug-tail block count = 1;
- source length = 20,917 characters (<23,000).

Repair commit: `3a89b7f`.

## Standard rule

Any automation that patches source through JavaScript must not use replacement-string semantics for arbitrary code payloads. Use literal slicing or a function replacer and perform structure/parse gates before deployment. A repeated source-generation mechanism failure is a process defect even when a downstream parser safely catches it.
