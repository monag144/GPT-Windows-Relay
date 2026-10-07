# Incident: PCE8.89 synthetic composer probe submission — 2026-10-06T22:00Z

A fault-test helper inserted synthetic relay-result text into the real ChatGPT composer. UIA then reported `DRAFT_READBACK_MISMATCH`; rollback restored v16, but the browser still retained the text and baseline v16 submitted it once.

PCE8.91 proved one draft detection, one send click, one send acceptance, and zero backend execution for sentinel `PCE8.79S-synthetic-draft-owner-release`. The composer later returned to semantic empty state (`Ask ChatGPT`).

The composer-injection technique was retired. Subsequent fault testing used a zero-UI virtual draft inside a temporary content script: no clipboard, no composer mutation, no relay-result markup, and the controlled failure occurred before `await send()`.

PCE8.97/PCE8.98 then exercised the intended owner-release path with zero send-path and zero backend activity for the virtual sentinel.
