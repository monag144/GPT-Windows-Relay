# Windows Relay local build inventory — 2026-10-10

**State:** Read-only source and metadata inventory, **not consolidation or deployment proof**. Source is an actual Windows execution receipt `PCE16.011-read-only-workspace-build-and-codex-inventory`, status **OK**, exit 0, received 2026-10-10 22:48:49 UTC. The requested preceding PCE16.010 attempt was **GOVERNANCE_BLOCKED**, with **no inventory executed**, because the local legacy preflight could not see the verified GitHub `.005–.009` audit. Do not reuse either ordinal.

## Classification

Paths are relative to `C:\Users\Craig Morgan\Downloads\Dev`. Do not move, delete, merge, alter Git state or copy sources to the live Client on the strength of this inventory.

| Role to investigate | Relative directory | Git branch and local HEAD | Representative code identity |
| --- | --- | --- | --- |
| **Primary candidate for source development** (not proven live) | `GPT-Windows-Relay-Main-Build` | `main` at `16856b6ebffc8430c430c01b2b5aed05b3dbd7dc` | `windows-relay/hud.py` SHA256 prefix `3c333c0fb9812be7`; backend `fb763bae1ca87824`; extension scanner `5169e84985e9452e` |
| **Current installed Client: preserve** | `GPT/Client/Relay` | No local .git; separate deployed tree | HUD `363c3d55446df3e8`; controller `79264e06ae53f54b`; backend `3ad004fdf3d22aa9`; extension scanner `34500934b214423a`; extension worker `dd43c9f50ab3a173` |
| **PCE11 Windows development: preserve for merge comparison** | `GPT/GPT-Windows-Relay` | `pce11/one-click-go-recovery-and-doc-hygiene` at `a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a` | HUD `aa941ce510f2f6a4`, backend `40bf131e3d7ad391`, scanner `8a1bd0222adf91e8` |
| **PCE8 reconciliation candidate** | `GPT/GPT-Windows-Relay-pce8-reconcile` | `pce8/reconcile-v17-owner` at `8ef01a9477b8246adc2c2f2e777a3b8a7a342e0b` | HUD `3c333c0fb9812be7` (same prefix as Main); backend `be9a326f3ce8d48c`; scanner `8582fd78c13efc6c` |
| **Old Android/Termux source, Windows fragments possible** | `GPT/GPT-Termux-Relay` | `development/runtime-control` at `18d5944a312c45058e8188b41977d199cd534177` | Windows HUD `73ab6106da06e380`; scanner `e96f5c3801aac1e4` |
| **Old consumer branch, Windows fragments possible** | `GPT/GPT-Termux-Relay-consumer` | `consumer/r29-firefox-offline-tray` at `249e3bb46c6ea57968d9ecf5157d73867a7f918d` | Controller `79264e06ae53f54b` matches Client prefix; HUD `2355e510640a7db6` |
| **R27 historical branch** | `GPT/GPT-Termux-Relay-r27` | `consumer/r27-user-test-recovery`, local git SHA not resolved by limited packed/ref read; **do not infer missing commit** | HUD `eeb531f524d59c35`; backend `49e142d87fd69ba` |
| **Preserve raw diagnostic evidence** | `GPT/Relay-Evidence` | Not a Git checkout | Timestamped evidence subfolders, do not delete |
| Parent folder only | `GPT/Client` | No .git | Contains `Relay` |

**Observed checkout facts:** All listed folders existed. Local `main` at the above SHA while canonical GitHub `main` had advanced through multiple documentation commits. The Main Build passed **129 narrowly selected unit/contract tests** across HUD (20), control harness (20), protocol (44), STOP (15), Firefox temporary manifest (3), safe cutover (10), and content scanner (17). These tests do not certify loaded-Firefox state, real end-to-end delivery, or backend atomic reservation. The Main HUD has START/STOP/RETRY; the installed Client has START/STOP/RESTART/OFF/KILL. Do not replace Client HUD with Main wholesale.

**Current runtime observation:** Local listener `127.0.0.1:8766`, PID `11700` (as of the inventory); actual source path loaded by that process **not yet established**. The Python interpreter used for the inventory was `GPT/Client/Relay/.venv/Scripts/python.exe`; this does not by itself establish which script PID 11700 loaded. `codex.EXE` exists under `AppData/Local/Programs/OpenAI/Codex/bin`; no Codex invocation was performed during PCE16.011.

