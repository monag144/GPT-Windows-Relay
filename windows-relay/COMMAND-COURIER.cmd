@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  for %%P in (python.exe) do set "PYTHON=%%~$PATH:P"
)
if not exist "%PYTHON%" (
  echo ERROR: Command Courier requires Python 3.10+.
  exit /b 2
)
"%PYTHON%" -B "%ROOT%command_courier.py" %*
exit /b %ERRORLEVEL%
