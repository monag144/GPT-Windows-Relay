# Incident — 2026-10-06T0701Z — HUD STOP reached PAUSED but browser result spam continued

## Status

OPEN — operator STOP is not yet a whole-product quiescence boundary.

## Director observation

During the delivery-v12 repeated-result incident, the Director clicked the HUD STOP control. The HUD changed to `PAUSED`, proving the durable backend pause interlock was set and the operator-facing backend state responded correctly.

Despite that, ChatGPT continued receiving repeated saved relay results. Examples immediately preceding the STOP included PCE7.429 and PCE7.430 envelopes with `replayed:true` and their original execution timestamps.

## Proven boundary

The existing STOP path controls the Windows backend/supervisor/watchdog resurrection boundary, but it does not synchronously cancel browser-resident work that has already entered result delivery/recovery.

A loaded content script can therefore continue to:
- hold an already-returned Windows result;
- retry or recover browser result submission;
- rediscover an older assistant action;
- request a saved backend replay before/around the stop transition;
- continue browser-side timers after the backend itself is paused.

This is why the HUD can truthfully say backend `PAUSED` while the overall relay product is still visibly active.

There is no evidence in this incident that the underlying Windows side effect executed twice. The repeated PCE7.429/PCE7.430 envelopes retained their original execution timestamps and explicitly reported `replayed:true`. Backend exact-once remained the safety boundary; browser delivery quiescence failed.

## Required correction

Explicit operator STOP must become authoritative across every relay plane, not only the listener:

1. Set the durable operator pause interlock before shutdown.
2. Stop/hold backend execution and prevent supervisor/watchdog resurrection.
3. Propagate operator-paused state to the browser plane.
4. Cancel content-script delivery retry, draft-recovery, recovery-scan, deferred-drain, page-refresh and post-submit timers that could cause autonomous relay output.
5. Prevent new assistant packet discovery/execution while operator-paused.
6. Positively owned relay drafts/results must never be auto-Sent while paused.
7. Browser recovery must remain dormant until explicit operator START/resume.
8. START must restore the same recovery machinery cleanly rather than requiring permanent disabling of resilience.
9. HUD language must distinguish backend-only pause from verified whole-product quiescence until this acceptance is proven.

The goal remains: keep the relay alive at all costs unless the human explicitly says STOP. Once STOP is explicit, every redundancy plane must yield immediately.

## Related evidence

- PCE7.429: one Windows execution followed by duplicate browser Send behavior.
- PCE7.430: forensic counts proved one execution and multiple Send clicks.
- Later PCE7.429/PCE7.430 envelopes returned with `replayed:true`, proving saved-result replay rather than repeated Windows side effects.
- delivery-v13 submit-once source correction: `0c67c623d2036c93d318fcefdf346ca8236561c3`.
- This incident adds a separate requirement: submit-once alone is insufficient unless operator STOP also cancels browser autonomy.
