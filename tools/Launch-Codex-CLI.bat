@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Codex CLI - GPT Windows Relay

rem PCE12: stand-alone, double-click Codex CLI launcher.
rem No Termux fallback. No GitHub Actions dependency.
set "WORKSPACE=%USERPROFILE%\Downloads\Dev\GPT\GPT-Windows-Relay"
set "START_DIR=%USERPROFILE%"
set "EXPECTED_HTTPS=https://github.com/monag144/GPT-Windows-Relay"
set "EXPECTED_SSH=git@github.com:monag144/GPT-Windows-Relay"

echo ==================================================
echo   Codex CLI - Windows
echo ==================================================
echo.

if exist "%WORKSPACE%\.git" (
  set "FOUND_ORIGIN="
  for /f "delims=" %%R in ('git -C "%WORKSPACE%" remote get-url origin 2^>nul') do set "FOUND_ORIGIN=%%R"
  if defined FOUND_ORIGIN (
    call :CheckOrigin
    if not errorlevel 1 (
      set "START_DIR=%WORKSPACE%"
      echo Verified canonical GPT-Windows-Relay checkout.
    ) else (
      echo WARNING: checkout remote does not match GPT-Windows-Relay.
      echo Codex will NOT run in this unverified project.
    )
  ) else (
    echo WARNING: cannot verify Windows checkout origin.
  )
) else (
  echo Canonical Windows checkout not found at:
  echo   %WORKSPACE%
  echo No fallback to the retired Termux repository.
)

echo Starting directory:
echo   %START_DIR%
echo.
cd /d "%START_DIR%"
if errorlevel 1 (
  echo ERROR: cannot enter the selected directory.
  pause
  exit /b 1
)

set "CODEX_COMMAND="
where codex >nul 2>&1
if not errorlevel 1 set "CODEX_COMMAND=codex"
if not defined CODEX_COMMAND if exist "%APPDATA%\npm\codex.cmd" set "CODEX_COMMAND=%APPDATA%\npm\codex.cmd"
if not defined CODEX_COMMAND (
  echo ERROR: Codex CLI is not on PATH and no npm launcher was found.
  echo Try opening a new Command Prompt and running: where codex
  pause
  exit /b 1
)

echo Launching Codex CLI. Close it with /exit or Ctrl+C.
echo Command-line arguments supplied to this BAT are forwarded to Codex.
echo.
call "%CODEX_COMMAND%" %*
set "CODEX_EXIT=%ERRORLEVEL%"
echo.
echo Codex CLI exited with code %CODEX_EXIT%.
pause
exit /b %CODEX_EXIT%

:CheckOrigin
set "NORMALIZED_ORIGIN=%FOUND_ORIGIN%"
if /i "%NORMALIZED_ORIGIN:~-4%"==".git" set "NORMALIZED_ORIGIN=%NORMALIZED_ORIGIN:~0,-4%"
if /i "%NORMALIZED_ORIGIN%"=="%EXPECTED_HTTPS%" exit /b 0
if /i "%NORMALIZED_ORIGIN%"=="%EXPECTED_SSH%" exit /b 0
exit /b 1
