# PCE11.013 historical v16 Git-object verification failed

Status: **OPEN** pending independently verified PCE11.014 diagnostic. Observed 2026-10-08T09:46:19Z–09:46:23Z.

## Delivery and impact
Packet `PCE11.013-independent-v16-supervisor-static-contract` executed with `COMMAND_FAILED`, exit code 2. Stderr: `PCE11_SUPERVISOR_BLOCKED=RuntimeError: v16 entrypoint blob mismatch`. This happened **before** mode `canary`; mode `preflight` only. No v16 server process was started, no main port/Firefox/HUD/STOP/mission queue mutation. The canonical GitHub source at that point was `1483167b0c0e376bec883f048d4f315169aac090`.

## Hypothesis, not yet proved
Source `windows-relay/tools/pce11_013_isolated_supervisor.py` hashes the on-disk historical `windows_relay.py` bytes as a Git blob. Windows checkout text conversion (for example CRLF under `core.autocrlf`) can change raw bytes while the checked-out Git object remains exact. The historical commit `694d47ab89596d5c3801f749caa352b951a2be52` has Git-tree blob `414b74121b1a5a5f2a049ebc84097223e7b5e69f` for `windows-relay/windows_relay.py` as independently fetched from GitHub. A clean working tree is not proof of raw-file byte equality.

## Corrective gate
GitHub-first source correction must compare both `git rev-parse HEAD:windows-relay/windows_relay.py` and working file's *normalized Git hash* via `git hash-object --path=windows-relay/windows_relay.py windows-relay/windows_relay.py` to the pinned historical blob; separately report raw byte SHA256 and raw Git-object difference. Fail closed if either normalized Git object differs. Test line-ending normalization and wrong Git object. Preserve old source and rollback; do not remove validation to force green.

## Additional independent-process safety finding
The existing canary code starts the process before `AssignProcessToJobObject`. If assignment fails, the child could survive without containment. **Do not run canary mode until launch-before-containment race is repaired and tested.** PCE11.014 should remain static validation only; live run later only under proven suspended-start/owned-job cleanup, independent port/state, and explicit source acceptance.

## Audit requirement
Include this attempted failed slot in the PCE11.010–.014 audit before ordinal .015. Record any further failure separately. Never retry the already-executed .013 action ID.