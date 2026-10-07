# PCE10.001 assumed canonical clone existed — 2026-10-07T2350Z

## Observation

PCE10.001 failed before repository or live-runtime mutation with:

`CANONICAL_WINDOWS_REPO_MISSING C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\GPT-Windows-Relay`

The source-of-truth index and workspace-discovery handoff describe that path as the **canonical local clone target / intended local clone**. They do not prove that a clone currently exists there.

## Classification

**ENGINEERING HARNESS / WORKSPACE-DISCOVERY CONTRACT VIOLATION**

The acceptance harness turned an intended path into an existence assertion instead of performing repository discovery by Git identity.

## Impact

- PCE10.001 executed no repository or live mutation.
- No rollback is required.
- Source acceptance remains pending.
- One PCE10 operation was consumed unnecessarily.

## Corrective rule

Before local repository work:

1. search bounded Windows development roots for Git repositories/worktrees whose `origin` resolves to `monag144/GPT-Windows-Relay`;
2. prefer the documented canonical target when it exists and has the correct remote;
3. if no valid local clone exists, create the canonical target from `monag144/GPT-Windows-Relay`;
4. never use an old `GPT-Termux-Relay` clone as the Windows mutation destination;
5. report the resolved local workspace path before mutation.

PCE10.002 retries the source-acceptance gate with this discovery rule.
