@echo off
setlocal
set "RELAY_DIR=%~dp0"
if not exist "%RELAY_DIR%tools\Run-ChatGPT-DesktopMonitor.ps1" (
  echo ERROR: Desktop monitor script not found. Pull the latest Windows Relay branch.
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
echo Starting ChatGPT Windows desktop relay monitor.
echo UIA command execution remains disabled until assistant-origin authentication is proven.
start "GPT ChatGPT Desktop Monitor" powershell.exe -STA -NoLogo -NoProfile -ExecutionPolicy Bypass -NoExit -File "%RELAY_DIR%tools\Run-ChatGPT-DesktopMonitor.ps1"
exit /b 0
