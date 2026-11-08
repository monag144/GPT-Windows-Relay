@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
set "PYTHONW=%ROOT%.venv\Scripts\pythonw.exe"
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
if exist "%PYTHONW%" (
  start "GPT Native Desktop HUD" "%PYTHONW%" -B "%ROOT%desktop_native_hud.py"
) else (
  echo HUD Pythonw missing; launch the HUD with the normal Python interpreter.
  start "GPT Native Desktop HUD" "%PYTHON%" -B "%ROOT%desktop_native_hud.py"
)
echo Native commands: CMD, Python, PowerShell, pwsh, Base64 packets.
echo ARM is persistent; STOP and OFF are controlled by the native HUD.
echo Existing browser relay components are not modified.
exit /b 0
