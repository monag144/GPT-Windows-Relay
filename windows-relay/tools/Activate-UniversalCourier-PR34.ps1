# Controlled activation from a validated isolated PR34 worktree.
# Run from CMD after the last old-relay output has been delivered/acknowledged.
# No git reset, stash, merge, force checkout, file delete, or app COM access.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ExpectedCommit,
    [switch]$EnableAutoSend
)
$ErrorActionPreference='Stop'
$project=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
if((Split-Path $project -Leaf) -notmatch 'PR34$'){throw 'NOT_ISOLATED_PR34_WORKTREE'}
$native=Join-Path $project 'windows-relay\desktop_native_relay.py'
$hud=Join-Path $project 'windows-relay\hud.py'
$nativeTools=Join-Path $project 'windows-relay'
if(-not(Test-Path -LiteralPath $native -PathType Leaf) -or
   -not(Test-Path -LiteralPath $hud -PathType Leaf)){
    throw 'QUALIFIED_NATIVE_OR_HUD_SOURCE_MISSING'
}
$gitHead=(& git -C $project rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0 -or $gitHead -cne $ExpectedCommit){
    throw ('SOURCE_HEAD_MISMATCH='+$gitHead)
}
$dirty=@(& git -C $project status --porcelain --untracked-files=no)
if($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0){
    throw 'TRACKED_WORKTREE_DIRTY_REFUSE_ACTIVATION'
}
$python=(Get-Command python.exe -ErrorAction Stop).Source
$stateFile=Join-Path $env:LOCALAPPDATA 'GPTWindowsRelayDesktop\state.json'
if(Test-Path -LiteralPath $stateFile){
    $state=Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach($item in $state.outbound_deliveries.PSObject.Properties){
        if($item.Value.phase -eq 'SUBMITTING'){
            throw ('INFLIGHT_DELIVERY_REFUSE_RESTART='+$item.Name)
        }
    }
}
Write-Output ('QUALIFIED_HEAD='+$gitHead)
Write-Output 'RESTART_PLAN=STOP_NATIVE_RELOAD_ORIGINAL_HUD_START_NATIVE_VERIFY_HASH'
# Collect stderr inside Python rather than letting Windows PowerShell 5.1
# convert unittest progress on stderr into a terminating NativeCommandError.
# This entire qualification stage MUST complete before any stop/restart.
$verify=Join-Path $project 'windows-relay\tools\verify_universal_courier_release.py'
if(-not(Test-Path -LiteralPath $verify -PathType Leaf)){
    throw 'OFFLINE_VERIFICATION_HELPER_MISSING_NO_RESTART'
}
$testReport=@(& $python -B $verify)
$testExit=$LASTEXITCODE
foreach($line in $testReport){Write-Output $line}
if($testExit -ne 0){
    throw ('OFFLINE_SUITES_FAILED_NO_RESTART_EXIT='+$testExit)
}
if($testReport -notcontains 'OFFLINE_QUALIFICATION=PASS'){
    throw 'OFFLINE_TEST_RECEIPT_MISSING_NO_RESTART'
}
Write-Output 'OFFLINE_SUITES=PASS'
# First disable automatic sending, then stop the old singleton gracefully.
& $python -B $native auto-send-off | Out-Null
& $python -B $native off | Out-Null
$released=$false
for($i=0;$i -lt 40;$i++){
    & $python -B $native check-running | Out-Null
    if($LASTEXITCODE -eq 0){$released=$true;break}
    Start-Sleep -Milliseconds 250
}
if(-not $released){throw 'OLD_NATIVE_STILL_RUNNING_NO_NEW_PROCESS'}
Write-Output 'OLD_NATIVE_STOPPED=TRUE'
# Retire ONLY canonical HUD Python processes whose CLI uses exactly these
# two repo paths. Do not kill terminal, Notepad, user apps or unknown HUDs.
$oldProject=Join-Path (Split-Path $project -Parent) 'Windows Relay'
$allowed=@(
    [IO.Path]::GetFullPath((Join-Path $oldProject 'windows-relay\hud.py')),
    [IO.Path]::GetFullPath($hud)
)
# Exact process CLI validation: never stop unrelated user applications.
$candidates=@()
foreach($proc in @(Get-CimInstance Win32_Process -ErrorAction Stop |
                   Where-Object {$_.Name -in @('python.exe','pythonw.exe')})){
    foreach($path in $allowed){
        if(([string]$proc.CommandLine).IndexOf(('"'+$path+'"'),
                     [StringComparison]::OrdinalIgnoreCase) -ge 0){
            $candidates+=,$proc
            break
        }
    }
}
if($candidates.Count -gt 2){throw 'MULTIPLE_CANONICAL_HUDS_REQUIRE_MANUAL_INSPECTION'}
foreach($proc in $candidates){
    Stop-Process -Id ([int]$proc.ProcessId) -Force -ErrorAction Stop
}
Write-Output ('OLD_CANONICAL_HUDS_CLOSED='+$candidates.Count)
& $python -B $native hud-mode | Out-Null
# arm only updates a policy JSON file; it does NOT start the singleton.
# restart starts the verified source after the old lock was released.
& $python -B $native restart | Out-Null
if($LASTEXITCODE -ne 0){throw 'NEW_NATIVE_RESTART_COMMAND_FAILED'}
& $python -B $native check-running | Out-Null
if($LASTEXITCODE -ne 10){throw 'NEW_NATIVE_NOT_RUNNING'}
$expectedHash=(Get-FileHash -LiteralPath $native -Algorithm SHA256).Hash.ToLowerInvariant()
$statusFile=Join-Path $env:LOCALAPPDATA 'GPTWindowsRelayDesktop\runtime-status.json'
$verified=$false
for($i=0;$i -lt 40;$i++){
    if(Test-Path -LiteralPath $statusFile){
        $status=Get-Content -LiteralPath $statusFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if($status.runner_source_sha256 -ceq $expectedHash){$verified=$true;break}
    }
    Start-Sleep -Milliseconds 250
}
if(-not $verified){throw 'NEW_NATIVE_SOURCE_HASH_UNVERIFIED'}
Write-Output ('NEW_NATIVE_SOURCE_HASH='+$expectedHash)
$reconcile=Join-Path $project 'windows-relay\tools\Reconcile-OriginalDesktopHUD.ps1'
$out=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $reconcile)
if($LASTEXITCODE -ne 0 -or ($out -notcontains 'ORIGINAL_HUD_RUNNING_COUNT=1')){
    throw ('HUD_RECONCILIATION_UNCONFIRMED '+($out -join ' | '))
}
Write-Output 'NEW_CANONICAL_HUD_COUNT=1'
if($EnableAutoSend){
    $state=Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $pending=@($state.outbound_deliveries.PSObject.Properties |
       Where-Object {$_.Value.phase -in @('READY','SEND_PENDING','PRE_SUBMIT_FAILED')})
    if($pending.Count -eq 0){
        & $python -B $native auto-send-on | Out-Null
        Write-Output 'AUTO_SEND=ON_NO_PREVIOUS_ELIGIBLE_RESULTS'
    }else{
        Write-Output ('AUTO_SEND=OFF_PRIOR_UNSENT_RESULT_REVIEW_REQUIRED_COUNT='+$pending.Count)
    }
}else{
    Write-Output 'AUTO_SEND=OFF_OPERATOR_MAY_ENABLE_AFTER_SELECTING_TARGET'
}
Write-Output 'CUTOVER=PASS; NO_MAIN_WORKTREE_MUTATION=TRUE'
