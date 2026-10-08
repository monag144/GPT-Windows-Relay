# A6.399h Consumer Firefox Zero-Touch Setup — Launcher PID / GUI PID Split — 2026-10-05T2341Z

**Class:** INCIDENT / CONSUMER FIREFOX ACCEPTANCE  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Operation:** `PCENG-A6.399h-consumer-firefox-zero-touch-setup`  
**Disposition:** ROOT CAUSE IDENTIFIED; FIX IMPLEMENTED; RE-ACCEPTANCE PENDING

## What passed

- consumer bootstrap completed;
- isolated consumer Python environment was created;
- consumer relay became ready on port 8767;
- development relay remained on port 8766;
- consumer/dev instance-isolation check passed.

## Failure

The first real consumer Firefox zero-touch setup failed in the semantic UI Automation adapter with:

`FIREFOX_WINDOW_MATCH_COUNT_0`

The consumer browser manager correctly treated this as a setup failure. The adapter did not fall back to coordinates, SendKeys, or an unrelated Firefox window.

## Root cause

The adapter's first managed-instance scope accepted only the launcher PID returned by Python `subprocess.Popen`. Firefox can assign its visible `MozillaWindowClass` browser window to a descendant Firefox process instead of that launcher PID. As a result, the fail-closed window lookup found zero windows even though the managed Firefox process tree existed.

## Fix

`firefox_tab_adapter.ps1` now expands an explicitly supplied launcher PID into its Firefox descendant process tree using `Win32_Process.ParentProcessId`, then accepts visible Firefox windows only from that managed tree.

Marker: `GPT_WINDOWS_FIREFOX_MANAGED_PROCESS_TREE_V1`.

This preserves isolation from the Director's already-running development Firefox session while accounting for Firefox's multiprocess ownership model.

## Acceptance requirement

Repeat the isolated consumer setup and require:
- consumer 8767 / dev 8766 separation;
- automatic temporary add-on installation;
- ChatGPT refresh;
- consumer Firefox browser heartbeat;
- no manual user action.
