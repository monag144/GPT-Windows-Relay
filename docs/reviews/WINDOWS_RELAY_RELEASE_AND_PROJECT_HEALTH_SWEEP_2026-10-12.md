# Windows Relay release and project health sweep — 2026-10-12

**Scope and evidence classification:** Reviewed GitHub WIP source and the pinned October 12 annotated tag; incorporated the operator's real Windows command receipt and native focused-test outputs. This document deliberately distinguishes **confirmed live results**, **remote source review**, **code fixes**, and **native tests still pending**. No remote document or model-side analysis can claim the user's local private/ignored runtime files were deleted, or run a Windows program on the user's device.

## 1. Canonical build and tag verification

- **Pinned accepted release:** [`windows-relay-v0.3.18-live-verified-20261012`](https://github.com/monag144/GPT-Windows-Relay/tree/windows-relay-v0.3.18-live-verified-20261012) is an annotated Git tag whose object was independently read and dereferenced to `f00307494a83338d29b4c35dd6264e71fa142dbd`. The tag itself is unchanged.
- **One Windows Relay source:** `windows-relay/` in the `GPT-Windows-Relay-Main-Build` Git checkout; Firefox source `extension-persistent/` v0.3.18 with `gpt-windows-relay@local`. `extension/` belongs to **One-Click Go** and is not another Windows Relay runtime.
- **Confirmed focused native tests:** 8/8 authenticated transport + 4/4 isolated owner HTTP/once-only + 1/1 browser Node transport mock = **13/13**.
- **Confirmed live positive path:** read-only canary `PCE17-CANARY-20261012-002` returned `status=OK`, `exit_code=0`, `duration_ms=1680`, empty stderr, full stdout beginning `GPT_WINDOWS_RELAY_CANARY_002_OK`.
- **What this does not prove:** whole-suite green, prolonged uptime, interrupted-command exact-once, negative STOP/cross-tab/replay live behavior, consumer packaging, deployed signed XPI, or every unrelated automation module.

## 2. Git-tracked project structure inspection

The remote project tree contains root compatibility guidance, `consumer/`, `windows-relay/`, `docs/`, `tools/` and `migration-reports/`. There were 316 Git-tracked blobs at the tagged release (tree not truncated); no `Prototype/`, `STUPID BACKUPS DO NOT USE/` or nested `windows-relay/runtime/` source files were tracked. Physical untracked/ignored files on the user's Windows disk are not included in the GitHub tree. Known Oct 12 local evidence reported a ~3,280-file untracked `windows-relay/runtime/` tree containing unique state; physical deletion remains **unverified and blocked for unique private data**.

No new local backup may be generated during remediation, testing, or deployment. The earlier 27 backup copies are recoverable only from the pinned **remote** `archive/preconsolidation-source-2026-10-12` branch, not checked out into the WIP working tree.

## 3. Verified source and documentation defects repaired after the tag

| Component | Discrepancy established in GitHub source | Resolution on WIP |
|---|---|---|
| Landing `README.md` | Named the removed historical `GPT/Client/Relay` as deployed runtime | Points to verified Main-Build and dated October 12 release |
| Dated documentation index | Still warned Codex launcher used the old checkout and was unsafe | Reconciled with the October 12 checkout-path repair and checkpoint |
| October 9 roadmap / October 11 capability review | Described an unverified/blocked live execution path | Explicit dated supersession without rewriting historical evidence |
| No-device-backup policy | Claimed backend/browser remained intentionally OFF after operator started them | Corrected to no *unrequested* restart; October 12 live acceptance acknowledged |
| `windows-relay/README.md` | Incorrectly described the consumer `extension/` as provenance-only | Clarified separately supported One-Click Go packaging |
| `windows-relay/README.txt` | Recommends retired browser-fix installer and creating local backups | **Historical file left untouched to preserve operator's uncommitted edit**; superseding [dated retirement notice](../facts/WINDOWS_RELAY_LEGACY_BROWSER_INSTALLER_RETIREMENT_2026-10-12.md) added |
| `windows-relay/build-extension-xpi.ps1` | Default XPI filename still hardcoded `0.3.17` while manifest is `0.3.18` | Reads/verifies canonical manifest; emits stable `gpt-windows-relay.xpi` and reports actual version |
| `windows-relay/install.ps1` | Leaked relay bearer token into consumer `extension/config.js`, misleadingly claimed auto-armed state, instructed Chrome/Edge install | Setup now leaves consumer extension and ARM untouched, validates backend `bridge.json` **without printing token** and identifies canonical persistent Firefox source |
| `tools/Launch-Codex-CLI.bat` | Printed wrong-origin warning but `START_DIR` could still point to the unverified checkout | Initializes no launch directory; refuses missing/wrong origin and launches only after verification |
| `windows-relay/tests/test_protocol.py` | Four legacy test calls omitted mandatory authenticated transport; one would remain STOPPED because state never armed | Test-only owner binding + packet hash issuance helper; explicit isolated arm for mocked execution. Runtime auth remains unchanged |
| Project-wide diagnostic | No single source-backed, read-only check of tracked Git provenance, code parsing, manifest version, docs links and obsolete local duplicate folder presence | New `windows-relay/tools/relay_project_health_sweep.py`; reports JSON to stdout, uses no backups or runtime writes |
| Canonical release regression | Existing tests did not guard installer token leak, misnamed Firefox XPI, Codex fail-closed requirement or pinned release note | New `test_canonical_release_tooling.py` covers all four plus manifest/release identity |

**Executable native health procedure:** `windows-relay/tools/relay_project_health_sweep.py` verifies the on-disk Git checkout/tag, canonical persistent manifest, all tracked Python source syntax, Node JavaScript syntax where available, JSON parsing, Markdown local links, PowerShell AST source syntax, old untracked local directories, and redacted dirty-file counts. It prints findings only; never writes a report file. `windows-relay/tools/relay_project_test_sweep.py` runs both the Windows Relay and One-Click Go `unittest` suites separately in subprocesses, limits each suite to 125 seconds, disables bytecode output and prints bounded failure names/traceback tails. Native source parse and test results are still **pending** until the operator's Windows receipt arrives. Python's built-in `unittest` does **not** automatically discover pytest-only function tests; those need separate coverage if pytest is available.

## 4. Limits of this review and next machine acceptance

Static GitHub files were fetched and inspected directly; tracked release/tag tree and updated sources were verified by GitHub API. The earlier native 13/13 success is operator-provided and real; **the newly changed source files and project-wide full test suite have not yet been run on native Windows**. The Python/PowerShell/JavaScript/JSON/Markdown read-only sweep must run on the operator's updated checkout, as well as focused packaging/regression tests and separately scoped `windows-relay/tests` and `consumer/tests` suites. Any failures should be corrected from exact native output, not guessed from static tests.

**Deployment boundary:** The pinned tag is the accepted working build; new GitHub WIP commits are development improvements only until tested. Do not auto-restart the existing authenticated live relay or reload Firefox just because GitHub source advanced. The eventual operator-approved restart/load must happen explicitly if behavioral code changes are made.

## 5. Follow-up risks retained, not concealed

- The untracked nested `windows-relay/runtime/` and locked Firefox-profile artifacts remain physically unverified from GitHub. Avoid reckless deletion of session data, bearer tokens, results or unique code.
- Historical documentation can legitimately mention old paths as history, but source-facing installation instructions must prefer the newer dated record.
- Broad Python unit tests include legacy archived/cutover fixtures; passing just the 13 focused tests never implied 100% project health.
- The separate consumer product has its own version/release process and must not be accidentally removed as a duplicate Windows Relay.
- No automated live replay, STOP toggling, invasive browser performance testing, or source-to-runtime cutover was performed for this sweep.


## Native full health sweep receipt — 2026-10-12 Pacific, 2026-10-13 01:12–01:13 UTC

Operator ran `PCE17-HEALTH-SWEEP-20261012-001` (execution completed, shell exit 1 due test/source issues) after clean fast-forward `9cf9d66 → d1330ffc`. Exact machine report:

- Verified Git head `d1330ffc4750d36115d0ccf62aaa857f2f160af6`, WIP branch/origin correct, annotated release tag unchanged at `f00307494a83338d29b4c35dd6264e71fa142dbd`, canonical Firefox extension `0.3.18`.
- Tracked scope: **322 files**, Python syntax **87/87**, JavaScript syntax **9/9** (Node available), JSON **5/5**, Markdown links **178 documents / zero unresolved**.
- PowerShell AST: **23 files inspected**, failed solely on retired `install-browser-fix.ps1` line 84 (`IncompleteDollarSubexpressionReference` and `TerminatorExpectedAtEndOfString`), unreachable because script already throws. Repair is a short, structurally parseable fail-closed tombstone with no dangerous legacy body; test now asserts *absence* of mutation code.
- Physical disk, **untracked**: `STUPID BACKUPS DO NOT USE`, `windows-relay/runtime` remain. Exactly **6 dirty/untracked Git status entries**. Do not infer these six items are backups or automatically remove unique private runtime state.
- **Windows Relay tests: 434 run, 9 FAIL and 4 ERROR.** Consumer independently **123/123 PASS**. The aggregate health sweep properly returned failure.
- Defects identified in the 9 failures: one-line content `recommended_action` drift between canonical persistent script and consumer/root copies (3 copy-equality tests), old browser source assertions expecting `callAction(m.packet)` instead of authenticated `callAction(m.packet,ownerDecision.owner)` (2), stale HUD STOP/launcher and unimplemented sixth RETRY expectations (3), outbound test neglecting mandatory explicit ARM (1).
- The **four errors** align with legacy protocol fixtures that omit ARM in three Windows sender claim tests and expect retired `OPERATION_DISCIPLINE_REMINDER` in the sandwich-only result test; exact individual exception stack traces were **not** present in the returned bounded summary, so they remain hypotheses pending native rerun.
- Corrections after this receipt, **source-focused and currently not native reverified**: synchronized just one diagnostic feedback line across the three otherwise identical content scripts (do not replace One-Click Go's separate worker); updated browser contract tests for canonical owner-bound dispatch; aligned HUD tests with five-button implementation and delegated startup; positively armed isolated sender fixtures; removed obsolete extra reminder expectations; replaced unreachable PowerShell parse error with fail-closed tombstone; improved retired-installer no-mutation test.
- Existing accepted live v0.3.18 process and pinned tag remain **untouched**. Source fixes alone do not change a running Firefox/Windows process.

**Next acceptance:** fast-forward WIP and run `python -B windows-relay/tools/relay_project_health_sweep.py` and `python -B windows-relay/tools/relay_project_test_sweep.py`. If any tests still fail, obtain bounded full failure names/messages and fix the real underlying causes; do not declare the project green from predicted outcomes.
