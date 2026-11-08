# Canonical Windows Relay backend and HUD preflight for native ChatGPT desktop.
# Uses the existing backend, HUD and watchdog. Never executes UIA action packets.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$starter=Join-Path $root 'START-GPT-WINDOWS-RELAY.bat'
$control=Join-Path $root 'relay-control.ps1'
$hud=Join-Path $root 'hud.py'
$watchdog=Join-Path $root 'relay-watchdog-loop.ps1'
$statePath=Join-Path (Join-Path $env:LOCALAPPDATA 'GPTWindowsRelay') 'state.json'
$configPath=Join-Path (Join-Path $env:APPDATA 'GPTWindowsRelay') 'bridge.json'
foreach($required in @($starter,$control,$hud,$watchdog)){
    if(-not(Test-Path -LiteralPath $required)){throw ('CANONICAL_SOURCE_MISSING='+[IO.Path]::GetFileName($required))}
}
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
$statusUrl='http://127.0.0.1:8766/status'
$alreadyRunning=$false
try{
    $status=Invoke-RestMethod -Uri $statusUrl -Headers $headers -TimeoutSec 2
    if($status.ok -eq $true){$alreadyRunning=$true}
}catch{}
if($alreadyRunning){
    if($status.armed -eq $true){throw 'BACKEND_RUNNING_ARMED_REFUSE_UNVERIFIED_DESKTOP_INPUT'}
    Write-Output 'CANONICAL_BACKEND=REUSED_DISARMED'
}else{
    & $starter
    if($LASTEXITCODE -ne 0){throw ('CANONICAL_BACKEND_START_FAILED_EXIT='+$LASTEXITCODE)}
    $good=$false
    for($i=0;$i -lt 20;$i++){
        try{
            $status=Invoke-RestMethod -Uri $statusUrl -Headers $headers -TimeoutSec 2
            if($status.ok -eq $true){$good=$true;break}
        }catch{}
        Start-Sleep -Milliseconds 400
    }
    if(-not $good){throw 'CANONICAL_BACKEND_STATUS_UNAVAILABLE'}
    if($status.armed -eq $true){throw 'CANONICAL_BACKEND_STARTED_ARMED_REFUSE_MONITOR'}
    Write-Output 'CANONICAL_BACKEND=STARTED_DISARMED'
}
# The authenticated HTTP status alone does not prove ownership of the listener.
$physicalStatus=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $control status)
if(@($physicalStatus | Where-Object { [string]$_ -match '^STATE=RUNNING\s+PID=' }).Count -ne 1){
    throw 'NONCANONICAL_BACKEND_LISTENER_REFUSE_MONITOR'
}
function Test-CanonicalProcess([string]$source,[string[]]$processNames){
    $quoted='"'+[IO.Path]::GetFullPath($source)+'"'
    foreach($item in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)){
        if($processNames -notcontains [string]$item.Name){continue}
        if(([string]$item.CommandLine).IndexOf($quoted,[StringComparison]::OrdinalIgnoreCase) -ge 0){return $true}
    }
    return $false
}
$watchdogNames=@('powershell.exe','pwsh.exe')
$hudNames=@('python.exe','pythonw.exe')
if(-not (Test-CanonicalProcess $watchdog $watchdogNames)){
    $watchdogArgs='-NoProfile -ExecutionPolicy Bypass -File "'+$watchdog+'"'
    Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $root -ArgumentList $watchdogArgs | Out-Null
    Write-Output 'CANONICAL_WATCHDOG=START_REQUESTED'
}else{
    Write-Output 'CANONICAL_WATCHDOG=ALREADY_RUNNING'
}
$hudFound=$false
for($i=0;$i -lt 20;$i++){
    if(Test-CanonicalProcess $hud $hudNames){$hudFound=$true;break}
    Start-Sleep -Milliseconds 250
}
if(-not $hudFound){
    # Reconcile the existing canonical HUD, not a second or renamed HUD.
    $hudPython=Join-Path $root '.venv\Scripts\pythonw.exe'
    if(-not(Test-Path -LiteralPath $hudPython)){
        $pyw=Get-Command pythonw.exe -ErrorAction SilentlyContinue
        if($null -ne $pyw){$hudPython=$pyw.Source}
        else{$hudPython=Join-Path $root '.venv\Scripts\python.exe'}
    }
    if(Test-Path -LiteralPath $hudPython){
        try{
            if(-not (Test-CanonicalProcess $hud $hudNames)){
                Write-Output 'CANONICAL_HUD_DIRECT_START=ATTEMPTED'
                Start-Process -FilePath $hudPython -WorkingDirectory $root -ArgumentList @('"'+$hud+'"') | Out-Null
            }
            Start-Sleep -Milliseconds 800
            $hudFound=Test-CanonicalProcess $hud $hudNames
        }catch{Write-Output 'CANONICAL_HUD_DIRECT_START=FAILED'}
    }
}
if($hudFound){
    Write-Output 'CANONICAL_HUD=RUNNING'
}else{
    Write-Output 'CANONICAL_HUD=NOT_RUNNING'
    Write-Output 'CANONICAL_HUD_DIAGNOSTIC=RUN_PYTHON_B_HUD_PY_TO_CAPTURE_EXCEPTION'
}
Write-Output 'CANONICAL_BACKEND_READY=TRUE'
Write-Output 'DESKTOP_AUTOMATIC_COMMAND_EXECUTION=DISABLED_PENDING_ASSISTANT_ATTRIBUTION'
