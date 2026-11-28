# Universal Command Courier — Implementation and Verification

**Branch:** `fix/pce20-single-send-no-duplicate-20261122` (draft PR #34)  
**Controlling design:** [Architecture lock](COMMAND_COURIER_UNIVERSAL_FOREGROUND_DELIVERY_ARCHITECTURE_LOCK_2026-11-27.md)  
**Deployment status:** Requires offline tests, PowerShell AST parse, and deliberate Windows GUI qualification **before** activation. This document is an implementation guide, not a claim of deployment.

## Architecture

- **Source:** explicit `queue-output-file`, `queue-output-clipboard`, or local `queue-output-stdin`. The result is stored in an atomic `explicit-output-requests` JSON request under `%LOCALAPPDATA%\GPTWindowsRelayDesktop`.
- **Owner:** only the running native singleton consumes the request and records `READY` in the existing `State` output journal. **No command execution or UI/DOM scraping occurs in this intake path.** Historical EXEC results remain journaled but cannot be automatically re-executed.
- **Payload:** a UTF-8 text result (1–16,000 bytes) is stored as plain text, not a ChatGPT-style result packet. A stable receipt is recorded separately in the outbox `.receipt.json` sidecar. The destination does **not** receive the receipt or the action metadata.
- **Delivery:** the foreground Windows UI Automation sender finds an eligible writable editor in the selected window, verifies that **every exposed Value/Text pattern is actually empty**, rechecks focus, types one saved result, and clicks one unambiguous exposed Send control if present.
- **Recovery:** a saved draft may get one receipt-bound Send-only attempt. `SUBMIT_UNCERTAIN` is not automatically retried; no repeated EXEC, no blind Enter, no duplicate insertion.
- **Manual controls:** HUD `FORCE SEND` asks the native owner to deliver an eligible saved output to the previously selected foreground window. HUD `FORCE CLEAR` closes journaled unresolved deliveries as ABORTED **without** touching another application's draft or composer.
- **Legacy:** `Watch-ChatGPT-ActionCandidates.ps1` and historical packet execution helper remain in the source tree for audit continuity, but the universal native runner **does not call them**. The old `force-delivery` ChatGPT-only sender path is disabled.

## CMD-only operator input examples

From `C:\Users\p0pe0\Projects\Windows Relay\windows-relay` after controlled activation:

```bat
python desktop_native_relay.py queue-output-file --file "C:\Temp\courier-output.txt"
python desktop_native_relay.py queue-output-clipboard
type "C:\Temp\courier-output.txt" | python desktop_native_relay.py queue-output-stdin
```

No command payload is accepted by these paths. They enqueue text only. For a custom app/API client, pipe its already-authorized output into `queue-output-stdin`, or deliberately write a UTF-8 text file and use `queue-output-file`. No ChatGPT/Gemini/Claude/Grok transcript access is required.

## What to expect

1. Keep **Auto Send OFF** while qualifying. Queue a known harmless output (e.g., a distinctive, non-sensitive phrase) using an explicit input method.
2. Select the intended app and an empty, writable field. With Auto Send OFF, click **FORCE SEND** once. The HUD must show the receipt-derived disposition.
3. In Notepad, there is usually no Send control; the result should be **TEXT_INSERTED**, not `SUBMITTED`. A nonempty Notepad field must remain untouched.
4. In messaging apps, if a unique accessible Send control is available, the sender clicks it once. If none is available, a recognized message field may retain `SEND_PENDING`. If the send was clicked but not independently confirmed, `SUBMIT_UNCERTAIN` is expected—**never blindly click again**.
5. If multiple eligible fields exist and none is selected, Courier must leave the output `READY`. Manual focus to one field takes priority over automatic selection.
6. FORCE CLEAR is an explicit journal reset only. It cannot erase Discord, ChatGPT, Telegram, or any other app draft.

## Category-driven foreground targeting (2026-11-27 update)

- The sender chooses a visible, writable UIA field by **focus, uniqueness, and emptiness**, not by ChatGPT, Gemini, Grok, Claude, Discord or Notepad process identities. A selected field wins; ambiguous unfocused fields remain untouched.
- The detected **field category** is either `MESSAGE_COMPOSER` (generic Ask / message / reply / compose / prompt semantics or an unambiguous visible Send control) or `TEXT_EDITOR` (writable ordinary editor). ChatGPT is simply a potential member of the former category; it is **not** an allowlisted special case.
- The sender reports `DESTINATION_CATEGORY`; the native runner records it; the HUD displays the last detected field category. These are capability labels, not assertions that a named provider has authorized or received a message.
- **Auto Send OFF is an explicit operator pause**, not a provider restriction or a field-detection error. With OFF, no automatic foreground delivery occurs; one eligible result may still be delivered manually via FORCE SEND. The HUD must say why it is paused instead of misleadingly reporting generic readiness.
- To resume autonomous delivery, select the intended empty text field and explicitly enable Auto Send. Do **not** silently override OFF or re-send older results. The cutover utility permits `-EnableAutoSend` only when no previously eligible unsent results remain.
- The controlled cutover utility is `tools/Activate-UniversalCourier-PR34.ps1`. Run it **outside the relay being replaced**, after its last response has been acknowledged. It re-runs both test suites, stops the old native singleton, closes only canonical relay HUD processes, starts the new engine/HUD, and verifies the native source SHA-256 and single HUD identity.
- The new universal engine intentionally **does not read commands from ChatGPT screen content**. After cutover, further command execution must use an independent authorized channel; text from clipboard/file/local-API stdin can be queued for delivery but is not executed.

## Release gates

- Python compilation of all modified modules and test files.
- Windows Relay suite + Consumer suite, including Windows PowerShell AST parsing.
- Read-only verification that the active runner contains no `read_scan` call and no ChatGPT-specific source acquisition.
- Real GUI check with Notepad (empty/nonempty), ChatGPT, Gemini, Claude, Grok, Discord, Telegram, and a custom text field, as available on the operator machine. A missing app is **UNTESTED**, never a pass.
- Deliberate cutover from the qualified draft worktree only after no outbound result is in `SUBMITTING` or unacknowledged `SUBMIT_UNCERTAIN`. Preserve existing main project staging and old stable checkpoint.
- **No automatic production deployment, restart, remote merge, or retroactive resend is authorized merely by this document.**

## Known limitations

- Foreground UIA Send control availability varies by application/version. Keyboard-only submit is intentionally not inferred.
- Unicode keyboard injection currently flattens line breaks to spaces to avoid accidental multi-message sends; this is a presentation limitation for multiline text and requires explicit cross-app qualification before claiming byte-for-byte visual fidelity.
- A generic GUI cannot always prove server-side message acceptance. A click without independent confirmation stays `SUBMIT_UNCERTAIN`.
