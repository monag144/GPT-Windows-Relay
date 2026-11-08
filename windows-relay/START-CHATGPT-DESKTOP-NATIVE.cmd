@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  for %%P in (python.exe) do set "PYTHON=%%~$PATH:P"
)
if not exist "%PYTHON%" (
  echo ERROR: Python 3.10+ is required. Run the existing source installer first.
  exit /b 2
)
if not exist "%ROOT%desktop_native_relay.py" (
  echo ERROR: Native desktop relay source is missing.
  exit /b 3
)
echo Checking the independent ChatGPT desktop relay...
"%PYTHON%" -B "%ROOT%desktop_native_relay.py" check-running
set "RUNNING_RC=%ERRORLEVEL%"
if "%RUNNING_RC%"=="10" (
  echo Existing native relay retained; no duplicate process launched.
) else (
  if not "%RUNNING_RC%"=="0" (
    echo ERROR: Cannot establish native relay singleton ownership.
    exit /b 4
  )
  echo Starting native desktop command monitor.
  start "GPT Windows Native Relay" cmd.exe /k ""%PYTHON%" -B "%ROOT%desktop_native_relay.py" run"
)
echo Selecting the existing upper-right Windows Relay HUD for native mode...
"%PYTHON%" -B "%ROOT%desktop_native_relay.py" hud-mode
if errorlevel 1 (
  echo ERROR: Original HUD transport selection failed.
  exit /b 5
)
echo Reconciling the original HUD; no separate mini HUD is permitted.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%tools\Reconcile-OriginalDesktopHUD.ps1"
if errorlevel 1 (
  echo ERROR: Original HUD reconciliation failed.
  exit /b 6
)
echo Native commands: CMD, Python, PowerShell, pwsh, Base64 packets.
echo ARM is persistent; STOP and OFF are controlled by the native HUD.
echo Existing browser relay components are not modified.
exit /b 0
