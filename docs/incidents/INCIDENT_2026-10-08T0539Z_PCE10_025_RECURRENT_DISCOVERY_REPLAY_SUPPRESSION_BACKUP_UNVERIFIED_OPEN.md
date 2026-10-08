# INCIDENT — 2026-10-08T05:39Z — PCE10.025 repeated DISCOVERED + replay suppression; backup status unresolved

**STATUS: OPEN (P0 recurring relay execution failure).**  
**Affected operation:** PCE10.025; **do not blindly reissue or replay.**  
**Director's evidence:** screenshot `image(20261008-053733).png` and accompanying local relay HTTP/event excerpt `Pasted text(20261008-053739).txt` (2,999 lines spanning 2026-10-07 22:28:25–22:37:34 America/Los_Angeles).  
**Canonical source:** `monag144/GPT-Windows-Relay`, branch `pce10/reconcile-control-and-rotation`.  
**Windows source checkout:** `C:\Users\Craig Morgan\Downloads\Dev\GPT\GPT-Windows-Relay`.  
**Live runtime:** `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay`.

## Observed failure

Director screenshot at roughly 2026-10-07 22:37 PDT shows HUD `DISCOVERED PCE10.025` at **326 seconds**, `Firefox IDLE • relay_packet_discovered • 326s`, `Relay ONLINE • ARMED • pending 2`, with UI `DISCOVERED • packet parsed; settling before execution`. The assistant packet is visible in ChatGPT code-rendering surface and the conversation URL is `https://chatgpt.com/c/6ac6cf1e-c210-83e8-be8f-77f4b2ca53c1`.

The director-supplied server event log captures:

- **22:32:05:** `BROWSER_EVENT relay_packet_discovered`, followed immediately by **`BROWSER_EVENT relay_result_replay_suppressed`**.
- Continuous `GET /status HTTP/1.1 200`, periodic Firefox `/browser-heartbeat?integration_connected=1`, and frequent `/mission-next` until the excerpt ends at **22:37:34**; these establish liveness/polling only, not action execution.
- There are **two `POST /action` events earlier in the capture**, at **22:28:39** and **22:30:54**, associated by timing with previous work (.024 and the governance audit sync); **there is no `POST /action` after the 22:32:05 discovery in the provided excerpt**. Action IDs are not printed on the HTTP lines; do not claim packet-level linkage from HTTP timing alone.
- No PCE10.025 `[GPT_WINDOWS_RESULT]` has been provided and no PCE10.025 backend processed/saved-result lookup is available. Status is **EXECUTION UNVERIFIED / LIKELY SUPPRESSED BEFORE DISPATCH**, not an unconditional assertion that no action could have executed.

**Incident classification:** repeat of the same discovery→false replay suppression failure pattern observed for PCE10.018 and PCE10.021. Operationally the >=45s watchdog/extension recovery failed to unstick a packet visible for 326s, despite online backend and heartbeat.

## Root cause and runtime revision investigation (OPEN)

Codex previously reported local commit `7c38e90 Fix false result suppression and stalled scanner recovery` with strict standalone `[GPT_WINDOWS_RESULT]` matching, authenticated `/packet-status`, and tab-scoped 45-second extension alarm recovery in both extension variants. PCE10.023 confirmed `7c38e90` and HUD commit `d5df0b3` in the **local checkout**, but the source acceptance Windows suite failed. PCE10.024 captured failing legacy selector / polling expectations, source acceptance remained BLOCKED. **No verified live extension activation of the Codex revision was recorded**; a disk copy does not prove running Firefox loaded the fix.

Required investigation by Codex:
1. Inspect durable backend `state.json`, `results/PCE10.025.json` and `browser-events.jsonl`, including packet_id, result-suppression reason, browser content-script startup revision, extension-background watchdog alarms, and `/packet-status` requests.
2. Determine whether PCE10.025 was falsely treated as completed because its ID appeared in a preceding user/assistant turn or because of stale page-local attempted IDs, or another actual mechanism. Do not conclude until state evidence is read.
3. Determine **running** extension content and worker revision, Firefox tab/conversation binding and permissions. Verify actual loaded code, not only local Git status or live JS hashes.
4. Repair the exact cause and follow with a bounded live delivery/recovery canary, honoring STOP and exact-once rules. No global Firefox termination or blind PCE10.025 replay.
5. Address `/status` polling storm separately while retaining timely STOP.

