# Windows Relay documentation index — 2026-10-09

**Repository:** `monag144/GPT-Windows-Relay` only. Do not use the old Termux relay as a Windows development source. The date is **Pacific local**, with **no clock time in filenames or document titles**. This directory index is a documented-navigation snapshot, not an assertion that GitHub or a running agent can never advance afterward.

## Dated, maintained reading order

1. [Document titles and date precedence](../policy/DOCUMENT_TITLES_AND_DATE_PRECEDENCE_2026-10-09.md) — title-first/date-last filename convention, safe conflict resolution and compatibility aliases.
2. [Windows Relay operating safety](../facts/WINDOWS_RELAY_OPERATING_SAFETY_2026-10-09.md) — operator controls, exact-once deficiencies, manual-only new-chat handoff and release blockers.
3. [Windows Relay project overview](../guides/WINDOWS_RELAY_PROJECT_OVERVIEW_2026-10-09.md) — system scope and limitations.
4. [Relay action sandwich](../guides/WINDOWS_RELAY_ACTION_SANDWICH_2026-10-09.md) — visible header, exact action fence and visible footer.
5. [Windows Relay mission and priorities](../roadmap/WINDOWS_RELAY_MISSION_AND_PRIORITIES_2026-10-09.md) — strategy and verified priority order.
6. [Windows Relay task backlog](../roadmap/WINDOWS_RELAY_TASK_BACKLOG_2026-10-09.md) — bounded open tasks and explicitly paused agent switching.
7. [One-Click Go consumer guide](../guides/ONE_CLICK_GO_CONSUMER_GUIDE_2026-10-09.md) — user setup, with historical Firefox-compatibility inconsistency identified.
8. [Document authority audit](../audits/WINDOWS_RELAY_DOCUMENT_AUTHORITY_AUDIT_2026-10-09.md) — exactly which misleading legacy documents were superseded and which still need migration.

## More specific later evidence and live gates

- [Script-only agent handoff](../policy/SCRIPT_ONLY_AGENT_HANDOFF_2026-10-09.md) — newer user directive **permanently retires automatic switching** and standardizes the existing CMD/PowerShell one-shot script. Supersedes the [historical temporary hold](../policy/POLICY_2026-10-10T0331Z_MANUAL_AGENT_HANDOFF_AND_AUTOMATED_ROTATION_HOLD.md); Git commit chronology resolves same-Pacific-date updates.
- [Agent switching retirement bin](../../windows-relay/bin/AGENT_SWITCHING_RETIREMENT_2026-10-09.md) — reasons, historical code SHA, archived rotation test sources and retained shared-component boundaries.
- [User-confirmed one-shot Windows script transfer](../handoffs/HANDOFF_2026-10-10T0331Z_ONE_SHOT_WINDOWS_SCRIPT_AGENT_TRANSFER.md) — known working `Run-Copy-Contents.cmd`, with PCE15 successor-series hitch.
- [PCE15 audit of operations 45–49](../audits/AUDIT_2026-10-10T0304Z_PCE15_OPERATIONS_045_049.md), [non-atomic claim incident](../incidents/INCIDENT_2026-10-10T0250Z_PCE15_NONATOMIC_ACTION_CLAIM_AND_OWNER_GUARD_GAPS.md), and [post-eviction replay incident](../incidents/INCIDENT_2026-10-10T0304Z_PCE15_DEDUP_RETENTION_POST_EVICTION_REPLAY.md). Preserve their original exact event timestamps; do not relabel historical events.
- Control-harness code, actual latest test results and current Client/Firefox runtime state are separate evidence sources and may be newer than this index.

The remaining work is the [Windows Relay task backlog](../roadmap/WINDOWS_RELAY_TASK_BACKLOG_2026-10-09.md); removed rotation projects are not open items.

## Stable compatibility entry points

`README.md`, `consumer/README.txt`, `windows-relay/README.md`, `docs/RELAY_OPERATIONAL_RULES.md`, `docs/relay-sandwich-procedure.md`, `docs/windows-relay-mission-and-roadmap.md` and `windows-relay/TASKS.md` remain at their old paths for references and tooling, but link to date-named sources instead of asserting independently current authority. Earlier full versions remain in Git commit `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8`.

**Precedence:** explicit user directives, validated runtime and source evidence, relevant dated records, then compatibility pointers. A date is a useful ordering signal—not proof of correctness or license to invent a time.
