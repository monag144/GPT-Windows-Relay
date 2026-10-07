# PC Engineering 6 → 7 handoff after failed operation-400 rotation

Timestamp: 2026-10-06T0246Z (2026-10-05 19:46 PDT)  
Class: HANDOFF / CONSUMER BUILD / FAILED ROTATION RECOVERY  
Development branch: `consumer/r29-firefox-offline-tray`  
Stable branch: `consumer/one-click-go` remains unpromoted at audited SHA `d5b9db7`.  
First Agent 7 engineering operation: `A7.1`.

## Boundary truth

A6.400 was intended to be the live 100-operation/new-chat rotation acceptance. It FAILED before execution.

Screenshot evidence shows `PCENG-A6.400-rotate-to-agent7` stuck at HUD state `DISCOVERED`, `relay_packet_discovered`, “packet parsed; settling before execution • 7s”. There is no A6.400 execution result. See `INCIDENT_2026-10-06T0245Z_A6_400_ROTATION_DISCOVERED_NOT_EXECUTED.md`.

Agent 7 must continue the mission; do not restart the audit. Do not count the rotation acceptance as passed.

## Entire Director mission

This is a CONSUMER BUILD ONLY audit, hardening, and acceptance program. The current dev Firefox is permitted as the live development/acceptance browser, but stable consumer promotion is blocked until the complete consumer matrix passes.

The required product is zero-touch for ordinary users:

1. Audit all consumer functionality and all dated docs so no requested feature is lost.
2. Harmonize relay redundancies: immediate packet discovery, remount/settle reacquisition, approximately 15-second broad reinspection, approximately five-minute dead-man, folded/collapsed sandwich recovery, exact-once backend replay protection, transition-specific watchdogs, and meaningful HUD phases.
3. HUD must show the exact dynamic operation label/instruction (A7.x after this handoff), real lifecycle state, and real stall/recovery reason. Idle is not stalled.
4. Rotate Firefox to a fresh ChatGPT conversation every 100 operations. The operation-series parser must be dynamic; nothing may hard-code A6.
5. Detect ChatGPT tool approval surfaces promptly. Report `APPROVAL REQUIRED` with provider/context. Do not silently bypass platform security confirmations. Once a GitHub or Google Drive connection is legitimately established, ordinary subsequent use should not repeatedly nag the user; final acceptance of connection persistence remains required.
6. When the normal browser/content integration is broken, recover independently. After bounded normal/probe attempts, the independent supervisor must diagnose health, use the newest timestamp-compatible GitHub recovery evidence, prompt GPT through an out-of-band browser control plane, validate GPT's bounded recovery-advice envelope, and execute only whitelisted repairs. Never send repair code through the broken relay.
7. Firefox refresh/recovery must automatically reload/reinstall the temporary relay add-on when required.
8. Unique or contradictory failure states must automatically capture a screenshot before repair. The screenshot must be presented to GPT through an audited independent attachment path; merely storing a local path is insufficient.
9. Result visibility and assistant-turn completion are separate. A visibly delivered relay result must be correlated to the exact packet. If ChatGPT remains generating/active after stable visible result content, enter a distinct finalization watchdog, capture evidence on timeout, recover without re-executing the completed Windows action.
10. Completely test One-Click GO for Firefox, Chrome, and Edge: update, isolated launch, browser setup, normal mission, injected relay harness, canonical sandwich, exactly-once execution, visible exact result, screenshot attachment, injected failure/recovery, and no unplanned Director action.
11. Exercise historical browser-specific failures, especially Firefox temporary-addon/profile topology and Edge false-ready/postload races.
12. Every recovery obligation must be durable and supervised. Scheduling a detached child is not success.
13. Documentation is timestamp-authoritative only. No CURRENT/ACTIVE/MAIN/LATEST naming convention may imply source-of-truth. Continue the dated index and log every new intervention/incident.
14. Do not promote `consumer/one-click-go` until Firefox, Chrome, and Edge acceptance plus recovery/screenshot/rotation gates all pass.

## What Agent 6 proved or implemented

