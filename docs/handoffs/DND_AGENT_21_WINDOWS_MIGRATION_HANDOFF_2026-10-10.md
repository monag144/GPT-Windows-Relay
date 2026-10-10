# D&D Roleplaying Bot — Agent 21 handoff — 2026-10-10

## Identity and immediate objective
**Recipient:** Agent 21 — **NOT** PC Engineer 21, and not a PCE-series engineering agent. Continue the D&D Telegram roleplaying bot migration from Android/Termux to Windows 10. User expressly permitted invoking **Codex CLI on the Windows computer** to do the remaining integration tasks. The user also expressly requested this **one-shot transfer** through the preexisting Windows script, including **Enter** to submit the entire handoff in the new chat. No automatic agent rotation or alternate chat-switching automation.

**STATUS: Do not assume switch or Codex invocation succeeded.** The browser bridge currently blocks execution with `relay_owner_transfer_requires_claim` (Codex attempt DND 064) and `relay_owner_unclaimed_inactive_tab` (write attempt 062). User must restore legitimate conversation ownership; do not bypass or spoof guard. Never blindly replay rejected side-effecting operations.

## Completed work and tests
- Isolated PR15.7 checkout: **56/56 distinct selected tests passed** on Windows 10 / Python 3.13.15 / pytest 8.4.2, **across segmented executions**. **Not** one uninterrupted full-suite run nor integration, bot runtime, deployment, Android data migration or live Telegram proof.
- Test breakdown: campaign creation 25/25 (first 20 in timed-out 041, isolated 21st in 047, final 4 in 048; unique coverage reconciled 049/056); learning structured-output schema 1/1 (050); learning runtime 4/4 (051); progression modernization 11/11 (052); continuity/congruity 15/15 (053–055).
- Windows repo `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot`, branch `fix/windows-python313-utf8-20261010`, HEAD `6bcc567ab75b62c2870c99319dcfc550fdd7823d`, preexisting untracked `?? cmd.exe` only at last verified receipt. **Do not modify, delete, or clean `cmd.exe`.**
- Isolated snapshot `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot\backups\pr157_a1b03ae2` sourced from `origin/codex/pr15-7-campaign-creation-20260930` commit `a1b03ae2cd0115a93fd9f5bef28acdfdc6c18112`. Diverged hundreds of commits: **do not wholesale merge**.
- Source archive rollback `backups/pr157_a1b03ae2_source.zip` SHA256 `0d0324d3b5fe9526d61285b071b699c4185760a398415c15b4c10aff6a75facc`.
- Strict fail-closed Windows ACL helper `app/services/windows_credential_security.py` SHA256 `aabbdd834adcddc983ef8471b24a53dba42c61eb372ec08b7e900dbea1a71b49`; credential-service implementation SHA256 `93ab3c55bf61f98870ec15b2c386b84cb44c2dd2fce1426dada53478e2d20fba`; isolated test SHA256 `20cc771c49ff204aae488a322fd870ec040641b3eab7c8823e6892b5a1fe69c4` (only synthetic temp-dir fixture adjustment); original test file backed up in `backups/security_portability_20261010_040`. Never disable Windows ACL checks to pass tests.
- Independent active-branch source stage created by **verified 061**:
  `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot-PR157-Windows-Stage-20261010-061`, **124 tracked source files**, 1,177,713 bytes. `STAGE_SOURCE_MANIFEST_2026-10-10.json` SHA256 `14e4a8efb3c71d422a35b064d33bb4ad563584ab0c89c00612e704b5b3d0101e`; no .git, .env, data or real secrets. Active checkout unchanged.
- Operation **062** intended to make backup `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot-PR157-Windows-Stage-Baseline-20261010-062.zip` and integration candidate `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot-PR157-Windows-Candidate-20261010-062`, but browser bridge rejected action. **Their existence and content have NOT been verified.** Temporary sibling names may also exist. **Read-only check first; do not blindly recreate/overwrite**.

## Integration discovery
Tests cover the isolated old snapshot, **not active application**. Operation 056 compared snapshot to active checkout:
- `app/services`: 31 absent, 14 different, 36 identical.
- `rpg_engine_bundle`: 2 absent, 3 different, 10 identical.
- `tests`: 26 absent, 6 different, 27 identical.
These totals are inventory differences, **not confirmed defects**, and not a prescription to copy every file.

Bounded campaign-creation import closure (059/060): **23 modules: 13 absent, six different, four identical.**
- Missing: `app/campaign_creation_schemas.py`; `app/services/campaign_creation_service.py`, `campaign_portability_service.py`, `api_credential_service.py`, `api_provider_catalog.py`, `api_setup_handoff_service.py`, `inference_access_service.py`, `windows_credential_security.py`, `model_router.py`, `model_runtime_service.py`, `aptitude_service.py`, `model_catalog.py`, `operation_trace_service.py`.
- Snapshot-only router wiring: `app/bot/campaign_creation_router.py`, `app/bot/inspection_router.py`; active router registration lacks same wiring.
- Files differing: `app/config.py`, `app/models.py`, `app/schemas.py`, `app/learning_schemas.py`, `app/services/group_game_service.py`, `app/main.py`, plus other existing services. Do **not** overwrite active definitions or regress other games.
- Snapshot `Settings` additions: `api_credential_store_path`, `openai_available_models`, `premium_ai_enabled`, `premium_ai_generation_units`. Snapshot `CheckProposal`: `aptitude_supports`, `aptitude_synergy`. Multiple snapshot-only campaign models/schema types need additive migration.
- Services `app/services/campaign_routing_service.py` and `campaign_service.py` were identical.

