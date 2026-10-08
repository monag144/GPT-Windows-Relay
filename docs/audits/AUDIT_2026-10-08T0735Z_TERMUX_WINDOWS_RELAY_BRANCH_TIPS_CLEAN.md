# Termux Windows Relay branch-tip separation verified — 2026-10-08T0735Z

## Scope and method
Connected GitHub API: `monag144/GPT-Termux-Relay` REST branch listing (13 branch heads), each commit SHA's full recursive Git tree. Exact test: no tracked path begins `windows-relay/` at the listed tips; Git history and `consumer/` branches deliberately preserved. This is not an assertion that history contains zero previous Windows data.

## Verified counts
- 13 branch tips visited successfully; 0 tree retrieval failures.
- 0 of 13 contain tracked `windows-relay/` paths.
- `development/runtime-control` (repository default) has 0 `windows-relay/`, 0 `consumer/` paths.
- Consumer product history intentionally remains in `consumer/one-click-go`, r26, r27, r28, r29 and three PCE7 safety tips; those branches still contain `consumer/` code and therefore Termux is NOT a repository exclusively containing Android history.
- Historic Git objects and safety refs were not force-pushed or deleted.

## Boundary
**CLEAN for active Windows Relay source-directory ownership**. Canonical future Windows commits belong ONLY in `monag144/GPT-Windows-Relay`. Consumer r28 history in Termux is the frozen baseline reference until migrated/promoted through tested Windows GitHub processes. No Android source mutation, deletion, or false full-history erasure is implied.
