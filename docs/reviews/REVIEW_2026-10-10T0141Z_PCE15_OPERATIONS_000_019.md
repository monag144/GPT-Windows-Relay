# PCE15.000–.019 — Installed-harness twenty-operation review compatibility record — 2026-10-10T0141Z

**REVIEW COMPLETE / PRODUCT BLOCKED, Grade F.** This is the required filename-matched companion for the older installed `consumer/control_harness.py`, whose PCE15.020 review matcher scans `docs/reviews/REVIEW_*_PCE15_OPERATIONS_000_019.md`. The complete evidence-backed review is `docs/reviews/REVIEW_2026-10-10T0141Z_PCE15_000_019_GRADING_AND_RELEASE_GATE.md`; four underlying five-operation audits are already verified on `monag144/GPT-Windows-Relay/main`. The matching filename does not bypass the original harness: it provides the missing evidence it requires.

| Attempt | Result | Independent evidence class |
|---|---|---|
| **PCE15.000** | COMMAND_FAILED | Historical preflight API signature mismatch; consumed, no mutation. |
| **PCE15.001** | OK | PCE14.029 headless receipt recovery. |
| **PCE15.002** | OK | PCE14.025–.029 receipt integrity census. |
| **PCE15.003** | OK | Isolated 98/98 tests; strict 11/28 gates, F / BLOCKED. |
| **PCE15.004** | OK | 8766 healthy snapshot; 8767 unreachable; source/Client content drift. |
| **PCE15.005** | OK | Two Firefox windows, 9 + 1 canonical tabs. |
| **PCE15.006** | OK | Selected conversation URL classes, New Chat and composer detection. |
| **PCE15.007** | OK | One foreground visible New Chat, Send hidden. |
| **PCE15.008** | OK | Stable read-only New Chat InvokePattern 3/3, no invoke/send. |
| **PCE15.009** | OK | Genuine source/Client content-script divergence. |
| **PCE15.010** | OK | Working source/Git HEAD discrepancy is normal CRLF normalization. |
| **PCE15.011** | OK | Client script maps to historical `b0a01eef1b2c...` Git commit. |
| **PCE15.012** | OK | Development and main diverge 569 vs 20 commits, 466 tip paths. |
| **PCE15.013** | OK | Eight shared changed paths among branch-exclusive changes. |
| **PCE15.014** | OK | Seven text conflicts, one clean file-level merge. |
| **PCE15.015** | OK | Legacy full-tree merge conflict markers corroborate 7 regions. |
| **PCE15.016** | OK | Source/Client executable file census finds 31 genuine shared drifts. |
| **PCE15.017** | OK | Deployment 38/26 allowlists; deploy-before-test, rollback deficiency. |
| **PCE15.018** | OK | 18 XPI archives, registered relay / loaded runtime identity unproven. |
| **PCE15.019** | OK | XPI 0.3.17 five sampled assets, 3 mismatched; release FAIL. |

This is 19 diagnostic `OK` results and 1 `COMMAND_FAILED`; **0 confirmed real user-role sends, 0 deployed repairs**. Existing pinned score **11/28 qualifying gates (39.29%), Grade F / RELEASE BLOCKED**; G26 0/60 traces, G27 0/2 endurance periods. No new measured improvement to claim.

**Extra governance incident:** `GOVSYNC15-AUDIT-015-019-20261010-01` successfully verified/installed all three preceding audit documents but then failed `engineering_preflight(R,20,series=15)` with `review checkpoint missing before PCE15.020: PCE15.000-.019`. This GOVSYNC ID is NOT an ordinal and does NOT consume PCE15.020. Do not repeat or relabel the command. No final postcondition assertions were printed; independently reverify protected evidence next sync.

Keep `docs/audits/AUDIT_2026-10-09T0808Z_PCE12_OPERATIONS_010_014.md` and its external backup SHA256 `3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab` intact. Never clean, reset, overwrite or stash these untracked assets. GitHub original review base `2d8fa5e4fba4f6633a9608658b505fa19e8a529e`. Product fixes remain blocked during grading.

Only after connected GitHub commit/PR/merge/verified-main readback, guarded documentation-only Windows sync, and successful actual installed `engineering_preflight(R,20,series=15)` reporting **both audit and review checkpoint records** may the first and only PCE15.020 packet be issued.
