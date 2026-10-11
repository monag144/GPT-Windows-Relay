# PCE16.037 ChatGPT ↔ Windows Relay scanner not yielding native receipt — 2026-10-10

**Status: OPEN / NO NATIVE RECEIPT AS OF OPERATOR SCREENSHOT.** This is a WIP engineering incident, not evidence that the operation executed or did not execute. Recorded on `wip/windows-relay-rebuilt-resynced-2047-101026` to preserve the existing `main` release boundary. Operator screenshot dated 2026-10-10 21:09 Pacific (2026-10-11 04:09 UTC).

## Direct evidence

- Intended assistant relay packet: `PCE16.037-readonly-file-smoke-test`, `session=pce16.1`, `EXEC`, `shell=powershell`, `timeout=20`, `result_mode=full`. Intended command: read first 3 lines of `C:\Users\Craig Morgan\Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay\TASKS.md` via `Get-Content -LiteralPath ... -TotalCount 3`. An execution would be read-only, but do not resend this already-issued ID.
- Operator provided Firefox screenshot: packet visible in ChatGPT within a UI element labeled **Code**. Do NOT infer that the browser content script extracted it as an executable packet merely because the text rendered.
- HUD screenshot: `READY`; `Relay ONLINE • ARMED • pending 2`; `Firefox IDLE • content_script_started • 2926s`; `READY • content_script_started • 2926s`. Last native item displayed is `WINDOWS-GOVERNANCE-VERIFIED-AUDIT-SYNC-030-034-20261010 / OK` rather than PCE16.037. Browser status bar appeared to be waiting for ChatGPT. The displayed Firefox age is stale; it is NOT proof that newly loaded persistent extension's content script injected successfully into this tab.
- There is **no native `[GPT_WINDOWS_RESULT]` visible** for PCE16.037 at observation time. No fresh backend ledger/event inspection for .037 has yet been supplied; do not assert that `.037` has no backend record.
- Prior operator read-only `state.json` reported `armed=false`, `outbound_owner=browser`, `.035` and `.036` absent from `processed` and `outbound_deliveries` at that earlier moment. It was **before** operator START and screenshot with ONLINE/ARMED. Current backend state must be checked again, read-only.
- Operator independently verified normal Firefox has one temporary `GPT Windows Relay` extension, Gecko ID `gpt-windows-relay@local`, background running, source `GPT-Windows-Relay-Main-Build\windows-relay\extension-persistent`. Both `GPT One-Click Go Relay` temporary extensions were manually removed. Backend + five-button HUD still launched from installed `GPT\Client\Relay`, not Main-Build. This mixed version configuration was deliberately retained until full migration acceptance.
- Verified WIP source snapshot: `Prototype/WIP-Windows-Relay-Rebuilt-Resynced-2047-101026`, commit `909415c8cd8de05fd74fac56f4b43f2d74043aab` on this WIP branch; contains 13 Client source/helpers, five persistent Firefox extension files, `WIP_MANIFEST.json`, `LIMITATIONS.md`. This is a source snapshot, not a deployed/stable release.
- `PCE16.035` and `PCE16.036` were previously issued without native receipts; `.035` has historical no-browser-event/processed evidence, `.036` was a read-only 3-line file scan with no confirmed result. Do not resend either or assume they are absent forever.

## Open failure hypotheses to distinguish with evidence

1. **Content injection or background-port failure:** The new persistent addon was loaded while ChatGPT was open; it is unclear whether a post-load tab refresh produced a live content script connection. Background service worker running alone is insufficient.
2. **DOM recognition/extraction failure:** Rendered `Code` surface and modern ChatGPT assistant wrappers may fail `ASSISTANT_SELECTOR`, `isAssistantUnit`, or `extractUnit`, or the live assistant turn may still be streaming/virtually remounting. Observe DOM shape without copying private chat content, avoid unsafe devtools mutation.
3. **STOP/owner/authentication boundary:** Establish `operatorPaused` state and whether authenticated worker-to-Client backend status/owner claim is valid, not inferred from HUD labels.
4. **Stale HUD telemetry:** HUD may surface previous Client instance `content_script_started` events from disk rather than present addon/browser instance; inspect browser IDs and timestamps.
5. **Result delivery vs execution:** Differentiate command never discovered, browser packet sent but backend refused, backend executed but saved result pending, result sent but ChatGPT failed to recognize. Never treat a visible assistant packet, or lack of user reply, as execution proof.

## Codex repair instructions — offline scope

- Work in the one `C:\Users\Craig Morgan\Downloads\Dev\GPT-Windows-Relay-Main-Build` workspace and existing `Prototype/` and `Backup/` only. Use `monag144/GPT-Windows-Relay/main` as source baseline, WIP branch snapshot as installed Client source record.
- First collect read-only live diagnostics: extension ID/runtime marker, content-script startup/port and owner, back-end status, `%LOCALAPPDATA%\GPTWindowsRelay\state.json`, the last relevant `browser-events.jsonl` entries, and exact PCE16.035/.036/.037 `processed`, `outbound_deliveries`, result and event matches. Report redacted operational metadata, not conversation text, tokens, secrets or personal state. Read source governance/harness and dated roadmap as appropriate.
- Reproduce the observed failure with a synthetic/isolated ChatGPT DOM fixture, including `Code` block rendering, assistant/user turn classification, assistant streaming/remount, content-script injected/reconnected, STOP, owner, duplicate/no resend, and result acknowledgment. Verify runtime source vs installed Client/Firefox interaction. **Do not** rerun `.035`, `.036` or `.037`.
- Stage a minimal component-level repair in Prototype, preserving installed Client's START/STOP/RESTART/OFF/KILL HUD and process lifecycle. Targeted tests, relevant full suite, SHA-256 and regression cases required. No autonomous new-chat/agent switching, no force refresh/retry.
- Commit reviewed **offline** source/test/incident artifacts to the existing WIP branch, report commit SHA and readback. Do not copy into working Client or live Firefox, change backend state, START/STOP, restart, reload addon/tab, clear queue/ledger, or execute test actions without separate explicit operator approval.
- Exit with cause or best evidence-bound hypothesis, exact changed files and tests, and a **single safe next live acceptance step** requiring operator consent.

## Acceptance and publication gate

`PCE16.037` is an **issued/consumed ID**. A new distinct ID is needed if future governed live acceptance is approved. End-to-end PASS requires: one assistant packet actually discovered by the verified singleton extension; one backend accepted action / only one execution; exact result saved and delivered into ChatGPT as a user-role `[GPT_WINDOWS_RESULT]`; confirmation/ack; preserved STOP/owner, no replay. Until such native evidence, classify as BLOCKED / WIP, never “working end-to-end.”

**As recorded here:** no live fix, no new relay action, no backend/Firefox/Client mutation or claim of Codex CLI launch was performed by the GitHub incident-log action.
