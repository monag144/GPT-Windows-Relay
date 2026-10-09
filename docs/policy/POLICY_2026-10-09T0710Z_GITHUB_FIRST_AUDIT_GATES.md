# GitHub-first PCE checkpoint audit policy — 2026-10-09T0710Z

## Authority and zero-CI-credit routing

Canonical GitHub destination: `monag144/GPT-Windows-Relay/main`. Use the **connected GitHub connector** for repository reads, audit creation, subsequent commits, pull requests, merges, and readback. This requires **no GitHub Actions workflow** and consumes no CI run credits. Do not issue a Windows Relay command merely to persist an audit or push a Git commit. The retired Termux repository is never a Windows source or fallback.

## Strict five-operation cadence

Before attempting `PCE<n>.005`, commit the audit of `.000–.004`. Before `.010`, audit `.005–.009`; continue at every multiple of five through `.100`. A blocked attempt is documented but must not be retroactively marked as executed. Treat any missing operation receipt as **UNKNOWN**, not a fictitious success. Do not advance past `.100` within one series.

For series PCE12 and checkpoint .005 the canonical audit is:

`docs/audits/AUDIT_2026-10-09T0710Z_PCE12_000_004_CHECKPOINT.md`

Future audits follow `docs/audits/AUDIT_YYYY-MM-DDTHHMMZ_PCE<n>_SSS_EEE_CHECKPOINT.md`, with three-digit inclusive operation ordinals. Store small bounded records, ideally under 10 KiB.

## Procedure: GitHub only until live machine work is necessary

1. Read the source-of-truth index, actual Windows `consumer/control_harness.py`, backlog, roadmap, and current incident/handoff records via GitHub. Never substitute an obsolete local Termux checkout.
2. Check whether the audit already exists and whether the exact range has previously been committed; never blindly create another audit for the same range. Record evidence (each action, outcome, incidents/manual rescues, repeated approaches, tests, rollback, roadmap, operation budget and uncertain side effects).
3. Use the GitHub connector to commit the audit in a Windows-only branch, review it, and merge it into `main`. Preserve the base commit for rollback and do not rewrite historical evidence.
4. Read the audit file **from `main`** via GitHub and independently read `main` head SHA. Pass the resulting receipt to `engineering_preflight(series, next_ordinal, github_audit_receipt=...)` before constructing a Windows command. Required fields: `repository`, `branch="main"`, `source="github_connector"`, `path`, `start`, `end`, `commit_sha` (the verified main commit), `file_sha` (the blob SHA), `readback_verified=True`, and `url` in canonical commit-blob form.
5. **Fail closed** if the GitHub audit is absent, cannot be read back, the metadata/range is inconsistent, or the preflight returns `ok=False`. The Python function checks **metadata**, not GitHub server authentication: it must only consume evidence obtained and verified via the actual connected GitHub tool.
6. Use Windows Relay only when a step intrinsically requires local Windows runtime observation or mutation. GitHub-side documentation, audit recording, branch/PR management and GitHub code changes are not such steps.

## CI and runtime caveats

GitHub Actions credits are exhausted: do **not** dispatch, rerun or depend on GitHub Actions workflows. Pure static reviews and locally run tests outside Actions are permitted, but never claim that a test ran when only source review occurred.

Merging a harness change to GitHub does not automatically update a running Windows relay or its older governance gate. To clear a local `GOVERNANCE_BLOCKED` state, the installed gate must consume the verified GitHub receipt or receive a reviewed sync; do not circumvent or disable the checkpoint.

## Provenance

PCE12.005 was refused because the preceding five-operation audit was not yet persisted. The audit was subsequently created directly through the GitHub connector with .000 marked unknown and .001 navigation unverified. The original audited operations made no repository mutations.
