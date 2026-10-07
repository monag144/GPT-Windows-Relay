# Incident: PCE9 operation-budget breach, wrong-repo drift, and repeated Firefox proof

## Proof

- Canonical rule: `docs/RELAY_OPERATIONAL_RULES.md` requires managed-chat rotation every 100 operations.
- Canonical handoff: `docs/HANDOFF_2026-10-07_PCE8_TO_PCE9.md` names the first PCE9 operation `PCE9BOOT-OP001`, session `pce9.1`.
- PCE9 later emitted IDs above the series ceiling. The first audited breach was `PCE9-OP101`; the chain continued through `PCE9-OP179A2`. Therefore the operation namespace was not rotated after OP100.
- Windows repository migration policy: `docs/MIGRATION_2026-10-06_WINDOWS_REPOSITORY_SPLIT.md` says `monag144/GPT-Windows-Relay` is canonical and `monag144/GPT-Termux-Relay` is no longer the Windows destination.
- Despite that, recent PCE9 Windows work was committed to the old Termux repository, including `4fd6269bb7419d0b2f55d67a018d47bae0992976` and `249e3bb46c6ea57968d9ecf5157d73867a7f918d`.
- Six consecutive operations redundantly re-probed the same Firefox continuity/restart-safety invariant while declaring no Firefox restart: OP177, OP177A, OP177B, OP177C1, OP177C2, and OP177C3. OP178 repeated the continuity check again, making seven. Existing established facts already record that the current add-on is temporary, a full Firefox exit removes it, and full restart acceptance is gated on the signed persistent-XPI path.

## Root cause

The per-operation discipline was not enforced from canonical Windows documentation on every turn. A stale established-facts path still pointed at the old Termux clone, allowing wrong-repository work to continue. Proven Firefox facts were treated as fresh discovery instead of reusable evidence.

## Corrective action

1. Windows work must fail closed unless the canonical repository is `monag144/GPT-Windows-Relay`.
2. Before issuing an operation ID, enforce the 100-operation series budget. No managed series may emit OP101.
3. Reuse established proof. Re-probe Firefox restart/temporary-extension facts only after a dependency-changing browser mutation or contradictory evidence.
4. Keep incidents compact. Incident files should remain under 16 KiB; general documentation above 64 KiB is a split/rotation candidate.
5. Freeze the oversized historical engineering log and continue chronology in a new bounded log rather than appending indefinitely.

## Impact

The 176+ PCE9 operations produced substantial technical progress, but the naming breach, wrong-repository drift, and repeated proof work consumed operations that should have been spent on remaining roadmap acceptance.
