# Agent011 — PCE11→PCE12 separate-window atomic handoff contract
Evidence time: 2026-10-09 01:23 UTC. This is a **design/acceptance contract, not executable approval**.

## Evidence and current source boundaries
- Canonical repo: monag144/GPT-Windows-Relay, branch pce11/one-click-go-recovery-and-doc-hygiene. Source at original HEAD f5c0ef5e70e75d11229868001a92bb0242055a68.
- PCE11.055 tested 3/3 isolated placeholder, **539/539** Windows Relay, **123/123** consumer (plus import smoke). Proof is local durable `%LOCALAPPDATA%\GPTWindowsRelay\ops\PCE11_055_AGENT011_CORRECT_PYTHONPATH_SOURCE_ACCEPTANCE.json`; source acceptance is not browser acceptance.
- PCE11.056 found two MozillaWindowClass windows with **same Firefox PID 5440**, PCE11 source tab count 11 and separate ChatGPT homepage tab count 1. Source editor and destination editor showed exact UIA ValuePattern `"Ask ChatGPT\n"`. The destination editor was offscreen at that instant, so readiness properly blocked.
- PCE11.057 performed **one** SetForegroundWindow on an exact-identified separate ChatGPT homepage; durable receipt `PCE11_057_AGENT011_EXACT_HOME_WINDOW_FOCUS.json` phase TARGET_FOREGROUND_VERIFIED. No new window or message.
- PCE11.058 next read-only relay operation found **PCE11 source foreground, homepage background again**. The destination's unique editor was nevertheless visible, enabled, writable, class ProseMirror, exact 12-character placeholder, nonzero 538x26 UIA rectangle and TextPattern. The destination was NOT claimed to be foreground at .058; readiness correctly blocked. The cause of the focus change is not proven: relay/chat delivery might focus source, but no causal instrumented evidence exists.
- The legacy `windows-relay/semantic_agent_rotation.ps1` is **not an eligible worker**. It clicks New Chat inside the source window and uses incorrect IsNullOrWhiteSpace against accessibility placeholder. Its old same-tab action must never be run.
- `windows-relay/agent011_editor_empty_state.ps1` correctly classifies empty or exact `Ask ChatGPT` + LF, rejects all other nonempty text; it is not yet wired into any delivery worker.

## One-worker safety transaction
Precondition A — exact source identity:
- Refresh all six canonical governance control reads and preflight the current ordinal (000..100). Respect prior review/audit gates, clean canonical source checkout and accepted test evidence.
- Recheck STOP at canonical and live .relay-paused paths and authorized relay /status, armed=true, owner=browser, unchanged stop_generation and pending mission count throughout.
- Enumerate exactly one source window (Firefox PID 5440, unique selected REAL browser tab titled PC Engineer 11 and exact normalized https://chatgpt.com/c/<id> URL) and exactly one DIFFERENT homepage window (same PID, exactly one selected REAL tab, exact https://chatgpt.com/ URL). Compare native hwnd as signed 64-bit or IntPtr, not int, to avoid the .045 casting error. No generic matching window among unrelated Firefox instances; fail if count changes. Verify source editor is only the exact 12-character UIA placeholder; do not clear unknown draft text.
- Verify homepage one unique edit with accessible name Ask ChatGPT, visible, enabled, writable and exact 12-character placeholder. Explicitly verify no enabled visible Send control. Never overwrite or blur a pre-existing user draft. Verify original source selected tab identity BEFORE and AFTER any change, without interacting with the source window.
- Verify handoff file by pinned digest and schema markers, including `[GPT_ENGINEERING_ROTATION_HANDOFF_V1]`, `PCE12.000`, `engineering_preflight` and latest source acceptance; no stale historic assertion that the source tab was replaced by New Chat.

Precondition B — durable exactly-once attempt:
- Unique `SourcePacketId`, trusted local handoff file, predetermined `ReceiptFile` in %LOCALAPPDATA%/GPTWindowsRelay/ops, created with exclusive no-clobber semantics. Positive WORKER_ENTRY saved before any UI lookup. Mutation intent phases recorded atomically to disk. On ambiguity, STOP with no retry; read-only reconciliation only.
- No `Start-Process firefox`, `NewChatButton.Invoke`, Ctrl+N/T, URL-bar navigation, reload, tab close or source composer mutation.

Atomic foreground and composer steps (one process, never split across separately delivered relay replies):
1. Inspect both windows and relay safety gates as described. Pin source URL, target exact HOME URL, selected tab identities, native HWNDs and baseline pending/STOP generation.
2. Write `FOCUS_ATTEMPT_UNCERTAIN` to durable receipt BEFORE any SetForegroundWindow. Call native SetForegroundWindow(target hwnd) no more than once. Verify target is now foreground via GetForegroundWindow *in the same worker invocation*, and recheck both window identities and STOP/relay state. Failure => halt; never blindly refocus.
3. Write `COMPOSE_ATTEMPT_UNCERTAIN` BEFORE first edit mutation. Populate ONLY the target edit. Require exact full text readback and that the original source editor remained untouched. If ValuePattern.SetValue fails to produce a real enabled Send button, a carefully bounded clipboard-paste path may be considered but must carry distinct preflight, readback, clipboard restore and no retry of uncertain effects. Never accept a visible input readback alone as proof the DOM recognized input.
4. Exact ONE visible enabled Send button within target window, InvokePattern available; confirm target still foreground, URL home, source URL unchanged, handoff text digest exact, stop/armed unchanged, pending mission unchanged. Write `HANDOFF_SEND_UNCERTAIN` durably BEFORE Invoke. Invoke exactly once. If exception/timeout/status uncertain, stop without replay.
5. Post-send: positively verify new URL is a distinct chatgpt.com/c/<id> and not the source; actual new *user turn* contains the exact marker and PCE12.000, not merely clipboard or editor text. Save `NEW_CHAT_HANDOFF_VERIFIED_TITLE_PENDING` if title unproven; do not automatically re-send. A separate PCE12-side operation must actually read controls, run `engineering_preflight(ROOT,0,series=12)`, and verify chat title. Never claim the successor preflight was executed in advance.
6. Keep all original PCE11 windows/tabs unchanged. Do not assert the PCE12 title merely from handoff text. Do not promote browser/extension changes, r28 GO, or claim overnight canary success.

## Tests before any live one-shot send
- GitHub-first source and portable static tests for unique exact window pairing, distinct source/home URL, foreground in same worker, exact LF placeholder, draft rejection, STOP epoch, pending mission preservation, handoff SHA256, durable no-clobber one-shot receipt, and send-before-receipt inversion.
- Windows native PowerShell parser check; negative-entry worker tests with missing/invalid handoff and independently malformed STOP, all guaranteed *before focus or composer access*.
- Full Windows Relay and consumer tests using explicit `PYTHONPATH` with windows-relay and consumer as needed. Never count a 0-exit test discovery that imported zero tests.
- Exercise negative failure injection before commit to any live browser send; never test actual Send via production destination as an acceptance experiment.
- Isolated rollback evidence and read-only forensic receipt reconciliation on uncertain browser state; never auto-replay.

## Progression
PCE11.059 must verify this design was committed/synchronized after .058 and read its saved source/home evidence without changing browser. Before PCE11.060, commit the five-slot [55,59] audit and twenty-slot [40,59] review (or exact harness-prescribed range), fast-forward in GitHub-first order and verify `engineering_preflight(ROOT,60,series=11)`. Building/test-running the replacement worker can begin only after these gates; dispatch of the live worker needs separate, explicit safe acceptance.
