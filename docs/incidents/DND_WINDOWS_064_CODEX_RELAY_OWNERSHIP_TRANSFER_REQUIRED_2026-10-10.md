# D&D Bot Codex CLI launch blocked by relay ownership — 2026-10-10

## Exact user-returned feedback
Command packet `DND-WINDOWS-20261010-064-CODEX-CLI-READONLY-INTEGRATION-PLAN` was submitted via single-action Windows relay sandwich after the user expressly requested Codex CLI integration work. The user returned **`[GPT_WINDOWS_FEEDBACK]` rather than `[GPT_WINDOWS_RESULT]`**:

- `version=1`, `type=RELAY_DIAGNOSTIC`, `source=windows_browser_bridge`
- `state=ACTION_FAILED`
- `packet_id=DND-WINDOWS-20261010-064-CODEX-CLI-READONLY-INTEGRATION-PLAN`
- `detail=relay_owner_transfer_requires_claim`

**Codex CLI was not confirmed invoked**; no `CODEX_VERSION`, scoped PID, stdout, or exit-code receipt exists. This packet must be treated as attempted and consumed. The action was planned to use `codex exec --skip-git-repo-check -C <isolated-stage> --sandbox read-only <prompt>`; it was not a merge, deployment, or write to the live bot. Do not state that Codex reviewed anything.

Related prior ownership feedback:
- `DND-WINDOWS-20261010-062-BACKUP-STAGE-AND-ADD-MISSING-PR157-MODULES` -> `relay_owner_unclaimed_inactive_tab`; **no executor receipt**, so effects of intended backup/candidate creation remain unknown. See `docs/incidents/DND_WINDOWS_062_RELAY_OWNER_UNCLAIMED_INACTIVE_TAB_2026-10-10.md`.
- After the 062 failure, a separate feedback was delivered for old packet `DND-WINDOWS-20261010-060-PR157-INTEGRATION-COMPATIBILITY-PREFLIGHT`, also `relay_owner_unclaimed_inactive_tab`. **There was already a complete OK executor receipt for 060 earlier**; this delayed/stale diagnostic does not disprove that verified 060 outcome and is not a reason to replay 060.
- `DND-WINDOWS-20261010-063-READONLY-STAGE-AND-AGENT21-HANDOFF-PREFLIGHT` had been authored after 062, but no `[GPT_WINDOWS_RESULT]` for 063 was provided. Do not infer that it executed.

## Operator recovery and STOP gate
The active browser conversation must establish legitimate relay ownership/claim before **any new Windows packet**, even read-only, is attempted. Honor cross-conversation owner guard. Do not force-arm, change owner records, spoof tab ownership, refresh ownership internals, restart services, switch conversations, or try fresh IDs to evade the guard. Direct operator to focus the original ChatGPT Firefox tab and use the supported user-visible claim/connection control if available. If the UI does not show a claim action, request a screenshot of the relay controls; do not invent a specific control. Wait for confirmed ownership before sending a fresh, uniquely numbered diagnostic operation. Do not retry 062 or 064.

User also expressly requested **Agent 21** handoff (this is **not a PCE engineer**), using the established operator-authorized one-shot `Client/Relay/test/Run-Copy-Contents.cmd` and companion PowerShell script, after writing comprehensive instructions to `Client/Relay/test/Copy Contents.txt`. Verify that the companion submits with **Enter**, confirm actual posted new chat before claiming success; never auto-switch without explicit request. The handoff remains pending because relay ownership blocks machine access.

## Existing, independently verified D&D state
- Isolated PR15.7 has **56/56 distinct targeted pytest tests passing across segmented Windows runs**; no combined uninterrupted five-module run, active checkout integration, or live bot E2E proof.
- Active D&D repo `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot`, branch `fix/windows-python313-utf8-20261010` pinned SHA `6bcc567ab75b62c2870c99319dcfc550fdd7823d`; last verified untracked `?? cmd.exe` only.
- Operation 061 verified a **124-file** independent source stage at `C:\Users\Craig Morgan\Downloads\Dev\DnD-RP-Bot-PR157-Windows-Stage-20261010-061`. Manifest SHA256 `14e4a8efb3c71d422a35b064d33bb4ad563584ab0c89c00612e704b5b3d0101e`; no real `.env`, `data/`, or `.git`.
- PR15.7 archive `backups/pr157_a1b03ae2_source.zip` SHA256 `0d0324d3b5fe9526d61285b071b699c4185760a398415c15b4c10aff6a75facc`.
- Active checkout missing **13** modules in bounded PR15.7 campaign dependency closure; six existing modules differ; preserve the active definitions and never bulk-merge.
- Remaining requested milestones: integrate campaign/schema/provider/router/Windows ACL code in an independent candidate; reconcile config/models/schemas and migrations; test synthetic credentials/DB/Telegram/gameplay; only then review deployment. User permits Codex CLI on their machine when ownership is restored.

## Governance and risk
Canonical documentation repo **`monag144/GPT-Windows-Relay/main`**, not retired Termux repo and not the D&D runtime repo. GitHub date-based source-of-truth controls inspected: `consumer/control_harness.py` SHA `ca2141c45726366abb889db0cb5a794ed8735075`, `windows-relay/TASKS.md` SHA `d49999dc29466a04ba2c27cc39f341b9162779e9`, index `bfa29203c03238015cb088d717810d818a980d90`, backlog `a7b65a643cbcdecd440d6675d1dfb7190300a6fb`, priorities `86c3e0c3f2d1c44de9cccdc819597f120c8732be`, safety `693ad770964352de7de26886ba3b4e295ac0357a`, sandwich guide `2b300c59320f144126f8a2a2c0b2dd5dbc349596`, manual one-shot handoff policy `944e6d0d5a4c573f848985cb2c01e0cda33a1ae2`. The function `engineering_preflight` applies to named PCE series, not DND task-scoped ordinals. No automatic agent rotation. Five-operation checkpoint for DND 060–064 must be committed/read back before issuing 065.
