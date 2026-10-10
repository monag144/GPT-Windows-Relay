# One-shot Windows script transfer between ChatGPT engineering agents — 2026-10-10T0331Z

**Outcome: USER-CONFIRMED HANDOFF WORKED.** This is a procedure and evidence record, not a declaration that automated rotation passed. Time recorded **2026-10-10 03:31 UTC (2026-10-09 20:31 America/Los_Angeles)**. Canonical GitHub repository: `monag144/GPT-Windows-Relay/main`. The user expressly instructed that *all other agent/conversation switching methods stay on hold for now*. Controlling timestamped policy: `docs/policy/POLICY_2026-10-10T0331Z_MANUAL_AGENT_HANDOFF_AND_AUTOMATED_ROTATION_HOLD.md`.

## Existing, verified working launcher

- Script/entry point: `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay\test\Run-Copy-Contents.cmd`
- Companion: `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay\test\Copy-Contents-To-ChatGPT.ps1`
- Handoff input text: `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay\test\Copy Contents.txt`
- Actual behavior confirmed by user: focus the existing Firefox session, create a ChatGPT new chat, paste the staged handoff, and submit with Enter. Use the existing launcher instead of recreating its detection/automation logic.
- This documentation confirms local script **existence at execution time**, not whether any of these three files is committed to GitHub. Do not substitute guessed source content for the installed script.

## Successful one-shot event

Windows Relay action ID `HANDOFF15-ONE-TIME-KNOWN-LAUNCHER-20261010-02`; session `pce15.1`, shell `python`, status `OK`, exit code `0` at **2026-10-10 03:21:02 UTC**. Verified SHA-256 of staged handoff body: `0090d560ac1a4d0b172d20bc9ac722f3270d7cf33315e43c288225237f6df8ea`. Launcher path was checked and delayed detached worker started with PID `7348`. Stdout declared `ONE_TIME_MANUAL_LAUNCH_REQUESTED=True`, `AUTOMATIC_AGENT_ROTATION_NOT_STARTED=True`, and `NEW_CHAT_DELIVERY_NOT_YET_VERIFIED=True`; therefore the command alone proves only staging and launch. **The user later confirmed: “Good job. That worked.”** This provides user confirmation of the actual new-chat handoff.

Preceding failed attempt `HANDOFF15-ONE-TIME-EXISTING-LAUNCHER-20261010-01` had `COMMAND_FAILED`, `SyntaxError: (unicode error) 'unicodeescape'`, before staging or launching. Cause was embedding `C:\Users\...` in a non-raw Python multiline string. Corrective technique uses `r"""..."""` for handoff prose and content-addressed backup/sha readback prior to launching.

## Replicable operator-facing method

1. Confirm the user specifically authorizes a **single new chat**. No new chat should be opened by an operation counter, scheduler, stalled-session watchdog, or agent guess.
2. Read GitHub `main` policy/index/control harness/audit and write a complete successor-ready handoff in `Copy Contents.txt`; preserve previous non-identical bytes under a hash-named backup, then SHA-256 verify the staged file. Use raw-string Windows-path handling.
3. Before staging, name the *source* series and the *intended target* series separately. For this historical example, the handoff body unfortunately labeled the recipient `PCE15`/`pce15.1` instead of establishing `PCE16`. **This is a known identity/numbering hitch.** On a future user-approved transfer, explicitly use the requested successor series/title/session and have the new agent verify it; do not automatically renumber an ongoing operation or assume a new chat increments the PCE series.
4. Verify `Run-Copy-Contents.cmd` and `Copy-Contents-To-ChatGPT.ps1` exist. Invoke the existing CMD launcher **exactly once** after staging. Delayed separate launcher process can avoid disrupting relay message display. Avoid building or enabling replacement systems.
5. Require delivery evidence in the actual new chat and then confirm the successor identity. A successful detached process ID is not sufficient by itself. Preserve any uncertain transition as UNKNOWN; never blindly resend a potentially delivered handoff.
6. Preserve active incident blockers, next unused PCE ordinal, user STOP/ARM authority, and audit cadence. Here the handoff carried `PCE15.050` as unconsumed after audit [45,49] preflight succeeded.

This workflow was successfully used in the **one manually requested event**; it is not acceptance evidence for unattended multi-agent rotation, session-title renaming, auto-detection of successor numbering, crash recovery, or exact-once execution safety.

## Freeze on alternatives

Only this user-requested script-based handoff is approved for now. Automatic ChatGPT fresh-chat rotation, browser-resident transfer, scheduled switching, the replacement agent-switching project, auto-handoff fallbacks and repair/resumption of those alternatives are **ON HOLD** until explicit user direction. Do not dismantle the relay's unrelated recovery controls. Documentation does not prove an already-running scheduled process was stopped. Do not silently send another new-chat handoff or consume `PCE15.050`.

**Evidence classification:** User-confirmed working one-shot manual handoff; successor numbering defect OPEN; automatic switching techniques PAUSED BY USER DIRECTIVE; no product release or installed background-process state claimed.
