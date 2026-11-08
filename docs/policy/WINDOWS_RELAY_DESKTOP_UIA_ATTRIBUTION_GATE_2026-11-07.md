# ChatGPT desktop UIA transport: structural attribution gate

Preflight 1 (MSI Katana): actual ChatGPT process has 1371 UIA elements, 830 TextPattern elements, one Edit/composer.
Preflight 2 (MSI Katana): 781 elements; marker seen in 3 text patterns / 2 accessible names, one writable composer, one Send button; no explicit assistant role signals.

The next probe, `windows-relay/tools/Inspect-ChatGPT-MessageShape.ps1`, inspects the accessibility shape of matching text nodes (up to eight), including their control-type ancestor chain, bounded structural role hints, relative horizontal placement, and a finite allowlist of nearby action-button categories. All output is categorical; conversation content, user identifiers, credentials, arbitrary accessibility names, screenshots, and clipboard are excluded. No mouse, keyboard, or command execution takes place.

**Critical safety gate:** a marker's presence in TextPattern alone is insufficient to authorize command execution because it might appear in a user message or quoted assistant content. Do not wire this into the executable backend until assistant-only attribution is independently proven with positive/negative tests. Position, action buttons, and generic class names are clues, not authentication.

CLI (Windows CMD):
`git -C "C:\Users\p0pe0\Projects\Windows Relay" pull --ff-only origin wip/windows-relay-rebuilt-resynced-2047-101026`
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\p0pe0\Projects\Windows Relay\windows-relay\tools\Inspect-ChatGPT-MessageShape.ps1"`

Do not run the historical Firefox installer or start a browser transport for this desktop pivot. Code is read-only and not a working native app relay.
