# Documentation structure policy — 2026-10-07T2034Z

## Goal

Make the repository easy for a lazy or stateless agent to browse without guessing which file is newest or authoritative.

## Hard rules

1. Maintained documentation target: <=10 KiB per file.
2. New source-of-truth filenames carry a UTC timestamp and descriptive subject:
   - `TYPE_YYYY-MM-DDTHHMMZ_SUBJECT.md`
3. The top heading repeats the descriptive title and timestamp.
4. Do not use CURRENT, ACTIVE, LATEST, LOOK HERE, MASTER, AUTHORITATIVE, or similar status words as the only authority signal.
5. When a document approaches 10 KiB, split sideways by subject/component. Do not create PART-2 merely to continue a giant stream unless the content is genuinely sequential history.
6. Oversized historical records are frozen. New work goes into compact timestamped successors and indexes.
7. Compatibility filenames that existing code/tests reference may stay temporarily, but they should become small pointers to timestamped truth once dependencies are migrated.

## Directory map

- `docs/index/` — compact entry points and repository maps.
- `docs/policy/` — engineering/documentation rules.
- `docs/facts/` — bounded established facts by subject.
- `docs/roadmap/` — timestamped roadmap/status snapshots.
- `docs/audits/` — repository, migration, repetition, size, and integrity audits.
- `docs/incidents/` — new incidents; old root incidents may remain frozen until migrated.
- `docs/handoffs/` — future agent/session handoffs.
- `docs/migrations/` — repository/runtime migration records.
- `docs/history/` — frozen oversized chronology indexes, not a dumping ground for new append-only logs.

## Sideways split examples

Instead of one 30 KiB `ESTABLISHED_FACTS.md`, use:
- `FACTS_..._REPOSITORY_AND_PATHS.md`
- `FACTS_..._FIREFOX_LIFECYCLE.md`
- `FACTS_..._RESULT_DELIVERY.md`
- `FACTS_..._HUD_AND_CONTROL_PLANE.md`

Instead of one giant roadmap:
- `ROADMAP_..._R0_RELIABILITY.md`
- `ROADMAP_..._R1_RECOVERY.md`
- `ROADMAP_..._R2_BROWSER_MATRIX.md`
- `ROADMAP_..._PRODUCT_CAPABILITIES.md`

Instead of one giant engineering log:
- one compact daily/session index;
- separate timestamped incident/audit/acceptance files for substantive events.

## Existing cleanup queue

Current Windows `main` has 48 documentation files.
Seven exceed 10 KiB:
- `docs/windows-relay-engineering-log-2026-10-01.md`
- `docs/job-application-engine-v2.md`
- `docs/windows-relay-established-facts.md`
- `docs/windows-relay-mission-and-roadmap.md`
- `windows-relay/TASKS.md`
- `docs/INCIDENT_2026-10-07_OP042_CORRECTED_SAFE_CUTOVER_STALL.md`
- `docs/INCIDENT_2026-10-07_OP032_POST_DELIVERY_CUTOVER_STALL.md`

Eleven documentation filenames currently lack a date/timestamp. These are migration/compatibility cleanup targets, not permission for new untimestamped truth.

## Agent browsing contract

Before broad forensics:
1. open the latest file in `docs/index/`;
2. follow its subject pointer;
3. use timestamp + title to resolve precedence;
4. only then inspect frozen history if necessary.

If two docs conflict, the newer timestamped source-of-truth wins unless a later incident explicitly rolls it back.
