# Command Courier — independent text-body forwarding

## Default auto-detect foreground delivery — new native egress (Windows acceptance pending)

**No configured input source is required.** Command Courier's existing native
execution journal already owns each new command's result body. With the
original HUD **ARMED** and **Auto Send: ON**, the runner checks the foreground
interactive Windows application's focused text entry field and forwards the
oldest claimable saved result there, whether the target is ChatGPT, Notepad
or another eligible app.

The focused destination control is discovered through UI Automation; the
relay does not need a configured input folder, a copied clipboard, or an
explicit application-name allowlist. It will not overwrite the editor's
existing text. When an eligible field is absent, the saved result remains
`READY` with `AWAITING_TEXT_FIELD` and no delivery-attempt inflation;
focusing a suitable editor lets automatic delivery continue. The ChatGPT
source scanner may still be used to issue EXEC packets, but **it is no longer
a prerequisite for delivery of an already queued result**.

**Result status meanings:**

- `TEXT_INSERTED` — the recipient editor contains the saved result.
  This is the correct outcome for Notepad and other non-messaging editors.
- `SUBMITTED` — an accessible, unique Send/Submit control was used and
  the result receipt was verified in the application's conversation view.
- `SUBMIT_UNCERTAIN` — the editor changed, an input was partial, or a
  Send click occurred without reliable confirmation. The runner does not
  blindly resend a possibly duplicated result.
- `READY` / `AWAITING_TEXT_FIELD` — no eligible focused field; nothing
  was typed and the result remains queued.

**Notepad live acceptance procedure:** After a clean pull and passing full
tests, restart the native runner to load the new sender, then use a **fresh,
harmless native EXEC packet** from the existing ChatGPT instruction source.
Once the command has executed and created its saved result, focus a blank
Notepad editor and keep it in the foreground. The relay should insert the
framed output automatically without Ctrl+C or an input folder. Confirm a
matching `TEXT_INSERTED` phase and preserved native result. Do not interpret
the unrelated TEST FIRE or SEND COPIED TEXT buttons as qualifying this
new foreground destination: they still test the **optional** file route.

Native terminal panes and password fields are excluded, and generic
delivery never presses a blind Enter key: it could run terminal commands
or prematurely submit a chat draft. Plain Edit/chat controls receive a
newline-flattened framed packet so Enter-like control characters do not
submit partial data; rich Document editors can preserve their line breaks.
A chat application with an inaccessible/unnamed Send control may support
`TEXT_INSERTED` but not confirmed `SUBMITTED` until an adapter is added.

**Restart after the pull:** The existing `COMMAND-COURIER.cmd start`
reuses an already-running native runner; it does **not** reload changed
Python code. Run `python -B "windows-relay\desktop_native_relay.py" restart`
after the test suite passes, then run `COMMAND-COURIER.cmd start` to
reconcile the original HUD. The restart preserves persistent ARM,
Auto Send, native results and historical delivery holds.

---

Status: explicit opt-in. Existing native ChatGPT UI sender, HUD, and packet
execution remain unchanged unless a text route is configured.

## Purpose

The relay is a courier for a **captured body of text**, not a mandatory
ChatGPT message sender. A source that can write a UTF-8 text file is a valid
producer; a selected folder or HTTP endpoint is a valid destination. The
body is forwarded exactly, including newline characters, without requiring
ChatGPT's window, composer, or Send button. No text in an input file is
executed as code.

The transport-independent route runs inside the **existing native singleton**
on every scanner iteration, *before* ChatGPT's read-only command scanner.
ChatGPT being closed, a ChatGPT draft, or a prior ChatGPT delivery hold cannot
block the other route. An HTTP error places only that route's delivery in its
own HELD ledger: it does not globally STOP/OFF the engine.

## Configure the first route (CMD from repository root)

Create an input and output directory under operator-owned paths, then run:

    mkdir "C:\CourierInput"
    mkdir "C:\CourierOutput"
    call "windows-relay\COMMAND-COURIER.cmd" route set --id my-app --source "C:\CourierInput" --to-dir "C:\CourierOutput"
    call "windows-relay\COMMAND-COURIER.cmd" route status
    call "windows-relay\COMMAND-COURIER.cmd" start

