# Incident — PowerShell DETACHED_PROCESS silently bypasses rotation script

2026-10-08T22:50Z UTC. Canonical repo monag144/GPT-Windows-Relay, branch pce11/one-click-go-recovery-and-doc-hygiene. **Observed and reproducible startup defect; semantic rotation still not proven.**

## Evidence

Operation PCE11.022 spawned a PowerShell worker with DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP. It exited with code 0 and produced no log or receipt. .023 checked a zero-byte log, no receipt, and PC Engineer 11 still selected. .024 found no living worker, Relay armed, two pending missions unchanged. .025 demonstrated that foreground execution with a missing handoff reaches HALT_BEFORE_CLICK. .026 failed a brittle static test before worker launch. .027 reaccepted source (7/7 focused, 532/532 Windows, 123/123 consumer, 5/5 JS) but DETACHED_PROCESS worker again exited 0 with phase None. .028 ran a five-mode negative startup matrix against the same script and deliberately nonexistent handoff file: foreground exit 2 receipt HALT_BEFORE_CLICK, new_process_group exit 2 receipt, detached exit 0 no receipt, detached+group exit 0 no receipt, CREATE_NO_WINDOW exit 2 receipt HALT_BEFORE_CLICK. No click and no handoff in these negative probes.

## Classification and repair

The Windows Python subprocess DETACHED_PROCESS creationflag is **disproven in the current Windows/PowerShell 5.1 runtime**. Exit 0 without receipt means startup path did not actually execute the script; it is NOT proof of rotation success. Do not repeat a DETACHED_PROCESS launcher in this environment. A separate CREATE_NO_WINDOW process does execute the script and writes a durable fail-closed receipt. Add a safe Windows-only regression test (test_semantic_rotation_launch_mode_agent011.py) exercising CREATE_NO_WINDOW with a missing handoff (must exit 2 and never click), and require source acceptance before use. Previously running detached workers no longer exist, verified as of .024; verify .027 no receipt and no process before any later attempted click.

## Next rotation and required proof

At next unique ordinal PCE11.029, reread six full controls and engineering_preflight(root,29,series=11), verify canonical head and new test, full Windows/consumer/JS acceptance, previous .027 no click/submit (inspect any prior receipt and worker processes), fresh operator STOP/arm/backend/browser owner/pending count, exact original extension SHA. Spawn the same unmodified tested script ONLY under CREATE_NO_WINDOW, never DETACHED_PROCESS, and wait for positive WAITING_FOR_SOURCE_RESULT receipt with process alive. Then the independent worker watches for the visible current result before a single semantic New Chat click and full PCE12 handoff. On any uncertain action, STOP and reconcile instead of replaying. Preserve PCE11.004 rollback, untouched pending missions and current Firefox extension.

Director's priority: the agent must semantically enact the new conversation and transfer its context, not ask the Director to navigate. Success requires a distinct new /c/ identity and handoff visible in the target; auto-title if possible, otherwise explicit unverified title marker, never falsely claim PCE12 governance ran. Rotation handoff source: docs/handoffs/HANDOFF_2026-10-08T2223Z_PCE11_TO_PCE12_SEMANTIC_ROTATION_20_OP.md.

**Incident status: root cause isolated; launch fix regression committed; live semantic transition pending.**
