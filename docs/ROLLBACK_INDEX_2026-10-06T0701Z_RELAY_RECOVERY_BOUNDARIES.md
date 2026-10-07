# Relay rollback index — 2026-10-06T0701Z

This timestamped index records known live rollback boundaries and the deployment rule adopted after the PCE7 delivery/recovery incidents.

It deliberately does not use CURRENT/LATEST/ACTIVE aliases. New rollback boundaries are appended to dated audit/log material and future timestamped indexes or handoffs.

## Mandatory live-change rule

From this point forward:

1. Before changing any live relay/HUD/extension file, create a new uniquely named rollback directory.
2. Copy every live file that will be changed into that rollback directory while preserving its relative path where practical.
3. Record the source Git commit and SHA-256 of affected files when available.
4. Run relevant targeted tests before staging; run the full relay suite when the change touches core lifecycle/delivery/recovery behavior.
5. Stage only after validation passes.
6. Do not destroy or overwrite the immediately preceding rollback boundary.
7. If the newly staged build breaks, restore the immediately preceding known-good snapshot first. Do not stack speculative emergency changes onto a broken live build.
8. After restoration, verify hashes/runtime identity and only then investigate the failed candidate.
9. Git commits provide source rollback history; the directories below provide exact Windows live-state rollback boundaries.

## Known rollback boundaries

| Boundary | Windows path | Scope / purpose | Evidence |
|---|---|---|---|
| PCE7.407 | `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay\rollback\PCE7.407-20261006T034645Z` | Paired live extension/service-worker boundary before PCE7.407 staging | Created and used during later recovery investigation |
| PCE7.422 | `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay\rollback\PCE7.422-20261006T053422Z` | Exact pre-approval-v3 / pre-spam content boundary; known `content.js` SHA-256 `26ce6b9bcd63ef5acb2043bef0216eba5d42623aeaf733c98df264e183f83ed5` | Preserve; important pre-spam reference |
| PCE7.428 | `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay\rollback\PCE7.428-pre-repaired-stage-20261006T0635Z` | Backup before repaired operator-control/content/HUD staging | Creation and twelve copy operations were live-proven; targeted HUD tests passed after staging |
| PCE7.431 | none | Candidate never reached backup/staging; validation failed first | No live change occurred, so no rollback directory should be invented |
| PCE7.432 | not yet proven | Emitted validation/staging candidate; no successful staging result recorded as of this index | Do not claim a rollback boundary until creation is observed |
| PCE7.433 break-glass | not created | Director ran the guarded CMD chain, but `test_browser_contract.py` failed 4/51 before `mkdir`/copy because the local source checkout had stale modified `content.js` | No live staging occurred; preserve this as a failed pre-stage gate, not a rollback boundary |

## Restore discipline

When a candidate breaks:
- identify the most recent rollback directory that predates that candidate;
- restore only the files that candidate changed;
- reload/restart only the runtime components required to consume those restored files;
- verify the restored runtime marker/hash;
- log the failed candidate and restoration as separate evidence.

A rollback is a normal engineering control, not a failure to preserve redundancy. The reliability target is aggressive autonomous recovery with deterministic escape hatches and cheap reversibility.


## 2026-10-06T0704Z source-checkout drift note

Remote forensic readback confirmed commits `7e2cf19` and `2ae9f24` both carried v13 content blob `39572edf843e680add6e3566748d5414276c53d2`. The Director's Windows test nevertheless read legacy v11 content from the local worktree. Before repairing that source checkout, preserve the dirty local file in a new uniquely named source-recovery snapshot. Only after restoring the canonical HEAD file and passing tests may a separate live deployment backup be created.
