# D&D Windows migration relay checkpoint — 2026-10-10

## Scope
User-directed migration of `monag144/DnD-RP-Bot` from Termux to Windows via the existing ChatGPT↔Windows Relay. These are `DND-WINDOWS-20261010-...` task-scoped IDs, **not PCE engineering ordinals**; this checkpoint is not a substitute for the separately enforced PCE five-operation audit. No Windows Relay source, running Client, browser add-on, or credentials were changed by these five packets.

## Verified 001–005 attempts
| ID | Status | Proven result | Uncertainty or defect |
|---|---|---|---|
| `DND-WINDOWS-20261010-001-ENV-PROBE` | ACTION_FAILED browser bridge | `relay_owner_transfer_requires_claim` | Rejected before execution; not replayed |
| `DND-WINDOWS-20261010-002-CLAIM-READONLY` | OK, exit 0 | Legitimate `owner_claim: true` accepted; D&D cwd and Python 3.13.15 verified | No general exact-once guarantee |
| `DND-WINDOWS-20261010-003-REPOSITORY-AUDIT` | COMMAND_FAILED, exit 1 | Audit marker printed | Nested CMD `python -c` quoting created unterminated string; no actual checkout facts |
| `DND-WINDOWS-20261010-004-NATIVE-CMD-AUDIT` | OK, exit 0 | `.git/HEAD` is `ref: refs/heads/main` | Conditional CMD concatenation omitted later checks |
| `DND-WINDOWS-20261010-005-CHECKOUT-INVENTORY` | OK, exit 0 | Confirmed `main`, Python 3.13.15; `dir` reported `File Not Found` for local `.env` and `data\\*.db`; `where git` reported no Git on PATH | `%LOCALAPPDATA%\\GitHubDesktop` probe gave path syntax error; bundled Git location NOT established. Overall exit 0 reflects last `echo`, not individual discovery check success |

## Independent migration baseline
User-supplied CMD report: after `set PYTHONUTF8=1`, `205 passed in 9.86s` with `.venv` Python 3.13.15. The two prior default cp1252 source-read failures are consistent with unqualified `Path.read_text()` calls. This is local manual test evidence, not a Relay live game launch.

## Evidence, current source and governance
GitHub `monag144/GPT-Windows-Relay/main` consulted: `consumer/control_harness.py` blob `ca2141c45726366abb889db0cb5a794ed8735075`; `windows-relay/TASKS.md` blob `d49999dc29466a04ba2c27cc39f341b9162779e9`; index `bfa29203c03238015cb088d717810d818a980d90`; dated backlog `a7b65a643cbcdecd440d6675d1dfb7190300a6fb`; dated mission `86c3e0c3f2d1c44de9cccdc819597f120c8732be`; operating safety `693ad770964352de7de26886ba3b4e295ac0357a`; sandwich `2b300c59320f144126f8a2a2c0b2dd5dbc349596`. Legacy `docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md` is NOT_FOUND on current main; replaced by dated index/backlog. The relay's actual loaded runtime is not established to equal source. Preserve operator STOP/owner controls, unique IDs, no replay, no automatic chat switching. PCE 000..100 ceiling and audits remain separate from these DND probes.

## Net-new progress and next experiment
Ownership was legitimately claimed, checkout `main` verified, local Python and test suite proven, and absence of matches for `.env` and `data\\*.db` observed; CMD Git not on PATH. No source/DB writes by 001–005; rollback is unchanged working tree. Next action 006: **read-only native `shell: python`** (no nested CMD `python -c`) to obtain HEAD commit ID, check ignored local files without printing contents, detect GitHub Desktop bundled Git through pathlib/glob, and if available run read-only Git status. Confirm exact relay receipt before any mutation. Do not launch bot or migrate credentials.
