# PCE15.020–.039 — Twenty-operation engineering review and graded release gate — 2026-10-10T0233Z

## Review basis and source provenance

Canonical `monag144/GPT-Windows-Relay/main`; independently verified pre-review base `683199401667e88e0cf42f98dc1fa0adecfca312`. This GitHub-only review is for session `pce15.1`, inclusive ordinals .020–.039, with **four** independently documented five-operation windows: `AUDIT_2026-10-10T0154Z_PCE15_OPERATIONS_020_024.md`, `AUDIT_2026-10-10T0206Z_PCE15_OPERATIONS_025_029.md`, `AUDIT_2026-10-10T0220Z_PCE15_OPERATIONS_030_034.md`, `AUDIT_2026-10-10T0233Z_PCE15_OPERATIONS_035_039.md`. The last is published in same reviewed PR as this review; older three are already independently merged, GitHub readback-verified and synchronized to Windows with SHA pins.

Target actual old Windows installed harness at `consumer/control_harness.py` has twenty-operation review requirement before .040. This full review is accompanied by filename-compatible `docs/reviews/REVIEW_2026-10-10T0233Z_PCE15_OPERATIONS_020_039.md` for its pattern matcher. **Do not send PCE15.040** until GitHub PR review/merge/readback of both review documents and both current audit documents, verified docs-only local synchronization with preservation, and installed `engineering_preflight(R,40,series=15)` passing both [35,39] audit and [20,39] review. GitHub Actions CI credit exhausted: no CI trigger.

## Twenty-operation ledger: attempted, observed, credited

| Ordinal | Receipt | Principal bounded observation |
|---|---|---|
| **PCE15.020** | OK / 0 | Actual listener on 8766 is Python launched from deployed Client backend; no 8767 listener. Loaded JavaScript unknown. |
| **PCE15.021** | OK / 0 | 19 examined dev source vs Client files; 15 Client files matched a historical Client Git commit, four Client control files unmatched by tested source snapshots. |
| **PCE15.022** | OK / 0 | Across 18 local reachable refs, no exact historical Git blob found for four Client control files: `hud.py`, `relay-control.ps1`, `relay-watchdog-loop.ps1`, `sync-live.py`. Search not exhaustive of unreachable Git. |
| **PCE15.023** | OK / 0 | 49 recognized local Client/backup snapshots scanned, no exact matching provenance for those four files. No restore or deletion. |
| **PCE15.024** | OK / 0 | Static diff/syntax comparison bounded four Client control divergences; provenance unresolved. |
| **PCE15.025** | OK / 0 | 38-file deployment allowlist omitted temporary extension popup.html and popup.js; five persistent active assets included. Existing XPI 15 members vs five source active files; deployment tests may be overwritten before pass. |
| **PCE15.026** | OK / 0 | Client XPI SHA256 `18a5b12032e106118e160c2842e3cbe5d80a2ce01988584414fe09001e47bbe8`; 10 backed-up .bak files (63,465 uncompressed bytes) accidentally eligible for packaging by directory-wide recipes. Three of five live package assets mismatch Client and development. |
| **PCE15.027** | OK / 0 | Client/development manifest `activeTab,alarms,storage,tabs`; existing XPI `activeTab,storage`; source/XPI API references differ. Not automatic proof of runtime permission failure. |
| **PCE15.028** | OK / 0 | Current dev/Client worker methods `alarms.clear/create/onAlarm`, `tabs.get/query/reload` absent from packaged worker; XPI worker 204 lines, dev 448, Client 413. Static only. |
| **PCE15.029** | OK / 0 | Packaged manifest and two popup files match some historical Git blobs; packaged content.js/service_worker.js match none examined. No complete five-file matching historical commit among two candidates. Non-exhaustive search. |
| **PCE15.030** | OK / 0 | Three clean in-memory fixed five-file XPI candidates, deterministic two builds each; main 29,267B, dev 37,947B, Client 33,646B; all CRC/pass and no .bak. None reproduces existing XPI. No signed/install artifact. |
| **PCE15.031** | OK / 0 | Four code variants share all 17 content feature labels yet bytewise differ. GitHub main's `tabs.query` reference without broad `tabs` permission is **not inherently an error**; source worker also uses sender tab URL with authorization context unverified. |
| **PCE15.032** | OK / 0 | 19/19 static owner/conversation/cursor guard patterns in main/dev/Client, 0/19 in existing XPI. Five sampled guard function hashes equal main/dev but differ Client; none proves loaded Firefox code. |
| **PCE15.033** | OK / 0 | 20 Firefox processes, 2 profiles discovered, 19 registered add-ons in one, no relay ID/installed extension match; zero process-to-profile binding. |
| **PCE15.034** | OK / 0 | Zero relay identity candidates in registry/31 UUID map keys. One 5,775B Firefox startup cache plus lock indicator, not live identity evidence. |
| **PCE15.035** | OK / 0; **decoder subtask FAIL** | Attempted startup cache LZ4 at offset 8 rather than after four-byte size at offset 12; reported `ValueError` and `DECODE_FAILED` despite good `mozLz40` signature. No data inferred from failed decode. |
| **PCE15.036** | OK / 0 | Corrected offset, valid 16,666-byte JSON decoded, 213 objects, no relay-related metadata entries. Does NOT rule out temporary add-on or prove loaded Firefox identity. |
| **PCE15.037** | OK / 0 | 21 Firefox processes with single Firefox executable, zero explicit debug/profile flags; checked distribution, autoconfig files and enterprise registry policy keys absent. |
| **PCE15.038** | OK / 0 | Four expected signing artifact paths, only Client 51,439B XPI present; contains 10 .bak and **zero signature metadata**. No signed XPI found or default enterprise policy. No cryptographic signature test and no signer/installer run. |
| **PCE15.039** | OK / 0 | Loopback listener `127.0.0.1:8766` Python PID 10684 parent 15820 launched via Client script, no 8767. Client on-disk backend hash differs GitHub main and development; loaded process module bytes not attested. |

