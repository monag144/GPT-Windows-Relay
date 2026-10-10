# PCE15.000–.019 — Mandatory twenty-operation engineering review — 2026-10-10T0141Z

## Scope, precedence and review disposition

Canonical repository `monag144/GPT-Windows-Relay`, GitHub `main`; prior verified review-base commit `2d8fa5e4fba4f6633a9608658b505fa19e8a529e` (rollback reference). Session `pce15.1`. **This is the required 20-attempt review before PCE15.020; it is NOT a product repair or authorization to send/deploy.**

Readback-verified five-operation source audits:
- `docs/audits/AUDIT_2026-10-10T0005Z_PCE15_000_004_CHECKPOINT.md` (GitHub blob `fec93e34015a7cfa8d556dce63b3be0c81dda03c`)
- `docs/audits/AUDIT_2026-10-10T0118Z_PCE15_005_009_CHECKPOINT.md` (blob `60c787b84393098be59916ad3e8cf049da00c6f5`)
- `docs/audits/AUDIT_2026-10-10T0127Z_PCE15_010_014_CHECKPOINT.md` (blob `95cd5be8428e63af6eb7eb0aade5addcbd53e0fd`)
- `docs/audits/AUDIT_2026-10-10T0136Z_PCE15_015_019_CHECKPOINT.md` (blob `3bb3704039f13404b35f44934f49efb3179d440b`).

Each audit also has an installed-harness-compatible `_PCE15_OPERATIONS_NNN_NNN.md` companion. Review the actual Windows command receipts for exact details; this review preserves classification rather than replacing them. All numbered PCE15.000–.019 attempts are accounted for; **PCE15.020 has NOT been issued**.

## Twenty-slot ledger: attempted, succeeded, failed, or blocked

| Ordinal | Observed outcome | Truthful completed/blocked acceptance |
|---|---|---|
| **PCE15.000** | `COMMAND_FAILED`, exit 1 | Incorrect assumption that local harness used the newer GitHub preflight signature. Installed signature actually `engineering_preflight(repo_root, ordinal, series=11)`. Invocation failed before preflight; no source mutation. **FAILED/CONSUMED**. |
| **PCE15.001** | OK/0 | Correct historical preflight; PCE14.029 durable result recovered; headless 75/75 test evidence, not GUI send. |
| **PCE15.002** | OK/0 | Recovered and audited PCE14.025–.029 unique results; headless-inner fallback at .029; earlier readiness failures retained. |
| **PCE15.003** | OK/0 | Isolated pinned Windows suite 98/98 (12.653 sec); 28-gate strict grader: 11 PASS, 7 FAIL, 10 UNPROVEN; 39.29% qualifying, **F/blocked**. |
| **PCE15.004** | OK/0 | Local port 8766 listener reachable with unauthenticated status 401 (expected); port 8767 unreachable at that instant; 3/3 source mirrors and 3/3 Client mirrors agree internally, but **source/Client differ**. Shallow UIA census inconclusive. |
| **PCE15.005** | OK/0 | Two same-PID Firefox windows; 9 foreground canonical TabItems, 1 selected; 1 secondary canonical, 1 selected. No originating-tab attestation. |
| **PCE15.006** | OK/0 | Both selected tabs are ChatGPT conversation URL classes; foreground two New Chat controls, one composer and one Send candidate. No originating tab verification. |
| **PCE15.007** | OK/0 | One visible actionable foreground New Chat of two matches; secondary none; enabled Send control actually hidden. No click. |
| **PCE15.008** | OK/0 | 3/3 stable read-only UIA snapshots of one visible `InvokePattern`-capable New Chat. Not three sends; no invocation or independent role receipt. |
| **PCE15.009** | OK/0 | True source vs deployed content-script drift: source 122,272 bytes/3,022 CRLF lines vs Client 103,925 bytes/2,746 LF lines; loaded code UNKNOWN. |
| **PCE15.010** | OK/0 | Raw source/Git HEAD anomaly explained: `core.autocrlf=true`, normalized LF source equals indexed Git blob for all 3 content.js files. Source checkout healthy. |
| **PCE15.011** | OK/0 | Deployed content.js Git blob `8a3232b521ee99640633318bcbe23aa1edfedbd1` matches historical commit `b0a01eef1b2c19b498195d7318541782904d6c8f`; not either current branch tip. |
| **PCE15.012** | OK/0 | Development and main diverged at `94de291a3173b04ef23a6575e562edd8e8156993`: 569 development-only commits, 20 main-only, 466 tip-different paths (at time of test). |
| **PCE15.013** | OK/0 | Eight independently changed overlapping paths from common base; 429 local-only path changes, 29 main-only. Path overlap not a proven merge conflict. |
| **PCE15.014** | OK/0 | Isolated three-way `git merge-file --diff3` on eight files: seven textual conflicts, one clean `windows-relay/README.md`. No real merge. |
| **PCE15.015** | OK/0 | Legacy read-only full-tree merge-tree: eight `changed in both` regions, seven heuristic conflict markers despite exit 0; not merge-success proof. |
| **PCE15.016** | OK/0 | Selected executable/config tree census: 166 source and 970 Client files; 77 shared = 31 byte equal + 15 LF-only + 31 true drift, plus 89 source-only and 893 Client-only. Do not delete unclassified historical Client assets. |
| **PCE15.017** | OK/0 | Local deploy allowlist 38 vs GitHub main 26; 17 true-drift allowed files; `extension/popup.html` omitted despite manifest reference. Existing sync edits live Client and replaces tests before running unit tests, with no explicit automatic rollback or atomic swap. |
| **PCE15.018** | OK/0 | 18 readable named XPI archives. Two Firefox profile extension-registration metadata files yield zero relay entries. Source/Client JS mismatches, loaded runtime/script SHA and signature validity **UNKNOWN**, not evidence that no relay runs. |
| **PCE15.019** | OK/0 | Persistent XPI `0.3.17` CRC valid; 5 examined required assets, **3 mismatch current source and Client** (manifest/content/service_worker), 2 popup assets match. Reproducibility gate **FAIL**. No build, reload, installation or send. |

