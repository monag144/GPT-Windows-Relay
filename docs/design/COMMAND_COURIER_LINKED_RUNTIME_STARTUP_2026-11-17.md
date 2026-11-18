# Command Courier — linked launcher, replaceable runtime

Command Courier is the user-facing name for the runtime coordinator. The
existing Windows relay engine and **original upper-right HUD** remain separate
modules. The currently implemented transport is ChatGPT's native Windows
desktop app; arbitrary destination apps are not implemented yet.

From CMD in the repository root:

```bat
call "windows-relay\COMMAND-COURIER.cmd" profile native-desktop
call "windows-relay\COMMAND-COURIER.cmd" start
call "windows-relay\COMMAND-COURIER.cmd" status
call "windows-relay\COMMAND-COURIER.cmd" startup install
call "windows-relay\COMMAND-COURIER.cmd" startup status
```

**Windows startup means interactive user sign-in, not pre-login system boot.**
The `startup install` command is explicitly opt-in, requires no elevation, and
creates one current-user shortcut called `Command Courier.lnk`. It points to
the repository's current launcher and reads the **current** runtime profile at
each sign-in. No Windows service, scheduled task, copied source tree, or fixed
binary is installed. Startup registration does **not** run the tool immediately.

To disable startup without deleting the owned shortcut:

```bat
call "windows-relay\COMMAND-COURIER.cmd" profile disabled
```

To remove startup registration entirely:

```bat
call "windows-relay\COMMAND-COURIER.cmd" startup remove
```

Changing profile affects the **next launcher invocation**, not already-running
processes. Existing `STOP` and `OFF` engine policy remains in force. Native
mode starts/reuses the existing singleton engine then reconciles exactly the
existing `hud.py` window. It does not arm an OFF engine, replay commands, clear
delivery holds, or touch the browser relay.

If a profile has not yet been selected, the launcher reads the previously
selected native `hud-mode.json`; without that selection it defaults to
`disabled` rather than starting an unexpected engine. Browser/other transports
can be added as separate adapters; they are not silently enabled now.

The existing `START-CHATGPT-DESKTOP-NATIVE.cmd`, `DESKTOP-NATIVE-CONTROL.cmd`,
`desktop_native_relay.py`, and `hud.py` remain compatible and independently
editable. The original HUD controls continue to work exactly as before.

**Acceptance:** run the new coordinator test and existing full sweep before
installing the sign-in shortcut. Live end-to-end message delivery is a separate
acceptance gate. An old `PRE_SUBMIT_FAILED` result remains held.

## HUD controls (2026-11-17)

The existing original top-right `hud.py` now contains a compact
**Start with Windows** checkbox. Checking it explicitly installs the owned
current-user sign-in shortcut **and** selects the implemented `native-desktop`
runtime; unchecking it removes the owned shortcut only. These operations run
on a worker thread and the checkbox reflects the **verified** shortcut and
profile state, not a speculative local setting. If an existing shortcut with
the same name points elsewhere, the manager refuses to replace it and the
gear settings display an error.

The **⚙** button opens a settings panel *inside the original HUD* using its
existing expanded geometry. It provides the same startup checkbox, the actual
startup status, and a selector for the **next-launch** runtime:
`native-desktop` or `disabled`. The browser backend and the five original
control buttons are unchanged. No duplicate HUD or extra top-level window is
created.

The native engine starts at user sign-in independently of when the ChatGPT
desktop app appears. Until a ChatGPT UI Automation document is detected, the
engine displays `WAITING_FOR_CHATGPT_APP` while keeping its singleton lock.
Once the document exists it suppresses already-visible packets as its
baseline before processing any newly visible command. A missing app must
**never** count as an empty baseline. This is an admission precaution, not
proof of assistant authorship; the current native transport still depends on
explicit operator trust in the visible desktop content.

**The checkbox does not start the engine immediately.** It controls future
interactive Windows sign-in launches. STOP and OFF remain authoritative.
Disabling the runtime while the shortcut exists makes subsequent sign-in
startup inert without deleting the shortcut. Actual command-result delivery
remains a separate live acceptance gate.
