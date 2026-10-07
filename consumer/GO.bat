@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1" -NoBrowser -NoGui
if errorlevel 1 (
  echo.
  echo GPT One-Click Go could not prepare its runtime.
  pause
  exit /b 1
)

set "RUNTIME=%~dp0runtime"
if not exist "%RUNTIME%\windows_relay.py" set "RUNTIME=%~dp0..\windows-relay"

set "PYW=%RUNTIME%\.venv\Scripts\pythonw.exe"
if not exist "%PYW%" (
  echo.
  echo GPT One-Click Go GUI runtime is missing.
  pause
  exit /b 1
)

if not exist "%~dp0recovery_supervisor.py" (
  echo.
  echo GPT One-Click Go recovery supervisor is missing.
  pause
  exit /b 1
)

rem GPT_CONSUMER_RECOVERY_SUPERVISOR_LAUNCH_V1
start "" /D "%~dp0" "%PYW%" "%~dp0recovery_supervisor.py"
if errorlevel 1 (
  echo.
  echo GPT One-Click Go recovery supervisor could not be launched.
  pause
  exit /b 1
)

start "" /D "%~dp0" "%PYW%" "%~dp0consumer_app.py"
if errorlevel 1 (
  echo.
  echo GPT One-Click Go GUI could not be launched.
  pause
  exit /b 1
)

exit /b 0
