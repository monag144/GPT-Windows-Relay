# Windows Relay document authority audit — 2026-10-09

**Scope:** `monag144/GPT-Windows-Relay/main` tree at SHA `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8` only. Excludes historical Termux repository, untracked Windows files and live Firefox/runtime state. Filenames reflect Pacific-local date, with no time suffix.

The GitHub tree contained 228 tracked blobs and 106 Markdown/text files: 67 with full minute UTC timestamps, 1 with a second-resolution UTC timestamp, 27 with calendar date only, and 11 without a date. The undated set includes `consumer/requirements.txt`, which is a dependency manifest rather than documentation. No literal `ACTIVE.md`, `CURRENT.md`, `LATEST.md`, `MASTER.md`, or `AUTHORITATIVE.md` filenames were found. The real risk came from **undated guidance claiming present authority**, not from those literal filenames.

## High-risk findings addressed by dated successors

- `docs/RELAY_OPERATIONAL_RULES.md`: unconditional automatic rotation and stale governance descriptions contradict later user policy.
- `windows-relay/README.md`: unsupported blanket exact-once guarantee despite PCE15.043/.047 isolated source failures.
- `consumer/README.txt`: unconditional Firefox-disabled text conflicts with release.json's automatic temporary Firefox configuration.
- `docs/relay-sandwich-procedure.md`: missing historical links and an obsolete 'current autonomous night mission' reference.
- `docs/windows-relay-mission-and-roadmap.md`: untimestamped 'current mission' claims, older automatic-rotation work and extensive chronology.
- `windows-relay/TASKS.md`: untimestamped current-priority claims and old managed-conversation rotation backlog.

These files are retained by path as compatibility pointers; descriptive date-only documents hold new maintained guidance. Prior full text is preserved in Git history at the pinned pre-cleanup commit. **This is documentation repair, not deployed product remediation.**

## Deferred naming backlog (do not silently rewrite history)

- `docs/windows-relay-established-facts.md` (~24.6 KB): untimestamped long historical record; needs subject-specific dated extracts.
- `docs/job-application-engine-v2.md` (~43.5 KB): mixed implementation chronology; needs history-preserving split.
- `windows-relay/README.txt`: browser-side repair instructions from Oct 1 housed in undated README name; convert to date-named archive after packaging dependency review.
- `README.md` (root): conventional GitHub entry point should remain a very short pointer; no wholesale rename.
- Existing dated incidents/logs and source artifacts should not have fabricated timestamps added. Review relative references before mass moves.
- `docs/index/INDEX_2026-10-07T2034Z_DOCUMENT_CATALOG.md` is a historical snapshot whose file sizes/counts are no longer an accurate current inventory.

**Limits:** contents in the local Windows checkout can lag this GitHub documentation commit. No source code, Client, Firefox installation, scheduler or agent-switching runtime was changed; an existing held watcher is not thereby demonstrably disabled.
