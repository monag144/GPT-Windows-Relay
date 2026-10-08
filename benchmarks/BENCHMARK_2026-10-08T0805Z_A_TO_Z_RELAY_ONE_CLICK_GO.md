# PCE011 Relay and One-Click GO A–Z benchmarks — 2026-10-08T0805Z

## Decision boundary
Standalone Windows Relay and One-Click GO are **different products**; score each candidate by pinned Git commit, installed/live hashes, browser and Windows version. No candidate is accepted solely for having newer source or passing unit tests. Never label an unmeasured night as a pass.

## Current historical contenders
- **Relay PCE8 v16:** strongest *specific live browser recovery* evidence: PCE8.101–106 consecutive exact-once operations, owner-lease/deadman tests. Reference commit `694d47ab89596d5c3801f749caa352b951a2be52`; recorded live content SHA-256 `9541A890A80A8200F949E6D7DA7132C10335BFABD487E0B89047919C6B1B899E`. Does **not** prove complete packaged snapshot, whole-product STOP or 12h night.
- **Relay PCE7 legacy live fallback:** explicitly restored usable legacy HUD/Relay after failed PCE7.446 STOP/OFF/START cutover. Exact full installed build hashes were NOT preserved in this GitHub audit; PCE7.447 branch tip is not automatically the restored binary.
- **Relay PCE8 v17 and PCE9/10:** improved source components; runtime acceptance remains disputed/failed. Compete in isolated tests, not baseline by default.
- **One-Click GO consumer r28:** distinct frozen reference `GPT-Termux-Relay/consumer/one-click-go` revision 28. Firefox is intentionally unsupported until signed persistent addon; run Chrome and Edge consumer matrix.

## Test catalog
| Case | Scenario | Applicable | Pass requirement | Challenge |
|---|---|---|---|---|
| A | Pinned acquisition/SHA | both | Verify commit and package hashes | Corrupt package |
| B | Clean bootstrap | both | Bootstrap from clean Windows user profile | Missing Python and path spaces |
| C | Credentials isolation | both | Loopback/token access; deny unauthorized requests | Invalid token and wrong host |
| D | Operator lifecycle | both | START STOP OFF RESTART KILL, no duplicate processes | Crash during START |
| E | Extension pairing/runtime | both | Current installed addon hash, handshake, one correct instance | Stale worker |
| F | Exact Firefox tab/PID/URL | firefox | Unique exact URL-bound Firefox identity or fail closed | Offscreen tab and wrapped UIA |
| G | One-Click GUI/Update | consumer | GO.bat setup choose browser connected GO and Update work | False READY |
| H | Authenticated transport | both | Correct selected browser and token-scoped request delivery | Bridge disconnect |
| I | 30-minute idle | both | No false STALLED and recovers instantly after idle | 30 minute idle |
| J | Packet discovery/settling | both | Correct assistant packet; bounded discovery timeout | DISCOVERED hang |
| K | Exactly-once effect | both | One side effect/reservation/saved result/visible receipt | Duplicate scanner |
| L | Lost HTTP reply replay | both | Saved result on same-ID retry, no repeat effect | Drop HTTP reply post-commit |
| M | Malformed and collision denial | both | Reject wrong platform, bad syntax and same-ID different payload | Forged packet |
| N | Connectivity recovery | both | Bounded reconnect, correct chat, no lost or duplicate action | Temporary network outage |
| O | STOP whole-product barrier | both | Exact generation browser/backend quiescence, no late actions | STOP mid-retry |
| P | Crash supervision | both | Supervised backend/HUD restart retaining state | Controlled process crash |
| Q | Scoped page refresh | both | Refresh exact tab, reacquire, no reexecute | Refresh mid-result |
| R | Firefox addon lifetime | firefox | Reinstall temporary after refresh; full restart only signed persistent | Dedicated Firefox restart |
| S | Error screenshot/recovery advice | both | Independent screenshot delivery plus whitelisted recovery | Error in input stream |
| T | Post-result GPT turn stall | both | Finalization watchdog acts without executing command again | Stuck generation |
| U | 12h overnight endurance | both | 43200s, >=99.5% heartbeat, zero rescue/effects, hourly full loops | Injected bounded failures |
| V | Exact visible result | both | Unique exact user result, no stale/false acknowledgment | Old receipt beside new packet |
| W | Windows restart/resume | both | Persist state/STOP and recover safely after reboot | Isolated Windows restart |
| X | Chrome/Edge consumer matrix | consumer | Separate Chrome and Edge E2E; Firefox only signed | Edge load race |
| Y | Zero unexpected manual rescues | both | Zero clicks, refreshes, retries, pastes or continue requests | Old babysitting failure |
| Z | 24h release qualification | both | 86400s, >=99.5% heartbeat, zero rescue/safety incident | 24h fault campaign |

