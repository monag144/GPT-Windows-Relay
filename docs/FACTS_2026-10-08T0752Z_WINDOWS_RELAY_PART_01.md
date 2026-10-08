# Archived source fragment 1/3 — 2026-10-08T0752Z

# Windows Relay Established Facts — Compatibility Knowledge Base — 2026-10-08T0650Z

Snapshot: `2026-10-07T2034Z`

This is the canonical short-form knowledge base for the Windows↔ChatGPT Firefox relay.

**Before starting new relay debugging or forensics, read this file and the engineering log first.** Do not rediscover facts already proven here unless new evidence directly contradicts them.

Current chronology and proof live in:
- `docs/windows-relay-engineering-log-2026-10-07.md`

Historical chronology is frozen in:
- `docs/windows-relay-engineering-log-2026-10-01.md`

## Canonical project locations

- GitHub repository: `monag144/GPT-Windows-Relay`
- Production/default branch: `main` (not the current engineering head)
- Active engineering branch: `pce10/reconcile-control-and-rotation` (249 commits ahead of `main` at source snapshot `5dac27c`)
- **Do not infer active runtime version from either branch:** PCE10.037 has not proved loaded Firefox code or the current tab identity.
- Canonical local clone: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\GPT-Windows-Relay`
- Active live relay tree: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay`
- Temporary Firefox manifest: `C:\Users\<LOCAL_USER>\Downloads\Dev\GPT\Client\Relay\extension\manifest.json`
- Persistent-extension source: `...\Client\Relay\extension-persistent`
- Current engineering log: `docs/windows-relay-engineering-log-2026-10-07.md`
- Frozen historical log: `docs/windows-relay-engineering-log-2026-10-01.md`

GitHub is the canonical engineering/audit record. Confirmed findings, root causes, fixes, false leads worth remembering, and proof of validation should be logged there.

## Proof-reuse / no-rediscovery rule

Established facts are reusable evidence, not suggestions to rediscover the same state. Re-run a Firefox restart/temporary-extension/profile/continuity probe only when a browser-affecting mutation occurred, contradictory evidence appeared, or a specific acceptance gate requires it. Routine source-only, documentation-only, or Git-only work must not re-prove unchanged Firefox state.

Before any Windows mutation or push, verify that the active repository is `monag144/GPT-Windows-Relay`; the old Termux repository is not a valid Windows destination.

## Relay packet / rendering contract

Canonical procedure: `docs/relay-sandwich-procedure.md`.

Every Windows relay command shown in ChatGPT must use the **sandwich technique**:

1. ordinary visible prose header;
2. one bare Markdown fenced block with no language tag;
3. inside the fence, only:
   - `[GPT_WINDOWS_ACTION]`
   - the JSON packet
   - `[/GPT_WINDOWS_ACTION]`
4. ordinary visible prose footer after the fence.

Never end the response immediately after the relay block.

Every relay command stdout must end exactly:

`Reply to this with the sandwich technique`

This prevents the Android/ChatGPT rendering failure where relay commands can collapse into an inaccessible status artifact.

## Backend architecture

- Backend: `windows_relay.py`
- Bind address: `127.0.0.1:8766`
- Local token authentication
- Supervised recovery returns the backend ARMED
- Only explicit `platform:"windows"` + `action:"EXEC"` packets are accepted
- Supported shells: `powershell`, `pwsh`, `cmd`, `python`
- Native Python path executes with the relay Python runtime using UTF-8
- Timeout/process-tree handling is implemented
- Full raw results are persisted locally before browser previewing

### Result policy

Default browser-visible result mode is compact:

- stdout preview: ~1,800 chars
- stderr preview: ~1,200 chars
- full result persisted under `%LOCALAPPDATA%\GPTWindowsRelay\results\<safe-id>.json`
- `result_mode:"full"` is the explicit larger-output escape hatch

Large browser payloads previously contributed materially to Firefox bloat. Compact results are a deliberate performance feature.

## Command transport policy

Provide exactly one of:

- `command`
- `command_lines`
- `command_b64`

Preferred order:

