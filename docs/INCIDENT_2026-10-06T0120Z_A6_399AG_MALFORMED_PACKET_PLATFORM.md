# Incident — 2026-10-06T0120Z — A6.399ag malformed relay probe omitted platform

**Class:** RELAY PACKET AUTHORING / FAIL-CLOSED VALIDATION  
**Observed at:** 2026-10-06T0120Z  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Operation:** `PCENG-A6.399ag-plane-d-relay-bootstrap-gate`

## Evidence

Director screenshot at approximately 18:20 PDT showed the A6.399ag action visibly rendered in the current Firefox ChatGPT conversation while the HUD simultaneously showed:

- Relay ONLINE / ARMED / pending 0;
- Firefox ACTIVE;
- fresh `scanner_snapshot` (~26 s);
- fresh `content script started` (~29 s);
- LAST operation still A6.399ae.

No A6.399ag discovery/execution occurred.

## Root cause

The assistant-authored A6.399ag packet omitted the required JSON field:

`"platform":"windows"`

The r29 content parser's `validPacketBody()` explicitly requires `p.platform === "windows"`. Therefore the visible block was rejected before `relay_packet_discovered` could be emitted. This is correct fail-closed behavior.

The assistant also rendered the packet in a language-tagged `text` fence instead of the required bare fence. The current primary DOM code-block parser is tolerant of the rendered code element, but the operational sandwich contract explicitly requires a bare fence and must still be followed.

## LocalAppData hypothesis

`%LOCALAPPDATA%\GPTWindowsRelay` does persist backend/HUD data such as `state.json` and `browser-events.jsonl`, so stale local state can affect historical HUD presentation and exact-once backend records.

However it cannot explain this specific non-discovery: the content script rejected A6.399ag locally in the page before any backend state lookup. Content-side attempted packet IDs are principally held in page `sessionStorage` under `gptWindowsRelayAttemptedIdsV2`, not in the backend LocalAppData state file.

No LocalAppData reset is justified by this incident.

## Corrective action

Resend a new unique probe ID with:
- `version: 1`;
- `platform: "windows"`;
- `action: "EXEC"`;
- bare sandwich fence;
- visible prose before and after the fenced packet.

A corrected packet must be used to judge live relay ingestion.

## Corrected live probe — A6.399ah — PASS

The corrected probe `PCENG-A6.399ah-plane-d-corrected-ingestion-gate` was ingested and executed exactly once. Backend result:

- status `OK`, exit code 0;
- duration 650 ms;
- `RELAY_OK=True`;
- `RELAY_ARMED=True`;
- relay PID 9900;
- `FIREFOX_CONNECTED=True`;
- Firefox age 0 seconds;
- current browser lifecycle event `action_received`;
- `A6_399AH_CORRECTED_INGESTION=PASS`.

This confirms the live scanner/extension/backend path was healthy once given a contract-valid packet. The A6.399ag non-discovery is closed as malformed authoring, not LocalAppData corruption.
