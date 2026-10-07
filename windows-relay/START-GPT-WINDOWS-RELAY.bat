@echo off
setlocal
cd /d "%~dp0"

echo Starting GPT Windows Relay...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
    echo GPT Windows Relay exited with code %RC%.
    pause
)
exit /b %RC%
