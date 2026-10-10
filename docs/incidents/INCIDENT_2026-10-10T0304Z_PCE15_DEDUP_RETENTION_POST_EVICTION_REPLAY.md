# PCE15 — Processed-ID eviction permits post-execution replay — 2026-10-10T0304Z

## Severity and scope

**HIGH, OPEN / source-level exact-once release blocker.** Product remains Grade F / RELEASE BLOCKED. Discovered with PCE15.046 and reproduced by PCE15.047 (corrected follow-on to failed .045 test harness). The backend `State.mark` caps `processed` at 500 and explicitly selects old entries with outbound `SUBMITTED` or `SUBMIT_UNCERTAIN` phase for removal. It also removes entries with no corresponding outbound delivery. However, the `process(packet,state)` duplicate and changed-payload rejection check first examines only `State.lookup(a.id)`, which uses the evictable `processed` mapping. An existing outbound delivery record is not checked prior to calling `execute(a)`.

**Consequence in isolated code execution:** once an old processed-ID is evicted, a repeated packet carrying an old ID can invoke execution again even if a corresponding outbound record survived. For a changed payload and SUBMITTED or SUBMIT_UNCERTAIN delivery, `State.mark` later raises `RelayError('outbound delivery id collision')` only **after** execution already occurred. Thus the late outbound guard does not protect shell/side effects.

This incident is distinct from the already documented non-atomic `lookup` -> `reserve` concurrent race (incident `docs/incidents/INCIDENT_2026-10-10T0250Z_PCE15_NONATOMIC_ACTION_CLAIM_AND_OWNER_GUARD_GAPS.md`). No live shell command was re-executed or ChatGPT message resent in either reproduction. Existing production backend loaded byte identity and loaded Firefox extension identity remain unverified; do not claim active exploitation or user harm.

## Controlled reproduction and test failures

**PCE15.045** Windows command OK/0, three child `JSONDecodeError` failures. Neither restart nor retention results can be credited from that attempt. **PCE15.046** corrected test successfully executed actual AST-extracted `State.load`, `State.lookup`, `State.mark`, `State._mutate_and_save` against in-memory data across GitHub main, development and Client. INFLIGHT becomes INTERRUPTED_RESTART; SUBMITTING becomes SUBMIT_UNCERTAIN; old SUBMITTED, SUBMIT_UNCERTAIN and no-delivery IDs were evicted on cache overflow, while READY was retained. Confirmed outbound record for sent/uncertain remained despite processed cache deletion.

**PCE15.047** isolated actual `extract`, `process`, selected `State` functions, mocked only process effects/governance/persistence, tested 8 scenarios per cohort; all three versions agreed:
- old `SUBMITTED` record: identical-payload retry invokes synthetic execute; changed payload invokes synthetic execute THEN outbound-ID-collision exception;
- old `SUBMIT_UNCERTAIN` record: same behavior;
- old `READY` record: processed ID preserved; identical replay suppressed, changed payload raises `ID_COLLISION` before execute;
- old `NO_DELIVERY`: processed ID evicted; identical and changed payload each invoke synthetic execute.

Child processes executed **zero real shell commands**, touched **zero actual state files**, made **zero HTTP requests**, sent no messages. Governance for dev/Client was an explicitly isolated stub; there was no real bypass of the running relay's operator controls. These tests demonstrate source-level reachability and ordering, **not a live duplicate execution incident**.

## Mitigation design results, failures and limitations

**PCE15.048** proposed identity-ledger diagnostic command **COMMAND_FAILED / exit 1** before its subtests because the authored assertion demanded previous audit checkpoint metadata at a non-multiple-of-five preflight: `AssertionError: PREVIOUS_AUDIT_NOT_ACCEPTED`. Previous [040,044] audit was correctly accepted on .045; .048 consumed with no tests or mutation, and was not retried. **PCE15.049** instead directly verified the prior GitHub audit bytes/SHA-256 and ran isolated prototype across main/dev/Client. Actual sources do **not** contain `operation_identity_ledger`.

