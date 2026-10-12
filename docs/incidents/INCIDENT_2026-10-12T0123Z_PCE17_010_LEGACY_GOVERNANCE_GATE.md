# PCE17.010 blocked by legacy runtime governance gate — 2026-10-11 PDT

Observed native result at 2026-10-12 01:23:40 UTC from session pce17.1.
Operation: PCE17.010-readonly-live-backend-and-hud-identity.
Native status GOVERNANCE_BLOCKED, exit_code null; stderr `GOVERNANCE_CHECKPOINT_BLOCKED: github_checkpoint_audit_missing; no action reserved or executed`.
The read-only identity command was not executed. No process, backup or browser mutations took place.
Earlier PCE17.005 showed the same checkpoint block immediately after a correctly committed GitHub audit. PCE17.006 then succeeded.
GitHub main checkpoint required before .010 is not missing: docs/audits/AUDIT_2026-10-11_PCE17_005_009_CHECKPOINT.md was committed at a0cb4e28df45e2c16c13590a49cb3dfdee054109, then fetched and verified with blob 5a7d6a58481302c485e64406083bcdd795a8773c. Canonical harness blob ca2141c45726366abb889db0cb5a794ed8735075.
Interpretation: legacy relay is still applying runtime governance and is not receiving the GitHub checkpoint receipt, whereas engineering governance belongs to the assistant. This result strongly indicates a legacy dispatcher but does not itself attest the loaded backend executable path.
.010 is consumed even though not executed. Next unique engineering ordinal is .011. Do not replay .010, do not remove authentication or STOP protections, do not bypass the one-time identity verification at deployment.
Existing verified backup PCE17-006 and clean pending mission queue after PCE17.009 are preserved. No source deployment or manual operator action inferred.
Use .011 for read-only process identity through the relay if accepted. If legacy gate persists, do not skip more ordinals merely to avoid guardrails; reassess operator-approved non-relay transition.
