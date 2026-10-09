# PCE12 — GitHub audit present, local gate still blocks — 2026-10-09T0732Z

## Observations
- PCE12.005-local-windows-authority-check returned `GOVERNANCE_BLOCKED`, `exit_code=null`, with `audit checkpoint missing before PCE12.005: PCE12.000-.004; no action reserved or executed`.
- GitHub PR #3 was subsequently merged. `main@7ce220ef9e7149a9849079464c1d539242d5cad3` includes the committed audit `docs/audits/AUDIT_2026-10-09T0710Z_PCE12_000_004_CHECKPOINT.md` and `consumer/control_harness.py::engineering_preflight`.
- The GitHub connector read back that audit on `main`: file SHA `ff63dd6a30d7ae832acedf73fd3986389b649913`.
- PCE12.005-verified-cursor-new-chat again returned `GOVERNANCE_BLOCKED` on 2026-10-09 07:32:05Z, with the identical range and `no action reserved or executed`.
- Current canonical `windows-relay/windows_relay.py` does not contain the marker `GOVERNANCE_CHECKPOINT_BLOCKED`. Thus this rejection occurs in an external or divergent locally deployed enforcement layer; exact location is not yet established.

## Impact and non-replay
No New chat click was dispatched by either attempted PCE12.005 packet. They are blocked requests, not successful executions. Repeating the same packet cannot fix an audit-consumption problem. Do not disable the checkpoint or forge a local audit entry.

## Current independent remediation
A narrow, manual Windows recovery is available as `tools/CLICK-NEW-CHAT.bat` in the canonical Windows repository. It locates exactly one visible enabled Firefox New chat element with UI Automation, foregrounds the target Firefox window, verifies the cursor position and dispatches one click. It is **not** a relay operation, local Git push, or GitHub Actions run. It must not be reported as executed until the operator actually runs it and supplies proof.

## Follow-up for local governance owner
Locate the actual `GOVERNANCE_CHECKPOINT_BLOCKED` implementation on the PC (installed relay/gate/updater), check whether it can read GitHub `main` audit receipts, and implement a verified secure readback/sync path. The v2 canonical harness API's mere existence on GitHub does not update the installed gate. Preserve rollback before replacing any local module; test checkpoint accept/reject, then resume relay once the real local gate is in sync.
