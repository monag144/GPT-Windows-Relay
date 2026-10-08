# Archived source fragment 1/23 — 2026-10-08T0752Z

# Windows Relay Engineering Log — 2026-10-01

## Scope

This log records the Windows/Firefox ChatGPT relay hardening and recovery work performed on 2026-10-01. The active Windows relay workspace is:

`C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay`

The relay listens on `127.0.0.1:8766`, uses token authentication, and is intended to accept only assistant-authored `[GPT_WINDOWS_ACTION]` packets from the ChatGPT DOM via a Firefox extension.

## Relay protocol and parser status

The backend parser/execution path was brought to a stable state with support for:

- `command`
- `command_b64`
- `command_lines` JSON string arrays joined by newline
- shells: Windows PowerShell, pwsh, cmd, and native Python
- Python launched with `-X utf8 -c`
- approximately 20 KB decoded command ceiling
- protocol v1 compatibility
- strict envelope parsing
- output and timeout limits
- duplicate/replay protection
- process-tree termination
- CLIXML filtering

A native UTF-8 Python live proof succeeded with nested JSON and stdout/stderr. Thirteen parser regression tests were passing at that point.

## Assistant-only DOM trust boundary

The content script was constrained to assistant message containers only:

- `[data-content-search-unit-key$=":assistant"]`
- `[data-chatgpt-search-unit-key$=":assistant"]`

The scanner must never be broadened to `document.body.innerText`, because user-authored messages can contain relay packets and must not become executable input.

Composer selectors in use include:

- `[data-composer-markdown][contenteditable="true"][role="textbox"]`
- Ask ChatGPT fallbacks
- `#prompt-textarea`

## Major content-script failure discovered and repaired

A previous no-scroll patch accidentally left malformed JavaScript in `autoScrollChatGPT()`, including an orphaned `catch{}` and extra braces. That caused the entire content script to fail parsing even though the backend and extension background worker were healthy.

The repaired implementation replaced the scroll helper with a no-op:

```js
function autoScrollChatGPT(){
  return;
}
```

The live and persistent content-script copies were synchronized after repair and verified to contain no `scrollIntoView`, `window.scrollBy`, or `window.scrollTo` calls.

A subsequent end-to-end action succeeded, proving:

assistant packet -> DOM content script -> extension background -> localhost relay -> PowerShell execution -> feedback injection -> auto-send.

## Relay ARMED policy

The requested policy is explicit: after restart/recovery, the relay should come back ARMED.

Changes made:

- initial relay state defaults to armed
- startup sets armed state
- restart/recovery returns armed
- shutdown no longer forces a persisted disarm
- manual `/arm` remains available during a running process
- `/arm` transitions log origin and user-agent without logging the token
- extension 423 backoff exists
- content fetch abort/in-flight recovery exists
- service-worker fetch timeout is approximately 15 seconds

## Client disconnect crash handling

A browser-abort failure had caused a WinError 10053 while sending a response, followed by another exception when the server attempted to write an error response to the same dead socket.

The relay was hardened so response sending tolerates:

- BrokenPipeError
- ConnectionResetError
- ConnectionAbortedError
- OSError

The server now logs a client disconnect instead of cascading through another failed response.

## Supervision architecture

The desired model is:

1. visible PowerShell supervisor console running `run.ps1`
2. relay backend as a supervised Python child
3. hidden watchdog process
4. watchdog reopens a visible supervisor if the supervisor disappears
5. supervisor internally restarts a failed relay backend after a short delay

Singleton mutexes are used for both supervisor and watchdog.

The watchdog is registered at user startup under the HKCU Run key and remains hidden. The supervisor is launched with a visible window.

### Verified process chain

A controlled failover test initially appeared to fail because the verification request landed during the recovery window. Logs later showed watchdog detection followed by supervisor launch and server startup.

Recovered steady state was verified with:

- one relay listener
- one supervisor
- one watchdog
- relay ARMED
- visible supervisor window titled `GPT Windows Relay`

The actual process ancestry was then traced:

```text
listener python.exe
  -> venv python.exe launcher
    -> visible run.ps1 PowerShell supervisor
      -> hidden watchdog parent
```

The supervisor was therefore confirmed as an ancestor of the socket-owning relay process.

## Firefox HUD attempt and rollback

A top-right diagnostic HUD was attempted after supervision became stable.

The first HUD implementation was appended directly into `content.js`. This was the wrong isolation boundary. The appended code later proved syntactically broken, including malformed `return` tokens, so a HUD syntax error could kill the entire relay content script.

A second HUD version was moved toward a separate `hud.js` content script with a Shadow DOM, but this also introduced another page-wide MutationObserver and contributed to concern about page performance.

The current direction is:

- remove/disable HUD code from the active relay path
- restore the core content script first
- do not couple HUD syntax/runtime health to packet ingestion
- if the HUD returns, keep it independently loaded and timer-driven rather than adding another whole-page mutation scanner

## Current browser-side performance problem

The backend can run, but browser-side packet ingestion has become unreliable and the ChatGPT page performance has degraded.

The likely hot path is the core content scanner:

- it watches a very large, actively streaming ChatGPT conversation
- mutation activity can be extremely high
- the scanner can repeatedly query assistant message containers across the conversation history
- repeated full-history rescans during token streaming are expensive

The next redesign should be incremental rather than full-history:

- inspect only new or changed assistant nodes
- debounce/coalesce mutation storms
- retain strict assistant-only trust boundaries
- execute a completed packet exactly once
- keep a slower fallback poll only for missed mutation events
- avoid all automatic scrolling
- keep HUD work independent of packet ingestion

## Current operational caveat

During the latest browser-side failure, the relay backend had to be bootstrapped manually from PowerShell because action packets could not be trusted to reach the backend while the content script was broken.

Manual bootstrap command used:

```powershell
$root='C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay'; Remove-Item "$root\.relay-paused" -Force -ErrorAction SilentlyContinue; & "$root\.venv\Scripts\python.exe" "$root\windows_relay.py" server
```

When the browser bridge is unhealthy, diagnostics and repairs must not be attempted through `[GPT_WINDOWS_ACTION]`; use direct PowerShell or file inspection first.

## Security incident discovered during relay hardening

A separate persistence audit found unwanted 360/Qihoo-related software and a scheduled persistence mechanism.

Key findings included:

- scheduled task `executor_stack_win32_lts`
- startup shortcut targeting the same payload
- `XServer.exe` identified as 360 Total Security-related and holding the payload
- live external connection observed from that process
- task disabled
- startup shortcut moved into evidence
- process terminated
- evidence preserved under the relay workspace

This incident is separate from the relay architecture but was discovered while investigating unexplained system/resource behavior.

## Working rules going forward

- Keep the visible-header -> bare fenced `[GPT_WINDOWS_ACTION]` -> visible-footer sandwich format for relay commands.
- Every relay command should emit: `Reply to this with the sandwich technique`.
- Never intentionally add a language tag or metadata to the relay fence.
- Never broaden packet scanning to user-authored DOM.
- Never patch scrolling behavior into the relay scanner.
- Do not make the HUD part of the core packet-ingestion failure domain.
- When the browser bridge is broken, repair it from direct PowerShell rather than through the relay.
- Keep live and persistent extension copies synchronized after each known-good browser-side change.

## Next engineering steps

1. Restore and verify a minimal known-good `content.js` with no HUD.
2. Confirm reliable packet pickup with several small consecutive actions.
3. Replace whole-history mutation rescanning with a debounced incremental scanner.