The proposed in-memory check is guarded by one lock and searches `processed`, `operation_identity_ledger` and `outbound_deliveries` before claiming or executing. Existing outbound records alone suppress same-payload and reject changed-payload retries when `processed` was evicted. If there is **no outbound record and no ledger tombstone**, the old ID is still CLAIMED—so an independent retained fingerprint is necessary. With a tombstone it returns DUPLICATE or COLLISION. 16 simultaneous identical IDs/payloads: one CLAIMED, 15 duplicates. Mixed-payload: one CLAIMED, 7 duplicates, 8 collisions. Injected save failure rolled in-memory records back and retry succeeded.

**NOT FIXED IN PRODUCTION.** The current ledger is only a synthetic in-memory prototype, never persisted across restart, not implemented in source or Client, untested across multiple backend processes, and not proven with real filesystem atomic transactions, crash windows or ChatGPT send semantics. It is a useful design candidate rather than a release improvement.

## Required fix and acceptance (requires separate change authorization)

1. Preserve an immutable operation ID -> payload fingerprint/terminal-state tombstone independently from bounded display/result cache. Define a safe retention strategy that never forgets an ID capable of replay. If historical identities cannot be reliably retained, fail closed, not assume a missing cache record means never executed.
2. Transactionally check existing processed, outbound, and tombstone records and atomically durably reserve a new ID before any shell side effect. Preserve governance and user STOP controls; no existing reservation may be overwritten. Handle cross-thread and cross-process callers.
3. On same-ID/same-payload return the stored result or explicit inflight/uncertain state without executing again. On same-ID/different-payload return collision **before execute**, even after the processed cache evicts.
4. Cover crash between reserve and execute, execute and persisted result, result persistence and outbound send, sender uncertainty, and restart: never auto-retry a possibly executed command.
5. Test forced concurrency (16+), >500 historical IDs, sent/uncertain/pending/no delivery, payload mismatch, disk-save error, process termination, restart, old-file migration, simulated controlled result-send faults, and compatibility with current browser ownership/cursor guards.
6. After reviewed source fix, independently verify build provenance and installed Client/Firefox behavior; require Mozilla signature and runtime-loaded artifact proof before any production release. Do not run GitHub Actions while credits exhausted.

## Source provenance, protected state and release decision

Verified pre-audit `monag144/GPT-Windows-Relay/main` commit `9bb7ccaedda29e8a72d155291ccd019590fb1ed0`; development checkout branch `pce11/one-click-go-recovery-and-doc-hygiene`, HEAD `a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a`. Normalized Python backend SHA256: GitHub main `be9a326f3ce8d48ce061f53d53cf47f01b0e916556f382b6161270268497638b`; dev `6a4590ddcfcb1742a462591ad7ec168723f2bd173f2323868c2b550d3cbb7957`; Client `c4c1c8b4b2f87a99c9f04328e016770e8ea8f8399f973c517f1da67f2358e4d4`.

Protected PCE12 local and external copies SHA256 `3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab`; historical Client XPI SHA256 `18a5b12032e106118e160c2842e3cbe5d80a2ce01988584414fe09001e47bbe8`. All .045-.049 operations preserved the 32 old untracked paths and modified no tracked source, running Client, Firefox profile, backend state, real shell effects, network or ChatGPT sends. No rollback or data restoration required.

**Incident OPEN / product F, RELEASE BLOCKED, 11/28 gates.** G16 loaded extension unknown, G26 independent live sends 0/60, G27 endurance 0/2. This documentation does not authorize source repair, production migration, user interaction or release. Full five-operation audit `docs/audits/AUDIT_2026-10-10T0304Z_PCE15_045_049_CHECKPOINT.md`. Before PCE15.050 publish/verify/install audit [045,049] through GitHub-first procedure.
