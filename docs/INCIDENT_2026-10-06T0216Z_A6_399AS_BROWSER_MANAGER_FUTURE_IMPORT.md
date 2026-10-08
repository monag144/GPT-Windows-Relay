# Incident — A6.399as browser-manager test import ordering

Timestamp: 2026-10-06T0216Z  
Scope: consumer/r29-firefox-offline-tray validation only  
Operation: PCENG-A6.399as-corrected-firefox-oob-submit-gate-and-stage

## Summary

A6.399as correctly repaired and validated the previously corrupted Firefox PowerShell adapter, then stopped during the browser-manager suite before live staging.

The browser-manager production module was not the failing component. The test module itself had:

```python
import base64
#!/usr/bin/env python3
from __future__ import annotations
```

Python requires a `from __future__` import to precede normal imports. The newly-added `base64` import therefore made the test module fail at import time.

## Containment

The deployment gate stopped before copying either Firefox adapter file into the live dev relay.

Already-passed A6.399as gates:

- PowerShell AST parse
- structural duplication checks
- production Python compile
- Firefox adapter regression suite

## Repair

The test header is now:

```python
#!/usr/bin/env python3
from __future__ import annotations

import base64
```

The next Windows gate must compile the relevant test modules themselves in addition to production modules before executing the suites.

## Classification

Harness-only validation regression. It does not invalidate the repaired Firefox adapter source, and it is not evidence of a Firefox or browser-manager runtime failure.
