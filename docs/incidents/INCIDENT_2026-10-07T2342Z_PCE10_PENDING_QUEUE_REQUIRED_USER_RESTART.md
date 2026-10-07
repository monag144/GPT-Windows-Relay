# PCE10 pending-queue / user-restart intervention incident — 2026-10-07T2342Z

## Observation

During PCE10 bootstrap/continuation, the operator-visible HUD showed:

- current discovered packet: `PCE10.000`;
- relay state: ONLINE / ARMED;
- pending count: 2;
- no autonomous transition to the next planned engineering operation `PCE10.001`.

The Director had to intervene again, point out that the successor should already know `PCE10.001` is next, and state an intent to restart the relay manually.

## Classification

**UNNECESSARY USER INTERVENTION / CONTINUATION QUEUE FAILURE**

This is separate from the earlier successor-continuity incident. The new failure is at the pending-operation/continuation boundary: after PCE10 bootstrap was visible, the system did not present or advance the next planned operation without another user turn.

## Impact

- one additional manual user intervention;
- one manual relay restart is being performed by the Director;
- autonomous engineering continuity remains unproven;
- the pending queue is not sufficient evidence that the intended next operation is correctly represented.

## Corrective contract

1. The active engineering session must maintain an explicit next-operation queue.
2. Once an operation completes or reaches a restart boundary, the next authorized operation must already be represented without requiring the user to say "continue".
3. PCE10.001 is the next authorized operation after PCE10.000.
4. A relay restart must not erase the planned successor operation.
5. PCE10.101 remains forbidden; rotation to PCE11 is required before that ordinal.
6. Pending-count telemetry must be diagnosable: "pending N" alone is not acceptable if the operator cannot tell which operation IDs are queued.

## Acceptance requirement

Close only after a restarted relay consumes the intended PCE10.001 operation without another manual continuation prompt and the queue/telemetry makes the next operation identity observable.
