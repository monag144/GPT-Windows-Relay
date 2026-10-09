# GPT Windows Relay - Work Backlog

**Repository gate (PCE12):** This backlog belongs only to `monag144/GPT-Windows-Relay/main`, local checkout target `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\GPT-Windows-Relay`. Start with `docs/index/INDEX_2026-10-07T2034Z_WINDOWS_RELAY_SOURCE_OF_TRUTH.md`; use `docs/windows-relay-mission-and-roadmap.md` as the current roadmap. Do not use the retired Termux repository, its local checkout, or an obsolete/missing PCE10 roadmap as a fallback.

## Current priority / execution state

1. **P0 — Scroll / conversation-follow UX: DEFERRED.** The contained V6 attempt regressed and was reverted; the stable runtime remains scroll-v5. Do not re-enter the scroll rabbit-hole unless the Director explicitly reopens it or new evidence materially changes the problem.
2. **P1 — Windows HUD MVP: COMPLETE.** Real-state HUD and synchronized relay controls are live-proven.
3. **P2 — Zero-intervention lifecycle hardening: PARTIAL / EXTERNAL GATE.** Backend-only restart recovery is live-proven. Full Firefox restart and Windows/login restart cannot be honestly closed while the development workflow depends on a temporary Firefox extension. Production continuation requires a Mozilla-signed persistent XPI and policy install.
4. **P3 — Clipboard + difficult job-application helper foundation: COMPLETE.** Clipboard, exact semantic field entry, resume mapping, and reasoning handoff loop are live-proven.
5. **P4 — Screenshot-on-request capability: COMPLETE.** Explicit bounded capture, authenticated return to ChatGPT, and post-delivery cleanup are live-proven.
6. **P5 — Broader Windows UI interaction adapters: COMPLETE.** Semantic UIA, Firefox tab adapter, and fixed-allowlist workflow composition with bounded visual fallback are live-proven.
7. **Next actionable mission:** remove the P2 external gate by obtaining/installing a signed persistent Firefox extension, then validate full Firefox restart and Windows/login restart with zero manual recovery.

## Completed
- [x] Parser v2: command, command_b64, command_lines.
- [x] Native Python execution with UTF-8 stdout/stderr.
- [x] Base64 retained as permanent fallback transport; Python is preferred for complex orchestration, but `command_b64` remains the resilience/compatibility path.
- [x] PowerShell CLIXML progress filtering.
- [x] Assistant-only ChatGPT DOM trust boundary.
- [x] Stable persistent-extension ID: gpt-windows-relay@local.
- [x] Persistent extension v0.2.0 contains no relay secret.
- [x] One-time Firefox local-storage pairing UI.
- [x] Reproducible XPI builder.
- [x] Firefox policy template for signed XPI.
- [x] Per-user relay watchdog registered in HKCU Run.
- [x] Watchdog self-heals relay every 60 seconds.
- [x] Explicit pause sentinel prevents unwanted auto-restart.
- [x] Relay start/stop/restart/pause/resume controls.
- [x] 360/Qihoo live + historical artifact sweeps.
- [x] Code Integrity block correlation.
- [x] Compact relay results by default; full stdout/stderr persisted locally.
- [x] Explicit `result_mode: "full"` escape hatch.
- [x] Event-driven browser scanner V8 with mutation-local discovery.
- [x] Bounded browser attempted-packet history and low-frequency recovery scan.
- [x] Browser performance contract tests.

## Next browser UX requirements
- [x] **Jump to last relay command on recovery/load implemented in scanner V9.** When the ChatGPT tab or relay content script loads/reloads, locate the newest assistant turn containing a valid `[GPT_WINDOWS_ACTION]` packet and perform a **single one-shot scroll** that brings that command into view. Do not reintroduce continuous whole-page autoscroll or observer-triggered full-history scanning. Manual user scrolling must remain authoritative after the one-shot recovery jump.
- [ ] **P2 external gate:** Zero-intervention full Firefox restart/recovery. Backend-only recovery is already GREEN; full Firefox restart still requires the signed persistent extension/policy path.
- [x] Persistent extension restores its saved relay token from `chrome.storage.local`; browser action requests retry transient localhost failures for 45 seconds and recover completed results by operation ID.
- [ ] **P2 validation remaining:** full Firefox restart and Windows/login restart. Backend-only restart is already GREEN; both remaining tests depend on the signed persistent extension.
- [x] Browser contract/regression coverage added for one-shot recovery scroll, bounded scanner behavior, persistent pairing storage, and backend action retry.
- [~] **DEFERRED P0 history:** Live-test scanner V9 one-shot recovery scroll after extension reload; superseded by later V11/scroll-v5 work and the contained V6 defer decision.
- [x] V11 continuous operation proven across successive actions with no manual reload/refresh between actions.
- [x] Relay handoff auto-scroll UX implemented and staged in persistent extension v0.3.4; bounded 8-second follow window yields back to manual scrolling afterward.
- [~] **DEFERRED / SUPERSEDED P0 history:** V4 runtime activation/handoff proof was overtaken by later V11/scroll-v5 delivery work; P0 is intentionally deferred after the contained V6 regression/revert.
- [x] Live-test action retry across an intentional backend restart while the browser extension remains loaded.

