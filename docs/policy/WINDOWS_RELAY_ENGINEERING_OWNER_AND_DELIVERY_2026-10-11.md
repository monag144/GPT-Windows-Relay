# Windows Relay engineering owner and source delivery — 2026-10-11

**Current operator direction:** ChatGPT is the primary engineer and working owner for Windows Relay source changes. Codex is a specialist escalation for major breakage and heavy engineering, preferably launched through a functioning authorized Windows Relay; otherwise the operator may launch Codex manually. Creating a GitHub issue does not launch Codex.

**Development source:** `monag144/GPT-Windows-Relay`, active work branch `wip/windows-relay-rebuilt-resynced-2047-101026`. Windows source checkout: `%USERPROFILE%\Downloads\Dev\GPT-Windows-Relay-Main-Build`. Current Firefox release source: `windows-relay/extension-persistent/`.

**Default delivery workflow:** ChatGPT inspects and edits actual GitHub source, verifies changes as far as available tools allow, pushes to the active development branch and provides a safe, explicit **pull command** for the Windows checkout *after* the remote commit is verified. Do not defer routine code modifications to Codex. Do not claim Windows installation changed until the actual pull succeeds.

**Operator pull command (CMD):**
```bat
git -C "%USERPROFILE%\Downloads\Dev\GPT-Windows-Relay-Main-Build" pull --ff-only origin wip/windows-relay-rebuilt-resynced-2047-101026
```
No force pushes, hard resets, silent stashes, checkout replacement, dropped uncommitted work, or mutation of the protected historical Client. A conflict or dirty checkout must be reported, not overwritten.

**Relay is the preferred delivery transport, not a prerequisite.** Use the authenticated, positively bound relay to issue the pull only after it is demonstrably reachable and the operator has approved the action. If the relay is offline, give the same command for local operator-controlled CMD/PowerShell. An offline relay cannot execute a command to restart itself. Runtime restart, Firefox reload, Client cutover, and live canaries remain separate approved actions, not implied by git pull.

**Role separation:** ChatGPT owns GitHub source engineering; the human operator owns Windows permissions, consequential actions and deployment approval; the authenticated runtime conversation owner identifies the legitimate ChatGPT tab/session and must not be silently re-bound by an engineering policy. STOP, pairing, owner binding and durable action identity are still security protections.

**No execution governance.** Engineering documentation, reviews, audit receipts or operation counts never gate Windows command execution. Historical six-failure Codex escalation recommendations are optional heuristics, not requirements. Codex is used based on severity and practical engineering needs.

**Source evidence:** Main-Build launcher/controller/supervisor are self-relative; historical `install-browser-fix.ps1` still defaults to `GPT\Client\Relay`, and `install.ps1` still targets the sibling extension tree. Codex Issue #28 observed no listener on localhost:8766 and could not verify the loaded Firefox extension, so a running old backend has not been proven. Issue #27 tracks the independent browser-to-backend identity protocol mismatch.
