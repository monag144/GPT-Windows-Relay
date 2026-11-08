# ChatGPT desktop — detection-only operational gate (2026-11-07)

MSI Katana evidence through PCE18 UIA gate 3: 796 ChatGPT UIA elements, marker in Document and Text nodes; role signals absent; `STRUCTURAL_ERRORS=3`. This establishes text presence, NOT assistant authorship.

## Delivered

`windows-relay/tools/Watch-ChatGPT-ActionCandidates.ps1` is a standalone **read-only instruction detector** using Windows UI Automation TextPattern on actual `ChatGPT` process Document elements. It locates *complete, line-anchored* `[GPT_WINDOWS_ACTION]` / closing-marker frames with JSON-shaped protocol fields, hashes them, suppresses duplicates within the run, and prints only a bounded set of metadata: packet ID/session/shell and truncated fingerprint. No command bodies, message text, pairing secrets, screenshots, or clipboard.

The monitor deliberately treats **all** candidates as untrusted (`BASELINE_UNTRUSTED`/`NEW_UNTRUSTED`), because a marker may appear in a user message, an assistant quote, or a spoofed block. It does **not** send any HTTP, start/arm the backend, modify the composer, run commands, or persist state. Fingerprints are for in-process repeat detection, NOT an authorization proof. If the app does not expose full text in Document range, result can be zero even when a marker is visible.

## CMD

`git -C "C:\Users\p0pe0\Projects\Windows Relay" pull --ff-only origin wip/windows-relay-rebuilt-resynced-2047-101026`
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\p0pe0\Projects\Windows Relay\windows-relay\tools\Watch-ChatGPT-ActionCandidates.ps1" -WatchSeconds 30`

Acceptance: open the ChatGPT Windows app on the conversation with an assistant-authored harmless test action packet while the monitor runs. Expect the packet ID as `CANDIDATE_ID=...`; no OS command should execute. Initial candidate may be classified BASELINE if rendered before startup. Do not mistake candidate discovery for positive role attribution or permission to dispatch. Next engineering stage is explicit, reliable assistant-turn role attribution and result-delivery testing before wiring the native desktop UIA scanner to the authenticated executor.
