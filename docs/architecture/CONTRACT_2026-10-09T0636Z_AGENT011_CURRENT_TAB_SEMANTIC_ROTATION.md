# Agent011 semantic PCE11 → PCE12 rotation contract — 2026-10-09T0636Z

Canonical director override. Supersedes the historical two-window handoff destination for current operations; keep that design as evidence only.

## PCE11/PCE12 semantic rotation: SAME CURRENT TAB ONLY — Director override 2026-10-09

**User-intent invariant (P0):** "New chat" means click ChatGPT's **New chat** control in the **same ChatGPT tab currently originating this relay conversation**. The existing browser window and tab are reused. There must be **zero calls to open a new tab, launch a new Firefox window, choose a separate destination window, or infer destination from the number of Firefox tabs**. The former distinct-window PCE11 handoff architecture and its historical pinned handoff document are superseded for the active workflow; retain those documents as incident evidence, never as the actionable rotation plan.

**Current-tab identity, not window heuristics:** Before any action, positively identify the selected tab that contains the current relay source conversation and this exact recent relay action/result exchange. Bind **that tab** to its canonical ChatGPT `/c/...` address, selected-tab automation element, hosting window HWND/PID, and observed command/result marker. Unrelated Firefox windows must not be enumerated as destinations, brought to foreground, or checked for `chatgpt.com/`. A foreground window or an 11-tab count is **not proof** of the invoking tab. If origin is ambiguous, identity changed, or new conversation already received the handoff, stop without action.

**Exact same-tab handoff sequence:**
1. Read mandatory governance controls, verify `engineering_preflight`, latest audits/reviews, canonical source commit and STOP/armed/outbound owner, and any unique previous attempt receipts. Never replay prior uncertain side effects.
2. Pin sender tab and unsent draft. **Do not overwrite or discard an existing draft silently.** The user specifically authorized current-tab New Chat, but preserving or reporting existing draft text remains mandatory.
3. **Once**, semantically invoke the unique **New chat** control inside the pinned *same* selected tab. If it is already a blank ChatGPT home/new-chat composer, skip this click. Verify the **same window HWND and same selected tab** after navigation, no popup or extra tab.
4. Focus **that same tab's** unique visible writable composer; paste the byte-verified PCE12 handoff once; verify exact editor readback and one enabled Send control. Store exclusive durable `click/paste/Send intent` receipts **before each corresponding effect**.
5. Send **once**, then verify a distinct `/c/...` URL and actual **user-role message** containing unique handoff markers in the *same tab*. A worker launch, Clipboard.SetText or new-chat homepage is **not** delivery.

**Hard prohibitions:** no `--new-window`, `--new-tab`, separate Firefox destination, new tab/window construction, 11-tab target heuristic, foreground-only target selection, global Firefox focus loop, or assuming a prior message was sent without positive source-specific proof. Do not repeat failed PCE11.074/.076/.083 workers. Source code and tests must reflect this contract before a new live attempt.
