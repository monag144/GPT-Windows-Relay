# Archived source fragment 1/2 — 2026-10-08T0752Z

# INCIDENT 2026-10-08T0502Z — PCE10 discovery-stall / false-result acknowledgment / Codex repair awaiting acceptance

**Status: OPEN — repair reported and locally committed; source acceptance, remote revision verification, live deployment, recovery, and incident closure remain unverified.**

**Affected components:** GPT Windows Relay content scanner, Firefox extension(s), local relay backend and packet-state API, background/watchdog recovery, HUD and governance controls.

**Canonical source:** `monag144/GPT-Windows-Relay`, branch `pce10/reconcile-control-and-rotation`. Local source: `C:\Users\Craig Morgan\Downloads\Dev\GPT\GPT-Windows-Relay`. Live runtime: `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay`.

## 1. Incident statement and user impact

Windows Relay repeatedly recognized an assistant-side `[GPT_WINDOWS_ACTION]` packet but remained at **DISCOVERED / packet parsed; settling before execution** for minutes or longer, despite `127.0.0.1:8766` remaining ONLINE and ARMED, with browser heartbeat and mission polling still operating. The Director had to intervene on multiple occasions. The failure defeated the explicit goal of autonomous, low-babysitting operation.

Notable events:
- **PCE10.005:** first documented `DISCOVERED` stall requiring Director intervention. Earlier source-side stale-settle fix was created but did not demonstrate live extension activation.
- **PCE10.018:** Director screenshot showed `DISCOVERED` at **3,774 seconds**. Subsequent PCE10.019 diagnostics found no saved `PCE10.018` result or backend `processed` entry; browser journal contained `relay_packet_discovered` followed by `relay_result_replay_suppressed`. This suppression was not proof of execution.
- **PCE10.021:** Director screenshot showed `DISCOVERED` at **784 seconds** and Firefox IDLE while backend displayed ONLINE / ARMED. The Director identified another stuck action and declined further manual browser rescue.
- **Rendering-related complication:** PCE10.015 was emitted in a temporary progress surface and collapsed to a `Worked for X` artifact; this is a related but distinct rendering/continuation problem with its own incident.
- **Other contributing operational failure:** PCE10.020 verified exact backups and staged three repaired content-script files on disk, but explicitly reported `ADDON_RELOAD_PERFORMED=False`; the browser running the repaired revision was not proven.

**Impact:** Two recent test/engineering operation slots (.018 and .021) were compromised by false suppression/stall, with additional earlier stalls and repeated user rescues. No action execution should be inferred solely from DISCOVERED, an HTTP 200 heartbeat, or a replay-suppression event.

## 2. Evidence and failure mechanism

Director-supplied Windows server log, approximately **2026-10-07 21:35:39–21:35:59** local, repeatedly shows:
- `GET /status HTTP/1.1` → 200, many times per second;
- `GET /mission-next?browser_id=firefox` → 200, approximately every one to two seconds;
- `GET /browser-heartbeat?browser_id=firefox&integration_connected=1` → 200, about every five seconds;
- **no `POST /action` appears in the supplied excerpt**.

Those requests prove a responsive backend and some extension connectivity, not the action execution or valid result-delivery chain.

Source investigation before the Codex handoff found:
1. `windows-relay/content.js:userTurnContainsPacketId` accepted broad `elementText(turn).includes(packetId)` matching in a user-result scan. An identifier appearing in a conversation wrapper could be mistaken for a delivered exact `[GPT_WINDOWS_RESULT]` envelope.
2. `run(p)` emitted `relay_result_replay_suppressed` when that broad predicate matched, even if backend persistent records showed no action. PCE10.018's event history matched that failure signature.
3. `DISCOVERY_SETTLE_MS=500` and `DISCOVERY_SETTLE_LEASE_MS=5000` were page-local. A blocked or outdated content script did not have an independent guaranteed recovery.
4. The original `relay-watchdog-loop.ps1` checked for an online listener and skipped ahead while port 8766 remained up. Source-side `discovery_stall_observer.py` was later committed to *observe* overdue packets independently, but detection alone was not a verified live fix.
5. `operatorControlPollTimer=setInterval(pollOperatorControlState,250)` produced excessive `/status` traffic. This was a separate efficiency/supervision weakness, not established as the direct cause of false result suppression.

