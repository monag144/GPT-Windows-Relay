# Documentation size/title/timestamp audit — 2026-10-07T2034Z

## Scope

Canonical `monag144/GPT-Windows-Relay/main` after repository-index cleanup.

- Documentation files: **52**
- Total documentation bytes: **446,272**
- Maintained-file target: **<=10 KiB**
- Files above 10 KiB: **7**
- Documentation filenames without a date/timestamp: **11**

## Oversized cleanup queue

1. `docs/windows-relay-engineering-log-2026-10-01.md` — 189,382 bytes — freeze/index, never append.
2. `docs/job-application-engine-v2.md` — 43,514 — split by architecture/provider/workflow.
3. `docs/windows-relay-established-facts.md` — 24,287 — split sideways by repository, Firefox, delivery, HUD/control.
4. `docs/windows-relay-mission-and-roadmap.md` — 22,240 — split by R0/R1/R2/product capability.
5. `windows-relay/TASKS.md` — 12,951 — replace with timestamped roadmap snapshots plus compact pointer.
6. `docs/INCIDENT_2026-10-07_OP042_CORRECTED_SAFE_CUTOVER_STALL.md` — 12,762 — freeze; create compact indexed summary if needed.
7. `docs/INCIDENT_2026-10-07_OP032_POST_DELIVERY_CUTOVER_STALL.md` — 12,439 — freeze; create compact indexed summary if needed.

## Untimestamped filename queue

- `README.md`
- `consumer/README.txt`
- `consumer/requirements.txt`
- `docs/RELAY_OPERATIONAL_RULES.md`
- `docs/job-application-engine-v2.md`
- `docs/relay-sandwich-procedure.md`
- `docs/windows-relay-established-facts.md`
- `docs/windows-relay-mission-and-roadmap.md`
- `windows-relay/README.md`
- `windows-relay/README.txt`
- `windows-relay/TASKS.md`

Six are compatibility/package entry points (README/requirements) and may remain stable aliases.
Five are living operational/authority documents and should migrate to timestamped source-of-truth files, leaving compact compatibility pointers.

## Authority-style title finding

There are **zero literal top-level CURRENT, ACTIVE, LATEST, LOOK HERE, MASTER, or AUTHORITATIVE titles** in the canonical Windows documentation set.

There is **one explicit “Read This First” top-level title**:
- `docs/windows-relay-established-facts.md` — `GPT Windows Relay — Established Facts / Read This First`.

The larger risk is not literal title wording but **untimestamped living authority**: Rules, Established Facts, Mission/Roadmap, Sandwich Procedure, and TASKS can silently drift while keeping the same filename. These five are the primary spring-cleaning targets.

## Source-of-truth policy

Timestamp + descriptive title decides precedence.
Stable untimestamped compatibility filenames do not become authoritative merely because an agent finds them first.
Use `docs/index/INDEX_2026-10-07T2034Z_WINDOWS_RELAY_SOURCE_OF_TRUTH.md` as the entry point.
