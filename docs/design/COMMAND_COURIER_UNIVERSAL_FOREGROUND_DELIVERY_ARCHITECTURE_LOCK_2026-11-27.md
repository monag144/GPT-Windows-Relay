# Command Courier — Universal Foreground Delivery Architecture Lock

**Status:** DIRECTOR-APPROVED / NORMATIVE DESIGN CONTRACT  
**Approved:** 2026-11-27 (PC Engineer 20)  
**Scope:** Command Courier output delivery; all future implementations, fixes, tests, integrations and PR reviews  
**Implementation status:** **NOT YET COMPLIANT** on draft PR #34. This file locks requirements, not a claim that running software already satisfies them.

## 1. Mission — what the Director actually requested

> Read an output from an explicitly authorized source. Detect a visible, writable, **empty** text field in the operator's chosen foreground window. Insert that output **once**. Where the destination has a **verifiable** Send/Submit control, activate it **once**. The destination application is irrelevant.

Representative destinations are **ChatGPT, Gemini, Claude, Grok, Discord, Telegram, Notepad, and user-built applications with/API-backed text fields**. These are examples, **not** a hardcoded list, preferred platform, or required integration.

### Two orthogonal capabilities must stay separate

1. **Source acquisition / transport:** get the output from a direct, explicit local result file, clipboard action, configured directory, authorized API, or an already completed and journaled command. No ChatGPT conversation reading is needed for universal delivery.
2. **Destination UI delivery:** discover the current foreground window, identify a safe empty editable field, insert the already-owned output and optionally activate its verified Send control. This layer must not know or care whether an app is an AI chat, messenger, ordinary editor, or custom program.

A separate, explicitly authorized command-execution or API integration can supply an output, but **neither the universal sender nor its control loop may infer executable instructions from arbitrary on-screen conversation text**.

## 2. Locked invariants (must not regress)

- **No app or conversation affinity:** no `ChatGPT.exe`-only scanner or `chatgpt.com` origin check in the **generic output acquisition/delivery path**, no fixed conversation ID/tab owner as a condition for delivery, and no application-name routing allowlist.
- **No transcript scraping as a generic source:** do not automatically scan an AI app's or messenger's conversation DOM/UIA transcript for packets, results, or instructions. An old ChatGPT-specific scanner may remain archived for compatibility analysis but is **not an approved active dependency** of the universal courier. Prefer explicit source files/clipboard or authorized documented APIs.
- **Visible foreground destination only:** use Windows' actual foreground window. Prefer the operator-focused editable control (including a child of an editable container), otherwise select a **uniquely identifiable** visible, enabled, writable field; never choose an ambiguous field.
- **Empty means empty:** check the actual writable control's value or text, **for every application** (including Notepad and rich editors). A known inert placeholder is not user content. If emptiness is unknown, stale, partially selected, read-protected, or nonempty, **do not insert**. Never overwrite or concatenate another user's text.
- **No unattended destination hop:** after field detection, retain/revalidate the same foreground HWND and focused editable element before insertion and Send; never redirect to a different conversation/window if focus changes.
- **One output, one insertion:** claim a durable saved-output ID before input. Never re-run the producing EXEC to retry delivery, never retype a saved unsent draft, never silently repeat a previously delivered result, never revive `ABORTED` after Force Clear.
- **Send only when distinguishable:** only click an unambiguous, enabled, reachable Send/Submit control in the **same** window after proving the **full exact saved output** occupies the selected field. Exactly one click attempt; no blind Enter, Ctrl+Enter, speculative keyboard fallback or button-name guessing. If no verifiable Send exists, retain the inserted content and record `TEXT_INSERTED` (ordinary editor) or `SEND_PENDING` (recognized message editor). Do **not** call insertion alone a confirmed sent message.
- **Post-send uncertainty is non-retryable by default:** an uncertain click/receipt is `SUBMIT_UNCERTAIN`; no additional click or insertion without independent evidence and an explicit operator-approved recovery path.
- **Explicit manual FORCE SEND:** button means **attempt delivery of an eligible unsent saved output** to the operator-selected foreground app; it is not a ChatGPT focus shortcut or a force-resend of an old result. Manual control is allowed when Auto Send is OFF, but must honor STOP/OFF, focus, empty-field, journal, and duplicate invariants.
- **No protected inputs:** never type into password fields, terminal/command shells, privileged input controls, or controls whose writable/visibility status is not verified. These exclusions are based on functionality, not a destination service preference.
- **Source/transport agnostic:** output may be original command stdout/stderr, an exported local text file, clipboard text intentionally copied by the user, or an authorized API result. Delivery logic does not run or inspect the provider that produced it.
- **Operator clarity:** clearly distinguish `READY`, `AWAITING_TEXT_FIELD`, `TEXT_INSERTED`, `SEND_PENDING`, `SUBMITTED`, `SUBMIT_UNCERTAIN`, `ABORTED`; never claim send success on receipt-free insertion.

