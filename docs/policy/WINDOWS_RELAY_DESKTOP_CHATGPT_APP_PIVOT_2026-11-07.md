# Windows Relay — ChatGPT desktop app transport pivot (2026-11-07)

## Director instruction

The MSI Katana installation target is `C:\Users\p0pe0\Projects\Windows Relay`. The proposed Firefox persistent extension installation is **cancelled for this machine**. Do not run the previous `install.ps1` / `START-GPT-WINDOWS-RELAY.bat` / Firefox temporary-add-on onboarding sequence as if it implements the native app path. Existing files are not deleted or modified by this direction; previously installed state, if any, requires inspection first.

## Target

Replicate the Android GPT-Termux relay architecture: accessibility tree detects the newest complete `[GPT_WINDOWS_ACTION]` fenced assistant-message packet in the **ChatGPT Windows desktop app**, authenticated localhost executor runs a bounded action, and an automated UI control returns `[GPT_WINDOWS_RESULT]` to the same ChatGPT conversation. Windows UI Automation is the primary text capture method, scoped to the native ChatGPT app window and an assistant message; Windows OCR is only a fallback when accessibility text is unavailable. Screen text alone is not a trust boundary: separate assistant attribution, complete-frame validation, unique IDs, operator START/STOP, pairing, timeout, and duplicate protections remain compulsory. Never execute packets from other apps, user text, a draft, or a partially rendered frame.

Prefer plain Python for complex orchestration; `command_b64` is an optional UTF-8 transport preservation mechanism, not an authentication or security feature. Existing `windows-relay/windows_relay.py` may be retained as backend; any desktop integration must not be confused with the old Firefox extension or assume it is available.

## First acceptance gate

`windows-relay/tools/Inspect-ChatGPT-DesktopAccessibility.ps1` is a **read-only preflight**, not an implementation. Run it from CMD via `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...` with ChatGPT's main window open. It enumerates matching application windows, control types, and availability of UIA TextPattern/compose candidates, printing NO conversation text, screenshots, clipboard content, pairing secrets, or commands. On-device native UIA text extraction and result composer controls must be proven before designing executable dispatch. Do not silently install/activate browser-based components.

Current code and installer are still the old browser transport; this document is an architectural direction, not a claim the desktop relay is built or installed.
