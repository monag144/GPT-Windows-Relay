# Windows Relay task backlog pointer — 2026-10-09

**GitHub repo:** `monag144/GPT-Windows-Relay` only (not the retired Termux Relay). The date-based [task backlog](../docs/roadmap/WINDOWS_RELAY_TASK_BACKLOG_2026-10-09.md), [priorities](../docs/roadmap/WINDOWS_RELAY_MISSION_AND_PRIORITIES_2026-10-09.md) and [documentation index](../docs/index/WINDOWS_RELAY_DOCUMENTATION_INDEX_2026-10-09.md) replace the previous untimestamped 'current execution state'.

**Do not resume automated new-chat or agent switching.** It is paused by explicit user direction; only a user-requested one-shot existing Windows script may transfer agents. Honor the PCE ordinal ceiling but stop rather than silently rotate.

**Critical unresolved backend safety:** PCE15.043 non-atomic reservation and PCE15.047 post-eviction replay were reproduced in isolated code tests; not fixed in production by the memory-only prototype.

Prior detailed PCE8/PCE9 chronology and task checkmarks remain [at the pre-cleanup Git commit](https://github.com/monag144/GPT-Windows-Relay/blob/24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8/windows-relay/TASKS.md). Consult a newly verified engineering ledger before calling work complete or assigning an ordinal. This pointer does not authorize a Client deployment or local sync.
