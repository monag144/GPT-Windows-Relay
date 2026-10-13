# Windows Relay overview pointer — 2026-10-09

This README filename is a compatibility entry point. The maintained dated [project overview](../docs/guides/WINDOWS_RELAY_PROJECT_OVERVIEW_2026-10-09.md), [operating safety](../docs/facts/WINDOWS_RELAY_OPERATING_SAFETY_2026-10-09.md), [action format](../docs/guides/WINDOWS_RELAY_ACTION_SANDWICH_2026-10-09.md), and [documentation index](../docs/index/WINDOWS_RELAY_DOCUMENTATION_INDEX_2026-10-09.md) provide the current navigation.

**October 12 verified build:** [Windows Relay live execution checkpoint](../docs/releases/WINDOWS_RELAY_LIVE_EXECUTION_CHECKPOINT_2026-10-12.md) records the real v0.3.18 Firefox → backend → PowerShell response and pinned Git tag. A full-project/endurance certification is still pending.

**Release/safety correction:** The older README claimed operation-ID reservation prevented duplicate replay. PCE15.043 and PCE15.047 isolated code tests disproved that blanket statement. Do not equate source or XPI existence with the loaded extension or a verified production release.

**Agent switching:** automatic new-chat rotation is on hold; the user-requested existing `Run-Copy-Contents.cmd` is the only approved handoff route. Preserve the engineering operation cap without silently rotating.

**Canonical build layout:** `windows_relay.py`, `hud.py`, `START-GPT-WINDOWS-RELAY.bat`, and `extension-persistent/` are the sole release-candidate source paths. The sibling `extension/` tree is deliberately retained for **One-Click Go consumer packaging**; it is **not** a second GPT Windows Relay extension. Historical Prototype snapshots are provenance, not deployment inputs.

Original extensive README is preserved [at this Git commit](https://github.com/monag144/GPT-Windows-Relay/blob/24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8/windows-relay/README.md).


**Active engineering ownership (2026-10-11):** ChatGPT performs routine code changes directly in the GitHub WIP development branch, verifies/pushes them, then supplies a safe `git pull --ff-only` command for the Main-Build checkout. Codex is an escalation for major repair. To confirm whether port 8766 or scheduled tasks point to the old Client, run the read-only `tools/Inspect-Relay-Runtime-Identity.ps1` on Windows. This does not identify Firefox's loaded add-on; verify that separately in `about:debugging`. See [current owner policy](../docs/policy/WINDOWS_RELAY_ENGINEERING_OWNER_AND_DELIVERY_2026-10-11.md) and [approval automation evidence](../docs/facts/WINDOWS_RELAY_GITHUB_APPROVAL_BEHAVIOR_2026-10-11.md).

**No on-device backups (2026-10-12):** do not create or retain second local source/runtime trees, dated backup archives or snapshots; use verified GitHub history and an explicit remote archive branch for publishable code. The historic `sync-live.py` and `safe_live_cutover.py` entrypoints are disabled because their legacy workflows require local backup snapshots. See [no-local-backups policy](../docs/policy/WINDOWS_RELAY_NO_ON_DEVICE_BACKUPS_2026-10-12.md). Existing unique private state requires an operator decision before deletion.