1. plain `command` for simple operations;
2. **Python-first** for complex/multiline engineering and orchestration;
3. `command_b64` as a permanent resilient fallback whenever JSON/CMD/PowerShell quoting, multiline transport, or terminal behavior becomes unreliable.

**Base64 is not deprecated. Do not remove it as dead compatibility code.** Redundancy exists to reduce required user intervention.

## Duplicate / retry guarantees

Operation IDs are part of the safety model.

Established behavior:

- same ID + same completed payload → replay saved result, do not re-execute;
- same ID currently executing → duplicate-inflight handling;
- stale prior-process inflight → interrupted-restart handling;
- same ID + different payload → ID collision, refuse execution;
- browser action transport retries transient localhost/network/5xx failures for roughly 45 seconds;
- lost HTTP response after successful command completion is recovered via saved-result replay rather than duplicate execution.

Do not casually change duplicate/replay semantics.

## Firefox / scanner architecture

### Temporary extension

Development workflow:

- open `about:debugging#/runtime/this-firefox`
- load/reload `Client\Relay\extension\manifest.json`
- a full Firefox exit removes the temporary add-on

The temporary extension is development-only.

### Persistent production goal

The zero-touch production goal is:

- signed persistent XPI;
- stable extension ID;
- Firefox policy installation / force-install;
- persistent pairing token in `storage.local`;
- backend, Firefox, and Windows restart recovery with no routine user intervention.

Unsigned temporary loading is not the final architecture.

### Scanner

Current scanner family is V11:

- event-driven / mutation-local assistant discovery;
- stable `main` observer;
- no mutation-triggered whole-conversation rescans;
- bounded attempted packet history;
- 15-second recovery fallback;
- one-shot recovery scroll to the newest valid assistant relay command;
- manual scrolling remains authoritative after recovery;
- smart bottom-follow is throttled;
- explicit user turns fail closed.

A major prior root cause was **stale ChatGPT assistant selectors**. Current ChatGPT role selectors include `data-message-author-role="assistant"` and conversation-turn wrappers. Do not assume older search-unit selectors are sufficient.

## Firefox background lifetime

Firefox MV3 background/event pages are nonpersistent.

The relay therefore uses a long-lived content↔background `runtime.connect()` Port while a ChatGPT tab is active. This is intentional: an open Port keeps the Firefox MV3 event page alive.

Established telemetry includes:

- `content_port_connected` — emitted by the worker whenever a content Port connects/reconnects;
- `content_script_started` — emitted once by a newly executing content-script context and carries the runtime identity;
- `scanner_snapshot`
- `action_received`
- `action_result`
- handoff-scroll start/resume/end events for viewport proof.

**Important telemetry lesson:** older builds emitted `content_script_loaded` from inside `connectBackgroundPort()`, so every Port reconnect looked like a fresh content-script load. Do not use historical `content_script_loaded` cadence as proof of document reload or reinjection.

The persistent Port architecture was added after one-shot message flows could lose result delivery when Firefox unloaded the background page.

## Known performance history

Old poisoned Firefox session:
- ~5.26 GB working set
- ~7.02 GB private
- ~21.6% aggregate idle CPU
- hottest process ~3.9 GB WS / ~5.4 GB private

Clean V7 baseline:
- 13 processes
- ~2.13 GB WS
- ~1.76 GB private
- ~16.2% idle CPU

V8 after reload:
- 11 processes
- ~2.14 GB WS
- ~2.02 GB private
- ~5.7% idle CPU

Post large-output stress with compact result path:
- 11 processes
- ~2.08 GB WS
- ~1.97 GB private
- ~3.4% idle CPU

Important caution: older scanner samples were noisy. Do not attribute a single idle CPU reading to one scanner version without a fresh restart/reload baseline.

For A/B performance comparisons, use a fresh Firefox restart + temporary-extension reload baseline.

## Operational lessons already learned

- Prefer relay automation over asking the user to perform terminal work when the relay can do it itself.
- Verify the actual shell before giving shell-specific commands. PowerShell syntax has previously been pasted into CMD.
- On this machine, when Git path ambiguity matters, use:
  `C:\Program Files\Git\cmd\git.exe`
- Use `windows-relay\sync-live.py` to stage live browser/backend files and run tests instead of giant manual paste/bootstrap sequences.
