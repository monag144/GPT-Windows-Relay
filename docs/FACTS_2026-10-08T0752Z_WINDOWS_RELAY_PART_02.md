# Archived source fragment 2/3 — 2026-10-08T0752Z

- `sync-live.py --restart-backend` can stage and intentionally restart the supervised backend.
- Machine effort should be spent before user effort. Recoverable failures should not become unnecessary manual steps.
- When a test fails after an architecture change, check whether the **test contract is stale** before concluding the implementation is broken. V4 scroll staging hit exactly this failure mode.
- Static source presence is not equivalent to active browser runtime proof. For browser features, verify the actual loaded runtime/telemetry before declaring success.

## Historical Firefox temporary-extension facts

These are confirmed observations from the October 2–3, 2026 debugging session, not universal constants.

Active Firefox profile observed:
- `3awtt83g.default-release`

Historical relay temporary IDs observed:
- `789b9cccc135a95bdd457f81c61d1f92e5acf18e@temporary-addon` — historical, installed=False
- `a246f5d3d4411a21157d03eb0b0b350de6b91797@temporary-addon` — historical, installed=False
- `415ba89c48af03b9a3da9331f264187d086ef1ee@temporary-addon` — historical, installed=False
- `55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon` — current during the observed session, installed=True

Live `about:debugging` UI Automation later proved:

- Temporary Extensions count: 1
- live relay location: `C:/Users/<LOCAL_USER>/Downloads/Dev/GPT/Client/Relay/extension/`
- live extension ID: `55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon`
- internal UUID during that session: `2583b6b1-f194-48c9-a8ab-cc1add6602ec`
- background script: Running

Therefore:
- multiple historical temp IDs in Firefox profile metadata do **not** imply multiple currently installed relay extensions;
- `installed=False` is the important distinction for historical reconciler entries;
- the one live temp extension was already proven to point at the expected `Client\Relay\extension` directory.

Do not redo profile archaeology merely to rediscover that source path. Use the live `about:debugging` card / UI Automation first if the active temporary instance needs to be checked again.

## Current Firefox identity checkpoint (2026-10-08T06:35Z)

**Required reading:** `docs/handoffs/HANDOFF_2026-10-08T0635Z_PCE10_037_TO_NEXT_AGENT_FIREFOX_IDENTITY.md`. The `3awtt83g.default-release` Firefox profile, temporary addon ID `55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon`, and unique installed addon card above were **historically proven on Oct 2–3**. They do not prove a current browser PID, loaded code, installed addon, selected ChatGPT tab, or matching conversation URL. PCE10.035 source acceptance is fully GREEN and PCE10.036 backup integrity was reverified, but PCE10.037 `resolve-conversation-tab` failed with `FIREFOX_CONVERSATION_MATCH_COUNT_0`. This is a specific **unresolved identity gate**, not proof of Firefox absence. The exact resolver's offscreen/tab-parent filtering and possible stale target URL must be investigated once using bounded read-only evidence, not repeated generic browser scans or profile archaeology. No automatic addon reload / live promotion before positive identity.

## Current scroll work status

The user requested a user-benefit behavior where relay result injection brings the conversation down to the newest turn and follows the beginning of the next assistant response briefly, then yields manual scroll control.

Progress through V4:

- V1/V2/V3 experiments established telemetry and lifecycle issues;
- V4 moved handoff ownership to the reliable worker result path:
  - worker sends `relay_handoff_scroll`
  - then sends `relay_action_result`
  - content script handles the ordered scroll-control message
- source/tests staged successfully in persistent package v0.3.7;
- runtime identity marker: `runtime:'v11-scroll-v4'`
- marker: `GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V4`
- marker: `GPT_WINDOWS_WORKER_DRIVEN_SCROLL_CONTROL_V1`

**Do not modify the scroll algorithm again until a freshly loaded content script is proven active.**

