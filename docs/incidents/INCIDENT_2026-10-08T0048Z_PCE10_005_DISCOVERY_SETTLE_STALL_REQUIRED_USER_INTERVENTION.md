# PCE10.005 discovery-settle stall required user intervention — 2026-10-08T0048Z

## Observation

The operator-visible HUD remained on:

- `DISCOVERED PCE10.005`;
- `relay_packet_discovered`;
- `packet parsed; settling before execution`;
- approximately 1116 seconds in that state;
- backend ONLINE / ARMED with pending count 2.

No `relay_action_execution_requested` transition followed.

The Director had to report the stuck state manually.

## Classification

**UNNECESSARY USER INTERVENTION / DISCOVERY-SETTLE LEASE FAILURE**

## Root cause

The content scanner stores a discovered packet in the in-memory `pending` map with a 500 ms timer.

On subsequent inspections, an unchanged packet on the same DOM unit immediately returns when:

`prior?.sig===sig && prior?.unit===unit`

The pending record has no timestamp/lease. If the original settle callback is lost, suspended, or otherwise never advances, every later recovery inspection sees the same pending entry and returns forever.

Existing recovery covered DOM disconnection and packet mutation during settle, but not a stale unchanged pending entry whose settle callback never advances.

## Impact

- PCE10.005 never reached Windows execution.
- Source acceptance did not run.
- No Windows backend/source/live mutation was caused by PCE10.005 itself.
- User intervention was required.
- The five-minute recovery scanner could not recover because the stale `pending` record short-circuited reinspection.

## Corrective change

1. Add a bounded discovery-settle pending lease.
2. Timestamp each pending settle record.
3. If an unchanged pending entry exceeds the lease, clear its timer/entry, emit an explicit stale-settle rearm event, and create a fresh settle timer.
4. Keep DOM-disconnect and packet-change reacquire behavior.
5. Add structural regression coverage for the stale unchanged pending case.
6. Promote the repaired content script to the managed Firefox runtime only after targeted/source tests are green.

## Acceptance

A valid visible packet must not remain in `DISCOVERED` indefinitely solely because an earlier settle timer failed to advance.
