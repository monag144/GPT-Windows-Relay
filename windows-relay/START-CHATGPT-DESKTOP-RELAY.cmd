@echo off
setlocal
set "RELAY_DIR=%~dp0"
if not exist "%RELAY_DIR%tools\Run-ChatGPT-DesktopMonitor.ps1" (
  echo ERROR: Desktop monitor script not found. Pull the latest Windows Relay branch.
  exit /b 2
)
where powershell.exe >nul 2>nul
if errorlevel 1 (
  echo ERROR: Windows PowerShell is not available.
  exit /b 3
)
echo Starting ChatGPT desktop relay monitor in its own terminal window.
echo This does not execute commands: the desktop UIA source is not yet authenticated.
start "GPT ChatGPT Desktop Monitor" powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -NoExit -File "%RELAY_DIR%tools\Run-ChatGPT-DesktopMonitor.ps1"
exit /b 0
