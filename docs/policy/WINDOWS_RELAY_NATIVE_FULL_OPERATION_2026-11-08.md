# GPT Windows Native Desktop Relay — independent full-operation path
Updated 2026-11-08. Active development branch remains
`wip/windows-relay-rebuilt-resynced-2047-101026`. Do not create a second branch,
fetch/write Termux, or overwrite the legacy Firefox pipeline.

## What the Director authorized

A continuously running, persistently armed native ChatGPT Windows app relay that
executes general CMD, Python, PowerShell and pwsh actions (plain commands,
command_lines, UTF-8 command_b64). The user explicitly accepts unattended operation.
The native path must not depend on Firefox, the browser extension or its 8766 backend.

## Entry points (all through Windows CMD)

Existing command name now delegates to the native build:

`"C:\Users\p0pe0\Projects\Windows Relay\windows-relay\START-CHATGPT-DESKTOP-RELAY.cmd"`

Equivalent explicit native launcher:

`"C:\Users\p0pe0\Projects\Windows Relay\windows-relay\START-CHATGPT-DESKTOP-NATIVE.cmd"`

Controls:

`"C:\Users\p0pe0\Projects\Windows Relay\windows-relay\DESKTOP-NATIVE-CONTROL.cmd" status`

`"C:\Users\p0pe0\Projects\Windows Relay\windows-relay\DESKTOP-NATIVE-CONTROL.cmd" stop`

`"C:\Users\p0pe0\Projects\Windows Relay\windows-relay\DESKTOP-NATIVE-CONTROL.cmd" arm`

`"C:\Users\p0pe0\Projects\Windows Relay\windows-relay\DESKTOP-NATIVE-CONTROL.cmd" off`

The native app now uses the **original top-right `hud.py`**, retaining the exact
START / STOP / RESTART / OFF / KILL control surface and layout. The obsolete
separate mini-HUD was removed. The original HUD switches its status and control
actions to the independent native runtime when the native launcher selects it.
Browser relay state remains separate and is not armed or modified by this HUD.

## Processing

1. The UIA scanner reads the running ChatGPT *Windows app* only.
   `-EmitPackets` emits locally base64-encoded complete frames; ordinary diagnostic
   scans remain redacted.
2. `desktop_native_relay.py` is one process per user session (Windows file lock).
   The first scan establishes a baseline so historical visible packets do not
   execute after first launch.
3. Newly detected complete packets are parsed by `windows_relay.extract`, with
   strict packet ID, shell, timeout, cwd and command-source validation.
4. Commands run using the existing Windows shell argv logic, in independent native
   state `%LOCALAPPDATA%\GPTWindowsRelayDesktop`. Reserved action IDs are durable
   before process launch. Duplicate IDs are not executed twice; STOP kills a live
   process tree and remains persisted.
5. Results are saved to the native results/outbound journal, then delivered
   through the native ChatGPT composer using the guarded UIA sender. Each result
   has a unique receipt marker. The durable outbound phase is READY, SUBMITTING,
   PRE_SUBMIT_FAILED, SUBMITTED or SUBMIT_UNCERTAIN. Never automatically retry a
   possibly-submitted result.
6. Fresh installations start ARM=TRUE because the user explicitly requested
   persistent arming. A subsequent STOP/OFF is preserved; a new start does not
   secretly override it. No scheduler/autostart-at-login is installed.

## Explicit trust boundary

Windows UI Automation can read packets, but is not yet a cryptographic proof that
a packet originated in an assistant response. **This build trusts complete packets
visible in the ChatGPT Windows app when native ARM=TRUE.** That means a user
message, quoted block, or malicious content that renders a valid action frame
could be executed. This is a deliberate operator-authorized high-trust mode,
not a claim of assistant-origin verification. Keep the native HUD STOP available.

## Verification

Run the repository sweep, then start the native launcher *with the current chat
open*. Send a **new** harmless assistant action with a fresh ID **after**
`NATIVE_BASELINE_COMMANDS_SUPPRESSED` is reported; already-visible commands are
intentionally ignored at startup.

Expected console stages: NATIVE_ACTION_EXECUTE, NATIVE_ACTION_RESULT,
NATIVE_DELIVERY_ATTEMPT, NATIVE_DELIVERY_PHASE. A received
`[GPT_WINDOWS_RESULT]` in the ChatGPT conversation confirms end-to-end result delivery.

This source has not been verified on the MSI Katana until the user reports
native results. Do not claim full readiness from static checks alone.
