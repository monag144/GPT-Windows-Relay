# Incident — Stale queued relay action attempted after operator standby

**Date:** 2026-10-06 (America/Los_Angeles)  
**Packet:** `PCE7.447R-interruption-reconcile-001`  
**Component:** Windows browser bridge / relay transport

## Summary

After the operator explicitly instructed the assistant to stand by and not advance PCE7.447/PCE7.448, the browser bridge later surfaced a diagnostic for the previously emitted reconciliation packet:

- state: `ACTION_FAILED`
- detail: `NetworkError when attempting to fetch resource.`
- recommended action from bridge: diagnose and reissue under a new unique ID

The packet was **not reissued**.

There is no evidence in the returned diagnostic that the Windows command executed. The failure occurred at the browser-to-relay fetch boundary, and no `GPT_WINDOWS_RESULT` for the packet was received.

## Why this is an incident

A prior relay action remained discoverable/eligible after the operator had explicitly halted relay work. Even though this attempt failed before a result was returned, operator standby must be treated as an execution barrier, not merely conversational intent.

This is consistent with prior evidence that delayed/out-of-order relay ingestion can occur.

## Containment

1. Do not reuse or resend `PCE7.447R-interruption-reconcile-001`.
2. Do not automatically reissue the intended command under a new ID.
3. Continue repository migration through the GitHub control plane only.
4. Treat the live Windows relay as unchanged until separately reconciled.
5. Preserve unique-operation-ID and saved-result semantics for any later restart.

## Required design follow-up

The Windows relay/browser control plane should gain an operator-cancel generation/epoch or equivalent barrier so that:

- packets discovered before an explicit operator halt cannot execute afterward;
- queued/discovered-but-unexecuted actions can be invalidated without touching completed-result replay safety;
- the bridge can distinguish transient network retry from an operator cancellation boundary;
- recovery logic never turns a deliberately halted action into a later surprise execution.

Until that exists, after an explicit operator standby/cancel, stale discovered packets must be treated as suspect and reconciled read-only before any new relay command is issued.
