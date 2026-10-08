# Codex implementation mission — FIX Windows Relay unattended execution

**Owner:** Codex operating on Windows; **priority P0**. The Director requests a real implementation and safe deployment, **not a test/research exercise**. Do not require the Director to reload Firefox, click RETRY, or keep issuing rescue prompts.

## Workspace and branch

- **Canonical source:** `C:\Users\Craig Morgan\Downloads\Dev\GPT\GPT-Windows-Relay`, GitHub `monag144/GPT-Windows-Relay`, branch `pce10/reconcile-control-and-rotation`.
- **Live runtime:** `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay`.
- **Durable backend:** `%LOCALAPPDATA%\GPTWindowsRelay\state.json`, `browser-events.jsonl`, `results\`, and `%APPDATA%\GPTWindowsRelay\bridge.json`.
- **Existing exact rollback staging:** `%LOCALAPPDATA%\GPTWindowsRelay\backups\PCE10.020-20261008T031613Z\manifest.json`. PCE10.020 staged three content JS files on disk but explicitly did **not** reload the running addon.
- **Read five controls first:** `consumer/control_harness.py`, `windows-relay/TASKS.md`, `docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md`, `docs/windows-relay-mission-and-roadmap.md`, `docs/relay-sandwich-procedure.md`. Follow 5-op audit, 20-op review, STOP priority, exact-once safety.

## Evidence that the relay is NOT fixed

- PCE10.005 stalled at `DISCOVERED` and required user intervention; PCE10.018 stalled for **3774 s**, PCE10.021 for **784 s**. Their execution cannot be assumed. The last two are the Director's uncompensated compromises.
- On 2026-10-07 21:35:39–21:35:59 local, localhost request log shows numerous `GET /status` per second, `GET /mission-next?browser_id=firefox` about every 1–2 seconds and `GET /browser-heartbeat?...integration_connected=1` about every five seconds; **no `POST /action` shown in that excerpt**. The backend accepts HTTP/Firefox heartbeats; that does not prove the command scanner is executing.
- `windows-relay/content.js`: `DISCOVERY_SETTLE_MS=500`, `DISCOVERY_SETTLE_LEASE_MS=5000`. `inspectUnit` creates `pending` with a timer; the lease re-arms **only when inspectUnit runs again**. A stuck/obsolete page script cannot independently trigger its own recovery.
- `windows-relay/relay-watchdog-loop.ps1`: `if(Listener){Start-Sleep -Seconds 10;continue}`. Historically it watches backend/HUD availability, so an ONLINE backend makes it skip browser failure. `discovery_stall_observer.py` and source hook were recently committed to observe stale discovery at 45 s, but they are **read-only and not deployed/proven live**; detection alone does not recover commands.
- `windows-relay/content.js:userTurnContainsPacketId` returns true on `elementText(nodes[i]).includes(packetId)` even with broad article/section conversation wrappers. This risks a false `relay_result_replay_suppressed` when an ID is merely mentioned, not delivered as a genuine user `[GPT_WINDOWS_RESULT]` turn. PCE10.018 recorded discovery followed by replay suppression with **no saved result/processed entry**, making this a high-priority root-cause candidate.
- `operatorControlPollTimer=setInterval(pollOperatorControlState,250)` drives roughly **four `/status` requests/second per connected content script**, plus HUD and other callers. This explains a large share of the request storm but not why execution stalls.
- A prior snapshot proved source JS SHA256 `269445f0a021e1219ce716bc70d6583513d26c16e7f250414c9b4aa37f1708d4` versus live JS `acab8626ccd7526ca159f2c52c63e8f5018a4235c69033141b5ee42f7d070804`, before staging. The extension's **in-memory/runtime revision is still unverified**. The page visibly runs the correct conversation despite older UIA resolver falsely saying no ChatGPT tab.
- Old status/HUD code declared DISCOVERED when it should have escalated to STALLED; source `hud.py` now has a 45 s age rule but live promotion was unverified.
- Code-bearing incident records: `docs/incidents/INCIDENT_2026-10-08T0420Z_PCE10_021_784S_DISCOVERY_WATCHDOG_BLINDSPOT.md`, `docs/incidents/INCIDENT_2026-10-08T0309Z_PCE10_018_DISCOVERED_STALL_USER_INTERVENTION.md`, `docs/incidents/INCIDENT_2026-10-08T0200Z_PCE10_015_USER_RESCUE_COLLAPSED_COMMENTARY_COMMAND.md`.

## IMPLEMENT — in this order

### P0-A. Make discovered commands execute or recover automatically
1. Inspect **durable state** of PCE10.018 and .021 before deciding anything. Do not replay either command or create another PCE operation merely as a workaround.
2. Fix the explicit result acknowledgment path. Replace broad `includes(packetId)` acceptance with genuine, author-role-verified user result parsing requiring `[GPT_WINDOWS_RESULT]`, exact ID, correct message boundary, and backend durable result identity. Reject assistant/code/prose/quoted text as acknowledgment; distinguish `RESULT_VISIBLE`, `EXECUTION_CONFIRMED`, `DELIVERY_UNCERTAIN`, `NO_EXECUTION`.
3. Fix `inspectUnit` settle behavior so a 500-ms settle cannot freeze forever. Pending records must have independently enforced deadlines and observable transitions. Trigger a safe recovery after 5 s even if the page-local timer is lost. A changed/disconnected unit must rebind and reparse; no duplicate execution.
4. Make one supervisor **outside the content script** responsible for stale discovery recovery, even while port 8766 remains ONLINE: use the existing watchdog/extension background architecture and durable packet-specific events, not an unscoped Firefox title search or a listener restart. Bind the recovery to the exact Firefox tab ID/conversation URL and operator generation. At 45 s or less show STALLED and initiate bounded tab-scoped scanner restart/reload if and only if backend processed state and exact-once rules permit. Never quit all Firefox, flood actions, or execute a reconstructed packet from event text.
5. Make the running extension actually load the fixed code. Reuse the PCE10.020 exact backups; determine and verify live addon identity/version/port PID and positive conversation binding. Complete the necessary managed addon reload and tab refresh **without Director intervention**, with rollback if activation fails. Avoid assuming a successful disk copy updated an already-running temporary addon.

### P0-B. Remove polling storm and improve liveness signal
1. Replace `setInterval(pollOperatorControlState,250)` with a single coalesced control-state channel plus a bounded low-frequency fallback; ensure operator STOP still interrupts promptly, handles disconnect/reconnect, and protects `stop_generation`.
2. Deduplicate concurrent `/status` calls from content/worker/HUD and log cause-specific stage events rather than treating a 200 heartbeat as execution health.
3. Surface actionable HUD states `DISCOVERED > STALLED > RECOVERING > EXECUTING > DELIVERING/COMPLETE` based on durable packet ID and timestamps; clearly distinguish listener alive, addon port connected, content scanner responsive, backend action executing, and result visible.

### P0-C. Restore keep-going behavior
1. Once a genuine result is visibly acknowledged, permit unattended continuation of the established mission. Do not require a new manual `continue`.
2. If ChatGPT's next response does not begin after a bounded interval, use the existing safe consumer-mission/handoff path to issue **one** deduplicated continuation prompt (not the original command). Only when operator ARMED, the exact conversation is owned, no generation is active, and no uncertain side effects exist.
3. Keep the progression source-controlled and observable: exact packet ID, assistant generation state, checkpoint gate, and no-repeat ledger. Operator STOP overrides recovery and continuing.

### P1-D. Clean up live Windows workspace AFTER P0 repair
Inventory `C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay`. Classify generated caches, old temporary scripts, duplicated source mirrors, abandoned staging, logs, backup manifests, live state/config/tokens, and captured evidence. Preserve ALL current runtime assets, `state.json`, result journals, incident evidence, secrets, the PCE10.020 rollback backup, and anything not proven disposable. Remove only safe debris; avoid recursive deletion of unknown files. Add a short before/after inventory and disk-space saving to TODO. Do not combine destructive cleanup with runtime cutover.

## Delivery requirements (FIX, not TEST)

- **Primary work is code changes and safe live activation**, not writing another test plan, generating fake probe operations, or running an expansive matrix. Do targeted inspection once, implement root-cause fixes immediately, and use only essential parse/compile sanity checks plus **one real bounded end-to-end canary** to prove observed execution and safe continuation.
- Stay on canonical Windows repository/branch. Commit meaningful repair(s), not test-only PRs. Mirror extension changes where required, but don't multiply duplicate scripts unnecessarily.
- Prioritize safe autonomous activation. If a hard product/security boundary makes a user action unavoidable, produce one precise blocker with proof; never silently hang, claim success without live evidence, or request repeated manual refreshes.
- Preserve exact-once/submit-once, STOP/disarm/kill intent, staged backups, and rollback. **No force killing Firefox and no blind retry/replay of PCE10.018/.021.**
- Completion report must provide: root cause found, files and commits changed, exact runtime/live revision, what watchdog now does after 5/45 s, reduction in `/status` polling, durable action result and visible acknowledgment, successful unattended continuation, any still-unresolved caveat, and cleanup disposition.