## User-interaction gate
- [ ] Submit dist\gpt-windows-relay-0.3.0.xpi to Mozilla Add-ons as an UNLISTED extension and download the signed XPI.
- [ ] Save signed package as dist\gpt-windows-relay-signed.xpi.
- [ ] Install Firefox policy using install-signed-extension-policy.ps1 (may require elevation).
- [ ] Restart Firefox once; pair using copy-pairing-token.ps1; arm relay.

## Final validation
- [x] Verify backend-only restart recovers relay without manual intervention.
- [ ] Verify signed extension survives Firefox restart.
- [ ] Verify policy auto-reinstalls signed XPI if profile registration disappears.
- [x] Run native Python command_lines end-to-end probe.

- [x] Worker-driven handoff scroll V4 staged in persistent extension v0.3.7 with runtime identity telemetry.
- [~] **DEFERRED / SUPERSEDED P0 history:** temporary-extension V4 activation target was superseded by later V11/scroll-v5 delivery-v8 runtime work.
- [~] **DEFERRED P0 history:** handoff-scroll validation remains intentionally deferred with P0.


## HUD mission
- [x] **P1:** Define minimal Windows HUD state model.
- [x] **P1:** Show relay ARMED/DISARMED and backend health.
- [x] **P1:** Show Firefox bridge/content-script runtime state.
- [x] **P1:** Show current/last action and compact error state.
- [x] **P1:** Add synchronized pause/resume or arm/disarm control tied to actual relay state.

## Future interaction branches
- [x] **P3:** Add clipboard read/write primitives suitable for copied application prompts and generated answers.
- [x] **P3:** Add explicit semantic target-field text entry primitive with exact UIA matching and read-back verification.
- [x] **P3:** Define resume-data representation for field/value lookup and reasoning.
- [x] **P3:** Build simple difficult-job-application loop: copied app context -> ChatGPT reasoning -> relay text/field input.
- [x] **P4:** Add explicit screenshot capture primitive for screen/window/region.
- [x] **P4:** Add screenshot return path suitable for ChatGPT visual inspection.
- [x] **P4:** Add bounded cleanup/storage policy; no continuous screenshot feed by default.

- [x] **P5:** Add fail-closed semantic UIA control discovery/invoke/select/toggle adapter.
- [x] **P5:** Live-prove semantic inspect/invoke/select/toggle against a disposable synthetic UI.
- [x] **P5:** Add first app-specific adapter using semantic controls, with visual fallback only when necessary.
- [x] **P5:** Define optional higher-level workflow composition after app-specific proof.
- [x] **P5:** Live-prove workflow composition across clipboard + Firefox + semantic UIA and fail-to-screenshot fallback.

- [x] **P2:** Build and validate current unsigned persistent XPI; add environment-only unlisted AMO signing automation.

- [x] **P2:** Install/verify local Node + npx + web-ext signing toolchain without requiring elevation.

- [ ] AUTONOMY: eliminate manual browser refresh after runtime deploy/rollback; relay must autonomously re-establish browser runtime ownership without duplicate delivery.


  - PCE8.7 proof: fresh relay action succeeded without the requested manual refresh; manual refresh request was unnecessary user action. Keep the autonomy task open until browser-runtime ownership handoff is deterministic after every deploy/rollback.

## PCE8 browser-session reliability gates — 2026-10-06
- [x] PCE8.23B: retire backend-completed packet before result-delivery ambiguity.
- [x] PCE8.29C: expire and conversation-scope durable recovery obligations; full suite 271/271.
- [ ] PCE8.26B SESSION ESCAPE: deterministic managed-conversation reacquisition after extension reload, page reload, rollback, and tab/context loss.
- [ ] Redesign canary so it owns its fresh discovery/execution/result proof instead of waiting for an unissued future packet.
- [ ] Browser acceptance must verify the exact expected conversation in addition to runtime identity.
- [ ] Do not deploy v15 until the three browser-session requirements above have regression coverage and source validation.
- [ ] Whole-product STOP/quiescence remains open.

