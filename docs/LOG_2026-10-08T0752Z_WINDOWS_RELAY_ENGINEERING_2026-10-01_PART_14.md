# Archived source fragment 14/23 — 2026-10-08T0752Z

- 241 proved delivery-v6 truly active with helper GREEN, one card-scoped Reload, ChatGPT document reload, and fresh `content_script_started` telemetry carrying `v11-scroll-v5-delivery-v6`.
- 242 armed a backend restart helper gated on browser `relay_result_delivery_complete` for that exact packet.
- 243 proved backend-only lifecycle recovery end to end: PID 8472 was replaced by PID 14312 and the next browser action reached the recovered backend without browser lifecycle intervention.
- 244 records the proof, updates the P2 checklist, and inspects signed persistent-extension readiness before any destructive Firefox restart.


## P2 signed persistent-extension gate — external prerequisite

Action 244 confirmed the backend-only restart path is GREEN, but full Firefox restart and Windows/login restart cannot be safely validated yet. No `gpt-windows-relay-signed.xpi` exists in the repo or live tree, no Mozilla Firefox enterprise policy is installed under HKLM/HKCU, and no persistent `gpt-windows-relay@local` registration was found in the active Firefox profile. The currently working relay is a development-only temporary add-on, which Firefox removes on full restart.

Therefore full Firefox/Windows restart validation is explicitly gated on Mozilla unlisted signing plus persistent policy installation. Do not destroy the live temporary add-on merely to demonstrate the known failure mode. Continue non-blocked roadmap work while this external prerequisite remains unresolved.


## P3 clipboard read/write primitives — GREEN

Added dependency-free native Win32 Unicode clipboard primitives in `windows-relay/windows_tools.py`: explicit read, write, and clear operations with bounded OpenClipboard retry behavior. Full relay tests passed, `sync-live.py` staged the adapter into the live relay tree, and an explicit Unicode round-trip succeeded. The pre-existing clipboard text was restored after the proof.


## P3 semantic target-field text entry — GREEN

Actions 246–252 added and live-proved fail-closed semantic Windows UI Automation text entry. WinForms was rejected as a proof target because its TextBox surfaced as `ControlType.Pane` without `ValuePattern`; no unsafe fallback was added. A WPF harness exposed exactly one visible enabled `ControlType.Edit` with Name `Application Answer`, AutomationId `application_answer`, and `ValuePattern=True`. Action 251 then exposed one implementation defect: PowerShell requires the variable passed by `[ref]` to exist before `TryGetCurrentPattern`, so `[ref]$pattern` failed because `$pattern` was undeclared. Action 252 initializes `$pattern=$null`, adds regression coverage for that requirement, re-stages the live primitive, successfully sets the Unicode value using `ValuePattern.SetValue`, and verifies exact read-back.


## AUDIT — PC Engineer 3 operations 250–252

- 250 proved the WinForms TextBox compatibility boundary: it surfaced as a Pane and provided no ValuePattern.
- 251 proved the WPF harness exposes the intended semantic UIA contract and isolated the remaining failure to an undeclared PowerShell `[ref]` variable.
- 252 repaired that defect, added regression coverage, re-staged live, and completed exact semantic field-entry/read-back proof.


## P3 resume-data representation and deterministic lookup — GREEN

Added `resume_profile.py` with schema versioning, local JSON loading/validation, normalized exact aliases for common factual application fields, exact normalized custom-field lookup, and an explicit `needs_reasoning` path for unmapped questions. The default representation covers identity/contact/links, work authorization, experience, education, certifications, skills, availability, and custom factual fields; it does not commit any real resume data. Unknown prompts are never guessed: they return structured resume context for higher-level reasoning. Full relay tests and live staging passed, and a synthetic local profile proved deterministic aliases, valid False booleans, custom lookup, and the reasoning handoff.


## AUDIT — PC Engineer 3 operations 250–254

- 250 proved the disposable WinForms field surfaced as `ControlType.Pane` without `ValuePattern`, establishing that it was an unsuitable semantic text-entry proof target.
- 251 proved the WPF harness exposed exactly one visible enabled Edit with the expected Name/AutomationId and `ValuePattern=True`; the remaining defect was an undeclared PowerShell variable passed by `[ref]`.
- 252 initialized `$pattern=$null`, added regression coverage, re-staged live, completed exact semantic field write/read-back proof, and pushed commit `169a9a1`.
- 253 was issued for the resume-data foundation, but the user received a stale duplicate result for Action 252 instead.
- 254 proved Action 253 never reached the Windows backend: no saved 253 result exists and no backend state entry was present.


## INCIDENT — stale Action 252 delivered instead of issued Action 253

User-visible symptom: after Action 253 was issued, the browser submitted the previously completed Action 252 result again. Action 254 proved Action 253 had no backend result and therefore did not execute. This is a browser-side continuity incident and required user-visible rescue.

Action 256 provisional classification was `CONFIRMED_DEFERRED_PACKET_LOST_NO_QUEUE`; Action 257 superseded the permanent-loss portion of that conclusion because Action 253 later executed successfully and pushed commit `56aa655`. The confirmed failure mode is delayed/out-of-order execution while an older result retains browser delivery ownership.


## INCIDENT — Action 255 diagnostic syntax error

Action 255 failed before execution because the generated Python diagnostic omitted a closing parenthesis in a `print()` statement. No repo mutation occurred. This was an avoidable assistant-authored relay-command defect; Action 256 reruns the intended diagnostic with corrected syntax.


## Delivery-v7 root cause and staged repair

The 252→253 incident showed that Action 252 was submitted once, but delivery confirmation timed out even though its composer payload was no longer present. While ChatGPT generated the next assistant turn, the old result retained `activeRelayOperationId`, waited for generation to stop, and later retried the already-submitted 252 result. Action 253 was consequently delayed and eventually executed out of order rather than being permanently lost.

Delivery-v7 adds two narrow safeguards: (1) after the existing pre-send idle gate, a cleared relay payload plus the appearance of the ChatGPT generation stop control is treated as positive acknowledgement that the send was accepted (`method:generation_started`); and (2) packets encountered while a draft or another operation owns the channel are stored in a bounded 16-entry deferred-action queue and explicitly drained when ownership is released. This removes dependence on a later DOM recovery scan for deferred command survival.


## AUDIT — PC Engineer 3 operations 255–259

- 255 failed before execution due to an assistant-authored Python syntax error; no repo mutation occurred.
- 256 reran the diagnostic, committed the then-provisional deferred-packet incident classification, and exposed the long 252 delivery retry interval.
- 257 proved Action 253 eventually executed successfully, changing the diagnosis from permanent loss to delayed/out-of-order execution.
- 258 compact state-machine probe backend-result presence at Action 259 time: `True`.
- 259 stages delivery-v7 with generation-start acknowledgement and a bounded explicit deferred-action queue, plus regression tests and package version 0.3.16.


## Backend atomic persistence transient-lock hardening

Action 262 reached the v7 browser/backend path but returned HTTP `PermissionError` before a normal relay result was persisted. Actions 263–264 localized the failure to backend persistence: the result directory was writable, Action 262 had no saved result, its state later appeared as `INFLIGHT`, and a stranded `.state.json.*` temporary file existed. Harmless atomic replace probes subsequently succeeded, establishing a transient Windows file-lock/replace failure rather than a persistent ACL denial.

