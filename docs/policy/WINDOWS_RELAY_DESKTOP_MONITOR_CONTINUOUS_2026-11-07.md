# MSI Katana native ChatGPT desktop monitor — continuous interception

Read-only comparison (November 7, 2026) against `monag144/GPT-Termux-Relay`, branch `development/runtime-control`, commit `ea772ec517c287ba7f86f163036298e52c65a023`: Android service `RelayAccessibilityService.java` uses accessibility-event debounce plus watchdog scanning, `PacketExtractor.java` for latest complete packet, local processed ID, background executor dispatch, pending-result injection and Send action. `BridgeClient.java` talks to the Termux socket over paired localhost transport. **The Termux repository was read only — no fetch/pull/write or state changes.**

Windows current evidence: native UIA text detects known canary, one writable composer and Send button, but no reliable assistant authorship. One-shot heartbeat failed closed at `COMPOSER_NOT_EMPTY_REFUSE_TO_OVERWRITE_USER_DRAFT`. One Firefox-era Node test remains red; consumer suite passed.

The CMD launcher `windows-relay/START-CHATGPT-DESKTOP-RELAY.cmd` opens a persistent PowerShell monitor using existing read-only UIA detection (`Watch-ChatGPT-ActionCandidates.ps1`). Monitoring is automatic until the operator closes the window or uses Ctrl+C. In-memory `HashSet` deduplicates seen packet IDs during each run. It never runs OS commands or calls the legacy backend, because user/quoted message attribution is not trustworthy yet.

A one-shot status sender automatically attempts `Send-ChatGPT-DesktopHeartbeat.ps1`, deferring if there is an existing user draft and retrying only that known safe no-send condition. The private status-only dedupe journal `%LOCALAPPDATA%\GPTWindowsRelay\desktop-heartbeat-ledger.json` reserves the send attempt *before* calling the sender; success/uncertainty/failure are terminal and require inspection, not blind resends. Journal contains no credentials, packet commands or chat text. This is operational state, not a backup.

To start via CMD after GitHub pull:
`"C:\Users\p0pe0\Projects\Windows Relay\windows-relay\START-CHATGPT-DESKTOP-RELAY.cmd"`

Expected console output includes `CHATGPT_DESKTOP_MONITOR_V1`, `DESKTOP_ACTION_DETECTED=PCE18-KATANA-DETECTION-001` and possibly `DESKTOP_HEARTBEAT=WAITING_FOR_EMPTY_COMPOSER` until the user draft is cleared. Do not remove user draft automatically. `DESKTOP_HEARTBEAT_SUBMITTED_ID` requires an actual GPT chat receipt for end-to-end acceptance.

Limitations: no OS command execution or native backend linkage, no verified assistant-only attribution, no guaranteed durable monitoring across reboot, and no claim of full relay completion. The legacy Firefox runtime remains untouched.
