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


## ARM / GO — original top-right HUD (2026-11-19)

The **existing** leftmost START control remains the same handler. In native mode
it displays **ARM** when disarmed/OFF and **ARMED** (disabled green confirmation)
when armed. Pressing ARM calls the native `arm` control; it does not deliver,
retry, or create a command packet. Browser mode retains its original START.

A prominent green **GO** button is at the far right of the original compact
HUD footer; the smaller Auto Send control remains immediately to its left.
The original 560 × 184 (expanded 560 × 386) geometry, top-right placement,
START/STOP/RESTART/OFF/KILL lifecycle handlers, Settings gear, sign-in checkbox,
and recovery controls remain on the same existing HUD.

GO invokes `command_courier.py go` on a worker thread. This uses the selected
runtime profile, **does not call the HUD reconciler** (which would kill/restart
the already-running HUD), and reuses the existing native singleton when the
selected transport is `native-desktop`. It refuses `disabled`/unimplemented
profiles, OFF, and disarmed states with an explicit message. ARM first after
an intentional OFF/STOP. GO is an activation/attachment control: it does not
create or submit a packet, force resend, abort, clear the queue, or change the
selected destination. Automatic send remains controlled separately.

**Future destinations:** Command Courier is intended to courier packets to
selectable recipients, not to hardcode ChatGPT as a permanent product limitation.
At this checkpoint only the native ChatGPT Windows app destination is
implemented in the runtime profile. Add other destination adapters explicitly
with their own dispatch, receipt/acknowledgement and deduplication contracts;
do not claim that arbitrary endpoints are currently operational.

**Separate existing client:** `consumer/GO.bat` is the historical one-click
browser-based GUI with its own browser setup and mission submission path.
It remains available independently and **is not launched by this native HUD
button**: launching it here would activate a different transport and could
create competing owners/sessions. No consumer client source was modified.

**Validation gates:** source and regression tests on the branch; Windows
user must run the repository sweep, open the HUD from the canonical launcher,
verify native ARM/ARMED state, GO status, retention of Auto Send and the
sign-in controls, and ensure no second HUD/consumer/backend appears.
That check does not certify delivery to an arbitrary external destination.
