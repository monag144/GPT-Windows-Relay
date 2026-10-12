# PCE17 periodic checkpoint failure — Proven legacy dispatcher root cause — 2026-10-11 Pacific

## Exact cause (verified from native PCE17.021 + GitHub control harness)

Live nested legacy backend: `C:\Users\Craig Morgan\Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay\runtime\windows_relay.py`, SHA256 `540F2589EEB4B6980C6947D26381E653F17C0886043514E39721268E998CAB93`. Last live listener PID `13344`.

The running backend calls **line 675**:
```python
evidence=module.engineering_preflight(f"PCE{series}",ordinal)
```
**It passes no `github_audit_receipt`.** The imported *local* `consumer/control_harness.py` is SHA256 `B3CA7A9458F485C0B3DC5719AD08398DF14D16E86E09ABF7D45BE7D37747495D` (different from canonical GitHub-main blob `ca2141c45726366abb889db0cb5a794ed8735075`). Local lines 250–258 confirm that `engineering_preflight` inspects `github_audit_receipt` and appends `github_checkpoint_audit_missing` if absent. The canonical GitHub harness has the same requirement for every fifth ordinal.

Therefore on PCE17 ordinals divisible by five, this legacy relay rejects the command *before reserve/execute* despite correctly committed GitHub audit files. This is a **missing argument / misplaced governance validation in the live legacy execution path**, not a missing GitHub file, user mistake, or auth failure.

Native observed rejected ordinals: `PCE17.005`, `.010`, `.015`, `.020`, all status `GOVERNANCE_BLOCKED`, none executed; .005/.010/.015/.020 each permanently consumed.

## Authoritative design

The operator expressly requires **no audit governance blockade in the Windows dispatcher**. Engineering cadence and GitHub-first audit/readback belong to the assistant engineer; actual Windows relay executor enforces real execution controls (authenticated transport, legitimate conversation ownership, operator STOP/disarm, dedupe and ID-collision protections). Do **not** remove those security protections.

The unified canonical development `windows-relay/windows_relay.py` at verified WIP commit `a35d325ce9a666a372e2a88bc7b60704bdf785f9`, SHA256 `BA29B6BFAAA453BE6669C47D5B5C4E8A9F36A07AAB9FAB046849CD93EC39F002`, has **no `engineering_preflight` call or `GOVERNANCE_CHECKPOINT_BLOCKED` dispatcher code**. Its `process` requires `validate_transport_identity`, checks `state.armed`, reserves action IDs, and handles duplicate/collision. HTTP POST retains authentication and operator token on owner binding. A separate unauthenticated `stdin` mode intentionally refuses execution and must not be treated as an audit block.

Regression test added to the same WIP branch: `windows-relay/tests/test_dispatcher_no_audit_gate.py`, commit `b85e26678065795338c2676cbe526dec0c75bb83`. Independently fetched and verified; **test execution has not yet been observed**, so do not report tests passing.

## Resolution/status

**Source-level corrective change already exists in staged canonical development build; it is NOT active yet.** Last positively verified live process remains the old nested backend and watchdog/HUD. Do **not** patch/restart the old nested runtime just to delete its gate: that would create further drift and possibly interrupt the user's working relay. Complete a bounded, independently scheduled and rollback-protected cutover into the single integrated development build, then verify a normal newly issued authenticated PCE ID divisible by five succeeds without a GitHub receipt being injected into the dispatcher. Preserve assistant-side periodic audits as administrative process without runtime blocking. Do not replay past blocked IDs.

## Safe next step

Current next unique ordinal PCE17.022. Before cutover, inspect/stage independent helper, legacy supervisor/process ancestry, 14 old scheduled tasks and any automatic triggers, pending/active side effects, backups and persistent Firefox extension. Avoid unrelated UI changes. User wants to USE the product with Relay+HUD+One-Click Go in one development build; later re-release from that same build after acceptance.
