# D&D Windows Relay incident — operation 063 owner mismatch / inactive tab — 2026-10-10

## Observed failure and evidence boundary

After operation **062** was rejected as `relay_owner_unclaimed_inactive_tab`, the next unique operation **063** was intentionally read-only and limited to reconciling the filesystem effects of 062. The user returned the following `[GPT_WINDOWS_FEEDBACK]` payload, not a successful Windows EXEC receipt:

- `version=1`
- `type=RELAY_DIAGNOSTIC`
- `source=windows_browser_bridge`
- `state=ACTION_FAILED`
- `packet_id=DND-WINDOWS-20261010-063-READ-ONLY-RECONCILE-062-OUTPUTS`
- `detail=relay_owner_mismatch_inactive_tab`
- `recommended_action=Before retry: read roadmap/facts/incidents/log; prove net-new progress; log this failure; update development log; preserve rollback; check PCE8/PCE9 budget; then diagnose and reissue with a new unique id.`

There is **no** `[GPT_WINDOWS_RESULT]` for 063, no saved-result path, and no stdout. Do **not** claim the 063 Python code executed or verified the filesystem. The error string indicates a browser-bridge tab/owner mismatch as reported by the relay, but it does not disclose the authoritative owning conversation ID or prove the root cause. The previous 062 error `relay_owner_unclaimed_inactive_tab` also lacks an EXEC receipt; its intended writes may or may not have happened.

An earlier delayed diagnostic for 060 carried an `ACTION_FAILED` owner-unclaimed error, but a preceding verified `[GPT_WINDOWS_RESULT]` for 060 had `status=OK`, `exit_code=0`; retain that actual execution receipt without replaying 060 or treating a later browser diagnostic as proof of a second execution. See the separate 060 incident.

## Safety response

**STOP issuing Windows Relay action packets.** The intended read-only ownership diagnostic 063 was blocked after 062 was blocked; repeatedly presenting new packets is not a corrective recovery and could cause duplicate-action ambiguity. Mark both action IDs **062 and 063 consumed**; never reuse.

Preserve the original ChatGPT conversation, existing operator ownership restrictions, STOP semantics and all source rollback material. Do not force owner reassignment, ARM, service restart, extension restart, chat-switch, or any automated new-chat handoff. The user can foreground the existing conversation tab and check that Firefox is displaying this conversation and the expected relay extension/HUD before resuming. If multiple tabs exist, do **not** assume which one owns the relay without inspection; use an authorized and witnessed ownership restoration path, not bypass.

The next unique task-scoped ordinal would be **064**, but issue **no 064 packet** until the user confirms the correct conversation/tab is focused and ownership is restored (or provides relevant safe diagnostics). Then re-check canonical controls and send only a read-only `062` artifact reconciliation under a new ID. If still rejected, pause again. The PCE 000–100 ordinal policy belongs only to PCE series; DND operation numbers are separate. Automatic agent switching remains retired.

## Unverified 062 artifacts

Last verified 061 stage: `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot-PR157-Windows-Stage-20261010-061`, 124 tracked files, 1,177,713 bytes, manifest SHA256 `14e4a8efb3c71d422a35b064d33bb4ad563584ab0c89c00612e704b5b3d0101e`. Operation 062 intended independent:
- `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot-PR157-Windows-Stage-Baseline-20261010-062.zip`
- `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot-PR157-Windows-Candidate-20261010-062`
- possible temporary `._tmp_dnd_stage062_backup.zip` or `._dnd_candidate062_*` siblings.

None of those 062 files has a verified execution/readback receipt. Do not overwrite, delete, trust or deploy anything from those paths before a permitted read-only reconciliation.

The isolated PR15.7 targeted testing was **56/56 distinct cases passing in segmented Windows runs**, not end-to-end active bot integration. Verified prior Windows checkout branch `fix/windows-python313-utf8-20261010` at commit `6bcc567ab75b62c2870c99319dcfc550fdd7823d`, preexisting untracked `?? cmd.exe`. No later checkout-attestation available.

## GitHub documentation / cadence

Source-of-truth repository exclusively `monag144/GPT-Windows-Relay/main`, not deprecated Termux and not D&D source repository. Current canonical controls read: `consumer/control_harness.py` blob `ca2141c45726366abb889db0cb5a794ed8735075`, `windows-relay/TASKS.md` `d49999dc29466a04ba2c27cc39f341b9162779e9`, dated index `bfa29203c03238015cb088d717810d818a980d90`, backlog `a7b65a643cbcdecd440d6675d1dfb7190300a6fb`, priorities `86c3e0c3f2d1c44de9cccdc819597f120c8732be`, operating safety `693ad770964352de7de26886ba3b4e295ac0357a`, sandwich guide `2b300c59320f144126f8a2a2c0b2dd5dbc349596`. Legacy requested roadmap path `docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md` returned `NOT_FOUND` and is superseded by dated canonical docs.

Audit **060–064** must be completed GitHub-first before DND **065**; do not manufacture a successful execution for 062/063 or fabricate 064. No Windows command was performed during the GitHub incident documentation.
