# PCE011 Relay & One-Click GO — Mandatory Daily Task Queue — 2026-10-08T0852Z

## Read THIS ENTIRE FILE and the ENTIRE control harness before EVERY operation
Read `consumer/control_harness.py` completely, this queue completely, `docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md`, established facts and relay sandwich procedure. Run `engineering_preflight(root, ordinal, series=11)` and log SHA256s. The full source is authoritative; a previous model summary is not a replacement.

## ACTIVE ORDER (no speculative detours)
- [x] GitHub verified legacy source references: historic full-tree One-Click GO r28 `d5b9db7ad785b5cae8dc3b64219303b9fcfa634a`; PCE8 v16 source `694d47ab89596d5c3801f749caa352b951a2be52`. Both original Git objects exist in Termux history; Termux branch tips have no `windows-relay/` folder.
- [x] A–Z Relay and consumer benchmark criteria committed; no overnight pass is yet claimed.
- [x] Corrected PCE011 harness scheduled reads/audit-reviews and created dated PCE011 queue on canonical Windows GitHub branch.
- [x] PCE11.004 source acceptance: backup integrity and staged SHA checks, **19/19 jobs PASS, 697 tests counted**, report `Client/Relay/bin/SOURCE_GATES_2026-10-08T091457Z/source-gates.json`; live activation and overnight qualification remain untested.
- [x] PCE11.001: exact PCE011 SHA pulled by fast-forward on clean canonical checkout; 5-control governance receipt returned. Preserve Codex-mapped paths and do not overwrite dirty future changes.
- [x] PCE11.001: 2532-file current Relay ZIP and SHA256 manifest saved non-destructively at `Client/Relay/bin/BROKEN_2026-10-08T090413Z.zip`; running listener left untouched.
- [x] PCE11.001: immutable historical v16 `694d47ab` and r28 `d5b9db7` staged in separate `Client/Relay/builds/` checkout trees; exact source HEAD verified. Live deployment NOT performed.
- [ ] Test both independently using pinned benchmark catalog: offline syntax/unit tests -> read-only identity -> STOP+rollback acceptance -> exactly-once canary -> 12h night -> 24h release gate.
- [ ] Recover exact PCE7 legacy rollback as independent standalone Relay challenger, not guessed from PCE7.447 branch.
- [ ] Qualify One-Click GO r28 Chrome and Edge consumer flows. Temporary Firefox development add-on is NOT signed persistent consumer Firefox support.
- [ ] Reintroduce newer HUD UI cautiously with **RETRY**; make STOP fully quiescent. Do not remove emergency KILL unless safety behavior of STOP is proven equivalent and recoverability retained.
- [ ] After five distinct repeated failures, optional Codex CLI scoped repair, preferred 5.6 or 6 Luna **if installed**, with GitHub-first commit and rollback.
- [ ] At PCE011.050 compile finding and send via connected mail only when an actual sender action is available; report send receipt, don't fake delivery.
- [ ] At PCE011.100 hand off/rotate to verified `💻PC Engineering 12🔧`, not OP101.