**Status accounting:** **20/20** operations returned execution `OK` and exit zero with preflight acceptance; **one functional diagnostic subtask failed** in .035 before corrected in .036. No independent runtime integration/pass, product repairs, version reconciliation or release authorization. No skipped or reused operation ordinals.

## Source drift and packaging findings

- Canonical GitHub main `683199401667...` vs development HEAD `a431cb6cbb7a5...` vs deployed Client disagree on several critical files. Main/development and Client extension content/worker hashes differ; historical XPI also differs. All four variants advertise 17 static feature markers and v0.3.17, which proves neither matching functionality nor deployed byte parity.
- Client `windows_relay.py` normalized SHA256 `c4c1c8b4b2f87a99c9f04328e016770e8ea8f8399f973c517f1da67f2358e4d4`; main `be9a326f3ce8d48ce061f53d53cf47f01b0e916556f382b6161270268497638b`; dev `6a4590ddcfcb1742a462591ad7ec168723f2bd173f2323868c2b550d3cbb7957`. Process argv Client launch evidence ≠ loaded module proof.
- Known deploy recipe excludes two temporary extension popup dependencies and packages extra persistent .bak files. Signed release artifact unproven: inspected Client XPI carries no META-INF signature members and includes all 10 historical backups; four candidate location search found no signed output. Do not infer malicious origin or exposed secrets from unexplained bytes.
- Firefox registration metadata, UUID map, corrected startup cache, conventional enterprise policy and launch flags do not identify the running extension. There is no active-profile process binding. A temporary about:debugging extension remains viable; **zero matching metadata is NOT proof of no extension.** G16 cannot be promoted.

## Strict release grading and roadmap implications

Pinned **11/28 evidence gates passing = 39.29%, Grade F / RELEASE BLOCKED**. Significant unclosed gates include **G04 source/deployment/runtime parity FAIL**, historical CI currency unavailable (credits exhausted), G16 originating tab identity UNKNOWN, G26 **0/60** independent actual user-role ChatGPT sends, G27 **0/2** unattended 12h/24h endurance periods. Historical isolated 98/98 tests do not satisfy these. No numerical gain in 20 operations despite meaningful forensic clarity. 38 of 100 numbered ordinal budget used through .038; 40 assigned inclusive .000–.039 (including earlier PCE15.000 failed preflight). Before .040, 60 potential future ordinals through .099 plus .100 allowed by governance, not a substitute for readiness.

Recommended safe critical path: attest actual loaded Firefox extension and originating conversation by approved read-only observation; reconcile source in reviewed GitHub branch, package from immutable five-member manifest excluding backups, verify permission/crypto signing, test before atomic deploy with rollback. Only after explicit change authorization perform integration real-send and endurance gates. Do not trigger GitHub Actions or mutate Client while grading.

## Incidents, evidence preservation, rollback, manual action

Covered incidents: `docs/incidents/INCIDENT_2026-10-10T0154Z_PCE15_FOUR_CLIENT_FILES_UNVERIFIED_ORIGIN.md`; `docs/incidents/INCIDENT_2026-10-10T0206Z_PCE15_XPI_RELEASE_REPRODUCIBILITY_AND_PACKAGE_HYGIENE.md`; `docs/incidents/INCIDENT_2026-10-10T0220Z_PCE15_FIREFOX_LOADED_EXTENSION_IDENTITY_UNVERIFIED.md`. Corrected decoding defect in PCE15.035 expressly acknowledged; PCE15.036 used a new ordinal, not a replay. No other failed numbered commands, unknown receipts, human manual rescues or incident suppression.

Every operation preserved tracked worktree, original Client XPI (SHA256 `18a5b12032e106118e160c2842e3cbe5d80a2ce01988584414fe09001e47bbe8`), two protected PCE12 copies SHA256 `3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab`, and preexisting untracked audit artifacts. Untracked scope rose only via controlled, GitHub-first unnumbered docs-only GOVSYNC (19→22→25); as of PCE15.039 **25 expected** (24 GitHub docs plus protected PCE12). No product Git edit, Client deployment, XPI rebuild/signing, browser interaction, HTTP send, clipboard use, destructive clean/reset/stash or profile mutation. **No rollback was required or performed.**

The actual installed five local governance files retained SHA256:
`consumer/control_harness.py` 76d13b46ddc0289291a7bc155785c0b160d55751c4d1b515ea44db3f4bc6d883;
`windows-relay/TASKS.md` cd62fda22cff02d5f813bd81db3707bfd999ae7567a05be8076aa357e1cb3055;
`docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md` a2c2a4c0708432ee9325a21a65a9c6f9ea814399fa02a84849592fcedd9092ce;
`docs/windows-relay-established-facts.md` b1590bab9ca5b79a1182a4418f9fdc2c1b488a0154b286701d08ba8661545b2a;
`docs/relay-sandwich-procedure.md` 8d9941f598a9e4154f83261081e483b022a590c63eb5bd83261081e483b022a590c63eb5bd832fbab5107b56d27f.

**REVIEW COMPLETE for 20 read-only diagnostics / product still F / BLOCKED.** Before .040, publish/merge/readback this full review and companion compatibility record plus five-op audit and compatible receipt. Pin main commit/blob SHA and synchronize docs alone, preserve protected copies, then require actual installed PCE15.040 preflight acceptance of audit and review. Never infer an accepted product release from governance pass.