## Evidence and overnight gate
- `both` applies to standalone Relay and consumer, `consumer` only One-Click GO, `firefox` only when browser is Firefox. All **applicable** cases must pass, including safety STOP and zero-unexpected-rescue; N/A must be reasoned by declared product/browser matrix.
- For U: at least **12 hours**, independently observed authenticated localhost heartbeat **>=99.5%**, no poll gap >120s, hourly successful fresh exact-ID packet/result loops, no unexpected user help, no duplicate effects, no unsafe action, no stale/false receipt.
- For Z: independently observed **24 hours** under the same gates, with controlled failures/recovery and morning resumption. If the observer dies, the night is not automatically a pass. A healthy `/status` alone does not establish browser autonomy.
- A passing score needs evidence receipts, not just a written PASS. Save raw sensitive evidence only locally; report SHA-256/metrics to ChatGPT. For comparison preserve immutable SHA and loaded/runtime identity; no changing build mid-run.
- Run fault injections on isolated profiles/VMs. Do not crash the active production Relay, restart the user's Firefox broadly, replay uncertain IDs, or bypass STOP or platform approval.
- Optional Codex CLI may suggest repairs **after** a failure is classified; changes remain separate GitHub commits, followed by rerunning the failed case and regression set.
- TCP observation does not read relay credentials; socket connection is evidence only of listener liveness. The independent monitor must be started under an external OS supervisor for restart survival. Its observation records remain local if the Relay dies. Run observer as separately supervised Windows process or Task Scheduler task. When the Relay returns it can deliver its existing local summary rather than having been the sole recorder.

## Runner
- `python benchmarks/benchmark_runner.py init --product relay --browser firefox --sha <40-hex> --label relay-v16 --output <run-directory>`
- `python benchmarks/overnight_observer.py --port 8766 --output <run-directory>/heartbeat.jsonl --hours 12` (independent read-only monitor)
- `python benchmarks/benchmark_runner.py record --run <run-directory> --case K --result PASS --evidence <path> --reviewer <id>`
- `python benchmarks/benchmark_runner.py evaluate --run <run-directory>`
- `python benchmarks/benchmark_runner.py compare --runs <dir1> <dir2>`

The observer reports localhost durability, not browser result success. Case U/Z require independent mission loop and rescue/effect accounting evidence in addition to observer metrics. No currently inspected Relay has met all gates.

## Historic evidence
`docs/audits/ACCEPTANCE_2026-10-06T2219Z_PCE8_V16_BROWSER_RECOVERY.md`;
`docs/audits/ACCEPTANCE_2026-10-06T2236Z_PCE8_STALE_OWNER_LEASE_DEADMAN.md`;
`docs/INCIDENT_2026-10-06T0953Z_PCE7_445_447_HUD_CONTROL_CUTOVER_CHAIN.md`;
`docs/audits/PCE8_2026-10-07T0002Z_CORRELATED_WHOLE_PRODUCT_STOP_SOURCE_ACCEPTANCE.md`.

**Release verdict:** none certified overnight yet.

## Structured JSON evidence fields
Every PASS uses a local evidence JSON file with `{"passed":true}` and an independent reviewer. Safety cases C/K/L/M/O/V/Y also require explicit zero-valued `manual_rescues`, `duplicate_effects`, and `unsafe_executions`. Overnight U and Z additionally require `observer_summary` (from read-only monitor), `hourly_receipts` for each elapsed hour (`hour`, `executions:1`, `visible_result:true`, `duplicate_effects:0`), and `unrecovered_stalls:0`. The scorer hashes this file; no PASS can be accepted after evidence bytes change. **Reviewer-attested is not independently proven.**
