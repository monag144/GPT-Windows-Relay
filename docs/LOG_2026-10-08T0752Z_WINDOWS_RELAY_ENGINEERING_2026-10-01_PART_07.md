# Archived source fragment 7/23 — 2026-10-08T0752Z

Next step: inspect the live about:debugging temporary-extension card through Windows UI Automation, which previously proved capable of seeing the relay card and Reload control.

## Live Firefox temporary relay mapping — Action 147

Action PC-ENGINEER-RELAY-147-LIVE-ABOUT-DEBUGGING-UIA-FORENSICS used Windows UI Automation against Firefox's live about:debugging page and definitively mapped the currently loaded temporary relay instance.

Confirmed live state:
- Temporary Extensions count: 1
- Name: GPT Windows Relay
- Location: C:/Users/<LOCAL_USER>/Downloads/Dev/GPT/Client/Relay/extension/
- Extension ID: 55840853a4b817e65769e2378ca65e060cbe18d1@temporary-addon
- Internal UUID: 2583b6b1-f194-48c9-a8ab-cc1add6602ec
- Manifest URL: moz-extension://2583b6b1-f194-48c9-a8ab-cc1add6602ec/manifest.json
- Background script: Running

Interpretation:
- Firefox is not loading the relay from an unknown or stale source directory
- the one live temporary relay instance points exactly at Client\\Relay\\extension, which Action 138 proved contains the current V4 content.js hash and runtime marker
- therefore the missing runtime:'v11-scroll-v4' telemetry from the ChatGPT tab is now best explained by stale injected content-script context / extension reload lifecycle rather than wrong source selection
- historical temporary-addon IDs remain profile residue only; about:debugging shows exactly one live temporary extension

Next step:
- verify/reload the live temporary extension instance and force a fresh ChatGPT document load, then require content_script_loaded to report runtime:'v11-scroll-v4' before testing handoff scroll again
- do not alter scroll implementation further until fresh-runtime activation is proven

## Canonical established-facts knowledge base added

To prevent repeated investigation of facts already proven in prior relay work, a short-form canonical knowledge base now lives at `docs/windows-relay-established-facts.md`.

Policy:
- read the established-facts file and search this engineering log before launching new relay forensics
- carry forward prior conversation/project-history facts when already established
- separate source state, staged live-tree state, Firefox extension-instance state, and actually injected content-script runtime state
- log newly confirmed findings, root causes, fixes, false leads worth remembering, and proof back to GitHub as they are established
- prefer machine effort over user intervention and avoid asking the user to repeat or manually rediscover known facts

The README now links this preflight requirement prominently.

## Fresh-runtime automation failure + telemetry semantics correction — Actions 148–149

Action 148 scheduled a detached PowerShell helper intended to reload the live temporary Firefox relay extension and then reload the ChatGPT document. Action 149 found no helper log, so the deferred helper did not successfully execute.

Action 149 also exposed a telemetry naming flaw:
- connectBackgroundPort() currently emits event content_script_loaded every time a Port is established/re-established
- therefore repeated content_script_loaded events do not necessarily represent fresh content-script injection or document reload
- the ~30-second cadence seen in the event log is compatible with Port reconnect behavior and must not be interpreted as repeated page loads

Implications:
- Action 149 did not prove that Firefox repeatedly loaded the stale content script; it proved only that the currently running stale content script repeatedly established a background Port
- runtime:'v11-scroll-v4' remains absent because the currently executing content-script context is still the older generation
- fresh-runtime activation remains unproven

Required fixes:
- distinguish true content-script startup telemetry from content-port-connected/reconnected telemetry
- replace the failed detached activation helper with a simpler deferred launcher whose execution can be proven independently
- do not use the old content_script_loaded event as a proxy for document injection until telemetry semantics are corrected

## v0.3.8 staging false-negative — stale content-load telemetry test

Action PC-ENGINEER-RELAY-150-STAGE-V038-AND-DEFERRED-LAUNCHER-PROBE failed during the browser contract suite before the deferred-launch probe ran.

Root cause:
- test_content_load_and_scanner_snapshot_telemetry still enforced the obsolete event name content_script_loaded and marker GPT_WINDOWS_CONTENT_LOAD_TELEMETRY_V1
- the implementation had already moved to one-time content_script_started telemetry with GPT_WINDOWS_TRUE_CONTENT_START_TELEMETRY_V1

