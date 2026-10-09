# Codex CLI workspace discovery mission — 2026-10-07T2034Z

**CLOSED / HISTORICAL HANDOFF (PCE12, 2026-10-09):** The Termux-worktree discovery steps below are archived evidence, not executable instructions. All current Windows engineering occurs solely in `monag144/GPT-Windows-Relay` using `docs/index/INDEX_2026-10-07T2034Z_WINDOWS_RELAY_SOURCE_OF_TRUTH.md`. Do not scan, fetch, pull from, or mutate the retired Termux repository as a fallback.


Read-only first. Do not delete, move, restart Firefox, reload extensions, stop/start relays, or rewrite Git history.

Canonical target:
- GitHub: `monag144/GPT-Windows-Relay/main`
- intended local clone: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\GPT-Windows-Relay`
- live runtime: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay`

Read first:
- `docs/index/INDEX_2026-10-07T2034Z_WINDOWS_RELAY_SOURCE_OF_TRUTH.md`
- `docs/audits/AUDIT_2026-10-07T2034Z_TERMUX_WINDOWS_CONTAMINATION.md`
- `docs/policy/POLICY_2026-10-07T2034Z_DOCUMENTATION_STRUCTURE.md`

Mission:
1. Map every Windows Relay source/runtime/state copy on disk.
2. Search at minimum:
   - `%LOCALAPPDATA%\GPTWindowsRelay*`
   - `%APPDATA%\GPTWindowsRelay*`
   - `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\`
   - `Client\Relay`
   - any `GPT-Termux-Relay` or `GPT-Windows-Relay` clone/worktree
   - Git worktrees/remotes, startup entries, scheduled tasks, Firefox policy/profile references only far enough to identify owned paths.
3. For every discovered copy record: absolute path, role, Git remote/branch/HEAD if applicable, last-write time, canonical/stale/unknown classification, and proposed disposition.
4. Find duplicate or escaped source trees, backups, generated deployment trees, ops/results/log/state directories, junctions/symlinks, and stale launchers.
5. Sniff documentation/file names and top titles for untimestamped authority words such as CURRENT, ACTIVE, LATEST, LOOK HERE, MASTER, AUTHORITATIVE, or READ THIS FIRST. Also flag any maintained documentation over 10 KiB.
6. Do not decide by filename alone: use Git remote + branch + HEAD + timestamps + current source-of-truth index.
7. Return a compact inventory and cleanup proposal. If output would exceed 10 KiB, split sideways by subject (source trees, runtime/state, browser/startup, documentation), not one giant report.

Do not mutate until the inventory is complete and the cleanup plan is reviewed.