## PCE11.005 checkpoint and read-only inventory
- [x] GitHub audit covering PCE11.000–.004 saved at `docs/audits/AUDIT_2026-10-08T0916Z_PCE11_OPERATIONS_000_004.md` (COMPLETE as an audit; live gates BLOCKED).
- [x] PCE11.005B read-only inventory completed after exact audited GOVSYNC: original 2,532-file backup verified, candidates clean, no changed live-vs-archive source hashes, 8766 loopback listener PID 18632, no 8767 listener. Live extension and browser identity unverified; live cutover blocked. Saved `Client/Relay/bin/RUNTIME_INVENTORY_2026-10-08T092221Z.json`.
- [x] PCE11.006: passive topology verified main PID 18632 on 8766; 8767 absent, all STOP/OFF/KILL sentinel flags false. Role classifier matched 2 HUD, 2 relay-server, 1 supervisor, 1 watchdog and 1 consumer-candidate; these are *unverified matches*, not proved independently running instances. Evidence in `Client/Relay/bin/PASSIVE_TOPOLOGY_2026-10-08T092500Z.json`.
- [x] PCE11.007: source report parsed; HUD 13408 and its child 4464 are both pythonw HUD matches. Other live records were truncated by Relay output; full topology JSON SHA 735cea44ba87… retained. Does not authorize cleanup.
- [x] PCE11.008: diagnostic FAILED (invalid escaped PowerShell path regex, then empty-output JSONDecodeError). No live mutation. Incident `docs/incidents/INCIDENT_2026-10-08T0928Z_PCE11_008_POWERSHELL_REGEX_DIAGNOSTIC_FAILURE.md`.
- [x] PCE11.009 corrected source test/probe passed. Port 8766 stays PID 18632; 8767 absent. HUD pythonw 13408→4464 and server python 4844→18632 remain live with unchanged parent associations; only 18632 is listener. Consumer-candidate PID 19104 disappeared. Saved `Client/Relay/bin/PROCESS_IDENTITY_2026-10-08T093134Z.json`; do NOT infer two independent GUI windows or duplicate effects.
- [x] Mandatory .005–.009 audit committed: `docs/audits/AUDIT_2026-10-08T0933Z_PCE11_OPERATIONS_005_009.md`. Incident .008 failure included. Live activation remains BLOCKED.
- [x] PCE11.010: separate audited sync passed, then authenticated GET /status proved PID 18632 ARMED=true, outbound_owner=browser, pending_missions=2, stop_generation=8 and browser_quiesced_generation=7. Visible top-level HUD window belongs only to PID 4464; parent HUD process 13408 has none. All STOP sentinels absent. Deployed `relay-control.ps1` SHA differs from canonical source. Saved `Client/Relay/bin/LIVE_READINESS_2026-10-08T093733Z.json`. No live mutation.
- [x] PCE11.011: control-script drift inspected and both PowerShell versions parsed with 0 syntax errors. Only 3 hunks; only named safety/control feature mismatch = canonical RETRY absent from live. STOP controls present in both. At time of .010, ARMED=true, pending=2, stop_generation 8 / browser_quiesced_generation 7, **latest STOP acknowledgement not proved**. Saved `Client/Relay/bin/CONTROL_DRIFT_2026-10-08T094030Z.json`; no live mutation.
- [x] PCE11.012: archive SHA256 verified, 2532 ZIP files and critical restoration paths present; port 8768 free while live 8766 remains PID 18632. Both historical stage trees exist and `windows_relay.py` supports --config and --state-dir, but the static checker flagged both as blocked for absent run-control.ps1. This historical standalone supervision prerequisite can be provided separately without patching stage; do not silently treat it as a running independent supervisor. Saved `Client/Relay/bin/SIDECAR_READINESS_2026-10-08T094255Z.json`.
- [x] PCE11.013 attempted and BLOCKED (source preflight, no launch): v16 raw worktree Git blob did not match pinned historical blob; likely CRLF/filter mismatch, not yet proven. Windows returned COMMAND_FAILED exit 2 before any sidecar start, while canonical source had pulled to `1483167b0c0e376bec883f048d4f315169aac090`. Incident `docs/incidents/INCIDENT_2026-10-08T0946Z_PCE11_013_HISTORIC_GIT_BLOB_MISMATCH.md`. Separate launch-before-Job-assign race found and canary mode hard-disabled until repaired.
- [ ] PCE11.014: **static-only** exact historical source SHA validation via Git tree blob and normalized worktree blob (`git hash-object --path`) plus expanded tests; prove whether CRLF is responsible. No process launch. First repair GitHub source/tests, verify remote SHA, then Windows clean FF pull and test under a new unique action ID.
- [ ] After verified inventory, design independently supervised, rollback-backed v16 canary before any consumer promotion.

## CHECKPOINTS
- Five-operation audit every .005/.010/... covering preceding five attempted IDs, including 0 baseline slot, failures and missing results. **Historical audit PCE10.015-.019 already recorded:** `docs/audits/AUDIT_2026-10-08T0316Z_PCE10_OPERATIONS_015_019.md`.
- Twenty-operation review every .020/.040/.060/.080/.100.
- Soft reporting/email checkpoint .050; mandatory safe rotation .100.
- Human STOP, uncertain side effects, ambiguous tab identity, failed rollback or dirty checkout always prohibit unsafe unattended mutation; reporting and read-only diagnosis may continue.

## HISTORICAL TASK DETAIL
Earlier full backlog was preserved at Git blob `9dd9080ed2e9b1a489c3f9258f3a5c829dce3763` and verbatim archives:
- [Part 1](TASKS_2026-10-08T0752Z_WINDOWS_RELAY_PART_01.md)
- [Part 2](TASKS_2026-10-08T0752Z_WINDOWS_RELAY_PART_02.md)

Do not confuse a user-reported running Relay with current source SHA or an accepted browser runtime.
