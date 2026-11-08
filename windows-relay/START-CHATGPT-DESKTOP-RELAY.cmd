@echo off
setlocal
set "RELAY_DIR=%~dp0"
if not exist "%RELAY_DIR%tools\Run-ChatGPT-DesktopMonitor.ps1" (
  echo ERROR: Desktop monitor script not found. Pull the latest Windows Relay branch.
  exit /b 2
)
if not exist "%RELAY_DIR%tools\Get-ChatGPT-DesktopMonitorStatus.ps1" (
  echo ERROR: Native desktop monitor status script missing.
  exit /b 2
)
if not exist "%RELAY_DIR%tools\Start-ChatGPT-DesktopBackend.ps1" (
  echo ERROR: Canonical backend startup guard not found.
  exit /b 2
)
where powershell.exe >nul 2>nul
if errorlevel 1 (
  echo ERROR: Windows PowerShell is not available.
  exit /b 3
)
echo Checking the canonical Windows Relay backend on 127.0.0.1:8766...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%RELAY_DIR%tools\Start-ChatGPT-DesktopBackend.ps1"
if errorlevel 1 (
  echo ERROR: Canonical relay failed safety preflight. Desktop monitor not started.
  exit /b 4
)
echo Checking for an existing native desktop monitor...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%RELAY_DIR%tools\Get-ChatGPT-DesktopMonitorStatus.ps1"
set "MONITOR_STATUS_RC=%ERRORLEVEL%"
if "%MONITOR_STATUS_RC%"=="10" (
  echo Existing native desktop monitor retained. No duplicate window launched.
  echo Stop that monitor with Ctrl+C if a newly pulled build must take effect.
  exit /b 0
)
if not "%MONITOR_STATUS_RC%"=="0" (
  echo ERROR: Desktop monitor ownership uncertain. Refusing duplicate start.
  exit /b 5
)
echo Starting ChatGPT Windows desktop relay monitor.
echo Native monitoring is active only after the new window reports CHATGPT_DESKTOP_MONITOR_V3.
echo Command execution remains disabled until assistant-origin authentication is proven.
start "GPT ChatGPT Desktop Monitor" powershell.exe -STA -NoLogo -NoProfile -ExecutionPolicy Bypass -NoExit -File "%RELAY_DIR%tools\Run-ChatGPT-DesktopMonitor.ps1"
exit /b 0
