# PCE14 strict performance gradebook — 2026-10-09T2300Z

## Scope and scoring contract
**OBSERVATION-ONLY; NO REPAIRS OR LIVE SENDS.** Canonical source `monag144/GPT-Windows-Relay`; graded evidence through authenticated PCE14.028 Windows results. **PCE14.029 was issued but has no returned outcome**; do not treat the headless-geometry fix as validated or replay its ID. Raw source of all 28 checks: `benchmarks/RELAY_STRICT_GRADES_2026-10-09T2258Z.json`. Strict Python scorer: `benchmarks/relay_strict_grader.py`. Associated grading-rule tests: `benchmarks/tests/test_relay_strict_grader.py`, **23 authored, not yet executed on Windows**. No existing sender, fixture behavior, relay, Firefox, deployed Client or user profile was altered by this grading work.

**Pass threshold: >=90%.** Bands **A 98–100%, B 95–<98%, C 90–<95%, F <90%**. Unexecuted test => **U (unproven, blocks critical gate)** with **no invented runtime pass percentage**. Required-case coverage uses `completed/required`; it is **not** a success rate. 100% for a single unit test is provisional, not statistical evidence of reliability or an end-to-end product qualification.

**Overall strict readiness evidence: F — 39.29% of defined gates have >=90% demonstrated results (11/28).** This number measures *evidence sufficiency*, not actual production success probability. Of 16 genuinely observed gates, 11 met threshold (**68.75% of observed gates**, also below 90%). There are 5 measured failures, 2 coverage failures, and 10 unproven checks. **Release status BLOCKED**, regardless of green unit suite.

## Passing results — what they establish (not what they imply)
| ID | Capability tested | Actual result | Grade |
|---|---|---|---|
| G01 | Verifies canonical controls before Windows relay operations | 9/9 = 100% | **A** |
| G03 | Confirms original untracked audit and backup hashes before test execution | 9/9 = 100% | **A** |
| G06 | Runs existing regression tests on a pinned Windows feature revision | 72/72 = 100% | **A** |
| G07 | Executes 21 independent fixture HTTP contract test methods | 21/21 = 100% | **A** |
| G08 | Tests that accepted synthetic payload has independently recorded SHA256 | 1/1 = 100%; limited sample | **A** |
| G09 | Verifies repeated operation ID returns conflict without a second effect | 1/1 = 100%; limited sample | **A** |
| G10 | Verifies receiver refuses further New Chat and Send after STOP | 1/1 = 100%; limited sample | **A** |
| G11 | Verifies unauthenticated or wrong-token requests are rejected | 1/1 = 100%; limited sample | **A** |
| G12 | Verifies stale conversation association cannot submit a new user turn | 1/1 = 100%; limited sample | **A** |
| G13 | Loads test fixture and produces valid screenshot with disposable profile | 4/4 = 100% | **A** |
| G14 | Parses embedded fixture JavaScript using Node before browser tests | 1/1 = 100%; limited sample | **A** |

## Failed measurements and coverage — improvement opportunities, not changes
| ID | Capability and purpose | Observed score | Why it misses 90%; conceptual improvement |
|---|---|---|---|
| G02 | Ensures mandatory audit is locally available before numbered dispatch | **4/5; 80% — F** | PCE14.005 blocked; .010, .015, .020, .025 accepted. Improvement: Automate GitHub-first audit synchronization before dispatch. |
| G04 | Checks canonical content script and installed Client content script match | **0/1; 0% — F** | PCE14.008 found different disk SHA256 across source and Client trees. Improvement: Reconcile deployed JS only after controlled staging and rollback proof. |
| G05 | Checks pinned benchmark feature through independent GitHub CI | **0/1; 0% — F** | Actions run 37999190794 failed before accessible steps. Improvement: Collect runner/job diagnostic evidence; restore CI signal. |
| G15 | Requires matching server-accepted geometry and launch nonce from Firefox | **0/3; 0% — F** | PCE14.026, .027, .028 had no accepted readiness; .028 diagnosed zero outerWidth/Height. Improvement: Validate explicit headless geometry mode separately from visible-window identity; pending .029. |
| G16 | Must bind input to single proven test window rather than first Firefox process | **0/1; 0% — F** | PCE14.025 found two visible Firefox windows with identical PID and bounds. Improvement: Pin disposable process creation and exact HWND/nonce/foreground before any input. |
| G26 | Completes 3 real independent trials for each of 20 behavior scenarios | **0/60 coverage; 0% — F** | 0/60 required real traces verified; offline scorer tests are not traces. Improvement: Run 60 independently witnessed scenarios after safe browser controls. |
| G27 | Completes both distinct unattended uptime acceptance windows | **0/2 coverage; 0% — F** | 0/2 scheduled endurance windows completed. Improvement: Run endurance only after short-run safety and receipt gates pass. |

