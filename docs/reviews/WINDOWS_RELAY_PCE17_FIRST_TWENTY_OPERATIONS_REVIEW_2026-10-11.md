# PCE17 first twenty attempted operations — Drift and rescue review — 2026-10-11 Pacific

**Repository:** `monag144/GPT-Windows-Relay`; audited through PCE17.019. Completed **before** PCE17.020. This is an engineering/evidence review, **not** production/re-release authorization.

## Four independently read-back checkpoint records
- .000–.004 `docs/audits/AUDIT_2026-10-12T0038Z_PCE17_000_004_CHECKPOINT.md` Git blob `1a7015838836f33386a241e004fe75deb108c8af`
- .005–.009 `docs/audits/AUDIT_2026-10-11_PCE17_005_009_CHECKPOINT.md` blob `5a7d6a58481302c485e64406083bcdd795a8773c`
- .010–.014 `docs/audits/WINDOWS_RELAY_PCE17_010_014_CHECKPOINT_2026-10-11.md` blob `aa554c0c615a11b22c74cd822023227976b6dc89`
- .015–.019 `docs/audits/AUDIT_2026-10-12T0158Z_PCE17_015_019_CHECKPOINT.md` blob `2748781d27a60999421610968b0d09872f440de3`

## Twenty-slot exact ledger and outcome
| PCE17 ordinal | Result | Material proof or fault |
| --- | --- | --- |
| .000 | OK | Root file evidence, later corrected misleading live-identity classification |
| .001 | OK | Root HUD/launcher initially missing required controls; later source repair |
| .002 | OK | HUD process parent/child lineage and Python confirmed |
| .003 | OK | Explicitly identified nested **legacy** backend and HUD |
| .004 | COMMAND_FAILED | Overbroad recursive backup entered previous backups/.venv and failed, incident |
| .005 | GOVERNANCE_BLOCKED | False missing GitHub checkpoint, no execution |
| .006 | OK | 2,628-file allowlisted hash-verified rollback snapshot |
| .007 | OK | Legacy PID 7464, 2 stale missions, authenticated state |
| .008 | OK | Verified legacy OFF controller/watchdog logic |
| .009 | OK | User-approved ACK/clearing exactly 2 Oct-4 Chrome-only missions; pre-cancel backup |
| .010 | GOVERNANCE_BLOCKED | False missing GitHub checkpoint, no execution, incident |
| .011 | OK | Native legacy backend PID 7464, HUD 1924→3340 |
| .012 | OK, persisted/independently verified | Temporary independent Windows Task Scheduler helper executed and task cleaned; result markers from .014 |
| .013 | OK | Detected .012 processed=OK and skipped duplicate scheduler task |
| .014 | OK | Verified .012 saved result + marker and 0 residual tasks; legacy PID 13344 |
| .015 | GOVERNANCE_BLOCKED | Third false missing GitHub checkpoint despite read-back audit |
| .016 | OK | Root critical hashes, backup/prerequisites validated, legacy still active |
| .017 | COMMAND_FAILED | Bad quoting of Python -c; pre-error read-only delivery counts valid |
| .018 | OK | Python 3.13.15/Tkinter/AST, browser-owned READY journal verified against legacy source |
| .019 | OK | Legacy controller/watchdog hashes and OFF path; canonical CLI import + extension manifest; zero missions |

Outcomes: **15 OK** (including independently confirmed .012), **3 GOVERNANCE_BLOCKED**, **2 COMMAND_FAILED**. Every ID consumed once; no local relay packet reused. .004 left a partial non-authoritative backup; .006 provides valid one. Old PID changed from 7464 to 13344 without proven cause.

## Alignment and drift against dated mission/backlog
- **Mission:** safe, auditable exact command execution and visible delivery, then single integrated development build (Relay + five-button HUD + One-Click Go + Firefox integration), later re-release **only after acceptance**.
- **Progress:** GitHub WIP development source repaired/consolidated; root critical source files verified on Windows. Established an independent Windows worker path, preserved rollback, classified browser-owned journal, and documented legacy shutdown.
- **Gap:** no live canonical backend; old nested `windows-relay/runtime/windows_relay.py` still runs and may respawn, old HUD/watchdog still own lifecycle. Zero canonical HUD/watchdog. A staged candidate is **not installed runtime**. Loaded Firefox extension is temporary/unverified and may have different bytes from root `extension-persistent/` even though the same ID `gpt-windows-relay@local` is in the manifest.
- **Exact-once:** previous PCE15 race/post-500 replay defects remain unresolved until loaded fix is tested. 520 READY outbound records with `outbound_owner=browser` do not imply unsent replies; do not replay or purge.
- **Reliability:** legacy HUD previously STALLED; user reports reprinting a packet sometimes prompts scanner recovery. Needs an automatic safe same-chat fix, not repeated packet execution or forced new conversation.
- **Operator usability:** user wants to **use** the product now; 20 engineering attempts have not yet achieved the cutover. Reduce further diagnostics, package independent self-contained bounded cutover and rollback once preconditions are proven. Don't make user paste long PowerShell commands; relay / CMD preferred.
- **Release:** last independently graded product checkpoint F/BLOCKED 11/28, live send/endurance gates absent; no public/production release claim.
- **Governance drift:** old runtime falsely enforces assistant-side five-operation checkpoint and returns stale PCE10 reminders. The correct GitHub control harness's preflight receipt must be independently read via connector; don't remove STOP/token/owner validations or automatically rotate agents. Need fix the legacy governance defect in unified development build.
- **Source attribution:** maintained dated docs and current observed runtime trump old `README.md`/historical `current.md`/PCE8 cutover scripts; only `monag144/GPT-Windows-Relay`.

## Failure signatures / rescues / lessons
- .004: overbroad backup recursion; exclude historical backups, verify marker + exact hash manifest.
- .005/.010/.015: legacy guard rejects correct GitHub audits at ordinal multiple of five; do not keep retrying issued IDs. After .015, .016 succeeded; still diagnose discrepancy before release.
- .017: quoted inline Python script lost quotes; corrected with quote-safe `-c` by .018, and `--help` by .019. Avoid repeating known-bad invocation.
- Human interaction: repeated user corrections to assumptions about active installation and PowerShell copy/paste; documentation updated with actual runtime paths and **one build development** policy. Old HUD stalls require proactive repair.
- No six consecutive same-signature non-successes. Codex escalation threshold not met. No live duplicate side effects evidenced.

## Rollback, risk, and next action
- Keep verified PCE17.006 backup and PCE17.009 mission state snapshot; never replay old missions or previously sent results.
- For independent cutover, prefer proven single scheduled task with persisted report after old relay dies. Pre-check exact full process identities, no pending missions/inflight other than issuing command, expected configuration and source hashes, and a single one-shot marker; use old OFF command, shut down old HUD process chain only after verifying identities, verify no foreign 8766 listener, launch root controller/watchdog/HUD, check root processes/port, preserve browser ownership/STOP state and verify rollback. All steps fail closed on anomalies.
- Source WIP `a35d325ce9a666a372e2a88bc7b60704bdf785f9` is staging reference, not a proven live backend. Do not run historical PCE8 `safe_live_cutover.py` unmodified.
- PCE17.020 is the next unique ordinal; audit for .015–.019 is committed and read back, 20-slot review here. Need explicit preflight metadata receipt for .020. Next review at .040; audit each five attempted ordinals.
