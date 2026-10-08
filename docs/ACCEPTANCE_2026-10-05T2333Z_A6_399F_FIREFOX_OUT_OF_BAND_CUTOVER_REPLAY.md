# Firefox Out-of-Band Cutover and Replay Acceptance — 2026-10-05T2333Z

**Class:** ACCEPTANCE / CONSUMER RECOVERY  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Operation:** `PCENG-A6.399f-live-cutover-replay-acceptance`  
**Result:** PASS

## Purpose

Prove that recovery of the development Firefox integration can occur outside the browser-extension transport being repaired, and that an action already executing during the cutover is not executed twice.

## Live sequence

1. A6.399f began executing at 2026-10-05T23:32:27Z and intentionally held for 45 seconds.
2. An independent PowerShell helper, scheduled before A6.399f, invoked the semantic Firefox recovery adapter without sending repair code through the relay.
3. The helper reloaded exactly one `GPT Windows Relay` temporary add-on from `about:debugging`.
4. The helper refreshed the selected ChatGPT Firefox tab.
5. The new content script reconnected to the still-healthy relay backend.
6. A6.399f completed once in the backend and its saved result was delivered after the browser cutover.

## Evidence

- relay action status: `OK`, exit code 0
- returned result metadata: `replayed: true`
- cutover log: `reload-addon` => `invoked: true`
- cutover log: `refresh-tab` => `invoked: true`
- `RELAY_HEALTH=PASS pid=9900`
- `FIREFOX_CONNECTED=PASS`
- content runtime: `v11-scroll-v5-delivery-v11-collapse-recovery-approval-v2`
- `APPROVAL_DETECTOR_RUNTIME=ACTIVE`
- `OUT_OF_BAND_FIREFOX_CUTOVER=PASS`
- the A6.399f result itself was visibly returned to ChatGPT after the cutover.

## Acceptance conclusion

PASS for the live development Firefox cutover/reconnect/durable-result replay path. The test demonstrates that extension reload and ChatGPT refresh can be performed by an independent control path and that the result survives transport replacement without duplicate backend execution.

This does **not** close consumer Firefox One-Click GO blocker F-001. The consumer build must still install/reinstall the Firefox add-on when absent (including after a full Firefox restart) and then pass the complete consumer zero-touch mission/result/screenshot/recovery acceptance contract.

## Rotation boundary

A6.400 is intentionally not consumed by this acceptance. The next numeric operation is reserved for deliberate validation of the every-100-operation fresh-chat rotation contract; after rotation the operation series must advance dynamically to A7.