At the last proven point:
- all known relay `content.js` copies on disk had identical current V4 content;
- live about:debugging pointed to the correct `Client\Relay\extension` source;
- but the ChatGPT tab's `content_script_loaded` telemetry still lacked the V4 runtime identity.

That narrowed the remaining issue to **content-script reload/document lifecycle**, not wrong source directory or multiple live temporary relay copies.

## Preflight checklist before new debugging

Before launching new forensics:

1. Read this file.
2. Search the engineering log for the subsystem/action already investigated.
3. Check whether the fact is already established in conversation/project history.
4. Distinguish:
   - source file state;
   - staged/live-tree state;
   - Firefox extension instance state;
   - actual injected content-script runtime state.
5. For browser behavior, require runtime telemetry or direct live UI proof before blaming source code.
6. Prefer live `about:debugging` / UI Automation for temporary-extension identity before deep profile archaeology.
7. Log new confirmed findings, root causes, fixes, and validation proof back to GitHub immediately.

The purpose of this document is to prevent repeated investigation of solved facts and minimize user intervention.


## Current product priority order

1. **P0 — Scroll / conversation-follow UX:** prove a genuinely fresh V4+ content runtime, then validate worker-driven handoff scroll end to end.
2. **P1 — Windows HUD:** compact real-state display for relay armed state, backend health, Firefox bridge/runtime state, last/current action, and synchronized pause/arm control.
3. **P2 — Lifecycle hardening:** backend restart, Firefox restart, Windows/login restart, signed persistent extension/policy path.
4. **P3 — Clipboard + troublesome job-application helper:** resume-backed field mapping; copied application text → ChatGPT reasoning → relay input.
5. **P4 — Screenshot on request:** explicit bounded screen/window/region capture returned to ChatGPT for visual reasoning.
6. **P5 — Broader Windows UI interaction adapters.**

The job-application branch is intentionally simple at first: the user copies difficult form text/context to ChatGPT, ChatGPT reasons using resume data, and the relay pastes/types the answer back. Screenshot capture is on-demand, not continuous by default.


## Human-intervention incident policy

Any unintentional user action required to keep an otherwise autonomous relay workflow moving is an engineering incident and must be logged in the canonical engineering record.

Examples include:
- manually submitting a relay result that should have been sent automatically;
- manually reloading Firefox or ChatGPT when automatic recovery was expected;
- manually visiting about:debugging to rescue the temporary extension outside an explicitly planned development test;
- manually re-pairing, re-arming, copying, pasting, clicking, or restarting something because the relay stalled;
- manually surfacing a stranded result or command.

Log the confirmed human action and mission impact immediately. Keep the technical root cause explicitly unresolved until telemetry or other evidence proves it. Do not normalize accidental user rescue as part of the expected workflow.


## Browser result-delivery contract

A Windows action result is **not delivered merely because the Send button was clicked**. The browser bridge must confirm that a user turn containing the packet ID exists before persisting that packet as attempted.

If ChatGPT rejects a send or leaves the result stranded in the composer, retry the same already-fetched result with bounded backoff. Do not re-execute the Windows command. Duplicate-ID saved-result replay remains the safety net after browser/content recovery.

A manually rescued stranded composer result is an autonomy incident and must be logged.


## Browser delivery anti-spam invariant

A backend result with `replayed:true` means **do not re-execute the Windows action**; it does not mean the browser should blindly post the result again.

Current delivery contract (delivery-v2):
- successful browser delivery may be confirmed either by an existing user `[GPT_WINDOWS_RESULT]` turn containing the packet ID or by the composer clearing and remaining clear without a send-error for the stability window;
- completed packet IDs persist in page `sessionStorage` across content-script/document reloads;
- startup recovery also hydrates completed IDs from existing user `[GPT_WINDOWS_RESULT]` turns;
- if a result for packet ID X is already visible in the conversation, `run(X)` must suppress backend replay/injection before calling the Windows backend;
