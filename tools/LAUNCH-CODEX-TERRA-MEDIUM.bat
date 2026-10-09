@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Codex 5.6 Terra - Medium - GPT Windows Relay
rem PCE12 user-authorized escalation launcher. No Termux fallback.
rem Runs existing verified checkout launcher; no GitHub Actions.
set "BASE=%~dp0Launch-Codex-CLI.bat"
if not exist "%BASE%" (
  echo ERROR: Canonical Launch-Codex-CLI.bat is missing.
  pause
  exit /b 1
)
echo Opening GPT-5.6 Terra at medium reasoning.
echo Verify the selected model in Codex using /status.
echo Repository origin must be the canonical GPT-Windows-Relay.
echo.
call "%BASE%" --model gpt-5.6-terra -c model_reasoning_effort=medium %*
exit /b %ERRORLEVEL%
