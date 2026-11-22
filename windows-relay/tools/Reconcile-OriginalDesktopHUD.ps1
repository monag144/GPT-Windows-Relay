# Reconcile to exactly one original top-right GPT Windows Relay HUD.
# Stops only processes whose command line contains the canonical source paths.
# Does not start, stop, arm or modify the browser relay backend.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$original=[IO.Path]::GetFullPath((Join-Path $root 'hud.py'))
$obsolete=[IO.Path]::GetFullPath((Join-Path $root 'desktop_native_hud.py'))
$venvPythonw=Join-Path $root '.venv\Scripts\pythonw.exe'
$venvPython=Join-Path $root '.venv\Scripts\python.exe'
if(Test-Path -LiteralPath $venvPythonw){$python=$venvPythonw}
elseif(Test-Path -LiteralPath $venvPython){$python=$venvPython}
else{$python=(Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source}
if(-not $python){throw 'CANONICAL_ORIGINAL_HUD_PYTHON_MISSING'}
if(-not(Test-Path -LiteralPath $original)){throw 'CANONICAL_ORIGINAL_HUD_SOURCE_MISSING'}

function Find-HudProcesses([string]$exact){
    $quoted='"'+$exact+'"'
    $processes=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        $_.Name -in @('python.exe','pythonw.exe') -and
        ([string]$_.CommandLine).IndexOf($quoted,[StringComparison]::OrdinalIgnoreCase) -ge 0
    })
    return @($processes)
}
function Stop-HudProcess($process,[string]$label){
    # A Python parent/child pair can disappear while its CIM snapshot is being
    # walked.  A vanished target is already reconciled; do not abort startup or
    # leave the canonical HUD unavailable because Stop-Process raced its exit.
    $targetPid=[int]$process.ProcessId
    if(-not(Get-Process -Id $targetPid -ErrorAction SilentlyContinue)){
        Write-Output ($label+'_ALREADY_EXITED_PID='+$targetPid)
        return
    }
    Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
    if(Get-Process -Id $targetPid -ErrorAction SilentlyContinue){
        throw ($label+'_STOP_FAILED_PID='+$targetPid)
    }
    Write-Output ($label+'_STOPPED_PID='+$targetPid)
}
Write-Output 'ORIGINAL_GPT_RELAY_HUD_RECONCILIATION_V1'
Write-Output 'TARGET=EXISTING_TOP_RIGHT_HUD_PY'
# The new native HUD was an unapproved duplicate, so stop that exact process.
$mini=@(Find-HudProcesses $obsolete)
foreach($p in $mini){
    Stop-HudProcess $p 'UNWANTED_MINI_HUD'
}
# Reuse an already-visible original HUD if its process is newer than the
# source file. Every blind restart causes a visible flicker and UI state loss.
# A git pull updates hud.py's timestamp, forcing one genuine code reload.
$prior=@(Find-HudProcesses $original)
$visiblePrior=@($prior | ForEach-Object {
    Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
} | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero })
$sourceUpdated=(Get-Item -LiteralPath $original).LastWriteTimeUtc
# Runtime imports can change without a hud.py modification. Reload once when
# any of these canonical dependencies is newer than the visible HUD process.
foreach($sourceName in @('desktop_native_relay.py','windows_relay.py','command_courier.py')){
    $dependency=Join-Path $root $sourceName
    if(Test-Path -LiteralPath $dependency -PathType Leaf){
        $modified=(Get-Item -LiteralPath $dependency).LastWriteTimeUtc
        if($modified -gt $sourceUpdated){$sourceUpdated=$modified}
    }
}
$reusable=$false
if($visiblePrior.Count -eq 1){
    try{
        $reusable=($visiblePrior[0].StartTime.ToUniversalTime() -ge $sourceUpdated)
    }catch{$reusable=$false}
}
if($reusable){
    Write-Output 'ORIGINAL_HUD_START=EXISTING_PROCESS_REUSED'
}else{
    # Restart only this canonical file after a source upgrade, missing window
    # or invalid singleton; never stop other transport processes.
    foreach($p in $prior){
        Stop-HudProcess $p 'ORIGINAL_HUD_OLD_CODE_RESTARTED'
    }
    Start-Sleep -Milliseconds 400
    $existing=@(Find-HudProcesses $original)
    if($existing.Count -eq 0){
        Start-Process -FilePath $python -WorkingDirectory $root -ArgumentList @('-B',('"'+$original+'"')) | Out-Null
        Write-Output 'ORIGINAL_HUD_START=REQUESTED'
    }else{
        Write-Output 'ORIGINAL_HUD_START=EXISTING_PROCESS_REUSED'
    }
}
# Interactive Windows sign-in may require more than 850ms for Tk to expose
# its visible HWND. Wait with a bounded read-only check; never spawn twice.
$active=@()
$visible=@()
for($i=0;$i -lt 12;$i++){
    $active=@(Find-HudProcesses $original)
    $visible=@($active | ForEach-Object {
        Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
    } | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero })
    if($visible.Count -eq 1){break}
    if($i -lt 11){Start-Sleep -Milliseconds 250}
}
if($active.Count -eq 0){throw 'ORIGINAL_HUD_NOT_RUNNING_AFTER_START'}
if($visible.Count -ne 1){throw ('ORIGINAL_HUD_VISIBLE_WINDOW_COUNT='+$visible.Count)}
Write-Output ('ORIGINAL_HUD_RUNNING_COUNT='+$visible.Count)
Write-Output ('ORIGINAL_HUD_HOST_PROCESS_COUNT='+$active.Count)
Write-Output 'ORIGINAL_HUD_FILE=hud.py'
Write-Output 'ORIGINAL_HUD_TRANSPORT=NATIVE_CHATGPT_APP'
