# GPT Windows Relay current-build capability audit

**Later evidence (2026-10-12):** The Oct 11 audit was correct for its own observation window. Its assertion that no live end-to-end execution was proven has been superseded by the [October 12 verified canary and Git tag](../releases/WINDOWS_RELAY_LIVE_EXECUTION_CHECKPOINT_2026-10-12.md). Focused native tests: 13/13. This does not retroactively prove other capabilities or a whole-project green suite.

Audit scope: GitHub Issue #28, read-only inspection of
`GPT-Windows-Relay-Main-Build`, isolated local tests, and non-mutating Windows
runtime checks. No source, credentials, browser profile, relay process, or
operational state was changed.

## Executive status

The checkout contains a substantial Windows Relay implementation, a five-button
HUD, a persistent Firefox extension, the One-Click Go consumer, durable JSON
state/result handling, ownership and STOP controls, and a broad test suite.
It is not presently a proven end-to-end build.

The local checkout is `e8e18e4135d8808c2cf2494a7d911154d58be09a` on
`wip/windows-relay-rebuilt-resynced-2047-101026`. After a read-only fetch, the
remote WIP branch is `1b249a7a25f7d52a838458ea5485dea1d6e60e8b`; local is 14
commits behind. Remote `main` is `baeec82ff9d36505ee4e894cafe106428dfe604d`.
Local uncommitted work was preserved and not reconciled.

No listener was present on `127.0.0.1:8766` during this audit. No matching
relay process or scheduled-task row was returned by the bounded checks. A local
`%APPDATA%\GPTWindowsRelay\bridge.json` exists with host `127.0.0.1`, port
`8766`, and a token present; the token value was not read into this report.
Firefox processes exist, but accessible profile metadata did not prove a loaded
GPT Windows Relay add-on or its source path. Loaded extension identity is
therefore **UNKNOWN**, not inferred from the on-disk manifest.

## Capability matrix summary

The companion CSV is the feature-by-feature matrix. The most important
findings are:

| Area | Evidence-based state | Notes |
|---|---|---|
| Backend packet parser/result envelope | PRESENT AND WIRED; TESTED OFFLINE | `extract`, `process`, `result`, saved full/wire results. |
| Durable action identity | PRESENT AND WIRED; TESTED OFFLINE | `State.reserve` persists `INFLIGHT`, rejects collisions, and avoids automatic replay after restart. |
| STOP/disarmed state | PRESENT AND WIRED; TESTED OFFLINE | `set_armed`, `stop_generation`, browser-quiescence acknowledgement, persisted disarmed startup. |
| HTTP authentication | PRESENT AND WIRED; TESTED OFFLINE | Bearer header is required for HTTP handlers. |
| Operator owner binding | PRESENT AND WIRED; NOT PROVEN LIVE | `/owner-bind` requires a separate operator header and validates URL/session/tab; state mutation rolls back on save failure. |
| Firefox scanner/result recognition | PRESENT IN SOURCE; TESTED OFFLINE; NOT PROVEN LIVE | Selectors, current-turn wrapper fallback, result confirmation/watchdog logic exist. |
| Firefox → backend action transport | **BROKEN / UNWIRED** | Persistent worker `callAction()` posts only `{packet}`. Backend `/action` constructs transport from `issuance` and `owner`, and `process()` rejects missing metadata with `transport_identity_missing`. |
| Extension issuance durability | PRESENT BUT UNSAFE/INCOMPLETE | Worker cursor/owner storage exists, but `chrome.storage.local` write failures are swallowed and no issuance object is sent in the action request. |
| Conversation ownership | PRESENT IN SOURCE; NOT PROVEN LIVE | Worker checks tab URL/focus and owner state; packet `owner_claim` can influence transfer. Backend independently checks bound owner/session. |
| HUD controls | PRESENT AND WIRED OFFLINE | START, STOP, RESTART, OFF, KILL are bound in `hud.py`; live HUD not observed. |
| Canonical process identity | PRESENT IN CONTROL SOURCE; NOT PROVEN LIVE | Controller/watchdog contain canonical-path checks and foreign-listener refusal. No listener was available to exercise them. |
| One-Click Go | PRESENT AND WIRED AS SEPARATE PRODUCT | `consumer/` contains bootstrap, browser manager, recovery supervisor, packaging and tests; it is not the Windows Relay backend. |
| Attachments/screenshots/UIA | PRESENT IN SOURCE; TESTED OFFLINE | Managed screenshot endpoints, attachment hydration, UIA/text-entry helpers exist. |
| Job-application automation | PRESENT IN SOURCE; TESTED OFFLINE | Multiple `job_application_*_v2.py` modules and tests exist. |

## Source and deployment identity

Critical local hashes:

| File | SHA-256 |
|---|---|
| `windows-relay/windows_relay.py` | `BA29B6BFAAA453BE6669C47D5B5C4E8A9F36A07AAB9FAB046849CD93EC39F002` |
| `windows-relay/hud.py` | `363C3D55446DF3E850CE53DC1C4DEF6CCAA1FF665126A5A41FF1D93B24CBC44E` |
| `windows-relay/relay-control.ps1` | `04EDFA01B2EBDA8933ED636ED09A2C2F518D123CD224B3A2F33129BDB334CCFE` |
| `windows-relay/relay-watchdog-loop.ps1` | `0C41060188A752755CD41B2D5D4798E8CB8794929C07339ACA19CADF1DEFCA6B` |
| `windows-relay/run.ps1` | `E075077BDF5E905581B901216F1417D95E7600500DBA9C0005818BC9CDD33FA5` |
| `windows-relay/START-GPT-WINDOWS-RELAY.bat` | `174995B2A2133021C280FF4D9B9101E6FFAB90BFE67F1560BB8DEF5D1CA86B22` |
| `windows-relay/extension-persistent/manifest.json` | `85418070F6C0CF3249844A88E868B3BB79F31F1D9077EC39D024AC3503585073` |
| `windows-relay/extension-persistent/content.js` | `5169E84985E9452E9E55EA29D5BCD56F4484E0B02EE7853C21D8CBE2BC3C151A` |
| `windows-relay/extension-persistent/service_worker.js` | `DF5943F14A2B808A0FD73AFF001EAAF4361D1167D590D83584F13FB402611555` |
| `windows-relay/extension-persistent/popup.html` | `0CC43EECACA320AE4E100BBC3A4CD72CF8C04B776183AE8CFECCA5B25E3B77DA` |
| `windows-relay/extension-persistent/popup.js` | `41F217ADB067482E5B2572CDB68C233AF4596AB54AB7EDC10224415A0F0FD415` |

The manifest declares GPT Windows Relay v0.3.17 with Gecko ID
`gpt-windows-relay@local`. This proves source contents only, not that Firefox
has loaded that package.

## Tests (not benchmarks)

Tests were run with Python 3.13 `unittest`, `PYTHONPATH=windows-relay;consumer`,
using isolated test fixtures. No live service calls, browser tab mutations, or
real command dispatches were used by the selected tests.

| Test file | Result | Duration |
|---|---:|---:|
| `test_dispatcher_no_audit_gate.py` | 2 passed | 0.025 s |
| `test_control_launch_runtime.py` | 3 passed | 2.853 s |
| `test_result_turn_recognition.py` | 1 passed | 0.002 s |
| `test_whole_product_stop_contract.py` | 15 passed | 0.375 s |
| `test_browser_contract.py` | 60 passed | 0.077 s |
| `test_firefox_adapter.py` | 15 passed | 0.329 s |
| `test_protocol.py` | 36 passed, 8 errors | 4.065 s |

The protocol errors are real contract drift, not waived failures: several
fixtures call `process()` without the now-required authenticated transport;
others expect old outbound-worker/disciplined-output behavior. The earlier
full-suite baseline (403 tests, 5 failures, 8 errors) was not treated as a
current result; this audit reran only the bounded set above.

Additional static checks passed: JavaScript syntax for the persistent
`service_worker.js` and `content.js`, and Python compilation for 79 source
files (0 failures). `pytest` is unavailable in the environment.

Private unmodified test logs were retained outside the repository and are not
published in this sanitized report.

## Benchmarks (separate from tests)

No live benchmark was run. No canonical benchmark harness or valid performance
artifact was found outside the archived/unverified runtime tree. Therefore this
audit provides no measured command latency, throughput, restart-recovery
latency, scanner latency, or end-to-end delivery rate. Historical strict-grade
and G26/G27 counters are evidence-history labels, not current measurements.

## Redundancies and unverified copies

- `windows-relay/runtime/` is an untracked nested consumer/runtime snapshot
  containing its own virtual environment and historical builds. It is archival
  or unverified, not proof of the canonical backend.
- `windows-relay/extension/` is a tracked temporary/consumer extension tree;
  packaging and browser-fix scripts still reference it. It must not be confused
  with `extension-persistent/`.
- `Prototype/` contains acceptance profiles, candidate packages, test evidence,
  and release-candidate material. It is experimental, not a deployment source.
- `Legacy/` and older GPT subtrees contain historical Git checkouts and
  rollback snapshots. They were not deleted or moved during this audit.
- `consumer/` is intentionally retained as GPT One-Click Go, a separate product
  variant rather than a duplicate Windows Relay backend.

## Priorities

1. Reconcile local WIP with the remote WIP branch without overwriting the local
   uncommitted work; local is currently 14 commits behind.
2. Repair the persistent extension/backend transport contract by supplying and
   validating authenticated issuance and owner metadata, with fail-closed
   storage errors. This is the smallest blocker to an end-to-end action path.
3. Run the protocol suite after the transport fixture contract is reconciled;
   preserve STOP, owner binding, collision, and no-replay behavior.
4. Establish isolated runtime identity evidence for backend, HUD, watchdog, and
   Firefox before any live cutover. The current audit observed no listener and
   cannot prove a loaded extension.
5. Only then measure end-to-end latency/recovery in a disposable environment;
   do not use live ChatGPT actions as a benchmark.

## Verdict

**Capability-rich but not end-to-end ready.** Core backend safety and offline
contracts are present, while the actual Windows listener is absent and the
persistent worker/backend action metadata contract is visibly disconnected.
The build should remain unchanged and un-deployed pending the transport repair,
protocol test reconciliation, and independent runtime identity evidence.