## Untested / unproven — not an observed 0% runtime failure
| ID | Capability and purpose | Grade | Needed evidence |
|---|---|---|---|
| G17 | Tests real OS mouse click on isolated fixture and server New Chat receipt | **U / blocked** | Run a single supervised disposable-window click trial. |
| G18 | Tests pasted synthetic message into correct isolated composer | **U / blocked** | Compare payload digest and bound composer with sender-independent observation. |
| G19 | Verifies exactly one OS Enter leads to exactly one local send effect | **U / blocked** | Verify actual receiver count after only one guarded Enter. |
| G20 | Confirms separate local HTTP receipt from GUI-origin submission | **U / blocked** | Tie unique fixture window and nonce to independent receiver digest. |
| G21 | Proves invoking tab identity survives new-chat workflow | **U / blocked** | Use origin-tab identity, not process name or coordinate assumptions. |
| G22 | Independently observes final sent user message and digest | **U / blocked** | Establish independently attested user-role receipt before promotion. |
| G23 | Verifies duplicate suppression across a real browser action and retries | **U / blocked** | Test duplicate key, replay, crash, stale ack and alternate tabs. |
| G24 | Ensures STOP suppresses real browser input at every stage | **U / blocked** | Simulate STOP between activation, click, paste and Enter. |
| G25 | Attests exact deployed and loaded content script build | **U / blocked** | Acquire actual loaded build identity with rollback-gated verification. |
| G28 | Measures wall-clock and p95 latency against an agreed acceptance ceiling | **U / blocked** | Set benchmark SLA and record end-to-end latency distribution. |

## What the grades do not allow us to assert
- A 72/72 unit/integration suite is **not** a ChatGPT sender success rate. Its synthetic loopback fixture explicitly differs from the production page, and several of its 21 receiver tests use direct HTTP calls rather than GUI input.
- Isolated headless Firefox rendered pages successfully (4/4), but **browser-to-receiver readiness 0/3** in measured .026/.027/.028. .028 confirmed `outerWidth=outerHeight=0` and `innerWidth=1382, innerHeight=744`; the feature-branch fallback correction is not yet verified by a Windows result.
- The working user's supervised GUI script is valuable prior context, but **no PCE14 independent GUI user-message receipt** was measured. Do not manufacture a numerator, denominator, or grade for unrun sending.
- Canonical source/Client on-disk JavaScript differs, and the running Firefox extension code SHA is unknown; zero observed 60-case live traces and zero endurance windows cannot count as test passes.
- The last CI workflow reported a failure with no accessible job steps; do not infer that unit assertions failed or claim independent CI green.

## Non-mutating next testing expansion (not authorized execution)
After PCE14.029's distinct result is received, complete the mandatory PCE14.025–.029 audit GitHub-first, synchronize it via a unique documentation-only GOVSYNC, and pass `engineering_preflight(root,30,series=14)`. Only then may the already-authored strict scorer and 23 added boundary tests run as PCE14.030 or later. Keep the scoring snapshot pinned to its observation cutoff; future measurements get a new timestamped revision, never reinterpret this baseline. **Do not repair or promote components as part of grading.**

**GRADEBOOK COMPLETE: STRICT EVIDENCE SCORE F (39.29%), measured-gate pass fraction F (68.75%), release BLOCKED.**
