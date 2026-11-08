# Desktop ChatGPT app — UIA probe gate 2 (2026-11-07)

User's MSI Katana (`C:\Users\p0pe0\Projects\Windows Relay`) completed gate 1:
- `CHATGPT_PROCESS=ChatGPT`, PID 25444 (ephemeral), 1371 UIA descendants
- 1 document, 1 editor/composer, 304 buttons, 830 text-pattern elements
- WindowsTerminal was also enumerated by title; it must **not** be treated as the ChatGPT app

This suggests a viable native Windows UI Automation transport, **not** proof of robust assistant-turn selection, packet extraction, composer write, or send.

The next read-only gate is `windows-relay/tools/Inspect-ChatGPT-DesktopTextRoute.ps1`. It:
- scopes *only* to top-level windows whose process name is **ChatGPT**, not terminal titles, browsers, or other programs
- uses UIA `TextPattern.DocumentRange.FindText()` and control accessible names to detect the unique non-executable probe marker `GPT_RELAY_DESKTOP_UIA_PROBE_20261107`, reporting presence/counts only
- reports number of likely Edit/ValuePattern writable composers and Send/Stop buttons, not their content
- checks whether a probe-marker node has structural assistant/user signals in its UIA ancestors; this is **not** sufficient proof of message origin
- never prints conversation text, reads or changes clipboard, clicks, types, executes packets, starts or arms a relay, writes files, or uses OCR

CMD invocation:
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\p0pe0\Projects\Windows Relay\windows-relay\tools\Inspect-ChatGPT-DesktopTextRoute.ps1"`

Before running, open the latest assistant response containing the marker in the native ChatGPT app, and keep it visible. A zero marker result may mean content is virtualized or the wrong conversation is open, not necessarily that UIA cannot read content.

**Next gates** (not implemented): reliable assistant-only attribution, fully-rendered frame parser, injection/send controlled no-op test, native owner/session binding, authorized backend handoff with durable result dedupe. No browser integration, no auto-start, no live command execution at gate 2.
