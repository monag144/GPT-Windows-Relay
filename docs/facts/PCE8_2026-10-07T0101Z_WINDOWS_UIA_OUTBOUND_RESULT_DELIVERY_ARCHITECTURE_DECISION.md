# PCE8 Windows/UIA Outbound Result Delivery Architecture Decision

UTC decision time: 2026-10-07T01:01Z
Pacific local time: 2026-10-06 18:01 PDT

## Status

Accepted architecture direction. Specialized sender foundation is source-accepted and committed, but backend integration and live deployment are not yet performed.

Foundation commit:
`14710a487933908fbddcd940ef65015a6c8c3984`

Foundation acceptance:
- 289 Windows relay tests passed.
- 99 consumer tests passed.
- PowerShell and Python parse gates passed.
- git diff --check passed.
- No real ChatGPT result send was performed.
- Live browser content remains protected v16.

## Decision

Split relay ownership by direction:

1. Browser extension remains the inbound sensor.
   - Discover GPT_WINDOWS_ACTION packets.
   - Observe ChatGPT turn state and browser conditions.
   - Report browser events and, where needed, visible-turn confirmation.
   - It must not reinject a result already handed to the Windows outbound sender.

2. Windows/UIA becomes the outbound result actuator.
   - Final GPT_WINDOWS_RESULT delivery is performed outside the content-script delivery state machine.
   - The specialized action is `send-relay-result`.
   - Result text is transported by UTF-8 file, not command-line payload.
   - The exact engineering Firefox tab is targeted through canonical `tabbrowser-tabs` identity and exact tab title.
   - Result insertion uses guarded clipboard paste as the primary and only insertion mechanism for this specialized path.
   - The composer must read back exactly before submission.
   - Submission requires exactly one semantic Send button and UI Automation InvokePattern.
   - There is no Enter-key fallback.

## Exact-once submission boundary

The outbound transaction has three states:

- `PRE_SUBMIT_FAILED`
  - Send was not invoked.
  - Automatic retry may be considered by the future integration layer after proving ownership and pause state.

- `SUBMITTED`
  - Send was invoked exactly once.
  - Composer clear was observed afterward.
  - Automatic resend is forbidden.

- `SUBMIT_UNCERTAIN`
  - Send invocation was attempted, but post-click confirmation was not proven.
  - Automatic resend is forbidden.
  - Recovery must inspect the actual ChatGPT turn before any further delivery decision.

The critical boundary is the moment immediately before `Invoke()` versus immediately after it. Any automatic retry logic must treat `send_invoked=true` as terminal for automatic sending.

## STOP semantics

The specialized sender contains operator-pause barriers before paste and immediately before Send invocation.

Target behavior for the integrated product:

- Explicit STOP prevents new Windows/UIA result transactions.
- A result pasted but not yet sent remains unsent.
- A transaction that has crossed the Send invocation boundary must never be automatically invoked again.
- Browser timers/recovery activity must still obey the whole-product quiescence generation protocol.
- Windows actuator quiescence must become part of the final whole-product STOP verification model before live acceptance.

The previously accepted correlated whole-product STOP source work remains preserved. The unfinished HUD durable-quiescence presentation candidate is frozen, not discarded, while this architecture is integrated.

## Why this replaces browser-owned outbound delivery

The browser-owned delivery state machine accumulated responsibility for:

- composer DOM mutation,
- Send discovery and click behavior,
- retry timers,
- draft ownership,
- recovery refreshes,
- deferred drains,
- post-submit watches,
- delivery confirmation,
- and STOP-time cancellation of all of the above.

Windows already contained a mature UIA/clipboard sender surface with exact composer targeting, clipboard preservation, semantic Send detection, InvokePattern support, and readback. Moving final result submission to that actuator reduces browser-side delivery complexity while retaining the extension for observation and inbound packet discovery.

## Specialized sender foundation

Committed files:

- `windows-relay/firefox_tab_adapter.ps1`
- `windows-relay/firefox_adapter.py`
- `windows-relay/tests/test_firefox_adapter.py`

Key guarantees already source-tested:

- UTF-8 file-backed result transport avoids Windows command-line length limits.
- Exact engineering tab title is required.
- Canonical Firefox tab parent AutomationId must be `tabbrowser-tabs`.
- Exactly one visible enabled `Ask ChatGPT` ProseMirror composer is required.
- Composer must be empty before result insertion.
- Clipboard is captured and restored in a finally path where available.
- Exact composer readback must equal the complete result text.
- Exactly one semantic Send button is required.
- Operator pause is checked before paste and again immediately before Send.
- Submission uses InvokePattern only.
- Enter fallback is forbidden.
- ValuePattern is not used to insert relay result text.
- Post-invocation uncertainty is reported instead of retried.

## Deliberately not done yet

- No backend result-completion integration.
- No automatic result sender orchestration.
- No content-script removal or simplification.
- No live Firefox adapter deployment.
- No live content-script deployment.
- No real-result canary through the new sender.
- No remote Git push.

## Integration sequence

The next phase must remain source-first:

1. Map the exact backend result completion and saved-result ownership boundary.
2. Add a durable outbound-delivery journal/state model with packet identity and terminal send phase.
3. Wire only completed results into the specialized sender.
4. Ensure STOP blocks scheduling and can verify Windows-actuator quiescence.
5. Disable browser-side reinjection only after equivalent visible-turn confirmation is proven.
6. Run focused tests and full regression.
7. Commit source integration independently.
8. Design a detached live cutover and rollback harness.
9. Perform one controlled real-result canary only after all preceding gates are green.

## Rollback discipline

The live relay remains on accepted browser v16 while this architecture is developed. Source commits do not imply live promotion. Any candidate integration failure must roll back source before stacking another behavioral change.

This document records an intentional workflow architecture change, not an incident.
