# Windows Relay — ChatGPT desktop app command-candidate detector
# READ ONLY. Never executes commands, calls the relay backend, sends UI input or modifies files.
# Candidate text is read into process memory only; no message content or commands are printed.
# Launch from CMD: powershell.exe -NoProfile -ExecutionPolicy Bypass -File "...ps1"
[CmdletBinding()]
param(
    [ValidateRange(1,120)][int]$WatchSeconds=30,
    [ValidateRange(1,5)][int]$IntervalSeconds=2,
    [ValidateRange(100,10000)][int]$MaxElements=5000
)
$ErrorActionPreference='Stop'
$open='[GPT_WINDOWS_ACTION]'
$close='[/GPT_WINDOWS_ACTION]'
$pattern='(?m)^[ \t]*\[GPT_WINDOWS_ACTION\][ \t]*\r?\n(?<body>[\s\S]*?)\r?\n[ \t]*\[/GPT_WINDOWS_ACTION\][ \t]*(?=\r?$)'
$maxPacketChars=65000
$maxDocumentChars=350000
$maxUnique=200
$seen=New-Object 'System.Collections.Generic.HashSet[string]'
$counts=@{scan=0; documents=0; candidates=0; invalid=0; errors=0; new=0; baseline=0}
$hashAlgo=[System.Security.Cryptography.SHA256]::Create()
try {
    Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
    Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop
}catch{
    Write-Output 'RESULT=UIA_ASSEMBLIES_UNAVAILABLE'
    exit 3
}
function Test-RelayCandidate([string]$body){
    if($body.Length -gt $maxPacketChars){return $null}
    try{$obj=$body | ConvertFrom-Json -ErrorAction Stop}catch{return $null}
    if($null -eq $obj -or $obj -is [array]){return $null}
    $names=@($obj.PSObject.Properties.Name)
    if($obj.version -ne 1 -or $obj.platform -cne 'windows' -or $obj.action -cne 'EXEC'){return $null}
    if($obj.id -isnot [string] -or $obj.id -cnotmatch '^[A-Za-z0-9._:-]{1,128}$'){return $null}
    $session=$obj.session
    if($null -eq $session){$session='default'}
    if($session -isnot [string] -or $session -cnotmatch '^[A-Za-z0-9._:-]{1,128}$'){return $null}
    $shell=$obj.shell
    if($null -eq $shell){$shell='powershell'}
    if($shell -isnot [string] -or @('cmd','python','powershell','pwsh') -cnotcontains $shell){return $null}
    $fields=0
    foreach($field in @('command','command_lines','command_b64')){
        if($names -contains $field -and $null -ne $obj.$field){$fields++}
    }
    if($fields -ne 1){return $null}
    if($null -ne $obj.command -and ($obj.command -isnot [string] -or [string]::IsNullOrWhiteSpace($obj.command))){return $null}
    if($null -ne $obj.command_lines){
        if($obj.command_lines -isnot [array] -or $obj.command_lines.Count -eq 0){return $null}
        foreach($line in $obj.command_lines){if($line -isnot [string]){return $null}}
    }
    if($null -ne $obj.command_b64){
        if($obj.command_b64 -isnot [string] -or -not $obj.command_b64){return $null}
        try{
            $bytes=[Convert]::FromBase64String($obj.command_b64)
            $utf8=New-Object System.Text.UTF8Encoding($false,$true)
            $decoded=$utf8.GetString($bytes)
            if([string]::IsNullOrWhiteSpace($decoded)){return $null}
        }catch{return $null}
    }
    if($names -contains 'timeout' -and ($obj.timeout -isnot [int] -and $obj.timeout -isnot [long])){return $null}
    if($names -contains 'timeout' -and ($obj.timeout -lt 1 -or $obj.timeout -gt 300)){return $null}
    # One exact, harmless CMD packet is permitted as a native smoke canary.
    # A user message can spoof UIA text, so this is not general authorization.
    $safeSmoke=(
        $obj.id -ceq 'PCE18-KATANA-OPTEST-003' -and
        $session -ceq 'katana.native' -and
        $shell -ceq 'cmd' -and
        $obj.command -is [string] -and
        $obj.command -ceq 'echo PCE18_OPERATION_003_SUCCESS' -and
        $names.Count -eq 7 -and
        @($names|Where-Object{$_ -cnotin @('version','platform','id','session','action','shell','command')}).Count -eq 0
    )
    return @{id=$obj.id; session=$session; shell=$shell; safeSmoke=$safeSmoke}
}
function Find-ChatGPTWindows {
    $root=[System.Windows.Automation.AutomationElement]::RootElement
    $windows=$root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
    $found=New-Object System.Collections.ArrayList
    foreach($item in $windows){
        try{
            $pidValue=[int]$item.Current.ProcessId
            if($pidValue -le 0){continue}
            $proc=Get-Process -Id $pidValue -ErrorAction SilentlyContinue
            if($proc -and $proc.ProcessName -ieq 'ChatGPT'){[void]$found.Add($item)}
        }catch{$counts.errors++}
    }
    return ,$found
}
function Read-DocumentCandidates($window){
    $nodes=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
    $limit=[Math]::Min([int]$nodes.Count,$MaxElements)
    $results=New-Object System.Collections.ArrayList
    for($i=0;$i -lt $limit;$i++){
        try{
            $node=$nodes.Item($i)
            $type=[string]$node.Current.ControlType.ProgrammaticName
            if($type -ne 'ControlType.Document'){continue}
            $counts.documents++
            $tp=$null
            if(-not $node.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$tp)){continue}
            # Full range is required to see end-of-conversation packets; cap before parsing.
            $value=[string]$tp.DocumentRange.GetText(-1)
            if($value.Length -gt $maxDocumentChars){
                $value=$value.Substring($value.Length-$maxDocumentChars)
            }
            foreach($match in [regex]::Matches($value,$pattern)){
                if($match.Value.Length -gt $maxPacketChars){$counts.invalid++;continue}
                $data=Test-RelayCandidate ([string]$match.Groups['body'].Value)
                if($null -eq $data){$counts.invalid++;continue}
                $payloadBytes=[Text.Encoding]::UTF8.GetBytes($match.Value)
                $hash=[BitConverter]::ToString($hashAlgo.ComputeHash($payloadBytes)).Replace('-','').ToLowerInvariant()
                [void]$results.Add(@{id=$data.id; session=$data.session; shell=$data.shell; hash=$hash; safeSmoke=$data.safeSmoke})
            }
        }catch{$counts.errors++}
    }
    return ,$results
}
Write-Output 'CHATGPT_DESKTOP_CANDIDATE_MONITOR_V1'
Write-Output 'MODE=DETECTION_ONLY_NO_COMMAND_EXECUTION_NO_HTTP_NO_COMPOSER_WRITE'
Write-Output 'ORIGIN=UNVERIFIED_UIA_TEXT'
Write-Output ('WATCH_SECONDS='+$WatchSeconds)
$clock=[Diagnostics.Stopwatch]::StartNew()
$first=$true
$foundApp=$false
while($clock.Elapsed.TotalSeconds -lt $WatchSeconds){
    $counts.scan++
    try{
        $windows=Find-ChatGPTWindows
        if($windows.Count -gt 0){$foundApp=$true}
        foreach($window in $windows){
            $candidateList=Read-DocumentCandidates $window
            foreach($candidate in $candidateList){
                $counts.candidates++
                $key=$candidate.id+':'+$candidate.hash
                if($seen.Count -ge $maxUnique -and -not $seen.Contains($key)){continue}
                if(-not $seen.Add($key)){continue}
                $classification=if($first){'BASELINE_UNTRUSTED'}else{'NEW_UNTRUSTED'}
                if($first){$counts.baseline++}else{$counts.new++}
                Write-Output ('CANDIDATE_ID='+$candidate.id)
                Write-Output ('CANDIDATE_SESSION='+$candidate.session)
                Write-Output ('CANDIDATE_SHELL='+$candidate.shell)
                Write-Output ('CANDIDATE_FINGERPRINT='+$candidate.hash.Substring(0,16))
                Write-Output ('CANDIDATE_STATUS='+$classification)
                $smokeLabel=if($candidate.safeSmoke){'TRUE'}else{'FALSE'}
                Write-Output ('CANDIDATE_SAFE_SMOKE_MATCH='+$smokeLabel)
            }
        }
    }catch{$counts.errors++}
    $first=$false
    $remaining=$WatchSeconds-$clock.Elapsed.TotalSeconds
    if($remaining -gt 0){Start-Sleep -Milliseconds ([Math]::Min(1000*$IntervalSeconds,[int]($remaining*1000)))}
}
Write-Output ('CHATGPT_APP_FOUND='+$foundApp)
Write-Output ('SCANS='+$counts.scan)
Write-Output ('DOCUMENT_READS='+$counts.documents)
Write-Output ('VALID_FRAME_MATCHES='+$counts.candidates)
Write-Output ('DISTINCT_BASELINE_CANDIDATES='+$counts.baseline)
Write-Output ('DISTINCT_NEW_CANDIDATES='+$counts.new)
Write-Output ('INVALID_FRAME_CANDIDATES='+$counts.invalid)
Write-Output ('UIA_ERRORS='+$counts.errors)
Write-Output 'ASSISTANT_AUTHORSHIP_VERIFIED=NO'
Write-Output 'EXECUTIONS=0'
Write-Output 'RESULT=READ_ONLY_DETECTION_COMPLETE'
$hashAlgo.Dispose()
