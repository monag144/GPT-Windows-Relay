# PCE10.011 unscoped Firefox list-tabs bootstrap incident — 2026-10-08T0118Z

## Observation

PCE10.011 passed the committed migration-blob proof and reached the managed Firefox preflight. It then failed at:

`firefox_adapter.py list-tabs`

called without `--firefox-pid` or `--profile-path`.

No live content staging had begun.

## Root cause

The semantic PowerShell adapter intentionally treats unscoped `list-tabs` as a single-window operation:

- it gathers all visible Firefox `MozillaWindowClass` windows in scope;
- for ordinary actions such as `list-tabs`, it requires `$fw.Count -eq 1`;
- otherwise it fails closed with `FIREFOX_WINDOW_MATCH_COUNT_<N>`.

For a known ChatGPT conversation URL, this is the wrong bootstrap primitive when multiple Firefox windows may be visible.

The same adapter already provides `resolve-conversation-tab`, which is explicitly designed to scan multiple Firefox windows, bind to the exact canonical conversation URL, restore prior tab selection, and return the exact Firefox PID/tab identity when there is one match.

## Classification

**ACCEPTANCE-HARNESS FIREFOX BOOTSTRAP SELECTION DEFECT**

This does not invalidate established Firefox lifecycle facts. The acceptance gate encountered changed/ambiguous visible browser state, so bounded re-proof is authorized.

## Safety boundary

The failure occurred before the rollback-backed browser staging block.

- no live content files were copied;
- no add-on reload occurred;
- no ChatGPT refresh occurred;
- no rollback is required.

## Corrective rule

When an exact ChatGPT conversation URL is known:

1. call `resolve-conversation-tab --conversation-url <exact>` without guessing a PID;
2. require exactly one canonical URL match;
3. take the returned Firefox PID and exact tab name as the managed identity;
4. only then call PID-scoped `list-tabs`, `reload-addon`, `refresh-tab`, or other actions;
5. use unscoped `list-tabs` only when single-window Firefox state is itself the named acceptance condition.
