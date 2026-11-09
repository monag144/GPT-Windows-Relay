# Windows ChatGPT desktop native safe-smoke gate.
# Executes exactly ONE fixed harmless CMD echo after UIA detects the matching
# packet. General command execution remains disabled because authorship isn't proved.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$id='PCE18-KATANA-OPTEST-003'
$expected='PCE18_OPERATION_003_SUCCESS'
$root=Split-Path -Parent $PSScriptRoot
$scanner=Join-Path $PSScriptRoot 'Watch-ChatGPT-ActionCandidates.ps1'
$sender=Join-Path $PSScriptRoot 'Send-ChatGPT-DesktopHeartbeat.ps1'
$local=Join-Path $env:LOCALAPPDATA 'GPTWindowsRelayNative'
$ledger=Join-Path $local 'safe-smoke-003.reservation.json'
Write-Output 'CHATGPT_DESKTOP_NATIVE_SAFE_SMOKE_V1'
Write-Output ('SMOKE_ACTION_ID='+$id)
Write-Output 'NATIVE_GENERAL_EXECUTION=DISABLED'
function StopRequested {
    foreach($name in @('.relay-paused','.relay-off','.relay-kill','.relay-kill-hud')){
        if(Test-Path -LiteralPath (Join-Path $root $name)){return $true}
    }
    return $false
}
function ConfirmExactCanary {
    # A second independent read prevents an outdated scanner response from
    # triggering a later test in another conversation.
    $rows=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scanner -WatchSeconds 2 -IntervalSeconds 1 2>&1)
    if($LASTEXITCODE -ne 0){return $false}
    $matchingId=$false
    foreach($row in $rows){
        $line=[string]$row
        if($line -match '^CANDIDATE_ID='){
            $matchingId=($line -ceq ('CANDIDATE_ID='+$id))
            continue
        }
        if($matchingId -and $line -ceq 'CANDIDATE_SAFE_SMOKE_MATCH=TRUE'){return $true}
    }
    return $false
}
try{
    if(StopRequested){throw 'NATIVE_OPERATOR_STOP_ACTIVE'}
    if(-not(Test-Path -LiteralPath $scanner)){throw 'NATIVE_SMOKE_SCANNER_MISSING'}
    if(-not(Test-Path -LiteralPath $sender)){throw 'NATIVE_SMOKE_SENDER_MISSING'}
    if(-not(ConfirmExactCanary)){throw 'EXACT_SMOKE_CANARY_NOT_VERIFIED'}
    if(StopRequested){throw 'NATIVE_OPERATOR_STOP_ACTIVE'}
    if(-not(Test-Path -LiteralPath $local)){New-Item -Path $local -ItemType Directory -Force | Out-Null}
    # FileMode.CreateNew is the durable reservation. A crash cannot replay a
    # command that may have executed before results were delivered.
    $record=[ordered]@{version=1;id=$id;phase='RESERVED';utc=[DateTime]::UtcNow.ToString('o')}
    $data=[Text.Encoding]::UTF8.GetBytes(($record|ConvertTo-Json -Compress))
    $stream=$null
    try{
        $stream=[IO.File]::Open($ledger,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        $stream.Write($data,0,$data.Length)
        $stream.Flush($true)
    }catch{
        throw 'SMOKE_RESERVATION_EXISTS_OR_FAILED_REFUSE_REPLAY'
    }finally{
        if($null -ne $stream){$stream.Dispose()}
    }
    Write-Output 'SMOKE_RESERVATION=CREATED_ONCE'
    if(StopRequested){throw 'NATIVE_OPERATOR_STOP_ACTIVE_AFTER_RESERVATION'}
    $cmd=Join-Path $env:SystemRoot 'System32\cmd.exe'
    if(-not(Test-Path -LiteralPath $cmd)){throw 'WINDOWS_CMD_NOT_FOUND'}
    # The command is a literal constant. Do not derive any shell input
    # from the ChatGPT UIA document or scanned packet body.
    $lines=@(& $cmd /d /q /c 'echo PCE18_OPERATION_003_SUCCESS' 2>&1)
    $exitCode=$LASTEXITCODE
    $stdout=(@($lines|ForEach-Object{[string]$_}) -join "`n").Trim()
    $passed=($exitCode -eq 0 -and $stdout -ceq $expected)
    $reportedExit=if($passed){0}else{1}
    $resultLabel=if($passed){'PASS'}else{'FAIL'}
    Write-Output ('SMOKE_CMD_EXECUTION='+$resultLabel)
    Write-Output ('SMOKE_CMD_EXIT_CODE='+$exitCode)
    Write-Output ('SMOKE_OUTPUT_MATCH='+$resultLabel)
    if(StopRequested){throw 'NATIVE_OPERATOR_STOP_ACTIVE_BEFORE_RESULT'}
    # Reuse the native ChatGPT guarded Send-button transport. This is not
    # the Firefox browser pipeline and it does not call /action.
    $reply=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File $sender -SmokeResult -SmokeExitCode $reportedExit 2>&1)
    $replyExit=$LASTEXITCODE
    foreach($row in $reply){
        if([string]$row -match '^(DETECTION=|COMPOSER_BASELINE=|HEARTBEAT_ID=|COMPOSER_INPUT=|COMPOSER_SENDINPUT_EVENTS=|UIA_SEND_BUTTON=|UIA_GUARDED_SEND_BUTTON_CLICK_|DELIVERY=|RESULT=|HEARTBEAT_ERROR=)'){
            Write-Output ('SMOKE_SENDER_'+[string]$row)
        }
    }
    $submitted=(@($reply|Where-Object{$_ -ceq 'RESULT=HEARTBEAT_SUBMITTED'}).Count -gt 0)
    if($submitted -and $replyExit -eq 0){
        Write-Output 'SMOKE_RESULT_DELIVERY=SUBMITTED_LOCALLY_GPT_RECEIPT_REQUIRED'
        exit 0
    }
    Write-Output ('SMOKE_RESULT_DELIVERY=FAILED_OR_UNCERTAIN_EXIT_'+$replyExit)
    Write-Output 'SMOKE_NO_AUTOMATIC_RETRY=TRUE'
    exit 5
}catch{
    Write-Output ('SMOKE_ERROR='+$_.Exception.Message)
    Write-Output 'SMOKE_NO_AUTOMATIC_RETRY=TRUE'
    exit 4
}
