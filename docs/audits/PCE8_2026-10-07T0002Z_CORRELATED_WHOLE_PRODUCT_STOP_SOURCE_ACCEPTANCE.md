# PCE8 correlated whole-product STOP — source acceptance

Acceptance timestamp: 2026-10-07T00:02:56Z / 2026-10-06 17:02:56 Pacific

## Status

Source implementation is accepted and committed.

- Accepted implementation commit: `f9fabddbec781dbfed7ba4895257ef65396f024d`
- Parent: `fe145d8e59fec85c1394169411f3135169d6c23e`
- Commit subject: `relay: require correlated browser quiescence on operator stop`
- Accepted source content SHA-256: `B3B0937DCE400BAC658B7A2DBD83543E4E7AD83601D156E84FA0CC233BBF8E4C`
- Working tree was clean immediately after commit.
- Remote push was not performed.
- Live Firefox/browser plane was not changed and remains on accepted v16.

This is a **source acceptance milestone only**. It is not live acceptance.

## Problem closed at source level

The earlier operator STOP path only paused the backend and then killed the listener after a fixed delay. Browser-resident result delivery, retries, recovery scans, deferred actions, observers, approval automation, and other timers could continue after the human had explicitly stopped the relay.

The accepted source implementation changes STOP into a correlated whole-product quiescence protocol.

## Accepted STOP protocol

1. The durable `.relay-paused` interlock is created before shutdown.
2. The controller disarms the exact active backend using credentials whose configured port matches the listener.
3. Backend disarm allocates a monotonically increasing `stop_generation`.
4. `/status` exposes `stop_generation` and `browser_quiesced_generation`.
5. Browser content starts paused by default and only resumes after an explicit armed state.
6. A disarmed control state synchronously quiesces browser autonomy before its ACK is sent.
7. Each content context ACKs the exact `stop_generation` after quiescence.
8. Each service-worker variant snapshots its connected content-port set for that generation.
9. Disconnecting a port does not shrink that frozen expected set.
10. The worker emits `browser_operator_quiesced_all` only after every expected content port has returned the matching generation ACK.
11. Backend accepts the aggregate browser ACK only while disarmed and only when its generation exactly matches the current stop generation. Stale ACKs are rejected.
12. `relay-control.ps1` waits for both `stop_generation` and `browser_quiesced_generation` to equal the requested generation before reporting verified browser quiescence.
13. The old fixed 700 ms success assumption was removed.
14. If the bounded acknowledgement wait expires, backend shutdown still proceeds, but the operator result explicitly reports `BROWSER_QUIESCENCE=UNVERIFIED` rather than claiming whole-product success.

## Browser quiescence scope

STOP guards or cancels active delivery, chat-idle waits, delivery confirmation, attachment work, composer injection, background actions, consumer missions, deferred drains, draft recovery, recovery refreshes, submitted-result watches, conversation/scroll observers, UI-error inspection, approval inspection, recovery intervals, and pending background requests.

The control-plane reconnect and operator-control polling path deliberately remains available while paused so START can be observed. Autonomous runtime reload remains blocked while paused.

START/resume restores persisted handoff recovery and the guarded browser automation loops only after an explicit armed state.

## Acceptance evidence

PCE8.145 full source acceptance:

- Whole-product STOP contract: 14 / 14 passed.
- Browser contract: 55 / 55 passed.
- HUD contract: 19 / 19 passed.
- Windows relay full suite: 287 / 287 passed.
- Consumer full suite: 99 / 99 passed.
- JavaScript parse gates passed for content and both service-worker variants.
- PowerShell parse gate passed for `relay-control.ps1`.
- Python compile gate passed for `windows_relay.py`.
- `git diff --check` passed.
- Exact expected 11-file write set was enforced.
- Three content-script source copies were byte-identical at the accepted SHA-256.

PCE8.146 performed the separate semantic diff audit and completed successfully. It confirmed stale-generation rejection, ACK-after-quiesce ordering, exact-generation controller waiting, frozen all-port expectations, no disconnect weakening, removal of the fixed 700 ms success assumption, and preservation of intentional differences between the two service-worker variants.

## Relevant incident and investigation chain

- `docs/INCIDENT_2026-10-06T0701Z_HUD_STOP_PAUSED_BUT_BROWSER_RESULT_SPAM_CONTINUED.md` — original browser-autonomy-after-STOP incident.
- PCE8.137 — proved the first v17 STOP candidate emitted browser quiescence but did not positively wait for its acknowledgement.
- PCE8.138–139 — mapped browser-event persistence, content-port topology, backend state, and insertion points.
- PCE8.140A1–C1 — built generation correlation, browser ACK, all-port aggregation, and regression contracts in the inert patcher.
- PCE8.145 — first complete correlated-STOP source acceptance.
- PCE8.146 — final semantic audit.
- PCE8.147 — accepted implementation committed.

## Live boundary

Live remains on v16 and must not be described as having the correlated STOP behavior yet.

The live cutover must retain the following rules:

- preserve a rollback copy of every live file before mutation;
- do not run `sync-live.py` because the live browser plane is intentionally composite;
- deploy the main and persistent service-worker variants independently rather than collapsing their intentional divergence;
- validate source-to-live hashes and parse gates before exercising runtime behavior;
- do not test real STOP through a relay action whose own backend will be killed;
- use a detached observer/harness for the eventual STOP canary;
- require a fresh exact-generation `browser_operator_quiesced_all` acknowledgement;
- require operator-visible `BROWSER_QUIESCENCE=VERIFIED` for successful whole-product STOP acceptance;
- treat timeout or missing ACK as `UNVERIFIED`, not success;
- verify START restores the browser control plane and a fresh exact engineering-conversation round trip;
- rollback live immediately on any failed acceptance gate.

## Next stage

Audit the exact source-to-live deployment topology and construct a guarded cutover/rollback plan. Only after that plan is independently validated should the committed source milestone be promoted to live.
