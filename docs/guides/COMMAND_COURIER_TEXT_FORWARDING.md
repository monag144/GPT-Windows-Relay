# Command Courier — independent text-body forwarding

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
