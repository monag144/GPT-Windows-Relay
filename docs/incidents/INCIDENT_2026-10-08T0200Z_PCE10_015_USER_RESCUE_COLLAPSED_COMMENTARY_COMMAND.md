# PCE10.015 user-rescue incident — collapsed commentary relay action

Observed after PCE10.014, reported by the Director on 2026-10-08 UTC (exact UI failure time unverified).

## User-facing observation

The Director reports that the assistant stopped or disappeared unexpectedly and the Windows relay command collapsed to a `Worked for X` artifact. The relay did not detect/recover it; the Director had to intervene and report the condition. The original PCE10.015 Windows result has not been supplied/verified.

## Confirmed conversation-side failure

The assistant emitted the PCE10.015 Windows action inside a **commentary/progress message**, then emitted a separate **empty final response**. This violates the canonical `docs/relay-sandwich-procedure.md` contract, which requires the complete visible-header → bare fenced `[GPT_WINDOWS_ACTION]` packet → visible-footer sandwich within the SAME DURABLE FINAL assistant response. Temporary commentary surfaces can collapse when a final message appears.

This EXACT failure class was previously documented as **Incident 6** in `docs/relay-rendering-incident-2026-10-03.md`, after packet `PCENG4-JOBAUTO-037`. Recurrence of a recorded DO NOT ATTEMPT is a harness/agent-output control failure.

## Detection gap

The current content script recognizes `COLLAPSED_STATUS_ARTIFACT` and contains `visibleExternalCollapseArtifact()`, but `scheduleExternalCollapseCheck()` immediately returns unless `consumerRecoveryContext()` is present. The same gate is used for consumer-only classification and recovery. PCE engineering commands have no guaranteed consumer mission context, leaving the `Worked for X` artifact unobserved at that boundary.

## Unproven items

- Whether the assistant was interrupted by model/runtime termination, a network transition, or merely finished with an empty final response: **unproven**. No authoritative generation/lifecycle telemetry has yet been retrieved.
- Whether PCE10.015 reached a backend: **unverified**. Do not replay the side effect based solely on an absent visible result.

## Classification / user impact

**REPEATED OUTPUT-CHANNEL RENDERING CONTRACT VIOLATION / ENGINEERING COLLAPSE DETECTOR COVERAGE GAP / UNNECESSARY USER INTERVENTION.**

The Director had to notice both the broken relay presentation and lack of autonomous detection. This is a regression against zero-babysitting.

## Corrective controls

1. Emit all relay command sandwiches in **one final assistant message**, never in commentary or a partial status. Opening and closing fences are exactly three bare backticks; no language or metadata; header and footer are visible prose in the same final message. Never send an empty final after a command in commentary.
2. Extend visible collapsed-artifact telemetry to PCE engineering conversations even without `consumerRecoveryContext`. Report a clear HUD incident, not generic idle.
3. Keep replay safety: do not infer packet bytes from `Worked for X`, and do not auto-execute or resend an uncertain original action.
4. Before reissuing PCE10.015 or assigning a successor operation, query durable relay state/results for `PCE10.015` and distinguish absent / in-flight / committed / delivery-uncertain states.
5. Test the engineering detection independently of consumer mission gating; prove a minimal **final-channel** read-only sandwich round trip before larger commands.

## Closure criteria

A PCE engineering `Worked for X` collapse is observed without a consumer mission, announced distinctly in HUD/evidence, and the next command safely round-trips via one durable final sandwich. Interruption cause remains open until generation lifecycle data exists.