## Required work — user expressly delegates to Codex CLI
1. **After relay ownership is restored and actual 062 paths are inspected**: run `codex --version`, `codex exec --help`, then a bounded **read-only** `codex exec` in verified stage to design minimal dependency and model/schema/router integration, report risk and milestones. User explicitly authorized Codex CLI on Windows; only Windows relay ownership guard prevented previous attempt 064. Do not claim it previously ran.
2. Establish immutable rollback (verified source ZIP, stage manifest, separate candidate baseline), then **add missing modules only to candidate**. Resolve diverging config, models, schemas, routers and DB migrations by minimal additive changes after reviewing all imports and existing definitions. Never directly overwrite live D&D checkout. Preserve fail-closed Windows credential storage.
3. Run isolated synthetic credentials, provider routing, campaign creation, portability/export-import, Telegram bound-chat router, persistence, progression/learning and full first turn tests. Compare against existing suite and check regression of current Windows branch; cap timeouts and isolate tests, no real keys/campaign data.
4. When candidate is passing, review integration via Git, create separate commit/PR on an explicitly reviewed D&D branch, establish rollback/deployment gates, then eventually configure legitimate live credentials, run end-to-end Windows bot and confirm before deeming migration complete.

## Incidents and relay safety
- Op041 100-second campaign-suite timeout after 20 PASS; Windows locked temporary SQLite files. Segmented tests later passed. Incident `docs/incidents/DND_WINDOWS_041_CAMPAIGN_MODULE_TIMEOUT_LOCKED_DB_2026-10-10.md`.
- Op062 `relay_owner_unclaimed_inactive_tab`; unresolved side-effect uncertainty. Incident `docs/incidents/DND_WINDOWS_062_RELAY_OWNER_UNCLAIMED_INACTIVE_TAB_2026-10-10.md`.
- Op060 later received stale browser feedback despite earlier OK executor result. Do not replay.
- Op063 read-only stage/handoff script check authored, no returned executor receipt.
- Op064 requested Codex CLI via relay but feedback `relay_owner_transfer_requires_claim`, no confirmed command invocation. Incident `docs/incidents/DND_WINDOWS_064_CODEX_RELAY_OWNERSHIP_TRANSFER_REQUIRED_2026-10-10.md`. Stop packets until legitimate owner claim.
- The backend exact-once/collision and 500-ID cache defects are not fixed in live Client. Respect STOP, session ownership, never reuse an action ID or replay uncertain writes. DND command ordinals 060–064 audited in `docs/audits/DND_WINDOWS_MIGRATION_OPERATIONS_060_064_2026-10-10.md`; next packet if ownership is legitimately restored must be **DND-WINDOWS-20261010-065-...** if still October 10 Pacific, with fresh valid unique ID, read-only inspection first. Each five operations audit on GitHub BEFORE next multiple-of-five operation, as task-scoped convention. `engineering_preflight` is only for PCE names, not DND ordinals.
- All canonical Windows Relay governance and incident documents belong in `monag144/GPT-Windows-Relay` **main**, not the old `GPT-Termux-Relay` source. Windows D&D runtime changes belong in its own separate repo, not the Relay repo.
- Policy `docs/policy/SCRIPT_ONLY_AGENT_HANDOFF_2026-10-09.md` confirms existing one-shot script only, with explicit user request. Other automatic rotation methods permanently retired.

## User-requested Agent 21 handoff mechanics
**Target agent:** `Agent 21` (**not** `PCE21` / `PC Engineer 21`).
Existing script folder:
`C:\Users\Craig Morgan\Downloads\Dev\GPT\Client\Relay\test`
- Source payload: `Copy Contents.txt`.
- Launcher: `Run-Copy-Contents.cmd`.
- Companion: `Copy-Contents-To-ChatGPT.ps1`.
User expressly instructed write this full handoff to TXT **before** launching, and **press Enter** so the new chat actually submits. The previously established launcher switches Firefox, creates new chat, pastes, sends with Enter; a new window/composer draft is not proof of successful transfer.
Only after rightful relay ownership is recovered: inspect existing scripts and verify their send/Enter behavior without changing or circumventing them; create/backup and SHA-check the TXT; run launcher **once**; verify the actual delivered new-chat message/Agent 21 ack. If ambiguous, **do not rerun**. Do not claim the TXT currently contains this payload or the new agent was launched: GitHub handoff document is a durable source for preparing it when host connectivity returns.

## Canonical links and hashes
Windows Relay audit 050–054 `docs/audits/DND_WINDOWS_MIGRATION_OPERATIONS_050_054_2026-10-10.md`, audit 055–059 `docs/audits/DND_WINDOWS_MIGRATION_OPERATIONS_055_059_2026-10-10.md`, audit 060–064 `docs/audits/DND_WINDOWS_MIGRATION_OPERATIONS_060_064_2026-10-10.md`.
Read before action: `consumer/control_harness.py` blob `ca2141c45726366abb889db0cb5a794ed8735075`; `windows-relay/TASKS.md` `d49999dc29466a04ba2c27cc39f341b9162779e9`; dated index `bfa29203c03238015cb088d717810d818a980d90`; dated priorities `86c3e0c3f2d1c44de9cccdc819597f120c8732be`; safety `693ad770964352de7de26886ba3b4e295ac0357a`; sandwich `2b300c59320f144126f8a2a2c0b2dd5dbc349596`; script-only one-shot policy `944e6d0d5a4c573f848985cb2c01e0cda33a1ae2`. Outdated PCE10 legacy roadmap URI returns 404; use dated maintained docs instead.

**First step for Agent 21:** state that Codex has NOT executed; pause Windows packets until browser relay owner claim is established; then read-only inspect unknown 062 backup/candidate, confirm handoff receipt and proceed with explicit Codex read-only integration review. No live bot startup yet.
