# Incident — A6.399c Firefox adapter Unicode console failure

**Class:** INCIDENT / FIREFOX RECOVERY ADAPTER  
**Timestamp:** 2026-10-05T2326Z  
**Operation:** `PCENG-A6.399c-firefox-addon-reload-control-map`

## Failure

The read-only Firefox UI Automation inventory stopped before changing tabs. `firefox_adapter.py list-tabs` successfully obtained a tab title containing the `💻` character but failed while printing its JSON through a Windows `cp1252` stdout host with `UnicodeEncodeError`.

No Firefox add-on reload or page refresh was attempted.

## Root cause and fix

The adapter attempted `sys.stdout.reconfigure(encoding="utf-8")`, but the host cannot be assumed to honor that path. CLI transport does not require literal Unicode, so the deterministic fix is to serialize the final adapter JSON with `ensure_ascii=True`. Unicode tab titles remain losslessly represented by JSON escape sequences and PowerShell's JSON parser reconstructs them.

Implementation: `a1f36a6`. Regression: `ff89d8d`.

## Acceptance

The adapter must list/select the existing emoji-bearing ChatGPT tab from the relay-hosted PowerShell context before any automatic Firefox add-on reload is permitted.
