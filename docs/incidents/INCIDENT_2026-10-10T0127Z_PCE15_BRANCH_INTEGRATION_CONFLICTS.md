# Incident — Seven simulated overlapping-file merge conflicts — 2026-10-10T0127Z

## Trigger and scope

PCE15.013 mapped Windows development `a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a` versus canonical GitHub `main` `9415ebb02cc64ee96b020e2ea04024c02d99650f`, common ancestor `94de291a3173b04ef23a6575e562edd8e8156993`. Of 437 local-side changed paths and 37 main-side changed paths, 8 overlapped. A no-index, temporary three-way `git merge-file --diff3` test in PCE15.014 yielded **7 conflicting files** and **1 clean textual merge**:

- Text conflicts: root `README.md`, `consumer/control_harness.py`, `consumer/tests/test_control_harness.py`, `docs/MIGRATION_2026-10-06_WINDOWS_REPOSITORY_SPLIT.md`, `docs/RELAY_OPERATIONAL_RULES.md`, `docs/windows-relay-established-facts.md`, `windows-relay/TASKS.md` (one conflict region each in this specific test).
- Clean: `windows-relay/README.md`.

These are **file-level merge simulations**, not completed full repository merge tests or compatibility judgments. They do not imply all 429 local-only files should be promoted. Most serious collision: current GitHub-first `consumer/control_harness.py` gate versus older local harness interface, with matching tests and source-of-truth task/document routing.

## Risk and disposition

Blind branch pull/merge or piecemeal Client deployment could silently override governance or mix runtime versions. Existing actual Client `content.js` maps to historical Git commit `b0a01eef1b2c19b498195d7318541782904d6c8f` rather than either tip; loaded Firefox script identity is unknown, and G04 production parity remains FAIL. The separate apparent source/HEAD raw-byte discrepancy was resolved at PCE15.010 as Windows CRLF conversion, **not repository corruption**.

**Incident OPEN for planned integration review, not active failure caused by this read-only diagnostic test.** No merge, branch change, checkout, production fix, deployment, UI interaction, clipboard change, or send performed. Protected PCE12 evidence remains intact. Use GitHub-first isolated reconciliation and explicit line-by-line governance conflict review, full regression tests, rollback-backed coherent deployment, and independent loaded-runtime/send attestation before release. PCE15 remains Grade F; no changes authorized during grading.
