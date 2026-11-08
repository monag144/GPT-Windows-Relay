@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  for %%P in (python.exe) do set "PYTHON=%%~$PATH:P"
)
if not exist "%PYTHON%" (
  echo ERROR: Python is unavailable.
  exit /b 2
)
"%PYTHON%" -B "%ROOT%desktop_native_relay.py" %*
exit /b %ERRORLEVEL%