## 3. Non-goals / prohibited shortcuts

- Do not build a specialized ChatGPT sender, a hardcoded Gemini/Claude/Discord/Telegram sender list, or any chat-specific hidden navigation.
- Do not scrape ChatGPT (or other third-party) text/conversation output as the automatic source for this **generic** sender. Potential platform/terms compliance concerns reinforce the preference for explicit documented sources; this design document is not a legal determination.
- Do not use a live command to restart the very engine which is supposed to deliver the command's own result; perform controlled cutover only after independently reconciled receipts.
- Do not delete, reset, stash, overwrite or contaminate the Director's active local staged changes or stable checkpoint. Work on an isolated branch/worktree until acceptance passes.

## 4. Required implementation sequence

1. **Decouple acquisition:** separate the old `Watch-ChatGPT-ActionCandidates.ps1` scanner from the active universal courier path. Provide explicit local/clipboard/API input adapters. Make app-specific legacy ingestion opt-in and outside generic delivery, if retained at all.
2. **Harden true-empty detection:** every supported editable field must be proven empty immediately before injection; otherwise leave output `READY`/blocked with a diagnostic.
3. **Preserve generic UIA selection:** prefer selected field; if not selected, unique, eligible, visible field; no application identity decisions.
4. **Retain durable exact-once insertion and send:** verified full frame, unique Send, one guarded click, independent receipt, bounded manual Send-only recovery, never duplicate.
5. **Qualify with a matrix:** ChatGPT, Gemini, Claude, Grok, Discord, Telegram, Notepad, custom writable app; focused empty, unfocused unique empty, multiple fields, nonempty field, stale focus, no Send button, icon-only Send, missing receipt, uncertain click, stop/off and duplicate attempt. Mark unsupported app controls honestly without fabricating success.
6. **Gate cutover:** full Windows unit suites + syntax parser + real cross-app GUI checks + snapshot/journal continuity. Keep draft PR and AUTO SEND OFF until verified. Preserve the original source/worktree. Integration requires a deliberate separate activation.

## 5. Known current gaps (2026-11-27)

- The **outbound** `Send-Foreground-TextResult.ps1` is designed for generic foreground UI Automation fields, but its empty-field checks are not enforced for all ordinary editor types; the requirement is **not yet satisfied**.
- The native runner still launches `Watch-ChatGPT-ActionCandidates.ps1` as its command scanner, so the complete active system remains **partially ChatGPT-specific**.
- The `FORCE SEND` HUD and journal-bound manual delivery exist in PR #34. They require live cross-app verification, especially Send control accessibility and independent submission receipts.
- Offline at commit `ee97ba8d2cc392d2b0f7f505725f9dbca9e82c62`: Python compile PASS, Windows Relay 646/646, Consumer 123/123 PASS. **769 passing tests do not certify this architecture or ToS/compliance.**

## 6. Authority and change control

This is the Director's approved design. An engineering change contradicting these invariants is a **regression**, even if unit tests pass. Propose and document a conflict before changing direction. Update acceptance evidence as the implementation advances; do **not** silently treat design lock as implementation completion.
