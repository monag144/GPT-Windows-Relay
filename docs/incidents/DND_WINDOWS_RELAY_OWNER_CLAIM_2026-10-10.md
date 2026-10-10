# D&D Windows Relay owner-claim diagnostic — 2026-10-10

## Scope and status
Windows Relay transport incident during user-requested D&D RP Bot Windows migration. Status: BLOCKED BEFORE EXECUTION; authenticated owner-claim canary pending. No observed Windows command execution, duplicate side effect, database mutation, or runtime change from the rejected packet.

## Observed failure
The user asked to use their already-running Windows Relay. First attempted read-only probe action ID `DND-WINDOWS-20261010-001-ENV-PROBE`, session `dnd-windows-migration`, targeted the local DnD-RP-Bot workspace and attempted only to print directory, Python version, and UTF-8 flag. Browser bridge returned:
`ACTION_FAILED / relay_owner_transfer_requires_claim`
with instruction to read governance sources, record failure, preserve rollback, check PCE8/PCE9 budgets, and reissue only with a fresh ID.

## Independent progress
Before this relay attempt, user-provided CMD test receipt established `205 passed in 9.86s` for DnD-RP-Bot on Windows Python 3.13 with `PYTHONUTF8=1`. This successful local test was manual CMD execution, not relay execution. The current migration task can proceed after legitimate claim and read-only transport acceptance.

## Sources and safety gates inspected
Canonical Windows Relay GitHub `main`: `consumer/control_harness.py` blob ca2141c45726366abb889db0cb5a794ed8735075; dated task backlog blob a7b65a643cbcdecd440d6675d1dfb7190300a6fb; mission/priorities blob 86c3e0c3f2d1c44de9cccdc819597f120c8732be; operating safety blob 693ad770964352de7de26886ba3b4e295ac0357a; action-sandwich blob 2b300c59320f144126f8a2a2c0b2dd5dbc349596; and PCE15 ownership/atomicity incident blob cc857e70757a5592e01c31d922ccb9af3ace49c4. Historical PCE8/PCE9 budget/rotation automation is retired; no auto-handoff or unbounded reissue. PCE16 chronology in dated backlog was last known at .004 but may have advanced; this DND-tagged probe is NOT a PCE-series ordinal.

## Recovery decision and rollback
Do not replay the rejected ID. A documented earlier authenticated `owner_claim: true` packet pattern (PCE16.000) is a candidate for an explicitly claimed new read-only probe. Do not reset processed IDs, bypass owner/STOP/ARM controls, deploy source, modify loaded browser scripts, execute queued missions, or assume live Client equals GitHub source. Any claim rejection stops further execution; solicit exact user-visible diagnostic. Rollback is the unchanged pre-probe runtime: no modifications were made by the failed attempt.

## Development-log update
D&D migration checkpoint: 205/205 unit tests pass on Windows; relay ownership is the only presently observed blocker for agent-driven commands. Transport acceptance, authenticated ownership, running Client identity and live game deployment remain unverified. Next safe step: one explicit claimed read-only environment probe with a unique ID; inspect result before any mutation.
