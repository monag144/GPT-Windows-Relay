# Canonical Windows Relay source installer — 2026-10-12
# Setup only: no automatic start, arm, Firefox mutation, consumer overlay or backup.
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
Write-Host 'GPT Windows Relay — canonical source setup' -ForegroundColor Cyan

$python=Get-Command python.exe -ErrorAction SilentlyContinue
if(-not $python){$python=Get-Command py.exe -ErrorAction SilentlyContinue}
if(-not $python){throw 'Python 3.10+ is required.'}

$venv=Join-Path $PSScriptRoot '.venv'
if(-not(Test-Path -LiteralPath (Join-Path $venv 'Scripts\python.exe'))){
  & $python.Source -m venv $venv
  if($LASTEXITCODE -ne 0){throw 'Failed to prepare canonical Windows Relay Python runtime.'}
}
$py=Join-Path $venv 'Scripts\python.exe'
if(-not(Test-Path -LiteralPath $py)){throw 'Canonical Python runtime not found after setup.'}

# Python backend owns bridge.json parsing/creation, including preserving the
# existing paired token. Never print or write the token into an extension.
& $py -B -c "import windows_relay as relay; cfg=relay.config(relay.cfg_dir()/'bridge.json'); print('PAIRING_CONFIG_VALID=True'); print('BACKEND_HOST='+str(cfg['host'])); print('BACKEND_PORT='+str(cfg['port']))"
if($LASTEXITCODE -ne 0){throw 'Failed to validate canonical backend pairing configuration.'}

$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'extension-persistent\manifest.json') -Raw | ConvertFrom-Json
if($manifest.name -ne 'GPT Windows Relay' -or
   $manifest.browser_specific_settings.gecko.id -ne 'gpt-windows-relay@local'){
  throw 'Canonical persistent Firefox extension identity mismatch.'
}
Write-Host ('FIREFOX_SOURCE=extension-persistent version='+[string]$manifest.version)
Write-Host 'This setup does not start the relay, change ARM, or install/reload Firefox.'
Write-Host 'For Firefox temporary add-on, select extension-persistent\manifest.json.'
Write-Host 'Pair only through the canonical extension popup; existing bridge.json token remains private.'
Write-Host 'Separate One-Click Go consumer extension/ is never modified by this installer.'
