# MSI Katana desktop: V3 guarded Send click + original HUD recovery

V2 observed: `[GPT_WINDOWS_HEARTBEAT]` text was inserted into the native ChatGPT app composer but not automatically submitted. It was posted manually by the operator. Treat that as **composer injection proven, automatic delivery not proven**.

V3 uses the same Windows Relay source tree, existing listener at `127.0.0.1:8766`, original `START-GPT-WINDOWS-RELAY.bat`, HUD and STOP/OFF/KILL controls. Native desktop monitor remains command-execution DISABLED, because UIA text alone is not assistant authorship authentication.

V3 sender uses a single actual UIA Send-button **mouse click** through user32 after verifying process, foreground, button enabled, bounds inside ChatGPT, unchanged heartbeat draft, conversation anchor and operator STOP latch. It does not invoke the unreliable UIA button pattern or send Enter, and never automatically retries after a possibly issued click. Pointer position is restored. In case of submission uncertainty, report it; do not resend the message.

V3 monitor uses a new status-only journal `desktop-heartbeat-ledger-v3.json` to preserve earlier attempt records. Diagnostic lines expose only detection status, heartbeat ID, send phase, safe error names and delivery status, not chat content or tokens.

Original HUD may be missing when a previously running backend causes the launcher to bypass the old START batch. The launcher now reconciles the original `relay-watchdog-loop.ps1` and checks for its `hud.py` process, with one direct canonical HUD launch fallback if needed. A saved HUD position on a disconnected display is rehomed on launch.

**CMD acceptance:** first stop old desktop monitor Ctrl+C, then pull, run `python -B "C:\Users\p0pe0\Projects\Windows Relay\windows-relay\tools\relay_project_test_sweep.py"`, and start `"C:\Users\p0pe0\Projects\Windows Relay\windows-relay\START-CHATGPT-DESKTOP-RELAY.cmd"`. Keep the main ChatGPT app conversation open with empty composer. A new `PCE18-KATANA-HEARTBEAT-V3-*` should appear as a newly submitted message only if the physical click succeeds.

Check for `DESKTOP_SENDER_UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN`, `DESKTOP_SENDER_UIA_GUARDED_SEND_BUTTON_CLICK_COMPLETED` and `DESKTOP_SENDER_DELIVERY=...` plus `CANONICAL_HUD=RUNNING`. If the UI does not show a sent message, do not manually assume a 100% end-to-end pass. Read the diagnostic and investigate before the next attempt.

The Termux Relay source was referenced read-only earlier; this change makes no edits to that repository.
