# PC Engineering 6 → 7 handoff

Timestamp: 2026-10-06T0234Z  
Boundary: operation 400 / new-agent rotation  
Development branch: `consumer/r29-firefox-offline-tray`  
Stable branch: `consumer/one-click-go` remains unpromoted at `d5b9db7`.

## Why rotate now

Director declared the operation-400 boundary and requested Agent 7. The existing service worker already contains `GPT_RELAY_CHAT_ROTATION_100_V1`; the A6 suffix sequence exposed that relying only on a numeric ordinal embedded in packet IDs can miss a conceptual 100-operation boundary. Agent 7 must preserve the date-indexed handoff as source of truth.

## Proven in Agent 6

- live Firefox relay backend healthy and exact-once execution functioning;
- HUD false-idle-stall fixed;
- exact instruction/HUD work deployed;
- forced reinspection + bounded five-minute watchdog source/tests present;
- recovery-advice secondary observer live;
- approval prompt detector source/live activation exercised;
- Plane-D zero-touch prompt submission PASS;
- recovery advice visible and extension observer PASS;
- guarded clipboard/Enter fallback staged, though A6.399au used semantic Send;
- non-self-parsing recovery prompt hardening and complete-envelope coaching guard committed;
- independent read failures are now observable in supervisor source;
- visible ChatGPT error detector + diagnostic screenshot supervisor path committed.

## Open defects at rotation

1. Independent Plane-D readback: A6.399au detached worker sent successfully, but all 60 reads exited 1. The same reader later succeeded in normal relay context. A6.399ay was intended to isolate detached context but stopped earlier on a stale test assertion; that assertion is now repaired. Re-run this first.
2. ChatGPT `Error in input stream` UI was previously invisible to health. Source detector/screenshot classification is committed; Windows/live validation remains.
3. Post-result assistant turn can remain active for minutes after visible result. Implement separate finalization watchdog + screenshot without re-executing action.
4. Screenshot capture exists in supervisor evidence, but broken-primary recovery still needs a trustworthy way to present the captured image to GPT, not merely a local path.
5. F-005 exact visible-result/stale-success semantics remain open.
6. Full consumer One-Click Firefox E2E remains open.
7. Full Chrome E2E remains open.
8. Full Edge E2E remains open, including historical false-ready/postload-race checks.
9. Approval connection persistence for GitHub/Google Drive requires final acceptance.
10. Deliberate 100-operation/new-chat rotation acceptance is this transition itself and must be logged.
11. Stable promotion is forbidden until the three-browser acceptance matrix and recovery/screenshot gates pass.

## Agent 7 first operations

- A7.1: sync r29, compile relevant production + test modules, run recovery-supervisor/content-contract gates, then run the detached read-context probe that A6.399ay never reached.
- A7.2: stage/activate the visible ChatGPT error detector in dev Firefox, reload the temporary add-on out-of-band, refresh the new Agent 7 chat, and live-prove detected/cleared lifecycle plus screenshot evidence.
- A7.3: implement/test the post-result turn-finalization watchdog.
- Then resume the browser acceptance matrix and remaining mission in the order above.

Do not restart the audit from scratch. Continue the dated audit/index and add only new evidence/incidents.