## Next governed, safe steps

1. **No destructive cleanup:** before any archiving, use a bounded **read-only Codex CLI** or other source inspection to determine whether each legacy checkout has unique commits, uncommitted tracked/untracked content, runtime assets, or useful features not in the Main checkout. Avoid exposing keys/tokens and other private working state.
2. **Source and runtime provenance:** identify PID 11700's actual launch script, Firefox loaded addon/profile/code (not inferred from on-disk manifest). Compare Client vs Main vs PCE11 vs PCE8 and capture explicit immutable source hashes. Respect live STOP/conversation ownership.
3. **Consolidation proposal:** Main Build is the **candidate** canonical local development checkout; Client remains separately installed. Classify other trees as **preserve/merge candidate, historical archive candidate, evidence**, with a rollback plan. No deletion/move without explicit operator approval.
4. **HUD merge:** new `docs/design/WINDOWS_RELAY_HUD_CONVERSATION_CONTROLS_2026-10-10.md` calls for visible FOCUS CHAT, SELECT CHAT / CLAIM–CONNECT, and a **physical FORCE button**, guarded by STOP, ownership and dedup. Keep five Client buttons and separately validate RETRY. Document only; not deployed.
5. **Governance:** GitHub audit `AUDIT_2026-10-10T0635Z_PCE16_005_009_CHECKPOINT.md` exists; legacy local gate rejected .010 due to missing compatibility-named local file. Later permanent fix must reconcile authenticated GitHub receipt support rather than disabling preflight. Read control harness/roadmap before each PCE attempt; at .015 commit/read back .010–.014 before issuance.

Canonical repo: `monag144/GPT-Windows-Relay` on `main`. Retired Termux is **never** the Windows source of truth. This document does not certify archival safety or live deployability.

## PCE16.013 source-only capability comparison — 2026-10-10
Native `PCE16.013-deterministic-source-capability-comparison` returned **OK / exit 0** at 2026-10-10 22:54:01 UTC. It did not invoke Codex or change repositories/Client/Firefox. Results compare Python/PowerShell/JavaScript named functions and selected literal markers across seven source variants; **same function name or marker absence is not semantic parity proof**.
- **Installed Client vs local Main:** HUD four extra `minimize_hud`, `control_state`, `marker_text`, `restore_borderless`; controller nine extra `GenuineHudProcesses`, `KillHudOnly`, `KillTree`, `StopBackend`, `GenuineRelayProcesses`, `GenuineSupervisors`, `GenuineWatchdogs`, `StartWatchdog`, `WriteReason`; backend four extra `packet_execution_status`, `_turn_discipline_lines`, `engineering_governance_check`, `engineering_operation_ordinal`; extension content 17 extra functions; worker 18 extra functions. Main has RETRY marker; Client does not. Client worker retains a legacy automatic rotation marker and functions.
- **PCE11 vs local Main:** many of those extra functions, plus source functions for page-error recovery/new-chat. Its worker also retains legacy rotation. Not a safe drop-in.
- **PCE8 vs local Main:** exact local HUD hash match `3c333c0fb9812be7`; still different backend/controller bytes and browser files, notably rotation handlers.
- **Older Termux source variants:** mixed historical functions; no evidence that any complete folder is safe to delete. Termux-Consumer controller SHA prefix `79264e06ae53f54b` matches Client controller, so lineage may be useful.
- A read-only `tasklist` snapshot showed **two** `codex.exe` processes, PIDs `2840` and `4936`; no parentage was established and no termination authorized. Earlier `PCE16.012` Codex analysis timed out, so it provided no completed review.
- This audit highlights a **deployment anti-goal:** never replace the current five-button Client HUD with the older Main HUD just because Main's selected unit suites passed 129/129. Preserve client-only process-management and delivery diagnostics pending semantic review and end-to-end acceptance.

Pending: measure tracked and untracked local modifications *without listing private filenames*, identify the observed runtime executable, and then design selective merged deployment on a separate stage. No archival or live migration approved by these observations.
