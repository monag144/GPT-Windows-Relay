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
Write-Output 'ORIGINAL_GPT_RELAY_HUD_RECONCILIATION_V1'
Write-Output 'TARGET=EXISTING_TOP_RIGHT_HUD_PY'
# The new native HUD was an unapproved duplicate, so stop that exact process.
$mini=@(Find-HudProcesses $obsolete)
foreach($p in $mini){
    Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
    Write-Output ('UNWANTED_MINI_HUD_STOPPED_PID='+$p.ProcessId)
}
# Old hud.py processes contain pre-pull code and cannot hot-reload the new
# native-status adapter. Restart only that exact file, preserving HUD position.
$prior=@(Find-HudProcesses $original)
foreach($p in $prior){
    Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
    Write-Output ('ORIGINAL_HUD_OLD_CODE_RESTARTED_PID='+$p.ProcessId)
}
Start-Sleep -Milliseconds 400
$existing=@(Find-HudProcesses $original)
if($existing.Count -eq 0){
    Start-Process -FilePath $python -WorkingDirectory $root -ArgumentList @('-B',('"'+$original+'"')) | Out-Null
    Write-Output 'ORIGINAL_HUD_START=REQUESTED'
}else{
    Write-Output 'ORIGINAL_HUD_START=EXISTING_PROCESS_REUSED'
}
Start-Sleep -Milliseconds 850
$active=@(Find-HudProcesses $original)
if($active.Count -eq 0){throw 'ORIGINAL_HUD_NOT_RUNNING_AFTER_START'}
Write-Output ('ORIGINAL_HUD_RUNNING_COUNT='+$active.Count)
Write-Output 'ORIGINAL_HUD_FILE=hud.py'
Write-Output 'ORIGINAL_HUD_TRANSPORT=NATIVE_CHATGPT_APP'
