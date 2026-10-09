# PCE11 → PCE12 semantic handoff at reviewed 20-operation boundary
2026-10-08 22:23 UTC | DIRECTOR AUTHORIZATION: the Relay operator must semantically click New Chat, transmit the handoff, verify destination, and never ask the Director to do these steps.
## Required successor identity
New chat title: 💻PC Engineering 12🔧. Session: pce12.1. First new operation: PCE12.000. The previous PCE11.021 source acceptance objective becomes PCE12.000 because the Director requested an immediate agent rotation; no old operation may be replayed. Allowed series operations 000..100 inclusive, rotate before 101. Every fifth operation audit, every twentieth review.
## FIRST TURN: nonnegotiable governance
Read FULL consumer/control_harness.py, windows-relay/TASKS.md, docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md, docs/roadmap/ROADMAP_2026-10-08T0735Z_PCE11_ONE_CLICK_GO_RECOVERY.md, docs/windows-relay-established-facts.md, docs/relay-sandwich-procedure.md, the source-of-truth index, and this handoff. Print full-file SHA256 proofs. On local Windows execute engineering_preflight(ROOT,0,series=12) and inspect STOP, repository and source identity. Follow the stricter current harness when wording differs from historic handoff.
Canonical source repository monag144/GPT-Windows-Relay on pce11/one-click-go-recovery-and-doc-hygiene. GitHub-first commits; Windows source is clean ff-only pull/test consumer. Do not claim acceptance from GitHub source alone.
## Next actual engineering task
PCE11.019 structural user-bubble detector failed one preexisting full Windows test: test_browser_contract.BrowserContractTests.test_conversation_hydration_requires_windows_result_marker. PCE11.020 reproduced that sole failure. Canonical GitHub source now RESTORES explicit const match=text.match(...) and JSON.parse(match[1]) within resultPacketIdFromUserUnit, retains original strict user-role check and a distinct structural fallback. 3 scripts have identical blob e1d4caac65786d7de0d850a27b6e7083dba2e414. One new regression raises dynamic structural suite to 12 cases; dynamic inline suite 11. These formerly new browser source commits have NOW passed Windows acceptance repeatedly: latest PCE11.033 was 535/535 Windows tests, 123/123 consumer tests, 2/2 Firefox URLbar tests, five JS checks and exact content mirrors. The subsequent composer-selector source repair (after PCE11.035) still requires fresh acceptance. PCE12.000 must inspect latest GitHub HEAD, run full source acceptance for any not-yet-accepted source changes, and inspect rotation receipts before acting. Fail closed on any failure.
## Release/rollback boundaries
The currently live Firefox temporary extension is Client/Relay/extension, original content.js SHA256 34500934b214423afc2d3c267877a961cd0ec46521e5860ed149502d7f4e2ae5. NO live reload, activation or mutation was performed .000–.020. Preserve nine-file bin/PCE11_004_AGENT011_PREACTIVATION_20261008/original backup, .009 and .016 stages, 2532-entry BROKEN ZIP. .019 failed and created NO new stage. Relay armed and two missions pending when last checked; do not assume current state. Canonical browser events under LOCALAPPDATA/GPTWindowsRelay/browser-events.jsonl and state.json. Recovery supervisor GitHub path fix accepted but running supervisor NOT reloaded.
Goal remains reliable page error → ONE exact-tab refresh → if persist semantically click New Chat → verified context handoff; STOP, exact-once, no replay. No 12h/24h canary or full R28 acceptance has yet occurred. Do not prioritize cosmetic naming over correctness, but verify successor chat title as required.
## Prior evidence
docs/audits/AUDIT_2026-10-08T2153Z_AGENT011_FRESH_EPOCH_PCE11_OPERATIONS_000_004.md
docs/audits/AUDIT_2026-10-08T2200Z_AGENT011_FRESH_EPOCH_PCE11_OPERATIONS_005_009.md
docs/audits/AUDIT_2026-10-08T2207Z_AGENT011_FRESH_EPOCH_PCE11_OPERATIONS_010_014.md
docs/audits/AUDIT_2026-10-08T2216Z_AGENT011_FRESH_EPOCH_PCE11_OPERATIONS_015_019.md
docs/reviews/REVIEW_2026-10-08T2217Z_AGENT011_FRESH_EPOCH_PCE11_OPERATIONS_000_019.md
docs/handoffs/HANDOFF_2026-10-08T2220Z_AGENT011_AFTER_PCE11_020_USER_TURN_RECEIPT_FIX.md
docs/incidents/INCIDENT_2026-10-08T2203Z_AGENT011_CANONICAL_JOURNAL_AND_RESULT_ACK.md
After twenty attempted PCE11 operations: 17 exit-0, 3 failed (.001 reporting, .013 test script, .019 actual suite). .020 succeeded to identify regression.
## Exact rotation safety
A transition is successful only when old action result completion is visible, semantic New Chat on a positively identified managed Firefox tab is invoked exactly once, target URL changes to a distinct new /c/ ID, handoff marker appears in the actual new user turn, target title verified, STOP and mission state preserved. On any uncertainty, halt and record, never repeat a click or submission based solely on timeout. The receiving PCE12 agent cannot claim to have read controls until it actually reads them.
## Updated observed rotation evidence (October 8, 2026, through PCE11.035)
- Previous audits: docs/audits/AUDIT_2026-10-08T2243Z_AGENT011_FRESH_EPOCH_PCE11_OPERATIONS_020_024.md, docs/audits/AUDIT_2026-10-08T2252Z_AGENT011_FRESH_EPOCH_PCE11_OPERATIONS_025_029.md, docs/audits/AUDIT_2026-10-08T2303Z_AGENT011_FRESH_EPOCH_PCE11_OPERATIONS_030_034.md. The local checkout must fetch/pull audit commits before an audit-due ordinal is submitted; otherwise pre-dispatch governance will block the packet.
- The PowerShell worker cannot use DETACHED_PROCESS: deterministic silent exit 0 and no receipt. Use subprocess.CREATE_NO_WINDOW, tested with intentionally missing handoff and no-click receipt. Incident docs/incidents/INCIDENT_2026-10-08T2250Z_AGENT011_POWERSHELL_DETACHED_PROCESS_FALSE_ZERO_EXIT.md.
- Firefox UIA URL bar omits https://; strict normalized URLbar matcher fixed and full tested. PCE11.029 stopped before click for missing URL scheme, and PCE11.031 process guard self-matched its own probe; .032 Python packet had indentation error before execution. Avoid both errors.
- PCE11.033 positively launched worker pid 16252, phase WAITING_FOR_SOURCE_RESULT; subsequent PCE11.034 receipt conclusively showed HALT_BEFORE_CLICK error ROTATION_COMPOSER_COUNT_0, click_invoked=false, send_invoked=false. No successor chat was created by that attempt.
- Read-only PCE11.035 UIA forensic found exactly two Edit controls named Ask ChatGPT: one visible, enabled, writable ValuePattern with a class unlike ProseMirror; the other ProseMirror but off-screen. The minimal GitHub source repair now requires exactly one visible, enabled, named writable Edit regardless of class; a source-level regression forbids the obsolete class lock. Do NOT loosen tab identity, STOP or exact-once gates.
- At PCE12 transfer, first inspect the final one-shot receipt at LOCALAPPDATA/GPTWindowsRelay/ops/PCE11_NNN_AGENT011_SEMANTIC_AGENT12_ROTATION.json. A handoff visible in a distinct URL is necessary but not sufficient to assert title, 12-series preflight or reliability canaries. Do not repeat a New Chat click after an uncertain click or send.
## Handoff marker
[GPT_ENGINEERING_ROTATION_HANDOFF_V1]
Target title: 💻PC Engineering 12🔧
Target session: pce12.1
First operation: PCE12.000
Source: this mandatory reviewed PCE11→PCE12 rotation
[/GPT_ENGINEERING_ROTATION_HANDOFF_V1]
