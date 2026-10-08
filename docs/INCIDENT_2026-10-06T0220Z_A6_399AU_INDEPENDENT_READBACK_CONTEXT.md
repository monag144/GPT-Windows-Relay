# Incident — A6.399au independent recovery readback/context split

Timestamp: 2026-10-06T0220Z  
Scope: consumer/r29-firefox-offline-tray recovery control plane  
Operations: A6.399au through A6.399ax

## Live evidence

A6.399au proved zero-touch independent prompt submission:

- detached worker started after the primary relay result was delivered;
- Firefox PID 19240;
- send exit 0;
- semantic Send button was invoked;
- composer departure was confirmed;
- the recovery prompt appeared as a real ChatGPT user turn without a reported Director submit action.

The extension-side secondary observer independently saw the response:

- 02:20:58Z: `gpt_recovery_advice_invalid`, reason `incomplete_envelope` while output was still streaming;
- 02:21:05Z: `gpt_recovery_advice_observed`, valid, repair `rebuild_browser_integration`.

The detached independent reader did not complete:

- 60 read attempts;
- every terminal read exited 1;
- verdict `RECOVERY_ADVICE_READBACK_TIMEOUT`.

A later foreground/relay-context probe using the same live adapter returned exit 0 and exposed the expected ChatGPT document text. This makes the failure an execution-context/timing problem rather than an envelope-regex failure.

## Additional production defect found during review

The production recovery supervisor embedded a fully parseable recovery-advice envelope containing the real incident ID inside its own user prompt. If UIA readback succeeded, the parser could mistake that prompt template for GPT's answer.

The malformed-advice coaching predicate also armed on either the opening or closing marker, allowing a streaming partial to look malformed prematurely.

## Source hardening

The r29 source now:

1. describes the required marker syntax without embedding a parseable bracketed envelope in the recovery request;
2. requires both opening and closing markers before malformed-advice coaching can arm;
3. records bounded `OOB_READ_RETRYING` recovery state on repeated independent-read exceptions instead of silently swallowing every error;
4. includes the last independent-read exception in the terminal timeout detail;
5. adds regression tests for self-parse prevention, streaming-partial handling, and read-error observability/recovery.

## Status

Partial acceptance only.

- zero-touch OOB send: PASS
- extension secondary observer: PASS after streaming completion
- independent Plane-D readback: FAIL / root execution-context error not yet captured
- production self-parse/streaming guards: SOURCE PATCHED, Windows validation pending
