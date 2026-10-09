# Windows Relay source-of-truth index — 2026-10-07T2034Z

## Canonical repository

- GitHub: `monag144/GPT-Windows-Relay`
- Canonical branch: `main`
- Canonical local clone target: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\GPT-Windows-Relay`
- Live runtime tree: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay`
- Retired Windows migration source: `monag144/GPT-Termux-Relay` (historical provenance only). Never use it for Windows engineering, local checkout fallback, remote fetch/pull/push, preflight, or active task routing. A missing Windows checkout is a fail-closed condition.

## Read order for an engineering agent

1. This index.
2. `docs/policy/POLICY_2026-10-07T2034Z_DOCUMENTATION_STRUCTURE.md`.
3. `docs/RELAY_OPERATIONAL_RULES.md`.
   - For five-operation checkpoints: `docs/policy/POLICY_2026-10-09T0710Z_GITHUB_FIRST_AUDIT_GATES.md`.
4. `docs/windows-relay-established-facts.md`.
5. `windows-relay/TASKS.md`.
6. `docs/windows-relay-mission-and-roadmap.md` when roadmap context is needed.
7. The newest timestamped audit/incident/handoff relevant to the subject.

Do not start by rereading the giant historical engineering log. Use it only when the compact index/facts do not answer the question.

If a relay-generated footer, earlier chat handoff, or copied checklist names the old Termux checkout or the missing `docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md`, treat it as stale guidance—not authority. Verify Windows repository files on `main` instead. The current roadmap and backlog are `docs/windows-relay-mission-and-roadmap.md` and `windows-relay/TASKS.md`. The original v2 harness lacked `engineering_preflight`; the PCE12 GitHub-first audit change adds that API. Read back its current signature before use.

## Historical migration reconciliation snapshot (2026-10-07)

The Windows split used old Termux r29 snapshot `d69666da530390146ba093dc1138dc794541b861`.
The old r29 branch later advanced to `249e3bb46c6ea57968d9ecf5157d73867a7f918d`.

That post-split Windows drift is bounded:
- 35 commits after the migration snapshot;
- 63 changed files;
- 4,779 additions / 354 deletions;
- 32 `windows-relay/` files, 5 `consumer/` files, 26 `docs/` files.

Against current Windows `main`, those 63 files classify as:
- 10 already byte-identical;
- 24 divergent and requiring merge/reconciliation;
- 29 absent from Windows and requiring review/import if valid.

These numbers document historical divergence, not an instruction to access the retired repository. If work remains, reconcile only from evidence already transferred into this Windows repository, preserving newer Windows-only work. Do not fetch, check out, or push to Termux.

Detailed move set: `docs/audits/AUDIT_2026-10-07T2034Z_TERMUX_WINDOWS_CONTAMINATION.md`.

## PCE12 verified New Chat interaction — 2026-10-09

PCE12.006 successfully reached a fresh ChatGPT chat; screenshots and operator acknowledgement document the acceptance. Reuse the guarded Windows click method **only after resolving the current New chat location**, since sidebar coordinates change. Details: `docs/acceptance/ACCEPTANCE_2026-10-09T0747Z_PCE12_006_NEW_CHAT_COORDINATE_CLICK.md`. Every emitted ordinal is consumed even if blocked; next is PCE12.007, not a repeat of .006.

## Current high-priority product state

- Result-confirmation selector/role-gate repair: live-proven.
- Browser stop-generation/quiescence protocol: live-proven.
- Rich HUD START/STOP/RESTART/OFF/KILL/MINIMIZE: present in the divergent PCE9 line.
- RETRY: already exists in canonical Windows source and must survive HUD reconciliation.
- Dedicated 8766 `run-control.ps1`: present in divergent PCE9 line and requires canonical reconciliation.
- Full Firefox/Windows restart acceptance: still blocked on the signed persistent Firefox XPI/policy path.
- Chrome/Edge clean-consumer matrix: still open.

## Documentation authority

New maintained source-of-truth docs use descriptive titles plus UTC timestamps in filename and heading.
Untimestamped compatibility names may remain only as small pointers during cleanup.
No file named or titled CURRENT, ACTIVE, LATEST, LOOK HERE, MASTER, or AUTHORITATIVE is allowed to become authority by implication.

Documentation target: <=10 KiB per maintained file. Split sideways by subject/component when the limit is approached.
