# A6.399af Stale Visible-Delivery Status Masks Undiscovered Packet — 2026-10-06T0005Z

**Class:** INCIDENT / RELAY OBSERVABILITY AND RECOVERY  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Observed:** 2026-10-06T0005Z (2026-10-05 17:05 PDT)  
**Trigger:** Director screenshot and explicit report that the relay was reporting visible delivery when the expected result was not visibly delivered.  
**Disposition:** RELEASE BLOCKER; ROOT CAUSE INVESTIGATION / LIVE RECOVERY PENDING

## Visible evidence

The screenshot shows the ChatGPT conversation already containing the complete new relay instruction for:

`PCENG-A6.399af-firefox-profile-close-barrier-live-gate`

At the same time, the relay HUD still shows:

- `READY`
- `Relay ONLINE • ARMED • pending 0`
- `Firefox IDLE • relay_result_delivery_complete • 312s`
- `READY • result visibly delivered • 312s`
- packet `PCENG-A6.399ae-read-self-diagnostic-firefox-failure`

The HUD therefore remains correlated to A6.399ae even though A6.399af is visibly present on the ChatGPT surface. The Director also reports that the claimed visible delivery is not actually present as expected.

## Failure class

This is a false-success / stale-success observability failure.

A historical `relay_result_delivery_complete` event must not be allowed to prove that the currently relevant result is visible. Likewise, READY must not hide a newer visible assistant packet that has not passed discovery -> execution -> result -> visible-result confirmation.

The existing watchdog/reinspection redundancy did not make the discrepancy sufficiently obvious or self-recover within the observed interval.

## Required invariant

Visible-delivery state is packet-correlated, not global.

For packet P, the HUD may say `RESULT VISIBLY DELIVERED P` only when the browser-side verifier can find the exact `[GPT_WINDOWS_RESULT]` user turn for P in the live conversation DOM. Backend completion, send-click, generation-started, a historical delivery-complete event, or another packet's visible result is insufficient.

When a newer relay packet Q is visible, the HUD must not continue presenting P's success as the primary READY state. It must show Q's phase, or an explicit stale/scanner-disconnected recovery state.

## Recovery requirement

If a visible relay instruction has not advanced after the bounded discovery attempts:

1. force whole-conversation reinspection;
2. verify browser/content-script heartbeat independently of backend health;
3. if still unconsumed, use the independent recovery control plane to reload/reinstall the Firefox add-on as appropriate and refresh the ChatGPT tab;
4. re-scan the exact visible packet;
5. preserve exactly-once execution by packet ID;
6. surface the reason and repair phase in the HUD.

Recovery must not send repair code through the transport being diagnosed.

## Acceptance

Inject or reproduce a stale-success condition and prove:

- a newer visible packet replaces the previous success headline;
- exact packet ID is shown throughout discovery/execution/delivery;
- false `visibly delivered` cannot survive without exact DOM evidence;
- bounded reinspection escalates to out-of-band Firefox add-on reload/refresh when required;
- the packet executes at most once;
- the returned result is visibly located in the live conversation before declaring success.



## Manual terminal forensics — 2026-10-06T0015Z

The Director preserved the failure before refresh/reload and ran read-only terminal checks.

Authenticated backend/browser status:
- relay `ok=true`, `armed=true`, PID 9900;
- Firefox `connected=false`;
- browser event age 711 seconds;
- last event `relay_result_delivery_complete`.

Exact local search:
- `PCENG-A6.399af-firefox-profile-close-barrier-live-gate`: **0 matches**.

Lifecycle evidence in `%LOCALAPPDATA%\GPTWindowsRelay\browser-events.jsonl` shows A6.399ae:
- discovered at `2026-10-06T00:00:04Z`;
- execution requested at `00:00:04Z`;
- result received at `00:00:05Z`;
- result text set at `00:00:11Z`;
- send clicked/confirmed at `00:00:12Z`;
- `relay_result_delivery_complete` at `00:00:12Z`;
- operation counted immediately afterward.

No later lifecycle record mentions A6.399af.

### Refined diagnosis

The Windows backend did not hitch. The Firefox content/extension integration stopped participating after A6.399ae. A6.399af was subsequently visible on the ChatGPT page but never entered packet discovery at all. The HUD then retained the historical A6.399ae delivery-complete state as if it represented present readiness.

This is direct evidence for both F-005 exact-packet delivery correlation and the missing executable Plane-D out-of-band recovery path. Refresh/reload may restore the immediate development session, but a consumer release must detect and repair this state without requiring the user to perform terminal archaeology.
