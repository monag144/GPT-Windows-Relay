# Windows ChatGPT desktop relay monitor (pre-execution phase).
# Continuously observes complete action packets via UI Automation, without executing them.
# On startup, attempts one canned heartbeat to this conversation, deferring non-empty drafts.
# This is an explicitly started operator process; close its CMD window or Ctrl+C to stop.
[CmdletBinding()]
param(
    [ValidateRange(3,60)][int]$ScanSeconds=8,
    [ValidateRange(2,60)][int]$PauseSeconds=4
)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$scanner=Join-Path $root 'Watch-ChatGPT-ActionCandidates.ps1'
$heartbeat=Join-Path $root 'Send-ChatGPT-DesktopHeartbeat.ps1'
$localRoot=Join-Path $env:LOCALAPPDATA 'GPTWindowsRelay'
$ledger=Join-Path $localRoot 'desktop-heartbeat-ledger.json'
$canary='PCE18-KATANA-DETECTION-001'
$known=New-Object 'System.Collections.Generic.HashSet[string]'
$created=$false
$mutex=[System.Threading.Mutex]::new($true,'Local\GPTWindowsDesktopMonitor',[ref]$created)
if(-not $created){
    Write-Output 'DESKTOP_MONITOR_ALREADY_RUNNING'
    $mutex.Dispose()
    exit 0
}
function Read-Ledger {
    if(-not(Test-Path -LiteralPath $ledger)){return $null}
    try{
        $v=Get-Content -LiteralPath $ledger -Raw -Encoding UTF8 | ConvertFrom-Json
        if($v.canary -eq $canary){return $v}
    }catch{}
    # Corrupt or ambiguous journal requires operator investigation, not resend.
    throw 'HEARTBEAT_JOURNAL_UNREADABLE_REFUSE_DUPLICATE'
}
function Save-Ledger([string]$status,[string]$id=''){
    if(-not(Test-Path -LiteralPath $localRoot)){New-Item -ItemType Directory -Path $localRoot -Force | Out-Null}
    $record=[ordered]@{
        version=1
        canary=$canary
        status=$status
        heartbeat_id=$id
        time_utc=[DateTime]::UtcNow.ToString('o')
    }
    # Journal records status/ID only. No packet body, results or secrets.
    $temp=Join-Path $localRoot 'desktop-heartbeat-ledger.pending'
    $json=$record|ConvertTo-Json -Compress
    [IO.File]::WriteAllText($temp,$json,[Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temp -Destination $ledger -Force
}
try {
    if(-not(Test-Path -LiteralPath $scanner)){throw 'SCANNER_MISSING'}
    if(-not(Test-Path -LiteralPath $heartbeat)){throw 'HEARTBEAT_SCRIPT_MISSING'}
    Write-Output 'CHATGPT_DESKTOP_MONITOR_V1'
    Write-Output 'MODE=CONTINUOUS_AUTOMATIC_DETECTION_AND_ONE_HEARTBEAT'
    Write-Output 'WINDOWS_COMMAND_EXECUTION=DISABLED_UNTRUSTED_UIA_ORIGIN'
    Write-Output 'OPERATOR_STOP=CLOSE_THIS_WINDOW_OR_CTRL_C'
    Write-Output ('SCAN_SECONDS='+$ScanSeconds)
    $iteration=0
    while($true){
        $iteration++
        $scan=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scanner -WatchSeconds $ScanSeconds -IntervalSeconds 1 2>&1)
        $exitCode=$LASTEXITCODE
        if($exitCode -ne 0){
            Write-Output ('SCAN_ERROR_EXIT='+$exitCode)
        }else{
            $ids=@($scan|Where-Object{$_ -match '^CANDIDATE_ID=[A-Za-z0-9._:-]+$'})
            foreach($line in $ids){
                $id=([string]$line).Substring('CANDIDATE_ID='.Length)
                if($known.Add($id)){
                    Write-Output ('DESKTOP_ACTION_DETECTED='+$id)
                    Write-Output 'DESKTOP_ACTION_STATUS=OBSERVED_NOT_EXECUTED'
                }
            }
            if($iteration%4 -eq 1){
                Write-Output ('MONITOR_HEARTBEAT_UTC='+[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))
                Write-Output ('MONITOR_CANDIDATE_COUNT='+$known.Count)
            }
        }
        $state=Read-Ledger
        $terminal=@('SUBMISSION_ATTEMPTED','DELIVERED_LOCALLY','DELIVERY_UNCERTAIN','FAILED_NEEDS_REVIEW')
        if($null -eq $state -or $state.status -eq 'BLOCKED_BY_DRAFT'){
            # First mark intent, then attempt. This is fail-closed after a crash;
            # it never automatically retries a possibly submitted heartbeat.
            Save-Ledger 'SUBMISSION_ATTEMPTED'
            $result=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $heartbeat -DetectionSeconds 3 -DeliveryTimeoutSeconds 15 2>&1)
            $heartbeatExit=$LASTEXITCODE
            $idLine=@($result|Where-Object{$_ -match '^HEARTBEAT_ID='}|Select-Object -First 1)
            $hbId=if($idLine.Count){([string]$idLine[0]).Substring('HEARTBEAT_ID='.Length)}else{''}
            $begun=(@($result|Where-Object{$_ -eq 'UIA_SEND_INVOKE_BEGIN'}).Count -gt 0)
            $draft=(@($result|Where-Object{$_ -match '^HEARTBEAT_ERROR=COMPOSER_NOT_EMPTY_REFUSE_TO_OVERWRITE_USER_DRAFT$'}).Count -gt 0)
            $passed=(@($result|Where-Object{$_ -eq 'RESULT=HEARTBEAT_SUBMITTED'}).Count -gt 0)
            $uncertain=(@($result|Where-Object{$_ -eq 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'}).Count -gt 0)
            if($passed){
                Save-Ledger 'DELIVERED_LOCALLY' $hbId
                Write-Output ('DESKTOP_HEARTBEAT_SUBMITTED_ID='+$hbId)
                Write-Output 'DESKTOP_HEARTBEAT_RECEIPT_REQUIRED=TRUE'
            }elseif($uncertain -or $begun){
                Save-Ledger 'DELIVERY_UNCERTAIN' $hbId
                Write-Output 'DESKTOP_HEARTBEAT_DELIVERY_UNCERTAIN=NO_RETRY'
            }elseif($draft){
                Save-Ledger 'BLOCKED_BY_DRAFT'
                Write-Output 'DESKTOP_HEARTBEAT=WAITING_FOR_EMPTY_COMPOSER'
            }else{
                Save-Ledger 'FAILED_NEEDS_REVIEW' $hbId
                Write-Output ('DESKTOP_HEARTBEAT_FAILED_EXIT='+$heartbeatExit)
                foreach($line in $result){
                    if([string]$line -match '^(HEARTBEAT_ERROR|RESULT|DETECTION)='){
                        Write-Output ('HEARTBEAT_DETAIL='+[string]$line)
                    }
                }
            }
        }
        Start-Sleep -Seconds $PauseSeconds
    }
}finally{
    try{$mutex.ReleaseMutex()}catch{}
    $mutex.Dispose()
    Write-Output 'DESKTOP_MONITOR_STOPPED'
}