## Backup verification request — IMPORTANT / NOT YET PROVED

The Director explicitly asks whether **the last build** is backed up, and whether a rollback copy exists.

**Historical evidence (partial backup reported):**
- PCE10.020 emitted `OK` and previously reported staging exactly three live content scripts (`content.js`, `extension/content.js`, `extension-persistent/content.js`) after creating an exact-byte backup/manifest at:
  `%LOCALAPPDATA%\GPTWindowsRelay\backups\PCE10.020-20261008T031613Z\manifest.json`
- The `staged_firefox_activation.py` source identifies these three backup entries, checks `previous_sha256` against each saved original under the manifest directory, and refuses mismatched/missing files.
- PCE10.020 did **not** reload the addon or refresh Firefox. Therefore the reported backup is of **three pre-stage script files**, **not independently evidence of a complete, runnable prior production build**.
- Codex local commit `d5df0b3` also reportedly changed `hud.py` in both source and the live workspace, but **no complete live snapshot immediately preceding that HUD change is established in supplied evidence**.
- `windows-relay/sync-live.py` contains backup-on-copy code, but its existence is **not proof it ran** for the latest version.
- Codex's local Git commits are source-version objects; **not proof of a separately verified, complete live-runtime backup**, and remote GitHub visibility was not confirmed in the preceding audit.

**CURRENT VERIFICATION VERDICT:**
- `PCE10.020 THREE-FILE ROLLBACK=REPORTED_FROM_SAVED_OPERATION`
- `CURRENT_BACKUP_FILES_PRESENT_AND_SHA256_MATCH=NOT_YET_CHECKED_ON_WINDOWS`
- `LATEST_FULL_LIVE_BUILD_BACKUP=NOT_VERIFIED`
- `LIVE_DEPLOYMENT_AFTER_CODEX_REPAIR=NOT_VERIFIED`
- `SAFE_ROLLBACK_READY=NOT_YET_ESTABLISHED`

**Codex must verify, read-only, before any new live mutation:**
1. Verify the named manifest actually exists, parses and retains `operation=PCE10.020`, expected file paths, `previous_sha256`, and `source_sha256`.
2. Verify each `manifest.parent/relative_path` backup file exists and hashes to `previous_sha256`; verify staged live files against `source_sha256`, explicitly reporting expected drift if later changes occurred.
3. Inspect dated backup/snapshot directories for a **full previous production build** (not only the three JS files). Inventory coverage of `windows_relay.py`, `hud.py`, service workers, manifests, extension content, control scripts and status; record exact timestamp, build/version, file counts, hashes and restore procedure.
4. Treat missing backups as a **HARD BLOCKER** for any new deployment. Before replacement of any live file, create a complete timestamped, hash-manifested, off-path snapshot with a bounded restore method. Preserve existing backup directories, tokens, state/results, and PCE10.020 manifest unchanged.
5. Publish an evidence-backed `BACKUP_VERIFIED` report showing physical file checks; **do not just print that backup support is implemented**.

## Status, links and safety

Prior composite remains OPEN: `docs/incidents/INCIDENT_2026-10-08T0503Z_PCE10_RECURRENT_DISCOVERY_STALL_CODEX_FIX_PENDING_ACCEPTANCE.md` and `docs/incidents/INCIDENT_2026-10-08T0502Z_PCE10_DISCOVERY_STALL_FALSE_RESULT_ACK_CODEX_REPAIR_OPEN.md`. The five-slot audit .020–.024 exists as `docs/audits/AUDIT_2026-10-08T0529Z_PCE10_OPERATIONS_020_024.md` and was synced into Windows checkout with `AUDIT_CHECKPOINT=GREEN` in `GOV-AUDIT-020-024-SYNC`. Next audit covering PCE10.025–.029 due before .030.

Do not overwrite the locally repaired `hud.py` (`d5df0b3`) with stale remote source while reconciling. Do not run a live deployment unless source acceptance, operator status, exact target identity and backup/rollback gates are proven. **This incident remains OPEN until Codex's runtime/backup evidence is received and a live autonomous recovery canary passes.**
