# Incident — crashed PowerShell and unexpected PowerShell process accumulation

Timestamp: 2026-10-06T04:27Z  
Branch: `consumer/r29-firefox-offline-tray`  
Status: **OPEN — strong causal lead, live/process-source reconciliation required**

## Operator observation

While recovering from the PCE7.408 `STARTING` stall, the operator manually inspected the Windows environment and found a **crashed PowerShell process**. At the same time, approximately **10 PowerShell processes** were present. The operator closed the crashed PowerShell and reported that this exposed the practical cause of the stuck condition.

Treat this as high-value incident evidence. Do not yet claim that all ten processes were relay-owned or that the crashed process is the fully proven root cause until PID/parent/command-line/start-time evidence is collected.

## Why this is abnormal

The relay deliberately has redundant recovery planes, but redundancy must not be implemented as uncontrolled accumulation of equivalent PowerShell processes. Expected helper processes must have:

- a named purpose/owner;
- a bounded lifetime;
- a parent/child relationship that can be audited;
- timeout and process-tree termination;
- no detached orphan left behind after success/failure;
- singleton/lease protection for long-lived supervisors;
- reconciliation after browser/backend restart.

Ten concurrent PowerShell processes therefore require classification. They may include legitimate one-shot Firefox UIA adapters, supervisor/watchdog helpers, Task Scheduler activation helpers, unrelated user shells, or leaked/orphaned processes. The incident remains open until these are distinguished.

## Relationship to PCE7.408

PCE7.408 crossed the Firefox add-on reload/page-refresh boundary and the backend later appeared terminal `OK` while the HUD stayed at `STARTING` and Firefox `IDLE`. Manual backend restart and add-on/tab reload did not initially clear that state. The subsequently observed crashed PowerShell is a plausible explanation for a blocked UIA/helper leg, but this causal link needs telemetry/process proof.

## Immediate investigation

1. Capture a read-only census of `powershell.exe` / `pwsh.exe` with PID, parent PID, creation time, executable path, and command line.
2. Map each relay-owned process to the source/launcher that created it.
3. Identify crashed/hung/orphaned helpers and whether any lack a timeout/kill-tree path.
4. Check supervisor/watchdog singleton behavior and Task Scheduler helper overlap.
5. Distinguish long-lived intended processes from one-shot Firefox adapter shells.
6. Add process-budget/leak telemetry: redundant planes must never silently multiply helper processes.
7. Add a reap/reconciliation rule for expired relay-owned helper shells without touching unrelated user PowerShell processes.
8. Re-run sustained relay operations after repair; process count must return to baseline after each helper action.

No stable promotion is authorized from this observation alone.

## Initial source audit — 2026-10-06T0430Z

Two relay-owned PowerShell launch sites are immediately relevant:

1. `windows-relay/firefox_adapter.py::_call()` invokes `powershell.exe -NoProfile -ExecutionPolicy Bypass -File firefox_tab_adapter.ps1 ...` through `subprocess.run()` **without an adapter-local timeout**. The outer relay action has its own timeout/process-tree kill, but an intermediate Python timeout/termination boundary must be verified to reap descendants rather than orphan a UIA PowerShell.
2. `consumer/recovery_supervisor.py::_restart_relay()` launches `runtime/run.ps1` through bare `subprocess.Popen(..., stdout=DEVNULL, stderr=DEVNULL)` and retains no process handle. It then polls relay health for 12 seconds. The supervisor itself has a named singleton, but this launch site does not by itself prove a singleton/lease for the spawned PowerShell. The generated/runtime `run.ps1` is not present at that repository path and therefore its live contents/locking behavior must be inspected on Windows.

The backend `windows_relay.py` does have a stronger boundary for action-shell children: it creates a new process group and on action timeout calls `taskkill /PID <pid> /T /F`. That makes the unbounded/detached adapter and supervisor helper boundaries higher-priority suspects than ordinary backend PowerShell actions.

These are source-level risk findings, not yet proof that the operator-observed ten processes came from either site.

## Operator clarification — 2026-10-06T0429Z

The operator confirmed that the relay PowerShell is configured to reopen when closed and is currently running. One auto-restored long-lived relay shell is therefore expected behavior and must not be counted as a leak by itself. The incident concerns the earlier observation of approximately ten PowerShell processes plus a crashed PowerShell. Investigation must classify process ownership/command lines before terminating anything further; never bulk-kill every PowerShell process merely because the relay uses PowerShell for multiple bounded helpers.



## Recovery evidence — PCE7.410–PCE7.415

The relay is again able to execute Windows actions: PCE7.410, 411, 412, 414 and 415 all reached the backend (413 was rejected at browser packet validation; 414 then failed Python syntax because its encoded payload was corrupted). This narrows the earlier outage away from a continuing listener failure.

PCE7.411 also confirmed the relay server itself can appear as two Python processes: the venv launcher/shim is parent of the real Python interpreter. PCE7.415 observed two `hud.py` processes after one HUD launch, so raw process counts must not be used as leak proof without PID/PPID classification.

The earlier approximately-ten-PowerShell observation remains an open leak/accumulation incident. The next read-only census must classify surviving PowerShell command lines and ownership; one configured auto-restored relay supervisor is expected. Do not bulk-kill PowerShell processes.


## PCE7.417 steady-state topology proof — 2026-10-06T0523Z

Read-only census `PCENG-PCE7.417-hud-topology-and-powershell-census` completed OK in 1.099 s.

Current persistent PowerShell count is **2**, with an explicit designed ancestry:

- PID 15900: hidden `relay-watchdog-loop.ps1`;
- PID 14180: `run.ps1`, parent PID 15900.

This matches the documented watchdog → visible supervisor architecture. It materially strengthens the earlier operator report: approximately ten PowerShell processes was not the intended steady-state redundancy shape. The current two-process chain is the expected baseline; future process-budget checks should classify by command line and parentage and alarm on extra relay-owned shells rather than bulk-kill PowerShell.
