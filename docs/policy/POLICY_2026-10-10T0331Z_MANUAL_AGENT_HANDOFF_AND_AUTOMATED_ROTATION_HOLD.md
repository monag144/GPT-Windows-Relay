# Manual agent handoff and automated rotation hold — 2026-10-10T0331Z

Date: **2026-10-10 03:31 UTC / 2026-10-09 20:31 America/Los_Angeles**. User directive in PC Engineering 15: the already working Windows launcher is the **only approved agent-to-agent handoff method for now**. **Put every other agent/conversation switching method on hold.** This is a scoped operational policy, not a claim that any pre-existing background process has been technically disabled.

## Effective user instruction and precedence

- **Allow only a user-requested, one-shot invocation** of the existing working launcher at `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay\test\Run-Copy-Contents.cmd`, after staging the next-agent handoff in `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay\test\Copy Contents.txt`. The existing `Copy-Contents-To-ChatGPT.ps1` is a required local companion. Do not reimplement this workflow while it remains functional.
- **Hold—not remove or rewrite—other ways of opening a new engineering chat / transferring to a new agent:** automatic rotation at a numbered-operation threshold, Firefox extension-managed fresh-chat rotation, unattended session-switch watchers/supervisors, fallback navigation/hand-off mechanisms, and the in-development/new replacement switching system. Do not trigger, schedule, resume, repair, or continue building those methods on the user's behalf unless the user explicitly lifts the hold.
- This newer, specific user instruction **overrides earlier planned or recommended automatic rotation behavior** for *agent/conversation switching*, including the instruction in `docs/RELAY_OPERATIONAL_RULES.md` to rotate every 100 operations, related roadmap rotation plans, and any stale preexisting handoff footers. It does **not** grant permission to exceed the engineering ordinal budget or to reuse operation IDs; stop safely at a series boundary and request an explicit manual handoff rather than silently auto-rotating.
- The hold is **not** a blanket suspension of existing relay transport reliability features, backend result recovery, crash protection, operator STOP, exact-once controls, or audit gates. Normal non-switching recovery must continue within its existing safety boundaries; it must not open a new chat or move agent ownership.
- No autonomous new-agent switching is authorized on a timer, operation count, or perceived chat length. **Every future handoff requires an explicit user request** until changed by a newer explicit directive.
- This repository policy **records the hold**. It does **not attest** that running Windows watchers/tasks or extension schedules have been disabled. Do not claim a process is stopped without observing and verifying that process. No Client/Firefox/service mutation was performed as part of this GitHub documentation change.

## Current approved manual handoff procedure

1. Confirm the user expressly requests the new-chat transfer. Identify the intended **successor** conversation/agent and next PCE series separately from the source conversation; do not equate a new ChatGPT chat with a new PCE number.
2. Read canonical `monag144/GPT-Windows-Relay/main` source-of-truth index, control harness, roadmap, backlog, previous audit, and current incidents for the handoff substance. Preserve the exact next unconsumed action ordinal and release-blocker status. Avoid invented successes.
3. Verify existing local files without searching/replacing a working script: `...\Client\Relay\test\Run-Copy-Contents.cmd` and `...\Client\Relay\test\Copy-Contents-To-ChatGPT.ps1`; stage the handoff in `...\Client\Relay\test\Copy Contents.txt`. Create a content-addressed backup of nonidentical previous text and verify staged SHA-256/readback before launch.
4. Stage handoff text with safe Windows-path quoting, e.g. Python **raw triple-quoted string** (do not embed `C:\Users\...` in a normal Python string, because `\\U` is a Unicode escape). Include source agent, explicitly intended target agent, the next unconsumed operation, known defects, git/audit provenance and the manual-switch-only instruction.
5. Launch the **known existing** `Run-Copy-Contents.cmd` **once**, on the user's request. An isolated delayed process can avoid interfering with the current relay result. Do not start a recurring watcher. The launcher itself implements existing Firefox focus → New Chat → paste → Enter behavior; this note does not attest its script contents or imply the launcher files are tracked in GitHub.
6. Distinguish `launcher request succeeded` from `new-chat handoff delivered`. Inspect for actual newly created conversation and received opening message. Record the exact successor-series/session identity separately: a pasted handoff that still says `PCE15` does **not** prove migration to `PCE16`.
7. Do not consume, reissue, or infer a PCE operation ordinal during unnumbered handoff scripting. If uncertain, report UNKNOWN and fail closed.

## Observed acceptance and known hitch

Proven successful handoff on **2026-10-10 at 03:21 UTC**: `HANDOFF15-ONE-TIME-KNOWN-LAUNCHER-20261010-02` returned `status=OK`, `exit_code=0`, staged SHA-256 `0090d560ac1a4d0b172d20bc9ac722f3270d7cf33315e43c288225237f6df8ea`, verified exact launcher path, and requested one detached launcher run (PID `7348`). Its immediate stdout correctly said `NEW_CHAT_DELIVERY_NOT_YET_VERIFIED=True`. **The user subsequently explicitly confirmed “That worked.”** This is user-confirmed delivery, not an automatic transport attestation. The old handoff still identified the new agent as **PCE15** / `pce15.1`; this is a known **successor-series identity defect** to correct in the *next manually authorized handoff*, not a reason to run or build automatic switching now. At time of handoff, `PCE15.050` was unconsumed and should not be presumed completed.

The first one-shot attempt `HANDOFF15-ONE-TIME-EXISTING-LAUNCHER-20261010-01` failed with Python `SyntaxError: unicodeescape` before staging/launching, caused by an unescaped `C:\Users\...` path in its handoff literal. The second one-shot used raw-string quoting and returned OK. Do not repeat that failure mechanism.

Further observed evidence: documentation sync `GOVSYNC15-AUDIT-045-049-20261010-01` had passed, with 34 GitHub documents verified, 35 expected untracked local paths, audit [45,49] accepted, and `mutation_authorized=false`. The earlier exact-once source-level backend defects are still open; do not mark relay product release-ready because handoff transfer succeeded.

## Resume conditions and safety

This hold stays in force until **explicit user approval to resume a named alternative method**. Any later proposal must first prove that no background/manual switch can accidentally issue a duplicate chat handoff; then obtain authorization before runtime modifications, enablement or unattended testing. Keep the one-shot script as fallback unless the user changes that preference. Do not claim the other methods were uninstalled, physically deactivated, or deleted.

Supporting dated method record: `docs/handoffs/HANDOFF_2026-10-10T0331Z_ONE_SHOT_WINDOWS_SCRIPT_AGENT_TRANSFER.md`.

**Policy: manual user-requested script only; all alternative agent/chat switching approaches ON HOLD.**
