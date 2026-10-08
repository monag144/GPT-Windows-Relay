# PCE10 documentation cleanup and deletion log — 2026-10-08T0650Z

Scope: documentation-only, GitHub-first change on `pce10/reconcile-control-and-rotation`. No source, manifest, live runtime, browser state, or protected restore copy is deleted.

## Removed from the tracked HEAD (available in Git history)
1. `windows-relay/README.txt` — obsolete October 1 one-off browser-side fix instructions. It stated `No HUD is loaded`, described an earlier scanner and asked for manual addon reload/page refresh; the current system has a HUD and controlled restart/identity rules. Keeping these as a live readme would mislead engineering agents. See source history for the original bytes.
2. `docs/DOCUMENT_SIZE_AUDIT_2026-10-07.md` — obsolete small audit of **46** documents and outdated sizing, replaced by `docs/audits/AUDIT_2026-10-07T2034Z_DOCUMENT_SIZE_TITLE_TIMESTAMP.md` plus PCE10 274-file inventory. Retaining it as an active audit confuses the measured scope.

## Standardized active entry-point headings
- `README.md`, `consumer/README.txt`, `windows-relay/README.md`, `windows-relay/TASKS.md`.
- `docs/windows-relay-established-facts.md`, `docs/windows-relay-mission-and-roadmap.md`, `docs/RELAY_OPERATIONAL_RULES.md`, `docs/relay-sandwich-procedure.md`.
- `docs/job-application-automation-defaults.md`, `docs/job-application-engine-v2.md`, `docs/job-applications/README.md`.
- Added timestamped PCE10 source-map index and this audit/deletion log. Old code-sensitive compatibility filenames remain in place intentionally; they now carry a dated heading but are **not** falsely claimed to satisfy strict timestamped filename policy.

## Remaining historical naming debt — not silently rewritten
- Pre-cleanup tracked documentation set: **140** entry-point/document paths, of which **53** filenames lack a full `YYYY-MM-DDTHHMMZ` token; 14 exceed the 10 KiB maintained-doc target. The older audit on `main` is not a reliable PCE10 branch count.
- The two removed documents reduce the original untimestamped set by **2**. Other legacy date-only incidents, historical logs, protected handoffs, and code-referenced stable filenames have deliberately been retained to avoid inventing incident times, breaking references, or removing the evidence the user wants recovered.
- This is **partial filename remediation**, NOT a claim that all titles/filenames have been migrated. A comprehensive rename must include link/reference rewrites and source test verification after the relay fast-forward pulls this GitHub commit.
- Large frozen records are retained because they contain unique historical proof. Do not trim them merely to hit a byte quota; split by subject and preserve references in a subsequent tested migration.

## Verification boundary
Validated tree counts, Git blob identity, branch ancestry, source/docs evidence and GitHub releases/tags through the connected GitHub API. No Windows local test suite, live loaded-extension canary, or full 658-file local backup rehash was performed as part of this documentation-only GitHub change.
