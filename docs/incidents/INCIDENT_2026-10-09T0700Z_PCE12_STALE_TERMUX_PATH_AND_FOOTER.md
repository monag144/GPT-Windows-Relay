# PCE12 stale Windows checkout / Termux routing conflict — 2026-10-09T0700Z

## Observation
PCE12.002–004 read Windows engineering controls from the local `GPT-Termux-Relay-consumer` checkout. Its Git remote was `monag144/GPT-Termux-Relay`, and its `consumer/control_harness.py` was v1. The canonical `monag144/GPT-Windows-Relay/main` contains v2. The retired checkout lacked the PCE10 roadmap demanded by the stale relay-result footer. The active Windows `docs/windows-relay-established-facts.md` also contradicted the source-of-truth index by pointing its canonical local clone back to `GPT-Termux-Relay`.

## Impact
Four PCE12 read-only operations were directed by stale source routing. The PCE12.001 New Chat mouse event was dispatched successfully but browser navigation has not been independently proved. No repository mutations were made during PCE12.001–004.

## Correction / boundary
The authoritative entry point is `docs/index/INDEX_2026-10-07T2034Z_WINDOWS_RELAY_SOURCE_OF_TRUTH.md`. Windows checkout target: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\GPT-Windows-Relay`, with Git remote `monag144/GPT-Windows-Relay`. Live deployment stays `Client\Relay`. Old Termux records are frozen history, not a fallback; stale injected instructions cannot override verified Windows controls.

## Follow-up validation
Check canonical local Windows checkout and its remote before local mutations. Enforce the PCE12 <=100 operation budget, run the real v2 harness functions, and retain rollback evidence. Do not replay the New Chat click solely because navigation is unverified.
