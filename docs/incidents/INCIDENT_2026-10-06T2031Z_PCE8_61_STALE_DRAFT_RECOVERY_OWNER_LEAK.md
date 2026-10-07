# Incident — PCE8.61 stale relay-result draft reacquired completed operation ownership

**Incident time:** 2026-10-06T20:31Z–21:14Z

**Affected live runtime:** protected Firefox v11 (`26CE6B9BCD63EF5ACB2043BEF0216EBA5D42623AEAF733C98DF264E183F83ED5`)

**Source corrective runtime:** v16, commit `694d47ab89596d5c3801f749caa352b951a2be52`

## Summary

PCE8.61 completed normally at 20:31:13Z: result send was confirmed, `relay_result_delivery_complete` fired, and the operation was counted. At 20:31:35Z the same completed packet was rediscovered as a relay-result composer draft. Draft recovery claimed `activeRelayOperationId` for PCE8.61 and attempted another send. The recovery attempt later failed/deferred because the Send button did not become ready within 90 seconds.

The live v11 `recoverExistingRelayDraft()` failure paths cleared `draftRecoveryInFlight` but did not clear `activeRelayOperationId`. The stale owner therefore survived the failed recovery attempt.

When PCE8.62 appeared at 21:07:41Z it was repeatedly queued and deferred with `reason=active_operation` for more than six minutes. It finally executed at 21:14:03Z only after the stale ownership condition cleared through later runtime activity.

## Root cause

`recoverExistingRelayDraft()` claimed the global action lane with `activeRelayOperationId=draft.id`, but ordinary unsuccessful exits (`chat_not_idle`, delivery-not-confirmed / send failure, and exception handling) returned without releasing that ownership. The `finally` block reset only `draftRecoveryInFlight`.

This violated the R0 bounded-owner requirement: failed recovery work must never monopolize the action lane indefinitely.

## Important distinction

The v15 source already contained additional protection that clears an already-attempted completed draft before adopting it. That protection reduces the exact v11 PCE8.61 replay symptom, but the general ownership leak still existed in v15 whenever draft recovery legitimately claimed an unresolved draft and then failed.

The corrective fix therefore addresses the general invariant rather than special-casing PCE8.61.

## Corrective change

Source runtime v16 now releases draft-recovery ownership in `finally` whenever the draft still owns `activeRelayOperationId`. It emits `relay_operation_owner_released` with `reason=draft_recovery_attempt_finished`, schedules the deferred-action drain, and schedules a watched-turn inspection.

A regression contract verifies that all ordinary unsuccessful draft-recovery exits pass through this owner-release `finally` path.

## Validation

- Targeted browser-contract suite: 55 tests PASS.
- Full Windows-relay suite under canonical `PYTHONPATH=<repo>\windows-relay`: 273 tests PASS.
- Consumer suite under canonical `PYTHONPATH=<repo>\consumer`: 99 tests PASS.
- Source content copies are identical at SHA256 `9541A890A80A8200F949E6D7DA7132C10335BFABD487E0B89047919C6B1B899E`.
- Corrective source commit: `694d47ab89596d5c3801f749caa352b951a2be52`.
- Protected live runtime remains v11 and was not mutated by the source repair.

## Acceptance still required

This incident is fixed in source, not yet closed in live acceptance. R0 still requires guarded v16 activation on the exact managed engineering conversation, a fresh exact canary, proof that failed draft recovery cannot strand a later packet, and a sustained multi-operation soak with zero unplanned user intervention.

Do not treat source-green v16 as a promoted live baseline until those runtime gates pass.

## Resolution evidence — PCE8.97 through PCE8.106

- PCE8.97/PCE8.98 live-proved failed-draft owner release with reason `draft_recovery_attempt_finished`; sentinel send/backend activity was zero.
- PCE8.100 proved exact-once forward progress after release with zero `active_operation` starvation.
- PCE8.106 proved five strict sequential exact-once operations with zero starvation, draft-recovery deferrals, duplicate anomalies, or non-v16 runtime starts.
- PCE8.61 regression is closed for this live Firefox failed-draft scenario; general stale-owner lease/deadman acceptance remains separate.
