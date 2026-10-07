@echo off
setlocal
cd /d "%~dp0"
echo Starting or resuming GPT Windows Relay...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0relay-control.ps1" start
if errorlevel 1 (
  echo.
  echo FAILED to start/resume GPT Windows Relay.
  pause
  exit /b 1
)
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0relay-control.ps1" status
echo.
echo You may close this launcher window. The relay supervisor/watchdog owns recovery.
pause
