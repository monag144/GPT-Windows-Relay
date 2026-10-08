# INCIDENT — 2026-10-08T05:44Z — PCE10.025 session-attempted latch / false replay suppression; Codex repair staged

**Status: OPEN — local source repair and live-file staging reported; no live activation, regression tests, or end-to-end canary.**  
**Related primary incident:** `docs/incidents/INCIDENT_2026-10-08T0539Z_PCE10_025_RECURRENT_DISCOVERY_REPLAY_SUPPRESSION_BACKUP_UNVERIFIED_OPEN.md`. Keep the earlier incident OPEN.  
**Prior recurrence:** PCE10.018 and PCE10.021 `DISCOVERED` stagnation.  
**Operator authority:** preserve STOP / OFF / KILL and exact-once; do **not** replay PCE10.025 without durable-state checks.

## New evidence provided by Director

Source: `Pasted text(20261008-054407).txt`, 112-line Codex session transcription, received 2026-10-08T05:44Z. Codex directly inspected the live state, `browser-events.jsonl`, `state.json`, the three JS script copies, canonical source and HUD.

Codex reported these exact durable browser events (UTC; both stamped **05:32:05Z**):

```json
{"time":"2026-10-08T05:32:05+00:00","event":"relay_packet_discovered","detail":{"packet_id":"PCE10.025","source":"watched_turn","browser_id":"firefox"}}
{"time":"2026-10-08T05:32:05+00:00","event":"relay_result_replay_suppressed","detail":{"packet_id":"PCE10.025","reason":"existing_user_result_turn","browser_id":"firefox"}}
```

Codex's backend inspection printed `NO_DURABLE_PCE10.025_RECORD` and found no corresponding `relay_action_execution_requested`. Therefore, **at time of inspection**, evidence supported PCE10.025 as discovered, falsely suppressed *before execution*, and not durably processed. The earlier Director screenshot showed `DISCOVERED PCE10.025` for 326 seconds while browser heartbeat and backend listener were healthy.

## Root cause identified by Codex — two stages, not one

1. The **running old live content script** treated PCE10.025's textual ID inside a visible result-like region as proof of a delivered prior `[GPT_WINDOWS_RESULT]`, emitting `relay_result_replay_suppressed` even though backend had no execution result. The previous canonical fix `7c38e90` had not been proved loaded in the browser.
2. The old content script had already **persisted the false suppression in its session's attempted-history ledger**. Merely loading a stricter matcher could leave `attempted.has('PCE10.025')` true and suppress it again. A robust repair must reconcile attempted-history with authenticated backend packet state, and remove only a genuinely unexecuted false marker.
3. The HUD did not classify `relay_result_replay_suppressed` as a terminal diagnostic. It kept displaying the earlier `DISCOVERED / packet parsed; settling before execution` phase rather than showing the actual suppression.

Codex initially attempted two exact-match PowerShell edits that failed (one for the JS `run` guard and one for HUD headline), then adjusted its edits and continued. No claim is made that either failed edit mutated the intended source.

## Codex implementation, as reported

**Local canonical commit:** `b0a01ee Rearm false relay replay suppressions`. Codex's local `git commit` transcript reports **four changed files, 72 insertions, five deletions**:

- `windows-relay/content.js`
- `windows-relay/extension/content.js`
- `windows-relay/extension-persistent/content.js`
- `windows-relay/hud.py`

Codex reports the new content behavior:

- Consult backend durable execution identity/status before accepting visible packet-ID evidence as a completed action.
- If a session attempted marker exists but the authenticated backend confirms **no execution**, discard that falsely latched marker and permit the **same exact visible packet** to re-arm, subject to STOP and exact-once checks.
- Make the HUD classify an explicit `relay_result_replay_suppressed` event as `REPLAY SUPPRESSED` instead of displaying the stale settling state.

