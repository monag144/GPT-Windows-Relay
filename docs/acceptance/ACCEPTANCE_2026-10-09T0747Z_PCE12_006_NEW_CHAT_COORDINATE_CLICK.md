# PCE12.006 — Verified New Chat navigation, 2026-10-09T0747Z

## Outcome and evidence
**User-confirmed success**, supported by two screenshots supplied in the PCE12 conversation:
1. Firefox at `chatgpt.com` on the empty **Where should we begin?** screen, with **New chat** in the left sidebar.
2. The user then returned to their PCE12 conversation (`chatgpt.com/c/6ac88ea9-3d7c-83e8-9784-f3794c920263`) and confirmed: "Congratulations, we did the thing. We are now back at PCE12 chat."

The Firefox relay HUD showed `WAITING` / `WAITING FOR GPT TURN END` while this navigation and result handoff were happening; these status labels by themselves are **not** proof of successful execution. The screenshots + explicit user acknowledgement establish that a fresh chat was opened at least once. No `PCE12.006` full backend stdout receipt is available in this conversation, so exact output lines remain unverified.

## Technique that worked

A **single native Windows mouse click**, using the existing Windows Relay with `shell: "python"`, and no UIA/PowerShell workaround. The packet ID was `PCE12.006-one-shot-firefox-new-chat-click`. The command:

1. `ctypes.WinDLL("user32", use_last_error=True)` and `u.SetProcessDPIAware()`.
2. Check `GetSystemMetrics(0/1)` matches the observed 1366×768 desktop; **abort** on mismatch.
3. Use `WindowFromPoint(POINT(110,165))`, `GetAncestor(hwnd,2)` and `GetClassNameW` to require `MozillaWindowClass`; **abort** if not Firefox.
4. `SetCursorPos(110,165)`, wait approximately 200 ms and verify `GetCursorPos` equals the requested coordinates; **abort** on mismatch.
5. Emit **one** mouse left-button down/up via `mouse_event(0x0002,...)` / `mouse_event(0x0004,...)`, separated by approximately 120 ms.
6. Print command ID, display, cursor, target class and click dispatch evidence; finish stdout with `Reply to this with the sandwich technique`.

**Important limitation:** The target is NOT a universal fixed coordinate. Sidebar scrolling/layout moved the control from around Y=139 to Y=165 across screenshots. Every subsequent operation must resolve the button again from current UI or use semantic UIA. A Firefox-class match proves window ownership, not the element identity. Never click blindly with an old coordinate.

## Rendering and operation rules
- Relay sandwich: visible prose header, **one bare fenced** `[GPT_WINDOWS_ACTION]` JSON payload, closing marker, visible prose footer.
- `result_mode: "compact"`; stdout final line `Reply to this with the sandwich technique`.
- **Each emitted action consumes an operation ordinal even when rejected, timed out or governance-blocked.** The old repeated PCE12.005 packets are incidents; after .006 use **PCE12.007**. See `consumer/control_harness.py::assess_next_engineering_operation`.
- Before any new side effect inspect existing evidence. Navigation may interrupt exact-result delivery; user confirmation and screenshot are valid evidence for achieved navigation.
- Source and audit work belongs in `monag144/GPT-Windows-Relay`, not Termux. Use the GitHub connector directly, without GitHub Actions credits.

## Next acceptance
PCE12.007 should open a new chat and submit one short introduction about the GPT Windows Relay. Confirm the greeting appears in the **new** conversation; successful click alone does not prove message submission. If only draft entry is proven, distinguish it from sending. Do not replay PCE12.007 if its outcome is uncertain.