Correction:
- regression test renamed/reframed around true content-script startup semantics
- old content_script_loaded assertion removed
- obsolete GPT_WINDOWS_CONTENT_LOAD_TELEMETRY_V1 source marker removed from canonical/live/persistent content-script copies

Interpretation:
- Action 150 does not indicate a runtime or relay failure
- the deferred-launch probe did not execute because sync-live exited on the stale test first
- staging and launcher validation must now be retried separately so failures remain isolated

## v0.3.8 staging false-negative — brittle content-start syntax assertion

Action PC-ENGINEER-RELAY-151-STAGE-V038-CLEAN failed in test_content_start_and_scanner_snapshot_telemetry.

Root cause:
- the implementation correctly emits content_script_started through emitRelayEvent('content_script_started', ...)
- the regression test incorrectly required the literal object-fragment syntax event:'content_script_started'
- this was a brittle source-shape assertion, not a behavioral failure

Correction:
- the test now asserts the actual behavior-bearing emitRelayEvent('content_script_started' call
- no runtime implementation change was required for this failure

## v0.3.8 clean staging — GREEN

Action PC-ENGINEER-RELAY-152-STAGE-V038-CLEAN-RETRY completed successfully through the live relay.

Observed:
- V11_STAGED=True
- HANDOFF_SCROLL_V4_STAGED=True
- SCROLL_TELEMETRY_V4_STAGED=True
- WORKER_DRIVEN_SCROLL_STAGED=True
- TRUE_CONTENT_START_TELEMETRY_STAGED=True
- RUNTIME_IDENTITY_STAGED=True
- PERSISTENT_PORT_STAGED=True
- BROWSER_TELEMETRY_STAGED=True
- persistent XPI built as gpt-windows-relay-0.3.8.xpi
- SYNC_LIVE=GREEN
- V038_CLEAN_STAGING=GREEN

Interpretation:
- v0.3.8 is now the clean staged baseline for the scroll/lifecycle mission
- remaining blocker is live activation of the fresh content-script runtime, not source staging or regression coverage
- deferred launcher validation should be tested independently before using it to automate Firefox reload

## Deferred child-process probe — Actions 153–154

Action PC-ENGINEER-RELAY-153-DEFERRED-LAUNCHER-ISOLATED-PROBE successfully created a detached PowerShell child process and returned PID 12988. The child was instructed to wait two seconds and write `%LOCALAPPDATA%\\GPTWindowsRelay\\deferred-launcher-probe.txt`.

Action PC-ENGINEER-RELAY-154-VERIFY-DEFERRED-LAUNCHER-PROBE found:
- PROBE_EXISTS=False
- DEFERRED_LAUNCHER_PROOF=FAILED

Backend inspection after the failure confirmed:
- `windows_relay.py` launches the action process with CREATE_NEW_PROCESS_GROUP
- normal successful completion does not explicitly kill descendants
- `taskkill /PID <pid> /T /F` is used only on command timeout

Therefore:
- a relay-command-spawned detached child is not a reliable post-result execution mechanism in the current environment
- the exact external reason the detached child disappeared is not yet proven by backend source and must not be stated as established root cause
- do not use ordinary detached child processes for post-result Firefox lifecycle actions

Next approach:
- use Windows Task Scheduler as an external process-ownership boundary
- create/run a scheduled task that performs a delayed marker write, verify it survives after the relay result returns, then reuse the proven scheduler primitive for Firefox extension/document reload

## Task Scheduler post-result execution primitive — Actions 155–156 — GREEN

Action PC-ENGINEER-RELAY-155-TASK-SCHEDULER-DEFERRED-PROBE created and immediately ran the one-shot task `\\GPTWindowsRelay-DeferredProbe`. The task waited three seconds and wrote a marker outside the relay action lifetime.

Action PC-ENGINEER-RELAY-156-VERIFY-TASK-SCHEDULER-DEFERRED-PROBE confirmed:
- PROBE_EXISTS=True
- TASK_SCHEDULER_DEFERRED_PROOF=GREEN
- Task Scheduler Last Result=0
- Logon Mode=Interactive only
- Run As User=<LOCAL_USER>
- the probe task was deleted after verification

Established design fact:
