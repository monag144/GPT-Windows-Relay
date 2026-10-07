# Incident: OP019 promotion stopped by missing repository-local Git author identity

Date: 2026-10-07

Operation: `PCE8BOOT-OP019-promote-reconciled-v17-owner-main`

## Summary

The reconciled v17 + whole-product STOP + conversation-owner candidate passed the repeated source health gate (383 Windows tests, 99 consumer tests), JavaScript compile gate, and privacy/canonicality audit. Git then refused `git commit` because the newly created reconciliation checkout had no author identity configured.

## Impact

The failure occurred before creation or push of the reconciliation commit. No GitHub branch or tag was changed by OP019, and the live relay, Firefox runtime, and HUD were not modified. `origin/main` remained at `73719b209e40cc7d93c9d43751da9abfeaf5ab3b`.

## Corrective action

OP020 configures `user.name` and `user.email` only in the reconciliation repository, using the GitHub account identity already associated with this repository. Global Git configuration is intentionally left untouched. The complete health gates are rerun before promotion.