**Operation execution tally: 19 OK/0, one COMMAND_FAILED (.000); no missing ordinal.** This is a count of diagnostic execution outcomes only. **Zero certified live ChatGPT message sends** in this review period. No source remediation was performed or required for a diagnostic PASS.

## Grade, trajectory and evidence gaps

Historical pinned independent strict benchmark `benchmarks/RELAY_STRICT_GRADES_2026-10-09T2258Z.json`, feature SHA `3503f40b2a52a4e62963084181b534dd726005ff`: **11/28 strict gates pass threshold = 39.29%, Grade F, RELEASE BLOCKED**. That ratio is evidence sufficiency, not estimated delivery success. G02 first-attempt audit timing 4/5; **G04** source/deployed/loaded runtime parity FAIL; **G05** GitHub Actions run `38002768072` failed even though the isolated .003 Windows 98/98 suite passed (no CI rerun, credits exhausted); **G15** historical headless readiness 1/4 = 25%, still not GUI acceptance; **G16** originating-tab/window identity unverified. G17–G25 and G28 end-to-end capabilities remain unproven; **G26 0/60** independently witnessed real behavioral traces; **G27 0/2** distinct 12h/24h unattended endurance windows. New investigations clarify what fails, but **do not promote strict scores without a new fully supported graded run**.

No actual authenticated initiating Firefox tab, independent user-role send readback, STOP/exact-once real canary, installed/signed persistent extension, loaded in-memory content-script identity, or rollback-backed coherent deployment has been proved. Unit suites and UIA control discovery must never be counted as live sends.

## Repeated approaches, incidents, rollbacks, manual rescue

Documented open incidents: PCE15.000 installed/newer preflight invocation mismatch (handled by correct invocation at .001, no source change); .009 source vs Client content drift, with apparent Git raw-byte HEAD mismatch subsequently **resolved as CRLF-only at .010**; .014 seven conflicting shared-file merges; .017–.019 non-atomic deployment script and 3/5 persistent XPI package asset divergence. All are evidence/architecture observations and/or fixed invocations; none permits a live fix during grading.

