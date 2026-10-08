# PCE10 engineering collapse repair: partial multi-file write after error

## Observation

An attempted multi-file GitHub content-script update returned a safety/error response. A subsequent source check showed that `windows-relay/content.js` had nevertheless been committed with the engineering-collapse observer, while `windows-relay/extension/content.js` and `windows-relay/extension-persistent/content.js` were unchanged.

## Classification

**PARTIAL REPOSITORY MUTATION AFTER A REPORTED TOOL FAILURE.**

A tool-level failure cannot be interpreted as atomic rollback of earlier writes in the same orchestration.

## Recovery

Fetch each path and its HEAD blob SHA individually. Reconcile the two extension mirrors to the canonical source in separate commits, then verify byte identity and run source tests. This has been done in source; runtime acceptance remains pending.

## Permanent rule

For multi-file source operations, on any error inspect repository HEAD and all intended paths before another edit. Do not claim all-or-nothing behavior; use idempotent, individually verified writes and preserve evidence. Live file staging remains forbidden until full source acceptance and rollback preparation.
