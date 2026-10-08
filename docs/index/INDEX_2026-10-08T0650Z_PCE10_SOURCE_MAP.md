# PCE10 Windows Relay source map — 2026-10-08T0650Z

## Engineering entry point
- Repository: `monag144/GPT-Windows-Relay`.
- Default/release baseline: `main@94de291a3173b04ef23a6575e562edd8e8156993`.
- Working engineering branch: `pce10/reconcile-control-and-rotation@5dac27c28a4bf927e0c8cfa7fb7ab9733708227b` at inventory time.
- Do not edit Windows source in the former Termux repository or directly patch live files as normal procedure.
- GitHub edit/commit/remote SHA -> Windows relay fast-forward pull -> targeted/full source tests -> STOP/backup/identity gate -> safe canary -> promotion.

## Read these BEFORE any PCE10.038 Windows or Firefox activity
1. `docs/handoffs/HANDOFF_2026-10-08T0635Z_PCE10_037_TO_NEXT_AGENT_FIREFOX_IDENTITY.md`.
2. `consumer/control_harness.py` and `windows-relay/TASKS.md`.
3. `docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md` and `docs/windows-relay-mission-and-roadmap.md`.
4. `docs/relay-sandwich-procedure.md`.
5. `docs/windows-relay-established-facts.md` for historical Oct 2–3 Firefox UIA/profile/addon observations; NOT current identity evidence.

## One-line checkpoint
**PCE10.035 SOURCE GREEN; PCE10.036 rollback backups SHA-verified; PCE10.037 Firefox exact-conversation resolver zero matches; LIVE ACTIVATION BLOCKED; next unique operation PCE10.038 read-only identity diagnosis.**

## Where the audit is
- `docs/audits/AUDIT_2026-10-08T0650Z_BRANCH_BUILD_CONTAMINATION_AND_REDUNDANCY.md` — counts, contaminated history, live drift, preserved mirrors.
- `docs/audits/AUDIT_2026-10-08T0720Z_PCE0_PCE10_LINEAGE_AND_PROVENANCE_GAPS.md` — PCE0–PCE10 work ancestry, retained features and **pre-migration history gaps**; the Windows repo's commit count does not represent the full project history.
- `docs/audits/CLEANUP_2026-10-08T0650Z_DOCUMENT_DELETION_LOG.md` — actual removals and documentation debt.
- Legacy status catalog: `docs/index/INDEX_2026-10-07T2034Z_DOCUMENT_CATALOG.md` (frozen, not current totals).

## Known historical Firefox facts to REUSE
- Development temporary add-on previously identified as `55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon` in profile `3awtt83g.default-release`; this is historical, not a current-session identity.
- Old automation exists in `consumer/browser_manager.py`, `consumer/recovery_supervisor.py`, `windows-relay/firefox_adapter.py`, `windows-relay/firefox_tab_adapter.ps1`, the extension worker and watchdog scripts.
- Temporary Firefox addons disappear after a full browser exit; signed persistent XPI/policy is still needed for unattended full Firefox restart.
- PCE10.037 failure is exact target discrimination, not proof Firefox is closed. Do not retry a guessed URL, reopen the investigation, refresh blindly or replay resultless IDs .018/.021/.025.
