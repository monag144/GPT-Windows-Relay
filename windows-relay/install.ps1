$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host 'GPT Windows Relay installer' -ForegroundColor Cyan
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3.10+ is required.' }
$venv = Join-Path $PSScriptRoot '.venv'
if (-not (Test-Path $venv)) { & $python.Source -m venv $venv }
$py = Join-Path $venv 'Scripts\python.exe'
$configDir = Join-Path $env:APPDATA 'GPTWindowsRelay'; New-Item -ItemType Directory -Force -Path $configDir | Out-Null
$configPath = Join-Path $configDir 'bridge.json'
if (Test-Path $configPath) { $cfg = Get-Content $configPath -Raw | ConvertFrom-Json; $token=[string]$cfg.token; $port=[int]$cfg.port }
else { $token=(& $py -c "import secrets; print(secrets.token_urlsafe(32))").Trim(); $port=8766; @{version=1;host='127.0.0.1';port=$port;token=$token}|ConvertTo-Json|Set-Content -Encoding UTF8 $configPath }
@"
export const RELAY_PORT = $port;
export const RELAY_TOKEN = "$token";
"@ | Set-Content -Encoding UTF8 (Join-Path $PSScriptRoot 'extension\config.js')
Write-Host 'Installed.' -ForegroundColor Green
Write-Host '1. Run .\run.ps1'
Write-Host '2. Chrome: chrome://extensions or Edge: edge://extensions'
Write-Host '3. Enable Developer mode -> Load unpacked -> select the extension folder'
Write-Host '4. Open ChatGPT, click GPT Windows Relay, then Arm relay'
Write-Host 'The relay starts ARMED and returns ARMED after recovery.'
