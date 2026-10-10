# D&D Windows migration — ownership recovery development log — 2026-10-10

## Verified baseline
- Isolated PR15.7 snapshot: **56/56 distinct targeted pytest cases passed across separate Windows runs**, not a single uninterrupted run or application integration proof.
- Operation 061: active Windows checkout copied to independent 124-file staging tree `DnD-RP-Bot-PR157-Windows-Stage-20261010-061`, manifest SHA256 `14e4a8efb3c71d422a35b064d33bb4ad563584ab0c89c00612e704b5b3d0101e`. No user credentials/data or active-checkout mutations at that verified checkpoint.
- Operation 060: user provided Windows **OK/exit0** receipt; later a delayed `ACTION_FAILED` bridge diagnostic bearing the same packet ID. Treat the successful execution receipt as the evidence of completed action; do not replay.
- Operation 062: intended to make ZIP rollback backup and 16-module additive candidate, but bridge returned `relay_owner_unclaimed_inactive_tab` without an execution receipt. ZIP/candidate existence **unknown**.

## Incident and response
- Recorded `docs/incidents/DND_WINDOWS_062_RELAY_OWNER_UNCLAIMED_INACTIVE_TAB_2026-10-10.md`.
- Recorded `docs/incidents/DND_WINDOWS_060_DELAYED_OWNER_DIAGNOSTIC_2026-10-10.md`.
- Recorded `docs/incidents/DND_WINDOWS_063_RELAY_OWNER_MISMATCH_INACTIVE_TAB_2026-10-10.md`.
- User-controlled next step: foreground the existing ChatGPT conversation and inspect/recover the actual tab owner using authorized controls; do not create a new chat, restart or re-arm the relay, bypass owner checks, or repeatedly submit packets. Only after confirmation consider a new **064 read-only** reconciliation.
- Operation 063: read-only reconciliation was **blocked**, not executed, by `relay_owner_mismatch_inactive_tab`; only `[GPT_WINDOWS_FEEDBACK]` returned, without an EXEC receipt or filesystem proof. **Stop issuing Windows relay packets** pending a user-confirmed owner/tab restoration. Do not reuse IDs 062/063.
- Before any subsequent mutation verify rollback/checksum of current stage and intended destination state, avoid overwriting and preserve strict Windows credential ACL safeguards. Operation 062 attempted writes, 063 read-only probe failed before verified execution, and delayed 060 ownership feedback conflicts with its earlier confirmed success. Audit 060–064 before 065; do not invent completion of 064 or manufacture source/active-checkout proof.

## Source of truth
Windows Relay repository only `monag144/GPT-Windows-Relay/main`; dated control harness, TASKS, documentation index, backlog, mission, operating safety, action sandwich procedure. Old requested PCE10 roadmap path is 404 and superseded. Automatic agent/chat switching retired.