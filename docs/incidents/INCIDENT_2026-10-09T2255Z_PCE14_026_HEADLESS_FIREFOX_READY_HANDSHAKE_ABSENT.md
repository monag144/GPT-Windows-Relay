# PCE14.026 headless Firefox fixture readiness handshake absent — 2026-10-09T2255Z

## Confirmed Windows result
Operation `PCE14.026-receiver-attested-firefox-geometry`, session `pce14.1`, Windows `status=COMMAND_FAILED`, `exit_code=1`, duration 20324ms. All five canonical source-of-truth controls passed local `engineering_preflight(root,26,series=14)`; original and backup protected PCE12 audit were guarded by the issued command. Branch/HEAD of the Windows checkout remained `pce11/one-click-go-recovery-and-doc-hygiene`/`a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a` at dispatch.

A pinned, temporary feature snapshot `f08377bb4bd18b25ea919eb02a7915c63c6f4197` ran its **69 unit/integration tests: all 69 PASS**, zero fail/error, unit-test process exit 0. A disposable `--headless --no-remote --profile` Firefox process returned exit 0 and generated a valid screenshot PNG. **Crucial acceptance FAILED:** `ready_attested=false`, `launch_id_matches=false`, `attested_geometry=null`; independent receiver `total_effects=0`, `visible_input=0`, `chatgpt_messages=0`. The issued Python raised `RuntimeError:FIREFOX_READY_ATTESTATION_FAILED` and correctly did not claim browser-ready. Screenshot appearance, page GET count, JavaScript console state, `/api/ready` request count and rejection reasons were **not** included in the result.

## Root cause
**OPEN / NOT VERIFIED.** Plausible distinct failure classes: browser page geometry returns null under headless frame dimensions; JavaScript error occurs before POST; screenshot renderer snapshots page before its async POST completes; server rejects the ready data. The existence of a PNG or a green 69-test suite cannot distinguish these. No evidence establishes a bug in Firefox or the relay extension, and no real ChatGPT Send occurred.

## Corrective gate
Next new unique PCE14.027 should run a **read-only-to-production, temporary local fixture diagnostic**: one disposable headless Firefox profile, one local loopback server, count page GET and `/api/ready` POST attempts and classify validation error codes without logging nonce, message text, URLs or user content; wait only a bounded interval for pending local POST after screenshot; independently verify `receiver.ready_report` and `total_effects=0`. Avoid another uninstrumented repetition of .026. If no readiness POST appears, inspect safe script execution/geometry telemetry in an isolated fixture only; if POST occurs but rejects, correct exactly that known condition via GitHub-first source update and test. Preserve protected PCE12 original/backup and never act on personal Firefox windows.

The feature draft PR #10 remains **unmerged** and its GitHub Actions CI status remains **RED/unknown cause** (earlier run without accessible steps). No runtime promotion, no manual rescue, no GUI Send or independent real-chat receipt in .026. This document is an incident record, not the five-op audit .025–.029 and does not itself qualify .027 for any additional permission.

**INCIDENT OPEN; .026 is a genuine runtime acceptance failure despite 69/69 isolated tests passing.**