GOVSYNC15 attempts were **documentation-only** and never counted as PCE15 ordinal slots. The most recent `GOVSYNC15-AUDIT-015-019-20261010-01` returned `COMMAND_FAILED` after **successfully SHA-verifying and creating all three newly published audit/incident docs** from GitHub `main` commit `2d8fa5e4fba4f6633a9608658b505fa19e8a529e`: its subsequent `engineering_preflight(R,20,series=15)` failed **`review checkpoint missing before PCE15.020: PCE15.000-.019`**. This is an authentic **mandatory twenty-slot review gate**, not a five-slot audit failure. Earlier plan incorrectly anticipated approval based only on five-slot audits; recover by creating this review, not bypassing harness or repeating issued PCE15 IDs. Last sync verified protected old docs before the failing preflight, but its last postcondition statements were **not reached**; next GOVSYNC must independently recheck integrity rather than claim an unprinted end-state proof. Local HEAD remained unchanged through preceding checkpoints; verify again.

No operator manual Firefox tab switching, manual resend, clipboard interaction, or recovery of side-effecting browser commands is documented in .000–.019. The user returned command receipts to the assistant; that is not proof of autonomous recovery. No rollback performed for these **read-only** tests. Preserve source baseline `a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a`, GitHub prior audit main `2d8fa5e4fba4f6633a9608658b505fa19e8a529e`, and persistent untracked audit/incident documentation.

## File preservation, controls and prioritization

Untracked protected PCE12 audit `docs/audits/AUDIT_2026-10-09T0808Z_PCE12_OPERATIONS_010_014.md` and backup `%LOCALAPPDATA%\GPTWindowsRelay\ops\GOVSYNC13-AUDIT-RESTORE-20261009-01\PCE12_010_014_preserved.md` SHA256 `3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab`; **never reset, clean, stash, overwrite or delete**. Five local harness controls SHA256: `consumer/control_harness.py` `76d13b46ddc0289291a7bc155785c0b160d55751c4d1b515ea44db3f4bc6d883`, `windows-relay/TASKS.md` `cd62fda22cff02d5f813bd81db3707bfd999ae7567a05be8076aa357e1cb3055`, dated roadmap `a2c2a4c0708432ee9325a21a65a9c6f9ea814399fa02a84849592fcedd9092ce`, established facts `b1590bab9ca5b79a1182a4418f9fdc2c1b488a0154b286701d08ba8661545b2a`, sandwich procedure `8d9941f598a9e4154f83261081e483b022a590c63eb5bd832fbab5107b56d27f`.

Reprioritized roadmap after reviewing twenty attempts: (1) finish GitHub review/checkpoint and verified local governance preflight **without product mutation**; (2) remaining read-only active runtime ownership and loaded extension identity, exact originating-tab identity; (3) source reconciliation of seven conflicts **through a reviewed GitHub development branch**, preserving modern governance and tests; (4) release-manifest completeness, staged tests, atomic/transactional backup+rollback, code/signature attestation and safe promotion; (5) real STOP/idempotent send/role-readback canaries and 60 trace + 12h/24h endurance campaign to >90% per gate. User specifically prefers **GitHub source-build → SHA-pinned guarded Windows pull → tests → GitHub repair → verified pull**, not piecemeal direct Client edits. In the current grading-only period **no product fixes/deployments are approved**.

**Review state: COMPLETE on the evidence, PRODUCT BLOCKED/F.** Commit/review/merge/readback both this full timestamped review and the companion historical filename `REVIEW_2026-10-10T0141Z_PCE15_OPERATIONS_000_019.md` via connected GitHub connector. Add a separate short GOVSYNC missing-review incident, then documentation-only SHA-pinned Windows sync; obtain actual installed `engineering_preflight(R,20,series=15)` with both audit and review checkpoints present and `ok=true` before attempting PCE15.020. Do not mark governance gate passed prematurely.
