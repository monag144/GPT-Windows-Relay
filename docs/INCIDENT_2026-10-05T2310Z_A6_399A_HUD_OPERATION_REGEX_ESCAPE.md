# Incident — A6.399a HUD operation-label regex escaping

**Class:** INCIDENT / HUD REGRESSION  
**Timestamp:** 2026-10-05T2310Z  
**Operation:** `PCENG-A6.399a-corrected-recovery-deployment-gate`

## Result

The corrected validation boundary proved the prior A6.399 problem was isolated:
- consumer suite: **70 tests, OK**;
- Windows-relay suite: **252 tests run, one failure**.

The sole failure was `test_discovered_headline_uses_dynamic_operation_series`. `operation_label('PCENG-A6.396-approval-helper-source-map')` returned the packet-name fallback rather than `A6.396`.

## Root cause

`windows-relay/hud.py` used a Python raw regex with doubled backslashes: the expression matched literal backslash sequences rather than regex word-boundary/digit tokens. This came from an escaping error in the implementation patch.

## Fix

Use the intended raw Python expression `r"(?i)\bA\d+\.\d+\b"`.

Implementation: `c947d5b`.

## Acceptance

Targeted HUD regression must pass for A6 and A7 examples before the full relay suite is repeated. A6.399a remains COMMAND_FAILED and is not counted as a deployment pass.
