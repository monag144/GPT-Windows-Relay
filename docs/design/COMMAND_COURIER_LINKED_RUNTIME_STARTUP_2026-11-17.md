# Command Courier — linked launcher, replaceable runtime

Command Courier is the user-facing name for the runtime coordinator. The
existing Windows relay engine and **original upper-right HUD** remain separate
modules. The original native ChatGPT transport remains available. An
additional opt-in directory-source text forwarder supports file and HTTP
destinations without a ChatGPT composer. Other app/API source adapters
remain future work; see docs/guides/COMMAND_COURIER_TEXT_FORWARDING.md.

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

**Destination evolution:** Command Courier is intended to courier text to
selectable recipients, not to hardcode ChatGPT as a permanent product limitation.
The existing HUD native mode sends to ChatGPT Windows UI. A later opt-in
file-source route now supports directory or HTTP output independent of UIA.
Additional source and destination adapters still need explicit dispatch,
receipt/acknowledgement and deduplication contracts.

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


## PC Engineer 19 — efficiency and correctness pass (2026-11-21)

- **GO readiness:** green GO success is only reported after the native
  singleton is running, ARM/OFF policy remains valid, and the scanner has
  established a valid receiver state (BASELINED, IDLE, EXECUTING, DELIVERING).
  WAITING_FOR_CHATGPT_APP / BASELINING reports a distinct waiting state.
  ERROR, DELIVERY_BLOCKED, DELIVERY_UNCERTAIN and runtime errors refuse GO
  readiness rather than promising success from a process lock alone. This is
  *not* a remote acknowledgement or packet delivery receipt.
- **Original HUD startup:** `Reconcile-OriginalDesktopHUD.ps1` checks the
  visible original HUD's process start time against `hud.py` source mtime.
  It reuses a current visible HUD; after a Git pull changes source, it
  restarts only the canonical HUD once. The first visible-window check now
  polls for up to about 3 seconds to absorb Windows sign-in GUI timing.
  It neither touches the historical mini HUD elsewhere nor runs browser
  backends or packet commands.
- **GUI responsiveness:** unchanged details are no longer deleted and
  reinserted every second, preserving an operator's selection; GO is
  disabled when OFF or disarmed and reports waiting appropriately. The
  native Force Resend button is enabled only for a PRE_SUBMIT_FAILED result,
  and Abort Send only for READY or PRE_SUBMIT_FAILED records.
- **Automation constraint:** the `native-desktop-ci.yml` workflow now has
  a full Windows Relay/Consumer sweep, but automatic push triggering was
  disabled after GitHub created jobs without allocating a runner (zero
  steps and failure in ~2 s). The workflow remains manual-dispatch only.
  No failed GitHub Actions check should be treated as a code-test failure;
  run the full sweep locally on Katana and inspect GitHub Actions settings
  separately. Do not claim the new source passes Windows tests until
  Katana reports the post-change sweep.
- **Further risk to resolve:** standalone abort/clear CLI opens a separate
  `State` while the runner also retains a live `State` instance.
  Concurrency and durable queue ownership need a dedicated design/test
  before promising reliable simultaneous operator recovery.


## PC Engineer 19 — FORCE CLEAR restoration (2026-11-21 local)

The original HUD's upper-right recovery area again has a **FORCE CLEAR**
button in the historical first-row, first-column slot. Its action now matches
its name: after a destructive-action confirmation, it focuses and clears the
**current ChatGPT Windows composer only**, verifying the unique ChatGPT window,
conversation document, writable editor, and empty editor afterward. It reports
`COMPOSER_CLEARED_NO_SEND` or a specific error. Clearing is disabled while the
native runner is actively `DELIVERING`. The PowerShell sender now offers
`-ClearComposerOnly` as a separate, incompatible-with-send/probe mode, and
does not run a sender, input a packet, update a delivery journal, release a
delivery hold, or click Send.

The distinct **ABORT SEND** control is retained on the second row next to
**FORCE RESEND**. They have different meanings:
- FORCE CLEAR: clear **only** an unsent ChatGPT editor draft (destructive;
  explicit confirmation; no packet delivery).
- ABORT SEND: mark the selected unsent outbound delivery aborted; keep
  execution result (requires its own confirmation).
- FORCE RESEND: explicit recovery of an eligible previously saved result,
  with duplicate risk, not a command execution.
- CLEAR QUEUE: destructive pending-delivery cleanup with separate confirmation.