**Reported live-file staging:** Codex also copied the three content scripts, `windows_relay.py`, extension service workers/manifest files, and HUD-related changes into the active `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay` workspace, stating that the content copies then matched the local canonical tree. Note the source commit lists only four files; the backend/worker/manifest files reportedly staged may originate from earlier local commit `7c38e90`. The exact staged file manifest and all SHA256s have not been supplied with this report.

**Runtime activation intentionally not performed:** Codex explicitly reports **NO Firefox reload, NO backend restart, NO pending packet launch, and NO tests**. Updating files on disk does not establish which content script is currently running in Firefox or which Python code is loaded in memory. Thus the repeated incident is **not closed**.

## Rollback / backup statement

Codex reports making a timestamped backup before staging:

`C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay\backups\pce10-replay-suppression-repair-20261007-224256`

**Backup status: REPORTED CREATED; NOT VERIFIED.** The supplied Codex transcript references the directory but does not expose an independently checked complete file list, all original/candidate SHA256s, backup manifest, or restore/cutover demonstration. This is not a certified full-build restore point. The older PCE10.020 three-script backup under `%LOCALAPPDATA%\GPTWindowsRelay\backups\PCE10.020-20261008T031613Z\manifest.json` remains separate and must not be overwritten. Do not state `BACKUP_VERIFIED` until filesystem evidence and rollback coverage are inspected.

**Source provenance warning:** As of this record's authoring, GitHub's canonical remote `pce10/reconcile-control-and-rotation` could not resolve abbreviated commit `b0a01ee` (422). GitHub `windows-relay/content.js` still contains the old suppression branch and remote `hud.py` still has the old `.relay-kill` early-exit. That remote snapshot is **stale relative to reported Codex local/live repairs**. Do not overwrite repaired local/runtime files by blindly syncing from remote; reconcile local and remote branch ancestry, preserve `7c38e90`, `d5df0b3`, and `b0a01ee`, and push after review.

## Requirements for acceptance / next Codex handoff

1. Confirm current durable state for `PCE10.025`, including any post-report execution/result, before allowing rearming. The incident evidence only proves its state **at Codex inspection**.
2. Verify physically the new backup directory, actual files, integrity hashes and coverage for complete live rollback (including content scripts, service workers, backend, HUD, manifests, control scripts and original state/config preservation).
3. Verify all staged source/live file hashes and exact running Firefox extension identity/revision; merely invoking a reload or observing heartbeat is insufficient.
4. Fix any remaining truly broken tests while updating stale pre-fix test expectations; do not reintroduce broad ID-only acknowledgment or unsafe 250ms polling.
5. Controlled activation only after rollback proof and explicit STOP/armed state validation; verify one fresh safe canary traverses discovery → backend action → durable saved result → visible confirmed user turn and that the independent 45s recovery works without Director intervention.
6. Keep the HTTP `GET /status` request storm and automatic keep-going reliability on the P0 list; this patch does not prove either issue closed.
7. Record test, activation, rollback and time-to-recovery evidence. **Do not close** until end-to-end production proof exists.

## Governance and relationship to other incidents

- Five-control read, five-operation audit every five attempted slots, twenty-operation review every 20 remain binding.
- Previous audit `PCE10.020–.024` completed and synchronized. Next audit `PCE10.025–.029` due before **PCE10.030**.
- PCE10.018/.021 remain unprocessed based on last confirmed evidence; no blind replay.
- Related `docs/incidents/INCIDENT_2026-10-08T0503Z_PCE10_RECURRENT_DISCOVERY_STALL_CODEX_FIX_PENDING_ACCEPTANCE.md`.
- HUD's `.relay-kill` startup incident was **provisionally administratively closed**; this replay-suppression HUD display change does not certify that the HUD launched.

**Final classification: P0 LIVE DISCOVERY FALSE SUPPRESSION, SOURCE+FILE REPAIR STAGED, BACKUP REPORTED BUT UNVERIFIED, INCIDENT OPEN.**
