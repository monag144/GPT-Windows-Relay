# Native desktop ChatGPT UIA heartbeat — one-message delivery gate

MSI Katana detection proof: assistant-posted `PCE18-KATANA-DETECTION-001` was discovered by the read-only UIA detector as `BASELINE_UNTRUSTED`. This establishes packet detection, **not** authorship or command execution.

`windows-relay/tools/Send-ChatGPT-DesktopHeartbeat.ps1` is an explicitly invoked single-shot heartbeat. It calls the read-only scanner for five seconds and then targets only one real ChatGPT process window containing the canary, exactly one initially empty editable composer, and at most one enabled Send button. It posts one canned `[GPT_WINDOWS_HEARTBEAT]` status message, never a relay action.

**Score:** if this heartbeat actually reaches the GPT conversation, `pass_percent_if_received=100` when the command candidate was detected, otherwise `50` (UI delivery worked but detector missed). 100% is the **detection+delivery heartbeat gate only**, NOT full relay, assistant attribution, OS command execution or durability acceptance. If it is not received, no score upgrade is justified. UIA document visibility and composer clearing is only a provisional local acknowledgment.

If the composer contains a user draft, multiple app windows are open, no canary document is visible, or Send cannot be safely invoked, fail closed and report to CMD. A failed messaging path cannot magically report failure through itself: do not claim a GPT response if none appears. On ambiguous submission, do not resend. Never erase the user's draft.

Use CMD: 
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\p0pe0\Projects\Windows Relay\windows-relay\tools\Send-ChatGPT-DesktopHeartbeat.ps1"`

No backend HTTP, Firefox extension, pairing token, OS command execution, clipboard or screenshots are used.