The existing HUD must have **ARMED** and **Auto Send: ON**. Afterward, any
new UTF-8 .txt file the operator or a connected app places in the selected
input directory will be written to the output directory as
"<route-id>-<sha256>.txt" with its original bytes. Files already present
when the operator configures a route are **baselined, not forwarded**, so
enabling a new destination cannot replay historical results. A subsequent
change to the filename or content creates a new delivery identity. Do not
use the input directory as the output directory; recursive routes are
explicitly rejected. Producers should write to a temporary name and rename
atomically to .txt.

### Forward native command result bodies to a folder

Native execution already records text results under:

    %LOCALAPPDATA%\GPTWindowsRelayDesktop\outbound

Configure that directory as the source and an explicit other directory as
the target. These result files are written independently of the ChatGPT
composer and contain the saved framed result, including command status.

    call "windows-relay\COMMAND-COURIER.cmd" route set --id native-result --source "%LOCALAPPDATA%\GPTWindowsRelayDesktop\outbound" --to-dir "C:\CourierOutput"

No ChatGPT composer clearing is needed for this file route.

### Forward to an API

Use an actual operator-controlled HTTP endpoint (not the example address):

    call "windows-relay\COMMAND-COURIER.cmd" route set --id api-result --source "C:\CourierInput" --to-http "https://YOUR_ENDPOINT_HERE.example/ingest" --bearer-token-env COURIER_API_TOKEN

Set the COURIER_API_TOKEN environment variable in the **runner's**
environment before starting it. The token is never stored in the route JSON.
If there is no required token, omit --bearer-token-env. The HTTP request body
is exactly the UTF-8 source file; Content-Type is text/plain and
X-Command-Courier-Idempotency-Key identifies the delivery. Only 2xx responses
count as accepted. Redirects are rejected. External plain HTTP is rejected;
explicit localhost/127.0.0.1/[::1] HTTP is allowed for local integrations.

To pause or re-enable forwarding:

    call "windows-relay\COMMAND-COURIER.cmd" route disable
    call "windows-relay\COMMAND-COURIER.cmd" route enable

The existing ARM/STOP/OFF and Auto Send controls also affect the new route;
the file/API route has an additional independent enabled flag.

## Delivery contract

* Explicitly selected source and receiver only; no unrestricted desktop
  scraping, clipboard monitoring or collection of unrelated private text
* UTF-8 .txt text only, up to 128 KiB per input, bounded 32 *new deliveries*
  per scanner cycle; all other files are skipped
* Independent persistent journal under
  %LOCALAPPDATA%\GPTWindowsRelayDesktop\courier-forwarding-state.json
* ID is derived from the selected route, source filename and exact body;
  rerunning the scanner does not retransmit the same body
* Persist SUBMITTING before writing/posting; DELIVERED after an immutable
  file copy or HTTP 2xx; HELD on a failure or uncertain acknowledgement,
  with no automatic blind replay
* No command re-execution when delivery fails; no shared ChatGPT hold files,
  no global dependency on ChatGPT's editable field

## Honest limitations

The implemented source adapter watches **explicit file-drop directories**.
An app or API integration that does not write files still requires a separate
source adapter. The HTTP adapter is an outbound text POST, not a generic API
polling client. This is not unrestricted observation of every visible app or
arbitrary remote destination. Additional input/output adapters should reuse
the same persistent route-specific receipt and deduplication rules.

Existing GitHub bookmark
bookmark/command-courier-hud-force-clear-2026-11-22 remains pinned and was
not modified by this integration.


## ChatGPT sender recovery without stopping the courier

A historical ChatGPT desktop sender failure must not prevent automatic file or
API forwarding. The original HUD displays **READY** when its engine is armed,
with unresolved ChatGPT outbound results in a **secondary outbox status**.
An old sender hold is not a universal delivery block; GO activates the engine.

When the operator can independently confirm one exact result frame was
received, matching its action ID and unique NATIVE-RECEIPT marker, reconcile
it on the existing runner:

    python -B "windows-relay\desktop_native_relay.py" queue-confirmed-receipt ACTION_ID NATIVE-RECEIPT-EXACT_NONCE

This queues metadata after validating the marker against the persistent
native outbox. **The running singleton applies it through its own journal**
before the next ChatGPT scan, marking only that outbound delivery SUBMITTED.
No command is rerun, no text is resent, no composer is cleared, and saved
execution, attempt count, outbox and historical hold file are preserved.

