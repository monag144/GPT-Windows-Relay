# PCE12.007–.008 New Chat verification failures — 2026-10-09T0756Z

## Observations
- PCE12.007 `COMMAND_FAILED`: native click at (110,139) was dispatched, but Firefox window title `Click New Chat — Mozilla Firefox` did not change within 7 seconds. The script refused to send the greeting. No proof that navigation failed: unchanged window title is not authoritative for a single-page application.
- PCE12.008 `COMMAND_FAILED`: UI Automation identified one Firefox window, but its document search returned `FRESH_BEFORE=False` and `NEW_CHAT_MATCHES=0`; aborted with `ABORT_NEW_CHAT_NOT_UNIQUE`. No greeting sent.
- Both action IDs are consumed and must not be repeated. The next emitted packet is `PCE12.009`, even if these attempts did not complete the intended side effect.

## Evidence-backed correction
Canonical `windows-relay/firefox_tab_adapter.ps1` already uses Firefox UI Automation `AutomationId='urlbar-input'` with `ValuePattern.Current.Value` for **exact URL readback**, and a visible `Edit` named `Ask ChatGPT` whose `ClassName='ProseMirror'` to identify the composer. This is stronger navigation evidence than browser window title or an inaccessible `Where should we begin?` heading. The direct coordinate click proved successful in PCE12.006, but coordinates depend on current UI screenshot.

PCE12.009: read exact URL first; if it is already `https://chatgpt.com/`, do **not** click New chat again. Otherwise invoke a guarded single click using current screenshot geometry and verify URL becomes the new-chat page before typing. For submission, require exactly one visible enabled semantic composer, focus it, enter greeting exactly once, read back draft and send only on verified draft. No clipboard mutation if avoidable.

## Safety
Do not infer message delivery from keyboard dispatch. If URL or composer identity cannot be established, abort without sending. No Windows source mutations, GitHub Actions, or Termux operations are needed. Before PCE12.010, audit PCE12.005–.009 directly in GitHub.
