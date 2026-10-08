# Archived source fragment 15/23 — 2026-10-08T0752Z

The backend now retries transient `PermissionError`/Windows sharing violations during atomic `os.replace` with bounded exponential backoff. State mutations also snapshot and roll back in-memory state when persistence fails, preventing a failed reservation/mark from later becoming a ghost record during an unrelated successful save. Failure-injection tests cover both behaviors. Action 262 is not re-executed because its exact execution boundary is not sufficiently proven; the scheduled backend restart will conservatively convert the stale `INFLIGHT` reservation to `INTERRUPTED_RESTART`.


## AUDIT — PC Engineer 3 operations 260–264

- 260 armed the proven structurally bound Firefox activation helper behind an exact result-delivery gate.
- 261 proved delivery-v7 live with fresh `v11-scroll-v5-delivery-v7` content telemetry and both v7 markers present.
- 262 reached the backend promptly but returned a raw `PermissionError`, revealing a separate backend persistence defect rather than the old browser starvation path.
- 263 ruled out result-directory ACL failure and showed no persisted Action 262 result.
- 264 showed Action 262 as stale `INFLIGHT`, found an abandoned `.state.json.*` atomic-write temp file, and proved atomic create/replace currently succeeds in both state and result directories.


## Hardened backend activation + delivery-v7 handoff proof — GREEN

Action 265 staged and committed transient-lock persistence hardening, then armed a backend restart only after browser delivery completion. Action 266 reached the replacement backend, proving browser-to-backend continuity. The helper replaced listener PID 14312 with 8800, the live backend contains atomic replace retry and state rollback safeguards, and stale Action 262 was conservatively reconciled to `INTERRUPTED_RESTART` without re-execution.

The same 265→266 transition provides the renewed delivery-v7 regression: Action 265 was confirmed by `generation_started`, produced zero send retries and zero long idle waits, and Action 266 reached the backend without draft/active-owner deferral. The stale-owner/out-of-order behavior observed at 252→253 did not recur.


## INCIDENT — Action 267 live-proof import harness defect

Action 267 created the P3 helper, passed the full source test suite, and staged it live, but its synthetic live-proof harness loaded `job_application_helper.py` with `importlib.util.spec_from_file_location` without adding the live relay directory to `sys.path`. The helper therefore could not resolve sibling module `resume_profile` and the operation stopped before any P3 commit or real application interaction. Action 268 corrected only the proof harness by reproducing normal script module resolution; no product fallback or path hack was added.


## P3 simple difficult-job-application loop — GREEN

Added `job_application_helper.py` as a small orchestration layer over the proven clipboard, resume-profile, and semantic UIA primitives. Exact factual fields resolve deterministically; mapped-but-empty facts stop as `missing_profile_data`; subjective or unmapped prompts return a structured `needs_reasoning` packet with copied application context, local profile context, and explicit no-invention constraints. Only a separate explicit apply step can write an answer to a semantically identified field.

The live proof used synthetic data only: clipboard text `E-mail address` resolved to `ada@example.invalid` and was written/read back through a disposable WPF field; a subjective `Why do you want to work here?` prompt stopped at `needs_reasoning` without generating or applying an answer. The original clipboard was restored and all synthetic proof artifacts were removed. P3 is complete.


## INCIDENT — Action 269 screenshot bitmap constructor parsing defect

Action 269 passed the source test suite and staged the initial P4 capture implementation, but its synthetic window proof failed before image creation because PowerShell `New-Object System.Drawing.Bitmap $w,$h,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb` parsed the enum expression as a string. No normal desktop capture occurred. Action 270 replaced that expression with the direct .NET constructor `[System.Drawing.Bitmap]::new(...)`; no fallback capture mechanism was introduced.


## P4 screenshot capture + bounded storage foundation — GREEN

Added an explicit on-request PNG capture primitive supporting the Windows virtual screen, one exact visible top-level window (optionally PID constrained), or an explicit rectangle. Captures are written only to `%LOCALAPPDATA%\GPTWindowsRelay\screenshots`; default retention is at most 20 PNG files and 24 hours, enforced during capture, with no background timer or continuous feed. Results include target bounds, MIME type, byte count, SHA-256, managed path, and retention status. Action 270 proved exact-window capture against a disposable synthetic WPF window and deleted the proof PNG afterward. The remaining P4 item is the return path suitable for ChatGPT visual inspection.


## AUDIT — PC Engineer 3 operations 265–269

- 265 added transient atomic-replace retry plus state rollback and armed the post-delivery backend restart.
- 266 proved hardened backend activation and delivery-v7 handoff GREEN; stale 262 was reconciled as `INTERRUPTED_RESTART` without re-execution.
- 267 built the P3 job helper but its live-proof import harness failed before commit.
- 268 corrected only the proof-loader issue, completed synthetic deterministic-field + reasoning-stop proof, and closed P3 at `9f08e395`.
- 269 staged P4 capture/retention but exposed a PowerShell bitmap-constructor parsing defect during the synthetic-window proof; no ordinary desktop image was captured.


## Delivery-v8 screenshot transport regression suite — GREEN

Actions 271–274 exposed only browser-contract test drift while staging the screenshot return path. Six tests still searched for the v7 function signature after `injectConfirmed` gained an attachment parameter, and one additional assertion still searched for the old two-argument call site. Action 275 updates that final stale assertion to the v8 call `injectConfirmed(r.result,p.id,r.attachments||[])`; the complete Windows relay test suite is GREEN and the source has been synchronized to the live tree. No backend restart or Firefox content-runtime reload has occurred yet, so delivery-v8 is staged but not activated.


## AUDIT — PC Engineer 3 operations 270–274

- 270 corrected the PowerShell bitmap constructor, proved exact-window PNG capture live against a disposable WPF window, deleted the proof image, and committed bounded P4 capture/retention at `a864cb72`.
- 271 staged the authenticated one-shot screenshot return architecture but stopped before commit when legacy browser-contract tests failed.
- 272 showed the failing tests were stale source-boundary assertions after the deliberate v8 `injectConfirmed(...,attachments=[])` extension; v8 implementation markers were present.
- 273 updated six legacy signature searches, then stopped because one separate assertion still expected the old two-argument `injectConfirmed` call.
- 274 isolated that sole remaining failure exactly; no additional implementation defect was demonstrated.


## AUDIT — PC Engineer 3 operations 280–284

- 280 enumerated Firefox UIA tab identities and established exact visible browser-tab names for `Debugging - Runtime / this-firefox` and `PC Engineering 3`.
- 281 armed a structural Firefox-only activation helper, but the generated PowerShell contained a syntax defect and therefore never entered its helper body.
- 282 correctly detected that no `HELPER_STARTED` record or fresh v8 telemetry existed; Firefox remained unchanged.
- 283 attempted a read-only PowerShell parser probe, but the probe itself supplied the parser path incorrectly and did not resolve the helper syntax failure.
- 284 corrected the parser invocation and localized the actual Action 281 helper defect to line 25: a nested `New-Object PropertyCondition(...)` expression inside `FindAll(...)` was missing a closing parenthesis.


## INCIDENT — Action 281 activation helper syntax defect

The Action 281 scheduled helper never executed because of an assistant-authored PowerShell syntax error in the ListItem condition used for extension-card discovery. Task Scheduler returned exit code 1 before `HELPER_STARTED`, so no Firefox selection, extension reload, or ChatGPT refresh occurred. Action 285 replaces the nested expression with a separately constructed UI Automation condition and parser-validates the complete helper before scheduling it.


## Delivery-v8 full backend + Firefox activation — GREEN

