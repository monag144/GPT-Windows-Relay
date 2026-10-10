# PCE15.020–.039 — Actual installed-harness twenty-operation review receipt — 2026-10-10T0233Z

**REVIEW COMPLETE / PRODUCT Grade F / RELEASE BLOCKED.** This name matches the older installed Windows `consumer/control_harness.py` review checkpoint matcher, `REVIEW_*_PCE15_OPERATIONS_020_039.md`, before PCE15.040. Comprehensive graded review: `docs/reviews/REVIEW_2026-10-10T0233Z_PCE15_020_039_GRADING_AND_RELEASE_GATE.md`. Underlying mandatory audits:
`docs/audits/AUDIT_2026-10-10T0154Z_PCE15_OPERATIONS_020_024.md`;
`docs/audits/AUDIT_2026-10-10T0206Z_PCE15_OPERATIONS_025_029.md`;
`docs/audits/AUDIT_2026-10-10T0220Z_PCE15_OPERATIONS_030_034.md`;
`docs/audits/AUDIT_2026-10-10T0233Z_PCE15_OPERATIONS_035_039.md`.

| Numbered attempt | Execution result | Independent diagnostic observation, not product gate |
|---|---|---|
| **PCE15.020** | OK | 8766 backend Client launch, 8767 absent; loaded runtime unknown. |
| **PCE15.021** | OK | 15/19 selected Client files historical match; four unexplained Client control-file divergences. |
| **PCE15.022** | OK | No exact provenance for those four across examined Git refs/path histories. |
| **PCE15.023** | OK | 49 recognized backups/snapshots, no complete matching origin. |
| **PCE15.024** | OK | Valid syntax/static control file comparison; provenance still unknown. |
| **PCE15.025** | OK | Two missing temporary popup assets in 38-file deploy allowlist; 10 obsolete XPI backups. |
| **PCE15.026** | OK | XPI 15 members (five active, ten .bak), three active asset drifts; wildcard bundling risk. |
| **PCE15.027** | OK | XPI lacks alarms/tabs permissions and matching current feature API references. |
| **PCE15.028** | OK | Client/development worker alarms/tabs methods absent XPI; no runtime assertion. |
| **PCE15.029** | OK | XPI packaged content/worker exact blobs not found in examined reachable Git history. |
| **PCE15.030** | OK | Three deterministically reproducible in-memory clean five-member ZIP candidates, no deployment/signing. |
| **PCE15.031** | OK | All four extension variants have 17 feature strings while actual script hashes differ. |
| **PCE15.032** | OK | Static origin/owner/cursor guard patterns 19/19 main/dev/Client, 0/19 existing XPI. |
| **PCE15.033** | OK | Firefox 2 discovered profiles, 19 registered addons in one, no relay ID; profile binding unknown. |
| **PCE15.034** | OK | No relay UUID mapping among 31 keys; startup cache and profile lock not live identity. |
| **PCE15.035** | OK **with decoder subtask FAILED** | Firefox cache LZ4 decoder skipped four-byte size field, reported ValueError. Failure fully acknowledged. |
| **PCE15.036** | OK | Corrected in fresh ordinal; decoded 16,666-byte JSON/213 objects with zero relay matches; temporary installs possible. |
| **PCE15.037** | OK | 21 Firefox processes, one executable, no conventional enterprise Firefox policies/flags. |
| **PCE15.038** | OK | Only Client historical XPI found; 10 backups, zero signature metadata; signed output missing at expected paths. |
| **PCE15.039** | OK | Local listener `127.0.0.1:8766`, Python PID 10684, Client script argv, on-disk backend diverges from main/dev; loaded module unverified. |

**Accountability:** all twenty command receipts `OK` exit zero with installed preflight `ok=true` and `mutation_authorized=false`. One genuine decoder subtask failure at .035, corrected at .036; not a rerun. No numbered attempts discarded or skipped, no manual rescues, product code changes, Git commits by Windows, browser sends, package signing, Firefox installation, Client deployment, HTTP tests, or new integrated test suite. No rollback necessary/performed.

**Grade:** strict existing **11/28 qualifying evidence gates = 39.29%, Grade F / RELEASE BLOCKED**. G04 source/deploy/runtime parity FAIL, G16 loaded Firefox/owner identity UNKNOWN, G26 independently witnessed user-role sends **0/60**, G27 unattended endurance windows **0/2**, CI historical and exhausted credits. Historical isolated 98/98 unit tests do not qualify. Even if a binary has all 17 advertised feature markers or 19 lexical guards, **that is not proof Firefox loaded it or a message safely delivered**.

**Evidence and protected state:** before new current-window docs, Windows checkout remained dev HEAD `a431cb6cbb7a5b712e5a1cfa022ef1b84ced4a`, 25 expected untracked files (24 GitHub docs and protected local PCE12 audit). Original local PCE12 and external copy SHA256 `3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab`. Client existing 51,439-byte XPI SHA256 `18a5b12032e106118e160c2842e3cbe5d80a2ce01988584414fe09001e47bbe8`. Do not clean/reset/stash, overwrite protected files or deploy while audit.

All installed required local control SHA256 unchanged:
- `consumer/control_harness.py` `76d13b46ddc0289291a7bc155785c0b160d55751c4d1b515ea44db3f4bc6d883`
- `windows-relay/TASKS.md` `cd62fda22cff02d5f813bd81db3707bfd999ae7567a05be8076aa357e1cb3055`
- `docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md` `a2c2a4c0708432ee9325a21a65a9c6f9ea814399fa02a84849592fcedd9092ce`
- `docs/windows-relay-established-facts.md` `b1590bab9ca5b79a1182a4418f9fdc2c1b488a0154b286701d08ba8661545b2a`
- `docs/relay-sandwich-procedure.md` `8d9941f598a9e4154f83261081e483b022a590c63eb5bd832fbab5107b56d27f`

Canonical GitHub base `683199401667e88e0cf42f98dc1fa0adecfca312`, no GitHub Actions. **Before PCE15.040**, publish both .035–.039 audit docs and both .020–.039 review docs, PR inspect/merge, verify exact paths and blob SHA from `main`; perform SHA-pinned documents-only GOVSYNC preserving 25 previous files; require installed `engineering_preflight(R,40,series=15)` to explicitly accept audit [35,39] and review [20,39]. A failed governance sync never consumes a numbered ordinal. **REVIEW COMPLETE; product blocked.**
