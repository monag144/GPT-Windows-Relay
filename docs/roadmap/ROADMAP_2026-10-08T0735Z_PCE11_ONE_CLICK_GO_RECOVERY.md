# PCE 011 — One-Click GO consumer release recovery — 2026-10-08T0735Z

## Mission and priorities
The target product is **consumer One-Click GO**: users download/extract, double-click GO.bat, select a user-supplied browser, sign into ChatGPT, and deliver a mission through a verified relay. It must recover safely without needing a developer at the machine. Firefox temporary-addon engineering must not dominate release readiness.

## Baselines — NEVER conflate
1. **Consumer r28:** frozen `monag144/GPT-Termux-Relay` branch `consumer/one-click-go` at `76a280bb3`, manifest 1.1.0 revision 28; Firefox intentionally excluded until signed. Use as currently defensible *consumer starting baseline*, NOT as a newly live-tested release.
2. **Consumer r29:** revision 29 source on Windows PCE11 branch; temporary Firefox profile/add-on workflow and recovery supervisor exist, but full restart/persistence and multi-browser acceptance are unproved. Its older README incorrectly says Firefox remains disabled. **Candidate only**.
3. **PCE6/PCE7 recovery:** documented independent browser manager, Firefox refresh, addon reloading, screenshot/error capture, UIA and watchdog. Reuse code after targeted tests; do not resurrect untrusted builds.
4. **PCE8 ownership and rotation:** retain URL-bound result sender, durable submitted/uncertain semantics, STOP and stale-owner leases; chat rotation into PCE9 failed acceptance.
5. **PCE9/PCE10 runtime:** active Firefox deployment not accepted. PCE10.035 source tested; PCE10.037 identity zero-match; no verified known-good full live backup.

## Immediate sequence
- P0: GitHub-only root cause and minimal regression of `firefox_tab_adapter.ps1` managed resolver, with no guessed current chat ID and no live mutation. Commit source/tests first.
- P0: verify PCE11 source on Windows after explicit `git pull --ff-only` once ready; PowerShell parse test, focused Firefox tests, full Windows/consumer suite; stop on failures.
- P0: source/live hash inventory, exact window/tab/selected URL binding, STOP gate, verified reversible backup, narrow staging. Run a NEW harmless unique-ID canary; never reissue uncertain old packets.
- P1: standard One-Click GO r28 **Chrome/Edge** end-to-end consumer acceptance: bootstrap, GUI, automatic extension, exact result, update, recovery and fresh Windows relaunch. No stable promotion before evidence.
- P1: independently prove r29 Firefox signed persistent-XPI/policy, restart and rotation lifecycle before declaring Firefox supported to consumer.
- P1: reconcile only validated improvements into a tested consumer release branch, then explicitly promote `main` once full matrix passes.
- P2: resume Job Application Engine v2 after consumer release core is accepted.

## PCE 011 operational rules
GitHub is source of truth; relay only pulls fast-forward after reviewed source; never fix the live tree in place. Avoid repetitive identical browser probes. Treat operator STOP, uncertainty, rollback, and exact conversation URL as gates. Do not confuse Python test success with loaded extension identity or production acceptance. Keep handoffs, audits and incident records date+UTC-timestamped. Avoid OP101 rotation; no unbounded keep-going or manual-babysitting loops.
