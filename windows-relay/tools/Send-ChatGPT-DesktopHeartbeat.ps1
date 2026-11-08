# Native ChatGPT desktop heartbeat; operator-invoked, UIA-only, NO command execution.
[CmdletBinding()]
param([ValidateRange(2,30)][int]$DetectionSeconds=5,
      [ValidateRange(3,30)][int]$DeliveryTimeoutSeconds=15)
$ErrorActionPreference='Stop'
$canary='PCE18-KATANA-DETECTION-001'
$script:wire=''
$script:submitted=$false
function Get-ChatGPTWindow {
    $root=[System.Windows.Automation.AutomationElement]::RootElement
    $windows=$root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
    $found=New-Object System.Collections.ArrayList
    foreach($node in $windows){
        try{
            $pidValue=[int]$node.Current.ProcessId
            if($pidValue -le 0){continue}
            $proc=Get-Process -Id $pidValue -ErrorAction SilentlyContinue
            if($proc -and $proc.ProcessName -ieq 'ChatGPT'){[void]$found.Add($node)}
        }catch{}
    }
    if($found.Count -ne 1){throw ('EXPECTED_ONE_CHATGPT_APP_WINDOW_FOUND='+$found.Count)}
    return $found[0]
}
function Descendants($window){
    # Preserve AutomationElementCollection as one object; PS pipelines otherwise
    # enumerate it and break the .Item(index) calls in the downstream probes.
    return ,($window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition))
}
function Has-Marker($document,[string]$value){
    $p=$null
    if(-not $document.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$p)){return $false}
    try{return $null -ne $p.DocumentRange.FindText($value,$false,$false)}
    catch{return $false}
}
function Get-AnchoredDocument($window,[string]$anchor){
    $nodes=Descendants $window
    $found=New-Object System.Collections.ArrayList
    for($i=0;$i -lt $nodes.Count;$i++){
        try{
            $node=$nodes.Item($i)
            if([string]$node.Current.ControlType.ProgrammaticName -eq 'ControlType.Document' -and (Has-Marker $node $anchor)){
                [void]$found.Add($node)
            }
        }catch{}
    }
    if($found.Count -ne 1){throw ('EXPECTED_ONE_DOCUMENT_WITH_CANARY_FOUND='+$found.Count)}
    return $found[0]
}
function Get-Composer($window){
    $nodes=Descendants $window
    $found=New-Object System.Collections.ArrayList
    for($i=0;$i -lt $nodes.Count;$i++){
        try{
            $node=$nodes.Item($i)
            if([string]$node.Current.ControlType.ProgrammaticName -ne 'ControlType.Edit'){continue}
            if([string]$node.Current.Name -notmatch '(?i)ask chatgpt|ask anything|message|prompt|chat'){continue}
            if(-not $node.Current.IsEnabled){continue}
            $p=$null
            if(-not $node.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$p)){continue}
            if(-not $p.Current.IsReadOnly){[void]$found.Add(@{node=$node; pattern=$p})}
        }catch{}
    }
    if($found.Count -ne 1){throw ('EXPECTED_ONE_WRITABLE_COMPOSER_FOUND='+$found.Count)}
    return $found[0]
}
function Get-EnabledSend($window){
    $nodes=Descendants $window
    $found=New-Object System.Collections.ArrayList
    for($i=0;$i -lt $nodes.Count;$i++){
        try{
            $node=$nodes.Item($i)
            if([string]$node.Current.ControlType.ProgrammaticName -ne 'ControlType.Button'){continue}
            if([string]$node.Current.Name -notmatch '(?i)^(send|send message|send prompt|submit)(\b|$)'){continue}
            if($node.Current.IsOffscreen -or -not $node.Current.IsEnabled){continue}
            $p=$null
            if($node.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$p)){
                [void]$found.Add(@{node=$node; pattern=$p})
            }
        }catch{}
    }
    if($found.Count -gt 1){throw ('AMBIGUOUS_ENABLED_SEND_BUTTONS='+$found.Count)}
    if($found.Count -eq 0){return $null}
    return $found[0]
}
# A blank ChatGPT composer can expose its placeholder as the UIA Value.
# Allow only the Katana-observed 11-char "Ask ChatGPT" placeholder plus
# surrounding whitespace, and only if no Send control is enabled, the
# composer is unfocused, and at least one disabled Send control is visible.
# Mere similarity to placeholder wording is NOT sufficient.
function Test-DisabledSendControlPresent($window){
    $nodes=Descendants $window
    $found=0
    for($i=0;$i -lt $nodes.Count;$i++){
        try{
            $node=$nodes.Item($i)
            if([string]$node.Current.ControlType.ProgrammaticName -ne 'ControlType.Button'){continue}
            if([string]$node.Current.Name -notmatch '(?i)^(send|send message|send prompt|submit)(\b|$)'){continue}
            if($node.Current.IsOffscreen){continue}
            $found++
            if($node.Current.IsEnabled){return $false}
        }catch{}
    }
    return ($found -ge 1)
}
function Assert-ComposableEmptyState($window,$composer){
    $value=[string]$composer.pattern.Current.Value
    if($value.Length -eq 0){
        Write-Output 'COMPOSER_BASELINE=EMPTY'
        return
    }
    $trimmed=$value.Trim()
    $looksLikeObservedPlaceholder=($trimmed -ceq 'Ask ChatGPT' -and $value.Length -le 16)
    if(-not $looksLikeObservedPlaceholder){
        throw 'COMPOSER_NOT_EMPTY_REFUSE_TO_OVERWRITE_USER_DRAFT'
    }
    if($composer.node.Current.HasKeyboardFocus){
        throw 'COMPOSER_PLACEHOLDER_AMBIGUOUS_FOCUSED_REFUSE'
    }
    if(-not (Test-DisabledSendControlPresent $window)){
        throw 'COMPOSER_PLACEHOLDER_AMBIGUOUS_SEND_STATE_REFUSE'
    }
    Write-Output 'COMPOSER_BASELINE=UNFOCUSED_PLACEHOLDER_WITH_DISABLED_SEND'
}
function Try-ClearOwnDraft($window){
    if($script:submitted -or [string]::IsNullOrEmpty($script:wire)){return}
    try{
        $c=Get-Composer $window
        if([string]$c.pattern.Current.Value -ceq $script:wire){
            $c.pattern.SetValue('')
            Write-Output 'OWN_UNSENT_DRAFT_CLEARED=ATTEMPTED'
        }
    }catch{}
}
Write-Output 'CHATGPT_DESKTOP_HEARTBEAT_V1'
Write-Output 'MODE=CANNED_MESSAGE_ONLY_NO_COMMAND_EXECUTION_NO_BACKEND'
Write-Output ('DETECTION_CANARY='+$canary)
$window=$null
try{
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    $detector=Join-Path $PSScriptRoot 'Watch-ChatGPT-ActionCandidates.ps1'
    if(-not(Test-Path -LiteralPath $detector)){throw 'DETECTION_TOOL_MISSING'}
    # Read-only detector; its results are untrusted until a controlled provenance test.
    $lines=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $detector -WatchSeconds $DetectionSeconds -IntervalSeconds 1 2>&1)
    if($LASTEXITCODE -ne 0){throw ('DETECTION_RUNNER_EXIT='+$LASTEXITCODE)}
    $detected=(@($lines|Where-Object{$_ -ceq ('CANDIDATE_ID='+$canary)}).Count -gt 0)
    $status=if($detected){'PASS'}else{'FAIL'}
    $level=if($detected){100}else{50}
    Write-Output ('DETECTION='+$status)
    $window=Get-ChatGPTWindow
    $doc=Get-AnchoredDocument $window $canary
    $composer=Get-Composer $window
    Assert-ComposableEmptyState $window $composer
    $id='PCE18-KATANA-HEARTBEAT-'+([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
    $payload=[ordered]@{
        version=1
        platform='windows'
        id=$id
        target='ChatGPT Windows desktop app'
        detection=$status
        delivery='RECEIPT_REQUIRED'
        pass_percent_if_received=$level
        canary=$canary
        command_execution='NOT_TESTED'
    }
    $eol=[Environment]::NewLine
    $script:wire='[GPT_WINDOWS_HEARTBEAT]'+$eol+($payload|ConvertTo-Json -Compress)+$eol+'[/GPT_WINDOWS_HEARTBEAT]'
    Write-Output ('HEARTBEAT_ID='+$id)
    $composer.pattern.SetValue($script:wire)
    $send=$null
    for($i=0;$i -lt 25;$i++){
        Start-Sleep -Milliseconds 200
        $composer=Get-Composer $window
        if([string]$composer.pattern.Current.Value -cne $script:wire){continue}
        $send=Get-EnabledSend $window
        if($null -ne $send){break}
    }
    if($null -eq $send){throw 'COMPOSER_SET_BUT_SEND_NOT_ENABLED'}
    $doc=Get-AnchoredDocument $window $canary
    if(Has-Marker $doc $id){throw 'HEARTBEAT_ID_ALREADY_PRESENT_REFUSE_DUPLICATE'}
    $composer=Get-Composer $window
    if([string]$composer.pattern.Current.Value -cne $script:wire){throw 'COMPOSER_CHANGED_BEFORE_SEND'}
    Write-Output 'UIA_SEND_INVOKE_BEGIN'
    # Once Invoke starts, delivery can be uncertain even if UIA throws.
    # Never clear an already submitted message or retry blindly.
    $script:submitted=$true
    $send.pattern.Invoke()
    $confirmed=$false
    $deadline=[DateTime]::UtcNow.AddSeconds($DeliveryTimeoutSeconds)
    while([DateTime]::UtcNow -lt $deadline){
        Start-Sleep -Milliseconds 300
        try{
            $doc=Get-AnchoredDocument $window $canary
            $composer=Get-Composer $window
            if((Has-Marker $doc $id) -and ([string]$composer.pattern.Current.Value).Length -eq 0){
                $confirmed=$true
                break
            }
        }catch{}
    }
    if($confirmed){
        Write-Output 'DELIVERY=UIA_CONVERSATION_VISIBLE_AND_COMPOSER_CLEARED'
        Write-Output ('LOCAL_PASS_LEVEL='+$level)
        Write-Output 'GPT_RECEIPT_STILL_REQUIRED_FOR_END_TO_END_PROOF'
        Write-Output 'RESULT=HEARTBEAT_SUBMITTED'
        exit 0
    }
    Write-Output 'DELIVERY=SUBMISSION_ATTEMPTED_ACK_UNCONFIRMED'
    Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
    exit 5
}catch{
    Write-Output ('HEARTBEAT_ERROR='+$_.Exception.Message)
    if($null -ne $window){Try-ClearOwnDraft $window}
    Write-Output 'RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY'
    exit 1
}
