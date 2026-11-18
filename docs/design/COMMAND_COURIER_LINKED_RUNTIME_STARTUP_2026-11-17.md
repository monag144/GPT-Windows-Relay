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
