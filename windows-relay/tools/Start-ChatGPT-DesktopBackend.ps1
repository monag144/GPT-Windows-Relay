# Start canonical GPT Windows Relay backend DISARMED before the native ChatGPT monitor.
# Reuse the historical START-GPT-WINDOWS-RELAY.bat; no new executor or listener.
# Explicit operator-owned launcher only. Do not alter Firefox or Termux.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$starter=Join-Path $root 'START-GPT-WINDOWS-RELAY.bat'
$control=Join-Path $root 'relay-control.ps1'
if(-not(Test-Path -LiteralPath $control)){throw 'CANONICAL_RELAY_CONTROL_MISSING'}
$statePath=Join-Path (Join-Path $env:LOCALAPPDATA 'GPTWindowsRelay') 'state.json'
$configPath=Join-Path (Join-Path $env:APPDATA 'GPTWindowsRelay') 'bridge.json'
if(-not(Test-Path -LiteralPath $starter)){throw 'CANONICAL_BACKEND_STARTER_MISSING'}
if(Test-Path -LiteralPath $statePath){
    try{$st=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json}
    catch{throw 'BACKEND_STATE_UNREADABLE_REFUSE_TO_START'}
    if($st.armed -eq $true){throw 'BACKEND_PERSISTED_ARMED_REFUSE_UNVERIFIED_DESKTOP_INPUT'}
}
if(-not(Test-Path -LiteralPath $configPath)){throw 'BACKEND_PAIRING_CONFIG_MISSING'}
try{$cfg=Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json}
catch{throw 'BACKEND_PAIRING_CONFIG_INVALID'}
if($cfg.host -cne '127.0.0.1' -or [int]$cfg.port -ne 8766 -or [string]::IsNullOrWhiteSpace([string]$cfg.token)){
    throw 'BACKEND_PAIRING_CONFIG_INVALID'
}
$headers=@{'X-GPT-Windows-Relay-Token'=[string]$cfg.token}
$url='http://127.0.0.1:8766/status'
$alreadyRunning=$false
try{
    $status=Invoke-RestMethod -Uri $url -Headers $headers -TimeoutSec 2
    if($status.ok -eq $true){$alreadyRunning=$true}
}catch{}
if($alreadyRunning){
    if($status.armed -eq $true){throw 'BACKEND_RUNNING_ARMED_REFUSE_UNVERIFIED_DESKTOP_INPUT'}
    Write-Output 'CANONICAL_BACKEND=REUSED_DISARMED'
}else{
    # Reuse the established supervisor/watchdog/HUD lifecycle.
    & $starter
    if($LASTEXITCODE -ne 0){throw ('CANONICAL_BACKEND_START_FAILED_EXIT='+$LASTEXITCODE)}
    $good=$false
    for($i=0;$i -lt 20;$i++){
        try{
            $status=Invoke-RestMethod -Uri $url -Headers $headers -TimeoutSec 2
            if($status.ok -eq $true){$good=$true;break}
        }catch{}
        Start-Sleep -Milliseconds 400
    }
    if(-not $good){throw 'CANONICAL_BACKEND_STATUS_UNAVAILABLE'}
    if($status.armed -eq $true){throw 'CANONICAL_BACKEND_STARTED_ARMED_REFUSE_MONITOR'}
    Write-Output 'CANONICAL_BACKEND=STARTED_DISARMED'
}
# A foreign process with a reused port or token is not the canonical backend.
$physicalStatus=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $control status)
if(@($physicalStatus | Where-Object { [string]$_ -match '^STATE=RUNNING\s+PID=' }).Count -ne 1){
    throw 'NONCANONICAL_BACKEND_LISTENER_REFUSE_MONITOR'
}
Write-Output 'CANONICAL_BACKEND_READY=TRUE'
Write-Output 'DESKTOP_AUTOMATIC_COMMAND_EXECUTION=DISABLED_PENDING_ASSISTANT_ATTRIBUTION'
