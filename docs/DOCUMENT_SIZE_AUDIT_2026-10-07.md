# Documentation size audit — 2026-10-07

Scope: every `.md`, `.txt`, `.rst`, and `.adoc` file on `monag144/GPT-Windows-Relay/main`.

- Documents scanned: **46**
- Total documentation bytes: **429065**
- Incident reports over 16 KiB: **0**
- General documents over 64 KiB: **1**

## Largest documents

- `docs/windows-relay-engineering-log-2026-10-01.md` — 189,382 bytes
- `docs/job-application-engine-v2.md` — 43,514 bytes
- `docs/windows-relay-established-facts.md` — 24,085 bytes
- `docs/windows-relay-mission-and-roadmap.md` — 22,240 bytes
- `docs/INCIDENT_2026-10-07_OP042_CORRECTED_SAFE_CUTOVER_STALL.md` — 12,762 bytes
- `docs/INCIDENT_2026-10-07_OP032_POST_DELIVERY_CUTOVER_STALL.md` — 12,439 bytes
- `windows-relay/TASKS.md` — 11,609 bytes
- `docs/HANDOFF_2026-10-06T0246Z_PC_ENGINEERING_6_TO_7_FAILED_ROTATION.md` — 9,190 bytes

## Finding

All current incident reports fit the 16 KiB incident target. The historical engineering log is the only document above 64 KiB and is now a rotation/split candidate; current chronology should move to a new bounded log rather than continue growing that file.

The audit itself is intentionally compact.