### Root-cause classification

**Codex's reported primary diagnosis:** **FALSE RESULT-DELIVERY ACKNOWLEDGMENT CAUSED BY OVER-BROAD PACKET-ID MATCHING**, suppressing commands before backend execution.

**Secondary systemic weakness:** listener-only health and missing independently activated browser recovery meant suppression/stall persisted indefinitely, while the HUD displayed an apparently healthy backend.

The primary diagnosis is consistent with observed PCE10.018 journal evidence and inspected prior source, but the new repaired implementation has **not yet been independently inspected or exercised** in this record.

## 3. Codex repair report — delivered by Director; verification pending

The Director reported that Codex committed:

`7c38e90 Fix false result suppression and stalled scanner recovery`

Codex's reported implementation:
1. **Strict visible-result acknowledgment:** only an exact standalone user result envelope may count as `[GPT_WINDOWS_RESULT]`, not a packet ID found in general conversation prose/wrappers.
2. **Durable backend confirmation:** before suppressing a potential duplicate/replay, the content side checks exact persistent packet identity/status.
3. **Authenticated `/packet-status` endpoint:** permits read-only identity/status resolution for a specific packet.
4. **Independent tab-bound recovery:** both Firefox extension variants reportedly have an alarm-driven, **45-second** scanner recovery path.
5. **Safe execution gates:** recovery acts only if the operator is ARMED and backend durable state confirms no execution.
6. **Extension permissions:** the necessary alarm/tab recovery permissions were reportedly added.

**Explicit limits from Codex's report:** Codex did **not** run tests, reload an extension, deploy source into the running Firefox add-on, activate Firefox, or change the live Relay directory.

**Repository visibility at incident creation:** GitHub connector failed to resolve abbreviated SHA `7c38e90` and GitHub commit search did not find its exact message. That is **not proof the local commit does not exist**; it may not have been pushed to the canonical remote. Do not state the remote branch contains or is running this patch until confirmed from the local Git history and file diff.

**Disposition:** IMPLEMENTATION REPORTED / LOCAL COMMIT REPORTED; SOURCE TESTS NOT RUN; LIVE PATCH NOT DEPLOYED; INCIDENT STILL OPEN.

## 4. Required independent acceptance and closeout evidence

Before declaring repaired:
- Read the current local Git HEAD and `git show --stat 7c38e90`; verify no unintended source contamination, that both extension variants and permissions match, and that `/packet-status` enforces authentication and packet identity.
- Run necessary regression checks for exact standalone user result versus false wrapper mentions, backend `NO_EXECUTION` versus `INFLIGHT` / `COMPLETE` / unknown states, multi-tab/conversation binding, and STOP/disarm/kill authority.
- Check JS parse and critical Python source acceptance. Continue to use the five-source mandatory control read and checkpoint schedule: **audit .020–.024 before PCE10.025; review .020–.039 before PCE10.040**.
- With the existing PCE10.020 backups preserved, stage and reload the actual running extension through the managed Firefox mechanism, prove the runtime revision and required permissions, and verify rollback remains exact.
- Use a new, unique **read-only** live canary; observe packet DISCOVERED → backend action → saved result → correct standalone visible `[GPT_WINDOWS_RESULT]` exactly once. Do not replay the ambiguous PCE10.018 or PCE10.021 payload.
- Deliberately exercise a safe bounded stall condition and prove independently timed recovery within policy while the listener is online; verify STOP blocks recovery and no duplicate side effect is executed.
- Assess `/status` request volume and user-babysitting frequency before claiming the system meets keep-going targets. Verify the required continuation after a genuinely acknowledged result.

