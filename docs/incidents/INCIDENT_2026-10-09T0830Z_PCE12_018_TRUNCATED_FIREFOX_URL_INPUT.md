# PCE12.018 — Firefox address-bar URL input truncated (2026-10-09 08:30Z)

## Receipt
- Packet: `PCE12.018-firefox-home-and-adapter-greeting`, Windows Relay `EXEC` PowerShell, `COMMAND_FAILED`, exit 1, duration 17,690 ms; ordinal consumed.
- Displayed initial URL: `chatgpt.com/c/6ac88ea9-3d7c-83e8-9784-f3794c920263` in Firefox's native address-bar `AutomationId=urlbar-input`.
- Script focused address bar using Ctrl+L and tried character-oriented `[System.Windows.Forms.SendKeys]::SendWait('https://chatgpt.com/')` followed by Enter.
- During next 14 seconds it read `NEW_CHAT_URL=tgpt`, **not** a verified root URL. `NEW_CHAT_URL_NOT_VERIFIED_NO_GREETING` prevented all composer and send actions. No greeting was sent.

## Interpretation and containment
- `tgpt` is direct proof that **the actual address-bar readback was not the requested complete URL**. Causes may include dropped simulated characters, focus transition, key interpretation or browser behavior; the precise cause is not established. Avoid repeating per-character SendKeys URL entry and guessing success from Firefox title.
- Next operation `PCE12.019`: foreground exactly one Firefox window, select address bar, paste the complete URL with a guarded clipboard, and verify the **entire pending address-bar value before Enter**. Restore previous clipboard. After Enter verify root URL, single visible ChatGPT composer and exact draft prior to any send. A submitted message must never be replayed on uncertain proof.
- Continue using GitHub canonical controls and audit cadence. Prior verified governance repair `PCE12.017` installed GitHub-backed legacy audit for .010-.014; did not disable checkpoints. Next five-operation audit is for .015-.019 before issuing .020, followed by the nonblocking 20-operation review.
- No user rescue required by this operation; no GitHub Actions, Termux, or Windows repo mutation occurred.
