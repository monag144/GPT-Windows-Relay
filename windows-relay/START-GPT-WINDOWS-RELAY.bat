@echo off
setlocal
cd /d "%~dp0"

echo Starting or reconnecting to GPT Windows Relay...
echo.
rem relay-control.ps1 and the watchdog use singleton locks; repeated launches reconnect.
start "GPT Windows Relay watchdog" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0relay-watchdog-loop.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0relay-control.ps1" start
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0relay-control.ps1" status
echo.
if not "%RC%"=="0" (
    echo GPT Windows Relay exited with code %RC%.
    pause
)
exit /b %RC%
