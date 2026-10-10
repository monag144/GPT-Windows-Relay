# Document titles and date precedence — 2026-10-09

**Scope:** `monag144/GPT-Windows-Relay` only. Calendar dates in newly maintained titles and filenames use **America/Los_Angeles** local date; on 2026-10-09 the local offset is PDT (UTC-07:00). Use a descriptive **title and date**, not a clock time: `SUBJECT_DESCRIPTION_YYYY-MM-DD.md`. This supersedes the older UTC-time-in-filename format prescribed by `docs/policy/POLICY_2026-10-07T2034Z_DOCUMENTATION_STRUCTURE.md` for newly written maintained documents. Existing historically timestamped originals do not need speculative renames.

## Rules

1. Title first, date last; Markdown H1 repeats both, e.g. `# Relay action sandwich — 2026-10-09`. Avoid `ACTIVE`, `CURRENT`, `LATEST`, `MASTER`, `AUTHORITATIVE`, `READ_THIS_FIRST`, and similar authority-by-adjective names or headings.
2. If two sources conflict, prefer **explicitly superseding, later verified evidence and user instructions**. Filename dates distinguish historical snapshots; a date alone is not proof a statement is accurate. On the same date, compare Git commit chronology, source provenance, and linked incident/acceptance receipts. Do not compare a Pacific date-only filename lexically to an older UTC timestamp to infer an exact ordering across time zones.
3. Document discovery goes through `docs/index/WINDOWS_RELAY_DOCUMENTATION_INDEX_2026-10-09.md`. Older indexes and old README navigation remain compatibility pointers only.
4. Existing code-referenced stable paths (`README.md`, `TASKS.md`, `RELAY_OPERATIONAL_RULES.md`, `relay-sandwich-procedure.md`, etc.) remain as **small compatibility pointers**, not competing truth. A stable alias does not gain precedence over a dated source.
5. Preserve Git history and original event timestamps. Do not rename or redate historic incidents, signed artefacts, software manifests, or source code just to make names look uniform. Freeze extensive historical text at its original Git commit rather than deleting its provenance.
6. Clearly separate tested source behavior from real loaded runtime, and never assert safety/release success that later evidence disproves. Status depends on verified evidence, not the adjective in a document title.
7. Do not silently auto-switch agents. The specific documented user hold at `docs/policy/POLICY_2026-10-10T0331Z_MANUAL_AGENT_HANDOFF_AND_AUTOMATED_ROTATION_HOLD.md` remains in force; this date-format change does not lift it.
8. A GitHub documentation change does not automatically update a running Windows checkout. Before local actions, check actual installed control files, hashes and compatibility gates. Do not force synchronization or alter Client deployment as part of documentation cleanup.

This policy records the user preference for **just a descriptive title and Pacific-local date**. Historical UTC timestamps may remain inside evidence where they identify real recorded events.
