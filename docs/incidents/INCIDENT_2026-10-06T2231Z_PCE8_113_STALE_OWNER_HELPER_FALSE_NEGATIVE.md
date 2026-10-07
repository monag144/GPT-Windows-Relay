# Incident: PCE8.113 stale-owner helper false negative — 2026-10-06T22:31Z

The detached PCE8.113 acceptance helper reported `REPLAY_RELEASE_EVENT_MISSING` and rolled back to v16 even though the browser had already emitted the required replay release event.

PCE8.115 bounded forensics found the complete product event chain at 22:30:39Z, including exactly one replay release with reason `stale_owner_lease_expired_for_exact_replay` and exactly one exact-visible release with reason `stale_owner_lease_expired_exact_result_visible`.

PCE8.116 classified the helper result as `HELPER_FALSE_NEGATIVE=True` and independently passed the product acceptance gates.

The rollback behavior itself was safe: exact v16 files were restored and a fresh baseline runtime was reacquired. The defect was therefore in event observation by the acceptance helper, not in stale-owner lease behavior.

Related audit-harness defects in this sequence were PCE8.114, which did not run because of a PowerShell parser error, and PCE8.114A, whose broad 30000-event object load timed out after already showing the helper rollback. Future audits should filter raw telemetry before JSON materialization and should not let helper terminal status override direct product telemetry.
