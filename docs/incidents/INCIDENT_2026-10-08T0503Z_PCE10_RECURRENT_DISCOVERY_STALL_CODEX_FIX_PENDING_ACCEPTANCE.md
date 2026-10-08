# INCIDENT — 2026-10-08T05:03Z — Recurrent command-discovery stalls / Codex remediation pending acceptance

**Status: OPEN — source fix reported and locally committed; verification, deployment, and live recovery evidence pending.**

**Canonical repository:** `monag144/GPT-Windows-Relay`, branch `pce10/reconcile-control-and-rotation`.  
**Windows source checkout:** `C:\Users\Craig Morgan\Downloads\Dev\GPT\GPT-Windows-Relay`.  
**Live workspace:** `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay`.

## Incident summary and user impact

Multiple PCE10 action packets reached browser discovery without progressing through backend execution and result delivery. The Director repeatedly had to notice and report the stalls, violating the unattended relay objective. Confirmed history:

- **PCE10.005:** command remained DISCOVERED and needed Director rescue.
- **PCE10.018:** screenshot showed DISCOVERED for **3,774 seconds**; no durable backend execution proof. PCE10.019 inspected journal and found `relay_packet_discovered`, then `relay_result_replay_suppressed`, but no saved result / processed backend record for .018.
- **PCE10.021:** screenshot showed DISCOVERED for **784 seconds**, Firefox IDLE, relay ONLINE/ARMED, two pending **consumer missions** (not an action queue). No .021 result was provided. Director declined further manual Firefox repair.
- Separate **PCE10.015** `Worked for X` commentary/final rendering collapse remains documented in its own incident and is adjacent to, but not proof of, the discovery-stall root cause.

The Director-provided HTTP excerpt for 2026-10-07 21:35:39–21:35:59 local showed numerous successful `GET /status`, approximately periodic `/mission-next` and `/browser-heartbeat`, **no `POST /action` within that excerpt**. HTTP 200 and browser heartbeat established transport/backend liveness, not command execution.

## Root-cause finding reported by Codex

Codex identified a **false result acknowledgment / execution suppression** defect: the content script treated a packet ID occurring anywhere in a broad conversation turn as sufficient evidence of a completed `[GPT_WINDOWS_RESULT]`. A command could therefore be marked replay-suppressed *before* backend execution, consistent with the .018 journal evidence.

Additional previously identified contributing failures:
- Watchdog used listener/HUD availability rather than unresolved command-discovery progress. On healthy listener 8766 it could bypass browser-stall supervision.
- The stale-settle lease and page-local recovery could not recover an old or stalled running content script independently.
- `operatorControlPollTimer=setInterval(pollOperatorControlState,250)` contributed to redundant `/status` requests.
- Earlier canonical source-to-live hashes differed; PCE10.020 staged updated JS files with backups but explicitly **did not** reload Firefox. Hence source edits did not demonstrate a runtime fix.

The precise live cause remains subject to deployment/canary evidence; Codex's diagnosis is reported evidence, not independently validated production closure.

## Codex repair — user-reported commit

Codex reported local commit:

`7c38e90 Fix false result suppression and stalled scanner recovery`

Changes reportedly implemented:

1. Result acknowledgment now requires a standalone, exact, author-verified user `[GPT_WINDOWS_RESULT]` envelope.
2. Suppression consults durable backend packet state instead of relying on a packet-ID text match.
3. Added authenticated `/packet-status` lookup for packet identity/execution status.
4. Added tab-bound, extension-background alarm-driven recovery after 45 seconds in **both extension variants**; recovery runs only when armed and backend establishes that the action has not executed.
5. Added extension permissions required for alarm and tab recovery.

**Important provenance limit:** At 2026-10-08T05:03Z the GitHub connector could not resolve abbreviated commit `7c38e90` on the remote repository. Codex stated it was committed locally; remote push/commit reachability and exact code diff were **not yet verified**. Do not claim this commit is merged, published, tested, deployed, or activated.

Codex explicitly stated **no tests**, **no Firefox extension reload**, **no live deployment**, **no Firefox activation**, and **no live Relay directory mutation** after its repair commit.

## Safeguards and unfinished acceptance

- Run the existing local source-acceptance procedure against the exact commit in the Windows checkout. Verify result parser, authenticated packet-status endpoint, dual-extension background watchdog, STOP/exact-once, and syntax.
- Inspect existing durable PCE10.018/.021 state before any potential replay or recovery; no blind resend of uncertain side effects.
- Perform a rollback-backed live activation using confirmed Firefox extension/tab identity and preserve PCE10.020's existing backup manifest.
- Verify a fresh action crosses **DISCOVERED → backend execution → saved result → visible user turn** exactly once, without false suppression.
- Verify an intentionally induced browser-scanner stall is detected/recovered at the intended 45-second deadline without user intervention and without skipping STOP.
- Quantify whether `/status` polling has been reduced; the Codex report did not claim to resolve that independently.
- Restore and measure unattended continuation after real result delivery. Neither a source commit nor passing tests alone proves autonomous keep-going.
- After P0 stabilization, inventory and carefully clean `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay`; preserve state, configuration, secrets, results, logs, incident evidence, and rollback backups.

## Related incident and mission records

- `docs/incidents/INCIDENT_2026-10-08T0309Z_PCE10_018_DISCOVERED_STALL_USER_INTERVENTION.md`
- `docs/incidents/INCIDENT_2026-10-08T0420Z_PCE10_021_784S_DISCOVERY_WATCHDOG_BLINDSPOT.md`
- `docs/incidents/INCIDENT_2026-10-08T0200Z_PCE10_015_USER_RESCUE_COLLAPSED_COMMENTARY_COMMAND.md`
- `docs/missions/MISSION_2026-10-08_CODEX_FIX_UNSTUCK_WINDOWS_RELAY.md`

## Next update / closure rules

**OPEN.** Append a follow-up with the tested full commit SHA, actual changed files, regression findings, live extension version, exact activation and rollback evidence, canary timeline, and no-babysitting outcome. If acceptance fails, record the failure and remediation without overwriting this chronology.

Close **only** when the runtime proves exact-once delivery, autonomous recovery of the previously failing discovery stage, respect for operator STOP, and successful unattended continuation. Keep open if only repository/source tests pass.