The new `FORCE CLEAR` action does **not** resolve or automatically retry
`PCE19-NATIVE-E2E-20261122-001`. The previous Katana acceptance for sender
`2338aab` is 541 Windows tests + 123 Consumer tests, **664/664 PASS**; native
composer probe returned `PROBE_VALUE_CLASS=PLACEHOLDER_CANDIDATE`,
`PROBE_TEXT_CLASS=PLACEHOLDER_CANDIDATE`, both length 12, disabled Send=1,
enabled Send=0, `PROBE_EMPTY_VERIFIED=True`, but the result remains held
`EXECUTION=OK, DELIVERY=PRE_SUBMIT_FAILED, ATTEMPTS=2, HELD=True`.
These receipts are *before* FORCE CLEAR restoration. New changes still require
Katana full test sweep, PowerShell parse gate and a deliberate editor-only
manual test; no live clearing or delivery was performed here.

## Director's transport-neutral forwarding contract (2026-11-21)

**Product identity:** Command Courier is a general-purpose relay, not a
ChatGPT-only automation tool. Its fundamental job is to capture the body of
output/text from an **operator-selected input** (for example, executed code,
another application's output, an API-connected client or a chat UI), and
automatically forward that body to the **operator-selected destination**.
The source and receiver can independently be ChatGPT, another application,
an authenticated API, or another explicit adapter. This is the intended
architecture, **not a claim that all those adapters exist today**.

Keep these boundaries separate:

1. **Input adapter:** listen to the chosen and authorized source, capture the
   selected text/result verbatim with its source identity and a unique
   delivery identity. Detection is not inherently a request to execute.
   The existing `[GPT_WINDOWS_ACTION]` parser is one *optional* command
   adapter, not the universal format required for arbitrary forwarding.
2. **Execution adapter (optional):** if the input was explicitly admitted as
   an authorized command, execute once and capture stdout, stderr and exit
   status. Otherwise forward input text without executing it. Output/error
   status must not be silently discarded or changed to `OK`.
3. **Courier/outbox:** persist the actual body and delivery status, preserve
   ordering where required, and route to configured sink(s). A failure for
   one sink must hold *that delivery*, not globally stop ingestion, execution
   or unrelated sinks. Do not re-run the originating command to retry a
   delivery.
4. **Destination adapter:** send via its appropriate API, IPC, local app
   integration, or, for the current ChatGPT Windows UI adapter, accessible
   editor. Only a destination that actually uses a composer needs a
   composer-empty/focus check. **No general preflight requirement to clear
   ChatGPT's composer before Command Courier can ingest or forward data.**
5. **Receipts:** track source capture, optional command execution, outbound
   submission and receiver acknowledgement independently. Retry based on
   per-destination confirmation/idempotency, not the mere appearance of an
   action ID in source text or in an unsent draft.

**Automatic forwarding** is the desired normal behavior when the configured
source/destination adapters are armed. The current GO button is a runtime
activation control, not itself a packet send. STOP/OFF/KILL remain applicable.

**Operator-safety boundary:** configurable source and target ownership,
permission and opt-in, size/encoding limits, cycle/loop prevention, preserved
unsent text, and duplicate-send protections remain necessary. Those
protections must be **adapter-specific** and must not masquerade as a global
ChatGPT-only dependency. In particular, blindly collecting *all* on-screen
text could forward passwords, messages or unrelated app content; do not
implement such indiscriminate monitoring without explicit scope.

**Implemented first non-UI transport (later revision):**
`courier_forwarder.py` now watches an explicitly selected UTF-8 text
directory and forwards exact bodies to a selected file directory or HTTP
endpoint, with an independent journal, per-route holds, and no dependence
on the ChatGPT composer. `desktop_native_relay.py` runs the router before
the ChatGPT scanner; `command_courier.py route set/status/enable/disable`
manages its configuration. The historical UIA command scanner, native
result sender and HUD remain supported. Further app/API **input** adapters
and Windows live acceptance are outstanding. Do not remove the ChatGPT
editor guard from its own destination adapter prematurely.

**Design correction:** The earlier instruction to FORCE CLEAR the ChatGPT
composer *before testing any new command* was overly broad. A busy composer
can block the **ChatGPT UI destination's send attempt**, but cannot logically
be a prerequisite for Command Courier's general detection, execution, or
API/non-UI forwarding. Keep the failed ChatGPT delivery held and test an
independent destination separately when its adapter exists.
