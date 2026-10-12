# PCE17.005 legacy runtime audit gate — 2026-10-11

**Local observation:** 2026-10-11 17:40 PDT / 2026-10-12 00:40:57 UTC. **Repository:** `monag144/GPT-Windows-Relay`.

## Observed result
- Submitted `PCE17.005-allowlisted-verified-operational-backup`, session `pce17.1`, over the still-running legacy Windows Relay.
- Native status `GOVERNANCE_BLOCKED`, exit_code null.
- Native stderr: `GOVERNANCE_CHECKPOINT_BLOCKED: github_checkpoint_audit_missing; no action reserved or executed`.
- The block occurred before backend reservation or PowerShell command execution. No backup from .005 was created by the attempted action. The earlier .004 partial backup is a separate unverified artifact.
- `.005` **is consumed** and must not be replayed, even though nothing executed.

## Independent GitHub audit verification
- Five-operation audit `docs/audits/AUDIT_2026-10-12T0038Z_PCE17_000_004_CHECKPOINT.md` was committed on canonical `main` at `dcd971faaf89f7e0eb8b3d4062bc1bdf7d0b00c1` and independently fetched with GitHub blob SHA `1a7015838836f33386a241e004fe75deb108c8af`.
- Canonical `consumer/control_harness.py` (blob `ca2141c45726366abb889db0cb5a794ed8735075`) requires the GitHub-first checkpoint before ordinal .005; it does not put a fifth-operation audit requirement on .006.
- The live nested `windows-relay/runtime/windows_relay.py` is older than the governance-cleaned canonical `windows-relay/windows_relay.py` on WIP `a35d325ce9a666a372e2a88bc7b60704bdf785f9`.
- It is **not established** why the old runtime failed to recognize a committed audit (possible missing local receipt or stale legacy preflight integration). Do not claim the audit is absent from GitHub, and do not weaken transport authentication or STOP to compensate.

## Next-action control
- At ChatGPT engineering layer, checkpoint for .000–.004 is satisfied by independently verified GitHub audit, and .005 is consumed. The next unique action is `PCE17.006`.
- A bounded allowlisted backup may be attempted with .006 if old runtime permits it; preserve original live state, excludes nested historical backups and virtual environments, and fail closed on unexpected directories or hash changes.
- If the old runtime continues to reject a legitimate next action, do not skip more ordinals blindly; use a separately user-approved local operator/Codex procedure for rollback and controlled activation of canonical build.
- Do not terminate the Windows Relay from a relay command expecting a result; old-runtime OFF and new canonical one-click START should be under explicit operator control after verified backup.