An action ID alone is not enough; an unsent composer draft is not confirmed
delivery. If no actual receipt is independently confirmed, leave that attempt
unresolved. It remains visible as outbox history without blocking the relay.

The earlier acknowledge-receipt CLI still works for a stopped/disarmed runner,
but is no longer needed when the live singleton processes receipt requests.
Avoid opening a second writable State while the runner is alive.


## Temporary TEST FIRE diagnostics — PC Engineer 19

The original 560 × 184 Command Courier HUD now has an operator-initiated
debug panel inside **gear ⚙ → Settings** (expanded 560 × 386). It does not
create a new window or change the compact lifecycle controls.

- **TEST FIRE** injects a new, unique diagnostic text into the existing
  configured **local-test** file route. When local-test does not exist, it
  selects the sole enabled file-to-file route; if more than one is available,
  it requires explicit route selection through the CLI. This button does
  **not** send an arbitrary external API request or transmit into ChatGPT.
- It waits for the real background forwarder, then checks BOTH its durable
  DELIVERED journal phase AND exact destination-file bytes before showing
  **PASS** with route, receipt, byte length and short nonce.
- **CHECK ROUTES** reads configured/enabled route count, historical delivered
  count and held count without forwarding anything.
- It runs asynchronously, so neither test blocks the Tk main event loop.
  ARM, Auto Send, OFF and actual native singleton status remain authoritative.
  An unavailable route or missing acknowledgement shows a failure instead
  of falsely claiming delivery.
- Test inputs and outputs use `courier-test-fire-<nonce>.txt` names and are
  intentionally left as inspectable diagnostic evidence. Historical result
  files and native command execution are not touched.

Equivalent CMD invocation from the repository root:

    call "windows-relay\COMMAND-COURIER.cmd" test-fire

To choose a specific enabled file-to-file route:

    call "windows-relay\COMMAND-COURIER.cmd" test-fire --route local-test

**Temporary:** The button and route-check pane are for engineering
qualification and can be removed once target adapters and the continuous
acceptance suite are established. This first test checks configured
file-to-file delivery only, not ChatGPT UIA submission or remote HTTP POST.


## Explicit ChatGPT/Notepad input test (no arbitrary screen scanning)

Typing into ChatGPT or Notepad alone does **not** select those editors as
automatic source adapters. The current route worker watches configured
UTF-8 file-drop directories. The original TEST FIRE button generates its
own file; CHECK ROUTES only reads route status. Neither button reads the
focused application window.

To qualify text copied from either application using the live, independent
forwarder:

1. Enter a **non-sensitive** test body into Notepad or an unsent ChatGPT
   editor. Click into that editor, then select the intended body and press
   **Ctrl+C**. Do **not** press Enter in ChatGPT as an attempt to relay it;
   Enter may send it to ChatGPT instead.
2. In Command Courier's original HUD, open **gear → Settings** and press
   **SEND COPIED TEXT**. Only this explicit click reads the current clipboard
   as text. It does not change or clear the source editor, send keyboard
   events to either app, or execute pasted command-looking strings.
3. The current configured local-test route (or the sole enabled local
   file-to-file route) receives the exact UTF-8 body. **COPY PASS** appears
   only after the real background worker has written the destination file,
   persisted the matching DELIVERED record, and the file bytes match.
   Debug receipts and route status also appear in a popup so Windows display
   scaling cannot hide the result below the bottom of the 386px HUD.
4. The diagnostic input and output files persist for inspection in the
   selected local directories. Do not copy credentials or private data.

Equivalent one-shot copy → CMD Enter workflow, after Ctrl+C:

    cd /d "C:\Users\p0pe0\Projects\Windows Relay"
    call "windows-relay\COMMAND-COURIER.cmd" test-fire --clipboard --route local-test

The clipboard is read by a short-lived hidden Tk reader. The result receipt
prints as COURIER_TEST_FIRE JSON; an empty/non-text clipboard or unavailable
route fails visibly. This does not enable continuous monitoring of ChatGPT,
Notepad or every other application's input field. Continuous source
capture requires a separately configured, explicit app/window integration.

The compact HUD and bookmarked pre-debug build remain unchanged. This is a
temporary diagnostic input adapter, not a universal always-on clipboard spy.
