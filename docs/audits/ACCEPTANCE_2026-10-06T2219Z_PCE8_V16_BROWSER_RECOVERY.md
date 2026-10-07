# PCE8 v16 browser recovery acceptance — 2026-10-06T22:19Z

v16 source fix: `694d47ab89596d5c3801f749caa352b951a2be52`.
Live SHA-256 on all three content-script copies: `9541A890A80A8200F949E6D7DA7132C10335BFABD487E0B89047919C6B1B899E`.

## Live evidence

- PCE8.73/PCE8.74A: guarded live v16 canary green.
- PCE8.97/PCE8.98: zero-UI virtual draft exercised the real failed-draft recovery path. Exactly one draft detection, controlled failure `PCE8_VIRTUAL_DRAFT_RECOVERY_FAIL`, and owner release `draft_recovery_attempt_finished`; zero backend execution and zero send-path activity for the sentinel.
- PCE8.99/PCE8.100: ordinary operation after release executed once and was accepted once with zero `active_operation` deferrals.
- PCE8.101-PCE8.106: five consecutive ordinary operations; each had exactly one discovery, execution, result, click, and acceptance. Zero active-operation starvation, zero draft-recovery deferrals, zero duplicate-count anomalies, strict sequential order, and zero non-v16 runtime starts.

## Conclusion

The PCE8.61 stale draft ownership regression is live-Firefox proven fixed for the failed-draft `finally`-release scenario. The v16 browser recovery gate for this regression is closed.

Still open separately: general stale-owner lease/deadman acceptance, whole-product STOP semantics, restart/signing/browser-matrix validation, managed-chat rotation, modern HUD recovery, and remote divergence review.
