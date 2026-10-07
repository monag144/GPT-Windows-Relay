# PCE8 stale-owner lease/deadman acceptance — 2026-10-06T22:36Z

## Scope

This record closes the general browser-side stale-operation-owner lease/deadman acceptance gate. It is broader than the PCE8.61 failed-draft `finally` release regression already closed by the v16 browser recovery acceptance.

## Contract

`RELAY_STALL_PATIENCE_MS` is 300000 ms. `expireStaleRelayOperationOwner()` runs from `forceRecoveryPacketInspect()`, refuses release while the owner is inflight or draft recovery is active, retains a fresh owner before expiry, and after expiry emits one of two reasons: `stale_owner_lease_expired_for_exact_replay` or `stale_owner_lease_expired_exact_result_visible`.

## Live evidence

PCE8.113 armed an exact-engineering-route, zero-UI, runtime-local probe. No real composer text, clipboard path, backend action, or relay-result markup was injected.

Direct browser telemetry at 2026-10-06T22:30:39Z proved the intended sequence exactly once:

- fresh synthetic owner: `released=False`, `owner_retained=True`
- aged replay owner: release reason `stale_owner_lease_expired_for_exact_replay`; owner and claim timestamp cleared
- aged exact-visible owner: release reason `stale_owner_lease_expired_exact_result_visible`; owner and claim timestamp cleared; attempted history marked
- probe completed with zero probe errors

PCE8.116 independently proved exact event counts, strict event order, zero synthetic backend executions, zero result receipt, zero send attempts, zero send clicks, zero send acceptances, exact v16 live-file restoration, one backend listener PID 10380, and a clean repository.

## Conclusion

`GENERAL_STALE_OWNER_LEASE_DEADMAN_GATE=LIVE_PROVEN`. Browser-side ownership recovery acceptance is complete for both failed-draft release and the general five-minute stale-owner deadman.

Remaining R0 work is outside ownership recovery: whole-product STOP semantics, restart/signing/browser-matrix validation, safe managed-conversation rotation, separately guarded modern-HUD recovery, and local-versus-remote divergence review before any push.
