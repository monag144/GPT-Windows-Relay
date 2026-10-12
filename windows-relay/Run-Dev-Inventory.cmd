@echo off
setlocal
set "SCRIPT=%~dp0Dev-Inventory.ps1"
if not exist "%SCRIPT%" (
  echo Dev-Inventory.ps1 was not found next to this launcher.
  pause
  exit /b 2
)
echo.
echo Windows Relay - read-only Downloads Dev inventory
 echo No files in Downloads Dev will be changed.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
set "RC=%ERRORLEVEL%"
echo.
echo Inventory finished with code %RC%.
echo The report directory and file name are printed above.
echo If Codex reported a problem, the PowerShell inventory is still available.
echo Attach the generated report files in ChatGPT.
pause
exit /b %RC%