## Reliability recovery checkpoint — 2026-10-06T2126Z

- [x] Reproduce the Director-observed sustained-forward-progress failure on protected live v11.
- [x] Prove PCE8.61 completed before stale draft recovery reacquired its packet ID.
- [x] Prove failed draft recovery leaked `activeRelayOperationId` and blocked PCE8.62 for multiple minutes.
- [x] Fix the general draft-recovery owner-release invariant in source runtime v16 (`694d47ab89596d5c3801f749caa352b951a2be52`).
- [x] Regression validation: 55 browser-contract tests, 273 Windows-relay tests, 99 consumer tests PASS under canonical suite environments.
- [ ] Guarded live v16 activation on the exact persisted engineering conversation.
- [ ] Fresh v16 exact roundtrip with exact-route proof and no duplicate Windows execution.
- [ ] Explicitly exercise a failed/deferred draft-recovery attempt and prove the next packet is not stranded behind stale ownership.
- [ ] Sustained multi-operation v16 soak with intervention count recorded.
- [ ] Promote v16 to protected live baseline only after the above runtime gates pass.
- [ ] Restore/reconcile the modern HUD only after the browser reliability baseline is stable; live HUD remains the rollback-era implementation.
- [ ] Close whole-product STOP so browser timers, result delivery, recovery refresh, deferred drains and watchdog resurrection all quiesce while stopped.

**Priority note:** R0 sustained relay forward progress remains ahead of the signed-XPI / restart-validation P2 external gate. P2 is still required, but it is not the next engineering action while browser forward progress is not yet accepted.

## PCE8 v16 acceptance status — 2026-10-06T22:19Z

- [x] Guarded v16 live Firefox canary.
- [x] Failed-draft owner-release path live proven.
- [x] Post-release exact-once forward progress proven.
- [x] Five-operation sustained soak proven with zero active-operation starvation.
- [ ] General stale-owner lease/deadman acceptance.
- [ ] Whole-product STOP semantics.
- [ ] Restart/signing/browser-matrix acceptance.
- [ ] Safe managed-conversation rotation.
- [ ] Separately guarded modern-HUD recovery.
- [ ] Audit local/remote divergence before any push.

## PCE8 ownership recovery closure — 2026-10-06T22:36Z

- [x] Failed-draft owner release live proven.
- [x] General five-minute stale-owner lease/deadman live proven.
- [x] Pre-expiry owner retention live proven.
- [x] Exact-replay and exact-visible stale-owner release branches live proven.
- [ ] Whole-product STOP semantics.
- [ ] Restart/signing/browser-matrix acceptance.
- [ ] Safe managed-conversation rotation.
- [ ] Separately guarded modern-HUD recovery.
- [ ] Audit local/remote divergence before any push.

## PCE9 reconciliation checkpoint — 2026-10-07
- [x] Result-confirmation selector/role-gate defect live-proven fixed with exact-once delivery canaries.
- [x] Browser stop-generation/quiescence protocol live-proven; STOP -> START acceptance returned with verified browser quiescence.
- [x] Rich HUD control surface restored live with START/STOP/RESTART/OFF/KILL/MINIMIZE.
- [x] Dual-runtime ownership diagnosed: 8766 control plane and isolated 8767 consumer runtime are intentional.
- [x] Dedicated 8766 control-launcher split implemented and deployed to the current live tree.
- [ ] Reconcile the richer HUD with canonical RETRY support; RETRY exists in Windows-repo source but is absent from the current richer live HUD.
- [ ] Reconcile any remaining PCE9 Windows behavior using provenance and evidence already migrated into `monag144/GPT-Windows-Relay`; preserve newer Windows changes. Do not reopen, fetch, or modify the retired Termux repository.
- [ ] Complete canonical STOP -> START ancestry acceptance proving restarted 8766 is owned by `run-control.ps1`; the pending attempt was interrupted during harness repair.
- [ ] Enforce operation-series rollover so no future managed series can emit OP101.
- [ ] Signed persistent Firefox XPI/policy and full Firefox + Windows/login restart acceptance remain open.
- [ ] Chrome and Edge clean-consumer browser-matrix acceptance remain open.
