# PCE16 HUD operator-visibility defect — 2026-10-10

Status: OPEN; documentation and backlog only. No live HUD changes are made by this record.

The HUD displayed READY/ONLINE while Firefox telemetry was stale and the extension showed NOT PAIRED. The pairing failure was not surfaced clearly in the HUD, causing a prolonged communication investigation. After pairing, PCE16.038 produced a native browser-to-backend-to-ChatGPT receipt, but execution was blocked by a separate governance/API compatibility problem.

This is a genuine operator-visibility defect, not operator error. This record does not claim that backend `armed=false` was independently verified at every moment.

Required status model:

- Execution: ARMED / DISARMED / STOPPED / UNKNOWN.
- Extension: PAIRED / NOT PAIRED / AUTHENTICATION FAILED.
- Separate backend connectivity, scanner freshness, and conversation ownership.
- READY must never imply execution authorization.
- Show actionable failure reasons and last successful communication time.
- Visually separate connection readiness from execution authorization.

Regression requirements: missing pairing, disarmed execution, stale scanner telemetry, backend offline, and owner mismatch.
