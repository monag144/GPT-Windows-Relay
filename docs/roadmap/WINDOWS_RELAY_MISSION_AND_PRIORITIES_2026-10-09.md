# Windows Relay mission and priorities — 2026-10-09

**Mission:** deliver a reliable, auditable ChatGPT ↔ Windows execution bridge that follows through on a requested action, returns its exact result, honors operator STOP and does not duplicate side effects. Project is `monag144/GPT-Windows-Relay` only; live Client is a separate deployment.

## Strategic cut — no agent-switching development
The Director **permanently retired** automatic ChatGPT conversation/agent switching: no operation-count rotation, extension-driven new-chat/rename, watcher-driven fallback, headless handoff or replacement switching architecture. Previous development belongs in `windows-relay/bin/AGENT_SWITCHING_RETIREMENT_2026-10-09.md`, with historical source available at pinned Git SHA. The `docs/policy/SCRIPT_ONLY_AGENT_HANDOFF_2026-10-09.md` policy supersedes the earlier temporary hold.

For an **explicitly user-requested** handoff, the source engineer infers its verified current PCE number and increments by one, stages complete successor instructions in `Copy Contents.txt`, then invokes the **existing unmodified** `Run-Copy-Contents.cmd` / PowerShell companion once. The human-visible new user turn is the completion criterion. The launcher must never embed a specific successor series. Do not autonomously initiate any handoff at 100 operations; stop at the ordinal budget boundary.

Native Firefox UIA, clipboard, browser tab selection and unrelated recovery components are temporarily disabled **as agent-switching techniques only**, not globally removed from normal command/reply delivery, STOP protection, or safe same-chat recovery.

## What remains: ordered engineering work
1. **P0 correct execution safety.** PCE16.000 confirmed non-atomic lookup/reserve and 500-entry eviction in Client source; PCE16.003 observed 501 processed records. Preserve no-live-duplicate-evidence distinction: retest with isolated safe concurrency/replay fixtures, then implement minimal durable identity/collision/uncertain-restart protections, without clearing live state.
2. **P0 end-to-end reliability.** Authenticated command detection, exact execution, durable result delivery, and the installed HUD controls **START, STOP, RESTART, OFF, KILL**. ARM is an internal backend permission/quiescence state, **not an operator HUD control**. Preserve cross-conversation owner rejection (PCE15.050) and STOP's real execution interlock.
3. **P1 prove and reconcile actual installed code.** Identify loaded Firefox extension/profile, compare reviewed GitHub -> development -> Client -> loaded bytes, address signing/packaging and deployment rollback.
4. **P1 live verification.** Independent real ChatGPT user-role send traces, negative/collision cases, screenshots, restart recovery and endurance. Last G26 0/60, G27 0/2; never substitute static tests or headless fixtures.
5. **P1 stabilize requested script-driven computer control.** Favor small deterministic user-requested actions with focus, paste, Enter and confirmation checks. Keep the successful one-shot agent-transfer launcher as a protected method; no automatic replacement.
6. **P1 HUD and diagnostic recovery.** Preserve the working five Client buttons; add guarded RETRY and a distinct, non-reexecuting FORCE current-chat scanner inspection. Detect stream/network errors, rate limits, stalls, and previously unexpected failures; capture evidence and create a proposed manual one-shot handoff only when bounded recovery has failed. PCE16.002/003 found RETRY only in development and no FORCE listener.
7. **P2 product experience.** Signed unlisted private Firefox extension, browser support (Firefox/Chrome/Edge), one-click installation, HUD improvements and optional job-application help, each independently tested.

**Release status:** last verified strict evidence 11/28 (Grade F/BLOCKED), loaded extension identity unknown, exact-once backend gaps open. GitHub branch modifications are not live rollout. Before **each** PCE operation, read GitHub control harness and dated roadmap and inspect relevant actual Client sources. Five-operation checkpoint rules remain required; every 20-operation review must explicitly assess drift, real progress, operator rescues and discarded approaches.

Detailed tasks: `docs/roadmap/WINDOWS_RELAY_TASK_BACKLOG_2026-10-09.md`. Old roadmap source remains in Git history for archaeology, not as active instruction.
