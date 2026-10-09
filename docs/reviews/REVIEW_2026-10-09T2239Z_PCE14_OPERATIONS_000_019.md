# PCE14 twenty-operation engineering review — operations .000–.019 — 2026-10-09T2239Z

## Reviewed authority / outcome
Canonical `monag144/GPT-Windows-Relay` engineering branch `pce11/one-click-go-recovery-and-doc-hygiene`. **REVIEW COMPLETE, not a release approval.** PCE14 slots .000 through .019 each attempted once, with one **GOVERNANCE_BLOCKED before command reservation (.005)**, successful read-only or isolated-test commands in the other 19 numbered slots, and two native MSAA diagnostic **inner** failures (.015/.016) resolved with a changed standard-interop method (.017). GitHub feature PR #10 remains draft and unmerged. Never claim these operations completed an autonomous live ChatGPT roundtrip.

## Exact slot coverage for mandatory harness checkpoint
- `PCE14.000`: canonical source/evidence preflight PASS; verified protected untracked PCE12 audit and backup.
- `PCE14.001`: listener 8766 PID 10684 TCP PASS; unauthorized 401 expected; 8767 not listening.
- `PCE14.002`: found pinned working PowerShell sender script and launcher; verbose output truncated.
- `PCE14.003`: working script source inspected; output truncated; source read only.
- `PCE14.004`: sender source extraction repeated with output truncated; no script execution.
- `PCE14.005`: **GOVERNANCE_BLOCKED** audit not present locally before pre-dispatch; no executable action reserved. Documented incident; unnumbered narrowly controlled GOVSYNC recovered checkpoint. Do not replay this operation ID.
- `PCE14.006`: verified clipboard, window activation, coordinate New Chat, composer click, Ctrl+V, Enter algorithm; no execution.
- `PCE14.007`: pinned isolated benchmark regression run **33/33 PASS**; no live trial.
- `PCE14.008`: live listener healthy; three canonical content.js hashes internally equal and three Client deployed hashes internally equal, but **source-to-Client mismatch FAIL**; loaded Firefox script identity unknown.
- `PCE14.009`: found **two visible Firefox windows** under PID 5692; first-process window selection ambiguous.
- `PCE14.010`: current selection matched foreground HWND `19466700`, but not uniquely established or tab-bound.
- `PCE14.011`: 11 additional targeting negative scenarios, **44/44 PASS** offline suite.
- `PCE14.012`: 7 independent UIA probe tests, **51/51 PASS** offline; native UIA 39 elements but 0 Tab/TabItem/Document/Edit, so no user turn.
- `PCE14.013`: checked transport inventory, no observed Marionette/BiDi listener or debug launch flags; native oleacc and UIA libraries exist; no observed selenium/playwright/geckodriver in expected location.
- `PCE14.014`: native MSAA root acquire succeeded; window 7 children, client 32 children; no roles yet.
- `PCE14.015`: custom COM role calls failed all **41/41**, although MSAA roots accessible; negative test result.
- `PCE14.016`: narrowed custom COM role call failure to RuntimeException HRESULT `-2146233087` all four samples; never call it a pass.
- `PCE14.017`: corrected wrapper via standard `Accessibility.IAccessible`; got root roles 9 and 14, client first-child role 11.
- `PCE14.018`: all 32 direct child roles resolved, 25 popup, 4 toolbar, 2 grouping, 1 alert.
- `PCE14.019`: all 32 direct children resolved to COM objects; 0 second-level descendants traversed; no ChatGPT document/receipt. Read-only.

## Twenty-operation checkpoint assessment
**Governance:** Each executed PCE operation ran local five-control SHA256 `engineering_preflight`, checked expected GitHub remote `monag144/GPT-Windows-Relay` and guarded the untracked PCE12 audit + backup. .005 was rejected *before* the command, which is correct fail-closed enforcement; later `GOVSYNC14-...` maintenance IDs synced audit prerequisites from published GitHub with pinned ff-only diffs. All source-side benchmark additions authored on GitHub feature branch, not the deployed Client or local tracked working tree. No STOP bypass, exact-once replay, browser click/paste/send, machine installation change, or source overwrite was evidenced by numbered runs. Operator returned every command result, so manual interaction cannot be labeled absent.

**Incidents / repetition:** The .005 deadlock is recorded in `docs/incidents/INCIDENT_2026-10-09T2218Z_PCE14_005_AUDIT_SYNC_GATE_DEADLOCK.md`; recurring overlong stdout in .002–.004 and .006/.008/.009 was instrumentation quality debt, later shortened. MSAA custom COM role binding .015/.016 genuinely failed; standard interop correction .017 produced unique new evidence, so do not repeat the disproven binding. Draft PR CI run `37999190794` job `114052814923` failed with no available step logs; linked source-only incident `benchmarks/INCIDENT_2026-10-09T2231Z_PCE14_GITHUB_ACTIONS_PRESTEP_FAILURE.md`. Windows isolated suite was green 51/51; **CI remains red, cause unverified**.

**Product acceptance gaps:** There were **ZERO actual new PCE14 live Send/receipt trials**. No exact invoking-tab proof, independently verified user-role message with payload digest, loaded Firefox content-script hash attestation, reliable same-tab handoff, 60 genuine R01–R20 trials, 12h U endurance or 24h Z qualification. A listening socket/401 authorization response, passing fixture tests, successful GUI source inspection and native accessibility counts do not establish end-to-end delivery. Existing working copy/paste script was successfully supervised in preceding user context, but the PCE14 runs did not execute it.

**Stop/change criteria:** Stop deeper MSAA probing in active Firefox given direct roles/no descendants. Stop adding unbounded synthetic tests. Prefer minimal guarded use of proven GUI sender in a **separate non-personal isolated Firefox profile**, with independently attested observer and exact tab/STOP/payload hash/receipt, after explicit approval for any new live send. In parallel, diagnose CI environment and draft integration without weakening rules. Preserve rollback and current desktop state. Do not merge PR #10 or promote anything until real evidence. If isolation/observer cannot be proven, mark BLOCKED, not PASS.

## Before next engineering operation
For `PCE14.020`, both `docs/audits/AUDIT_2026-10-09T2239Z_PCE14_OPERATIONS_015_019.md` and **this** `REVIEW_*_PCE14_OPERATIONS_000_019.md` must already be installed locally. Publish GitHub-first and execute unique `GOVSYNC14-AUDIT-015-019-REVIEW-000-019-01` documented-only ff update, exact path/blob checks and pinned remote HEAD. Then local `engineering_preflight(root,20,series=14)` must return **both** audit window `[15,19]` and review window `[0,19]` before an actual numbered .020 packet may be sent. Source-only preflight does not authorize any live mutation. **REVIEW COMPLETE for PCE14.000 .001 .002 .003 .004 .005 .006 .007 .008 .009 .010 .011 .012 .013 .014 .015 .016 .017 .018 .019.**
