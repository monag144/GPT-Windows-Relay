# Windows Relay documentation index — 2026-10-09

**Repository:** `monag144/GPT-Windows-Relay` only. Do not use the old Termux relay as a Windows development source. The date is **Pacific local**, with **no clock time in filenames or document titles**. This directory index is a documented-navigation snapshot, not an assertion that GitHub or a running agent can never advance afterward.

## Relay execution safeguards — 2026-10-11

- [Relay execution without governance — 2026-10-11](../policy/WINDOWS_RELAY_EXECUTION_WITHOUT_GOVERNANCE_2026-10-11.md) supersedes old five-operation GitHub audits, preflight receipts and periodic review requirements. Auth/STOP/owner/dedupe remain mandatory runtime security.
- Past audit and PCE12–PCE17 governance incident files are historical evidence only, not live command admission instructions.

## Device cleanup and source retention — 2026-10-12

- **[No on-device backups — 2026-10-12](../policy/WINDOWS_RELAY_NO_ON_DEVICE_BACKUPS_2026-10-12.md)**: authoritative operator rule; GitHub is the source-only version archive, no persistent local backup/snapshot/rollback folders. Pinned remote archive `archive/preconsolidation-source-2026-10-12`; local backup copies are removed from the WIP branch.

- [Multiple-build disk audit — 2026-10-12](../reviews/WINDOWS_RELAY_MULTIBUILD_DISK_AUDIT_2026-10-12.md): 23 backends, 26 HUDs, competing untracked nested runtime/Prototype/backups and operator's one-runtime/no-local-backups target. Disk findings are operator-provided; GitHub alone cannot establish loaded/runtime state.
- [Codex cleanup issue #30](https://github.com/monag144/GPT-Windows-Relay/issues/30): classify and choose the actual newest functional runtime, reconcile useful untracked code, physically remove proven redundant files without generating new backups, and preserve sensitive untracked data until explicit disposition.
- **Launcher repaired by October 12:** `tools/Launch-Codex-CLI.bat` now selects the verified `GPT-Windows-Relay-Main-Build` checkout and refuses an unverified Git origin. [Issue #30](https://github.com/monag144/GPT-Windows-Relay/issues/30) continues to track remaining local runtime duplication; the old path warning is obsolete.

## Windows Relay live execution checkpoint — 2026-10-12

- **[Windows Relay live execution checkpoint — 2026-10-12](../releases/WINDOWS_RELAY_LIVE_EXECUTION_CHECKPOINT_2026-10-12.md):** verified annotated Git tag, 13/13 focused tests and a real PowerShell canary using Main-Build and Firefox v0.3.18.
- [Release and project health sweep — 2026-10-12](../reviews/WINDOWS_RELAY_RELEASE_AND_PROJECT_HEALTH_SWEEP_2026-10-12.md): source fixes, pending native broader tests, and unresolved untracked-disk scope.
- [Legacy browser installer retirement — 2026-10-12](../facts/WINDOWS_RELAY_LEGACY_BROWSER_INSTALLER_RETIREMENT_2026-10-12.md): old README.txt installer guidance is superseded while preserving the operator's modified local text.
- Oct 9/10/11 inventory and capability records are historical snapshots, not evidence the legacy Client is installed or that live execution has never succeeded.

## Engineering owner and source evidence (2026-10-11)

- [Engineering ownership and GitHub-push → relay-pull workflow](../policy/WINDOWS_RELAY_ENGINEERING_OWNER_AND_DELIVERY_2026-10-11.md): ChatGPT leads routine engineering, Codex handles major escalations, runtime owner security stays separate.
- [GitHub permission-prompt automation evidence](../facts/WINDOWS_RELAY_GITHUB_APPROVAL_BEHAVIOR_2026-10-11.md): source markers, test limitations and loaded-extension uncertainty; not proof of live authorization.
- [Read-only Windows runtime identity inspector](../../windows-relay/tools/Inspect-Relay-Runtime-Identity.ps1): backend listener, PID, scheduled-task and old-Client path evidence, no state changes.
- [Full-stack Main-Build provenance — 2026-10-11](../reviews/WINDOWS_RELAY_FULL_STACK_PROVENANCE_2026-10-11.md): launcher, backend, HUD, watchdog, pairing, Firefox policy/profile and content-script path checks.

## Dated, maintained reading order

1. [Document titles and date precedence](../policy/DOCUMENT_TITLES_AND_DATE_PRECEDENCE_2026-10-09.md) — title-first/date-last filename convention, safe conflict resolution and compatibility aliases.
2. [Windows Relay operating safety](../facts/WINDOWS_RELAY_OPERATING_SAFETY_2026-10-09.md) — operator controls, exact-once deficiencies, manual-only new-chat handoff and release blockers.
3. [Windows Relay project overview](../guides/WINDOWS_RELAY_PROJECT_OVERVIEW_2026-10-09.md) — system scope and limitations.
4. [Relay action sandwich](../guides/WINDOWS_RELAY_ACTION_SANDWICH_2026-10-09.md) — visible header, exact action fence and visible footer.
5. [Windows Relay mission and priorities](../roadmap/WINDOWS_RELAY_MISSION_AND_PRIORITIES_2026-10-09.md) — strategy and verified priority order.
6. [Windows Relay task backlog](../roadmap/WINDOWS_RELAY_TASK_BACKLOG_2026-10-09.md) — bounded open tasks and explicitly paused agent switching.
7. [One-Click Go consumer guide](../guides/ONE_CLICK_GO_CONSUMER_GUIDE_2026-10-09.md) — user setup, with historical Firefox-compatibility inconsistency identified.
8. [Document authority audit](../audits/WINDOWS_RELAY_DOCUMENT_AUTHORITY_AUDIT_2026-10-09.md) — exactly which misleading legacy documents were superseded and which still need migration.

## HUD feature design (proposed, not shipped)

- [Windows Relay HUD conversation controls — 2026-10-10](../design/WINDOWS_RELAY_HUD_CONVERSATION_CONTROLS_2026-10-10.md) — user-requested exact-conversation **FOCUS CHAT**, **SELECT CHAT / CLAIM–CONNECT** and visible **FORCE** button; requires STOP/owner/dedup gates, preserves five working Client buttons and prohibits automatic handoff. **Design only; no live Client changes.**

## Historical and operational evidence — 2026-10-10

- [Script-only agent handoff](../policy/SCRIPT_ONLY_AGENT_HANDOFF_2026-10-09.md) — newer user directive **permanently retires automatic switching** and standardizes the existing CMD/PowerShell one-shot script. Supersedes the [historical temporary hold](../policy/POLICY_2026-10-10T0331Z_MANUAL_AGENT_HANDOFF_AND_AUTOMATED_ROTATION_HOLD.md); Git commit chronology resolves same-Pacific-date updates.
- [Agent switching retirement bin](../../windows-relay/bin/AGENT_SWITCHING_RETIREMENT_2026-10-09.md) — reasons, historical code SHA, archived rotation test sources and retained shared-component boundaries.
- [User-confirmed one-shot Windows script transfer](../handoffs/HANDOFF_2026-10-10T0331Z_ONE_SHOT_WINDOWS_SCRIPT_AGENT_TRANSFER.md) — known working `Run-Copy-Contents.cmd`, with PCE15 successor-series hitch.
- [PCE15 audit of operations 45–49](../audits/AUDIT_2026-10-10T0304Z_PCE15_OPERATIONS_045_049.md), [non-atomic claim incident](../incidents/INCIDENT_2026-10-10T0250Z_PCE15_NONATOMIC_ACTION_CLAIM_AND_OWNER_GUARD_GAPS.md), and [post-eviction replay incident](../incidents/INCIDENT_2026-10-10T0304Z_PCE15_DEDUP_RETENTION_POST_EVICTION_REPLAY.md). Preserve their original exact event timestamps; do not relabel historical events.
- Control-harness code, actual latest test results and current Client/Firefox runtime state are separate evidence sources and may be newer than this index.

The remaining work is the [Windows Relay task backlog](../roadmap/WINDOWS_RELAY_TASK_BACKLOG_2026-10-09.md); removed rotation projects are not open items.

## Stable compatibility entry points

`README.md`, `consumer/README.txt`, `windows-relay/README.md`, `docs/RELAY_OPERATIONAL_RULES.md`, `docs/relay-sandwich-procedure.md`, `docs/windows-relay-mission-and-roadmap.md` and `windows-relay/TASKS.md` remain at their old paths for references and tooling, but link to date-named sources instead of asserting independently current authority. Earlier full versions remain in Git commit `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8`.

**Precedence:** explicit user directives, validated runtime and source evidence, relevant dated records, then compatibility pointers. A date is a useful ordering signal—not proof of correctness or license to invent a time.
