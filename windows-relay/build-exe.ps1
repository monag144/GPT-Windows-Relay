$ErrorActionPreference='Stop'; Set-Location $PSScriptRoot
$py=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if(-not(Test-Path $py)){ & (Join-Path $PSScriptRoot 'install.ps1') }
& $py -m pip install --upgrade pyinstaller
& $py -m PyInstaller --noconfirm --clean --onefile --name GPTWindowsRelay windows_relay.py
Write-Host "Built $PSScriptRoot\dist\GPTWindowsRelay.exe" -ForegroundColor Green
