@echo off
setlocal
cd /d "%~dp0"
echo INTENTIONAL OPERATOR STOP: stopping GPT Windows Relay...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0relay-control.ps1" stop
if errorlevel 1 (
  echo.
  echo FAILED to stop GPT Windows Relay.
  pause
  exit /b 1
)
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0relay-control.ps1" status
echo.
echo Relay is STOPPED. START-RELAY.bat or the HUD START button starts it.
pause
