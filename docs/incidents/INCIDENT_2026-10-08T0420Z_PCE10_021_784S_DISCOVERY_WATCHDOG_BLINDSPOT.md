# PCE10.021 discovery hang: watchdog blind spot and user rescue

## User-visible observation
On October 7 2026 at roughly 21:18 PDT, Director screenshot: `DISCOVERED PCE10.021`, Firefox `IDLE • relay_packet_discovered • 784s`, `DISCOVERED • packet parsed; settling before execution • 784s`. Relay reported `ONLINE • ARMED • pending 2` (two consumer missions, not two engineering jobs). The ChatGPT conversation was visibly open and Firefox had an about:debugging tab. No `PCE10.021` execution result has been provided. Director again had to detect/report the failure.

## Verified code diagnosis
- `windows-relay/relay-watchdog-loop.ps1` monitors localhost 8766 listener and existence of a HUD process; if listener is up its control path is `if(Listener){Start-Sleep -Seconds 10;continue}`. It never reads `relay_packet_discovered` age, content-script heartbeat, pending action, or a PCE result. Thus a browser-side DISCOVERED hang cannot trigger recovery while backend stays online.
- `windows-relay/content.js` has a 500ms settle timer, a 5000ms stale pending lease rearmed only when `inspectUnit` is invoked, a 15s periodic `recoverLatestAssistant` scan, and a 300s guarded page-refresh recovery obligation. All run INSIDE the page content script; none is an independent server/OS supervisor. A dead/stale content script cannot supervise itself.
- The five-minute refresh is conditional on no `inflight` and no `activeRelayOperationId`; pending state, falsely observed result wrappers, page timer blockage, or stale extension implementation can prevent it.
- PCE10.019 independently proved live content script SHA was `acab8626..` while canonical source was `269445f0..`. PCE10.020 staged three source files into live disk and explicitly reported `ADDON_RELOAD_PERFORMED=False`. Thus the current Firefox-running extension **was not proven to have loaded** the repaired version.
- HUD source has 45s STALLED age rule but PCE10.021 screenshot still shows DISCOVERED at 784s; live HUD promotion not proven.
- PCE10.021 itself is execution-uncertain; do not reissue the original or use a later ordinal as a replay without durable state proof.

## Root failure class
**FALSE HEALTH THROUGH LISTENER-ONLY WATCHDOG / PAGE-LOCAL SELF-SUPERVISION / SOURCE-LIVE GAP / THIRD USER RESCUE OF DISCOVERY STALL.**

Exact runtime mechanism remains unproven until backend state and browser-events journal are inspected. This record is not evidence that a particular JS timer fired or failed.

## Smallest safe changes
1. Add independent **observe-only** discovery-stall telemetry to the Windows supervisor from durable backend browser events (noninterfering when 8766 is online). Track unresolved packet-specific discovery age, log at 45s, alarm distinctly in HUD, do not auto-replay or reload from ambiguous identity.
2. Add an independent extension-background watchdog (with persisted per-tab packet intent, strict tab/conversation binding, and STOP/armed checks) that can recover a blocked content script without depending on content-script timers. Test 5s stale lease, late result, multiple tabs, STOP, and restart before enabling any automatic reload.
3. Verify exact addon runtime revision on reload, plus a bounded fresh canary. PCE10.020 backup manifest is required for rollback; runtime activation still unverified.
4. Interim rescue if safe controlled recovery unavailable: one ordinary browser tab reload, after inspecting `PCE10.021` durable result to avoid blind replay.
5. Continue governance reads five files every operation; audit .020-.024 before PCE10.025, review .020-.039 before PCE10.040.

## Promotion verdict
**BLOCKED: live Firefox recovery remains unverified.**