- relay backend health/exact-once execution path worked in live checks;
- HUD idle false-stall fix deployed and dynamic operation labels support future A7.x;
- forced scanner reinspection, remount/settle reacquisition source, and approximately five-minute watchdog coverage exist;
- approval-prompt detector implemented and activated in r29 runtime;
- Firefox out-of-band add-on reload + ChatGPT refresh + durable replay passed in A6.399f;
- recovery supervisor architecture/implementation and deterministic repair whitelist exist;
- Plane-D Firefox semantic UIA supports list/select/refresh/reload-addon/ensure-addon/send-prompt/read-text;
- base64-safe prompt transport plus guarded clipboard/focused-Enter fallback and submission confirmation were implemented;
- A6.399au zero-touch OOB prompt submission succeeded and the extension secondary observer recognized valid recovery advice;
- recovery prompt was hardened against self-parsing; malformed coaching requires complete envelope boundaries;
- independent read failures were made observable;
- semantic ChatGPT visible-error detection and `CHATGPT_UI_ERROR` screenshot classification were committed;
- the long-active-turn-after-visible-result failure was identified and documented;
- consumer/unit/relay suites repeatedly passed at intermediate checkpoints, while validation-harness defects and PowerShell source-corruption recurrences were logged and repaired rather than hidden.

## Open defects / release blockers in order

1. **A6.400 DISCOVERED→execution failure / rotation fallback.** New evidence. Repair the transition-specific watchdog and independently complete the Agent 7 rotation acceptance.
2. **Plane-D detached readback context.** A6.399au sent successfully, extension observer saw the valid envelope, but detached independent reader failed all 60 attempts while later normal-context read succeeded. Re-run the corrected probe and preserve exact read errors.
3. **Visible ChatGPT error live acceptance.** The earlier `Error in input stream` surface was invisible. Source detector/screenshot classification is committed; prove detected/cleared lifecycle and screenshot on Windows/live Firefox.
4. **Post-result turn-finalization watchdog.** A relay result can be visible while ChatGPT remains active for minutes. Implement/test a no-reexecution finalization state.
5. **Independent screenshot-to-GPT delivery.** Supervisor can capture diagnostic screenshots, but broken-primary recovery still needs a trustworthy audited way to attach/show the image to GPT.
6. **F-005 exact-packet result visibility/stale success.** Old delivery-complete state must never mask a newer visible undiscovered packet.
7. **F-001 Firefox zero-touch consumer One-Click setup and full Firefox E2E.**
8. **Chrome full One-Click E2E including injected recovery.**
9. **Edge full One-Click E2E including false-ready/postload-race acceptance.**
10. **GitHub + Google Drive connection-persistence acceptance** and approval UX verification.
11. **Fresh-chat rotation acceptance** after transition recovery is hardened.
12. Final screenshot/result/recovery evidence bundle, dated audit/index closure, and only then consideration of stable promotion.

## Agent 7 starting sequence

### A7.1 — establish truthful source + failure state
- sync `consumer/r29-firefox-offline-tray`;
- read this handoff, the dated index, mission reconciliation audit, recovery architecture, and A6.400 incident;
- compile/run recovery-supervisor and content-contract gates;
- inspect exact backend/browser lifecycle around A6.400 and prove whether any reservation/execution ever occurred;
- run the corrected detached read-context probe A6.399ay never reached;
- log any new discrepancy before changing code.

### A7.2 — harden discovery/rotation recovery
- implement/test bounded DISCOVERED→execution transition deadline;
- exact-once-aware replay decision;
- screenshot-before-mutation;
- out-of-band rotation/handoff fallback;
- prove HUD leaves stale DISCOVERED with an actionable reason.

### A7.3 — visible-error + finalization acceptance
- activate/reload current dev Firefox add-on if needed;
- live-prove ChatGPT visible-error detected/cleared lifecycle + screenshot evidence;
- implement/test `WAITING FOR GPT TURN END` / finalization-stall behavior without backend re-execution.

Then close F-005, Firefox E2E, Chrome E2E, Edge E2E, connection persistence, screenshot-to-GPT delivery, and deliberate rotation acceptance in that order unless new evidence forces an earlier recovery blocker.

## Governing evidence rule

Never convert “scheduled”, “discovered”, “parsed”, “send clicked”, “result visible”, or “child launched” into success without the next required semantic acknowledgement. A contradiction is a diagnostic event, not a reason to wait silently.

Director should not need another multi-hour manual recovery session to restore the relay.
