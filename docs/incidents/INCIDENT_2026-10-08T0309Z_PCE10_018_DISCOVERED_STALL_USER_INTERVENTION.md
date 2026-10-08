# PCE10.018 DISCOVERED stall requiring user intervention

## Observation (user screenshot, 2026-10-07 evening PDT / 2026-10-08 UTC)
- Windows HUD: `DISCOVERED PCE10.018`, `Firefox IDLE • relay_packet_discovered • 3774s`, `DISCOVERED • packet parsed; settling before execution • 3774s`.
- Windows relay: `ONLINE • ARMED • pending 2`. **pending 2** means backend consumer missions; do not label it as an execution queue depth.
- Firefox is visibly displaying this ChatGPT conversation at `https://chatgpt.com/c/6ac6cf1e-c210-83e8-be8f-77f4b2ca53c1`, with a selected sidebar entry titled `Rename Current Chat`. A Firefox `about:debugging` tab is also visible.
- No corresponding PCE10.018 Windows result was supplied. The screenshot's last browser event is the discovery phase; no start/completion proof.
- The Director had to recognize/report the stall after nearly 4000 seconds.

## Confirmed failure boundary
The content-side action was discovered but did not visibly progress to execution. A non-executed, indefinitely idle discovery is not a successful relay action. PCE10.018's desired source-acceptance steps remain unconfirmed.

## Strong but unproven root-cause hypothesis
Canonical source already has a 5-second pending-settle lease, re-arming event, 15-second recovery scan, and separate 5-minute refresh watchdog, but no successful deployment of that content source to live Firefox was established. A 3774-second discovery with no subsequent browser events is consistent with a stale content script / disabled recovery scan / suspended browser timer. The exact live content-script revision has not been read from the running browser. Do not claim proof of the hypothesis.

## Contradicted earlier assumption
Earlier Windows UIA browser probes reported no visible ChatGPT conversation. This screenshot conclusively shows the target URL and an interactive Firefox browser. The negative UIA result is a probe limitation, **not** proof the browser is absent.

## Additional gap
The HUD continues to display `DISCOVERED` after >3700 seconds. An overdue `relay_packet_discovered` should be classified `STALLED` by age when no execution or delivery event follows. Report the event distinctly without inferring or replaying its original action.

## Classification
**RECURRING BROWSER DISCOVERY STALL / MISSING LIVE PATCH VERIFICATION / MISLEADING HUD PHASE / USER RESCUE.**

## Safety and next gates
1. Keep PCE10.018 unverified until durable backend records/state are inspected. Never blindly rerun uncertain side effects. The intended PCE10.018 is source tests (read-only) but duplicate delivery still must be checked.
2. Patch/test HUD late-DISCOVERED state independently of Firefox runtime.
3. Reprove extension runtime identity and prepare exact backup/rollback before content-script promotion. User screenshot confirms URL only, not Firefox PID or installed add-on source revision.
4. If no programmable, positively scoped browser control path works, request a **single** Firefox page refresh as the recovery bootstrap; do not advise killing Firefox, clearing profile, or force-terminating processes.
5. After refresh, verify saved result, source tests, extension version, and rollback-backed live canary, then measure fresh operations without user rescue.

## Promotion verdict
**BLOCKED** pending live browser recovery and positive fresh canary.
