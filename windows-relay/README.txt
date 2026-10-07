GPT Windows Relay browser-side repair — 2026-10-01

What this fixes
- Removes the broken HUD V1 code from the core content script failure domain.
- Removes hud.js from both extension manifests and disables any existing hud.js file.
- Replaces the full-history MutationObserver scanner with an incremental scanner.
- Keeps the assistant-only trust boundary.
- Keeps automatic scrolling disabled.

Performance changes
OLD:
- Every ChatGPT DOM mutation called scan().
- scan() queried all assistant turns and walked backward through history.
- HUD added a second page-wide MutationObserver and repeated assistant scans.
- HUD also polled every 2 seconds.

NEW:
- One MutationObserver only.
- Mutation callback only queues the assistant turn that actually changed.
- Streaming mutation storms are coalesced with a 200 ms flush.
- Packet completion is settled for 500 ms before execution.
- Uses textContent instead of innerText to avoid forced layout/reflow.
- Fallback poll every 5 seconds inspects only the newest 4 assistant turns.
- Startup recovery scans only the newest 6 assistant turns once.
- No HUD is loaded.

Validation
- content.js passed `node --check` before packaging.
- Expected SHA-256 of packaged content.js:
  5517B413FF62577565805A5C17D8E841EA9D747B298DA17F916A85B932F70984

Install
1. Extract this ZIP.
2. Right-click PowerShell / open a PowerShell prompt in the extracted folder.
3. Run:
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-browser-fix.ps1
4. In Firefox open about:debugging#/runtime/this-firefox.
5. Reload GPT Windows Relay.
6. Refresh ChatGPT once.

The installer backs up the current live and persistent content.js, manifest.json,
and any hud.js before changing them.
