# Native ChatGPT desktop heartbeat V5; operator-invoked; one UIA-targeted physical Send click.
# Never dispatches Windows shell commands or calls the backend executor.
[CmdletBinding()]
param([ValidateRange(2,30)][int]$DetectionSeconds=5,
      [ValidateRange(3,30)][int]$DeliveryTimeoutSeconds=15,
      [switch]$SmokeResult,
      [ValidateSet(0,1)][int]$SmokeExitCode=1,
      [string]$NativeResultPath='',
      [string]$NativeActionId='',
      [string]$NativeReceiptMarker='')
$ErrorActionPreference='Stop'
$canary=if($NativeResultPath){$NativeActionId}elseif($SmokeResult){'PCE18-KATANA-OPTEST-003'}else{'PCE18-KATANA-DETECTION-001'}
$script:wire=''
$script:submitted=$false
# Targeted keyboard event must never reach another app or CMD.
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class DesktopHeartbeatForeground {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int command);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [StructLayout(LayoutKind.Sequential)] public struct MousePoint { public int X; public int Y; }
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out MousePoint pt);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint buttons, UIntPtr extraInfo);
    [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public INPUTUNION U; }
    [StructLayout(LayoutKind.Explicit)] public struct INPUTUNION { [FieldOffset(0)] public KEYBDINPUT ki; }
    [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT {
        public ushort wVk; public ushort wScan; public uint dwFlags; public uint time; public UIntPtr dwExtraInfo;
    }
    [DllImport("user32.dll", SetLastError=true)] public static extern uint SendInput(uint count, INPUT[] inputs, int size);
    const uint INPUT_KEYBOARD=1, KEYEVENTF_UNICODE=0x0004, KEYEVENTF_KEYUP=0x0002;
    public static uint TypeUnicode(string text) {
        if (String.IsNullOrEmpty(text)) return 0;
        INPUT[] inputs=new INPUT[text.Length*2];
        for(int i=0;i<text.Length;i++) {
            inputs[i*2].type=INPUT_KEYBOARD;
            inputs[i*2].U.ki.wScan=text[i];
            inputs[i*2].U.ki.dwFlags=KEYEVENTF_UNICODE;
            inputs[i*2+1].type=INPUT_KEYBOARD;
            inputs[i*2+1].U.ki.wScan=text[i];
            inputs[i*2+1].U.ki.dwFlags=KEYEVENTF_UNICODE|KEYEVENTF_KEYUP;
        }
        return SendInput((uint)inputs.Length,inputs,Marshal.SizeOf(typeof(INPUT)));
    }
}
'@
# The desktop app transport shares STOP/OFF/KILL with the canonical relay.
$canonicalRoot=Split-Path -Parent $PSScriptRoot
$stopMarkers=@('.relay-paused','.relay-off','.relay-kill','.relay-kill-hud')
function Assert-OperatorAllowsDesktopSend {
    foreach($marker in $stopMarkers){
        if(Test-Path -LiteralPath (Join-Path $canonicalRoot $marker)){
            throw 'CANONICAL_OPERATOR_STOP_ACTIVE'
        }
    }
}
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
            # Real Send buttons may not expose a functioning InvokePattern.
            [void]$found.Add(@{node=$node})
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
# UIA ValuePattern may normalize CRLF to LF. Preserve all text bytes except
# newline representation when proving the editor still contains OUR draft.
function Test-OwnHeartbeatDraft([string]$value){
    if([string]::IsNullOrEmpty($script:wire)){return $false}
    $actual=$value.Replace("`r`n","`n").Replace("`r","`n")
    $expected=$script:wire.Replace("`r`n","`n").Replace("`r","`n")
    return $actual -ceq $expected
}
function Assert-ChatGPTForeground($window){
    $chatHandle=[IntPtr]::new([int64]$window.Current.NativeWindowHandle)
    if($chatHandle -eq [IntPtr]::Zero){throw 'CHATGPT_NATIVE_WINDOW_HANDLE_MISSING'}
    [void][DesktopHeartbeatForeground]::ShowWindow($chatHandle,9)
    [void][DesktopHeartbeatForeground]::SetForegroundWindow($chatHandle)
    Start-Sleep -Milliseconds 250
    $foregroundHandle=[DesktopHeartbeatForeground]::GetForegroundWindow()
    $foregroundPid=[uint32]0
    [void][DesktopHeartbeatForeground]::GetWindowThreadProcessId($foregroundHandle,[ref]$foregroundPid)
    if($foregroundPid -ne [int]$window.Current.ProcessId){throw 'CHATGPT_NOT_FOREGROUND_REFUSE_INPUT'}
}
function Set-ComposerTextBySendInput($window,$composer,[string]$text){
    # ValuePattern.SetValue made text visible but did not prove ChatGPT received an
    # editor input/change event.  Use real Unicode keyboard input only after both
    # the ChatGPT window and its composer have been independently verified.
    Assert-ChatGPTForeground $window
    $composer.node.SetFocus()
    Start-Sleep -Milliseconds 120
    if(-not $composer.node.Current.HasKeyboardFocus){throw 'COMPOSER_NOT_FOCUSED_REFUSE_SENDINPUT'}
    $expected=[uint32]($text.Length*2)
    $sent=[DesktopHeartbeatForeground]::TypeUnicode($text)
    if($sent -ne $expected){throw ('SENDINPUT_PARTIAL_INPUT='+$sent+'/'+$expected)}
    Write-Output ('COMPOSER_SENDINPUT_EVENTS='+$sent)
}
function Try-ClearOwnDraft($window){
    if($script:submitted -or [string]::IsNullOrEmpty($script:wire)){return}
    try{
        $c=Get-Composer $window
        if(Test-OwnHeartbeatDraft ([string]$c.pattern.Current.Value)){
            $c.pattern.SetValue('')
            Write-Output 'OWN_UNSENT_DRAFT_CLEARED=ATTEMPTED'
        }
    }catch{}
}
Write-Output 'CHATGPT_DESKTOP_SENDER_V4'
Write-Output 'MODE=CHATGPT_DESKTOP_OUTBOUND_ONLY_NO_COMMAND_EXECUTION'
Write-Output ('DETECTION_CANARY='+$canary)
$window=$null
try{
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    if($NativeResultPath){
        $status='NATIVE_RESULT'
        $level=0
        Write-Output 'DETECTION=NATIVE_RESULT'
    }elseif($SmokeResult){
        # Smoke executor has already validated an exact, fixed CMD canary.
        # No general UIA-origin authentication is implied.
        $status='NOT_APPLICABLE'
        $level=0
        Write-Output 'DETECTION=SMOKE_ONLY'
    }else{
        $detector=Join-Path $PSScriptRoot 'Watch-ChatGPT-ActionCandidates.ps1'
        if(-not(Test-Path -LiteralPath $detector)){throw 'DETECTION_TOOL_MISSING'}
        # Read-only detector; its results are untrusted until a controlled provenance test.
        $lines=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $detector -WatchSeconds $DetectionSeconds -IntervalSeconds 1 2>&1)
        if($LASTEXITCODE -ne 0){throw ('DETECTION_RUNNER_EXIT='+$LASTEXITCODE)}
        $detected=(@($lines|Where-Object{$_ -ceq ('CANDIDATE_ID='+$canary)}).Count -gt 0)
        $status=if($detected){'PASS'}else{'FAIL'}
        $level=if($detected){100}else{50}
        Write-Output ('DETECTION='+$status)
    }
    $window=Get-ChatGPTWindow
    Write-Output 'SENDER_STAGE=APP_WINDOW_FOUND'
    Assert-OperatorAllowsDesktopSend
    $doc=Get-AnchoredDocument $window $canary
    Write-Output 'SENDER_STAGE=CONVERSATION_ANCHOR_FOUND'
    $composer=Get-Composer $window
    Assert-ComposableEmptyState $window $composer
    Write-Output 'SENDER_STAGE=COMPOSER_EMPTY_VERIFIED'
    $eol=[Environment]::NewLine
    if($NativeResultPath){
        if($NativeActionId -cnotmatch '^[A-Za-z0-9._:-]{1,128}$'){
            throw 'NATIVE_ACTION_ID_INVALID'
        }
        if($NativeReceiptMarker -cnotmatch '^NATIVE-RECEIPT-[0-9a-f]{32}$'){
            throw 'NATIVE_RECEIPT_MARKER_INVALID'
        }
        $nativeDir=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'GPTWindowsRelayDesktop\outbox'))
        $actual=[IO.Path]::GetFullPath($NativeResultPath)
        if([IO.Path]::GetDirectoryName($actual) -ine $nativeDir -or
           [IO.Path]::GetExtension($actual) -cne '.txt' -or
           -not(Test-Path -LiteralPath $actual -PathType Leaf)){
            throw 'NATIVE_RESULT_PATH_INVALID'
        }
        $bytes=[IO.File]::ReadAllBytes($actual)
        if($bytes.Length -lt 30 -or $bytes.Length -gt 180000){
            throw 'NATIVE_RESULT_SIZE_INVALID'
        }
        $utf8=New-Object System.Text.UTF8Encoding($false,$true)
        $rawResult=$utf8.GetString($bytes)
        if(-not $rawResult.StartsWith('[GPT_WINDOWS_RESULT]') -or
           -not $rawResult.TrimEnd().EndsWith('[/GPT_WINDOWS_RESULT]') -or
           $rawResult.IndexOf($NativeReceiptMarker,[StringComparison]::Ordinal) -lt 0){
            throw 'NATIVE_RESULT_FRAME_INVALID'
        }
        $parsed=$rawResult.Substring('[GPT_WINDOWS_RESULT]'.Length)
        $parsed=$parsed.Substring(0,$parsed.LastIndexOf('[/GPT_WINDOWS_RESULT]'))
        try{$obj=$parsed.Trim() | ConvertFrom-Json -ErrorAction Stop}
        catch{throw 'NATIVE_RESULT_JSON_INVALID'}
        if($obj.id -cne $NativeActionId -or
           $obj.native_delivery_receipt -cne $NativeReceiptMarker){
            throw 'NATIVE_RESULT_BINDING_MISMATCH'
        }
        $id=$NativeReceiptMarker
        $script:wire=$rawResult
        Write-Output 'SENDER_STAGE=NATIVE_RESULT_BOUND'
    }elseif($SmokeResult){
        $id='PCE18-KATANA-SMOKE-RESULT-003'
        $passed=($SmokeExitCode -eq 0)
        $payload=[ordered]@{
            version=1
            platform='windows'
            id=$id
            source_action_id='PCE18-KATANA-OPTEST-003'
            session='katana.native'
            action='EXEC'
            shell='cmd'
            status=$(if($passed){'OK'}else{'ERROR'})
            exit_code=$SmokeExitCode
            stdout=$(if($passed){'PCE18_OPERATION_003_SUCCESS'}else{''})
            stderr=$(if($passed){''}else{'Fixed smoke command failed validation or execution'})
            origin_authentication='NOT_PROVEN'
            execution_scope='EXACT_SMOKE_ALLOWLIST_ONLY'
        }
        $script:wire='[GPT_WINDOWS_RESULT]'+$eol+($payload|ConvertTo-Json -Compress)+$eol+'[/GPT_WINDOWS_RESULT]'
    }else{
        $id='PCE18-KATANA-HEARTBEAT-V3-'+([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
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
        $script:wire='[GPT_WINDOWS_HEARTBEAT]'+$eol+($payload|ConvertTo-Json -Compress)+$eol+'[/GPT_WINDOWS_HEARTBEAT]'
    }
    Write-Output ('HEARTBEAT_ID='+$id)
    # Newlines require Enter-like semantics in some Electron editors.  The result
    # protocol accepts whitespace around its JSON, so keep the typed wire on one
    # line and reserve the only click for the actual Send control below.
    $script:wire=$script:wire.Replace("`r",'').Replace("`n",' ')
    Write-Output 'SENDER_STAGE=INPUT_BEGIN'
    Set-ComposerTextBySendInput $window $composer $script:wire
    Write-Output 'SENDER_STAGE=INPUT_COMPLETED'
    $send=$null
    for($i=0;$i -lt 25;$i++){
        Start-Sleep -Milliseconds 200
        $composer=Get-Composer $window
        if(-not (Test-OwnHeartbeatDraft ([string]$composer.pattern.Current.Value))){continue}
        $send=Get-EnabledSend $window
        if($null -ne $send){break}
    }
    if($null -eq $send){throw 'COMPOSER_SET_BUT_SEND_NOT_ENABLED'}
    Write-Output 'COMPOSER_INPUT=SENDINPUT_UNICODE_ACCEPTED'
    Write-Output 'UIA_SEND_BUTTON=ENABLED'
    Write-Output 'SENDER_STAGE=SEND_BUTTON_ENABLED'
    $doc=Get-AnchoredDocument $window $canary
    if(Has-Marker $doc $id){throw 'HEARTBEAT_ID_ALREADY_PRESENT_REFUSE_DUPLICATE'}
    $composer=Get-Composer $window
    if(-not (Test-OwnHeartbeatDraft ([string]$composer.pattern.Current.Value))){throw 'COMPOSER_CHANGED_BEFORE_SEND'}
    # Never activate an unverified button via a blind Enter keypress.
    # SendKeys and UIA Invoke did not yield a confirmed ChatGPT submission.
    # Instead, click exactly the enabled UIA Send button in this ChatGPT window.
    Assert-OperatorAllowsDesktopSend
    Assert-ChatGPTForeground $window
    $composer=Get-Composer $window
    if(-not (Test-OwnHeartbeatDraft ([string]$composer.pattern.Current.Value))){
        throw 'COMPOSER_CHANGED_BEFORE_MOUSE_CLICK'
    }
    $doc=Get-AnchoredDocument $window $canary
    if(Has-Marker $doc $id){throw 'HEARTBEAT_ID_ALREADY_PRESENT_REFUSE_DUPLICATE'}
    $send=Get-EnabledSend $window
    if($null -eq $send){throw 'SEND_BUTTON_UNAVAILABLE_BEFORE_MOUSE_CLICK'}
    $rect=$send.node.Current.BoundingRectangle
    $windowRect=$window.Current.BoundingRectangle
    $cx=[int][Math]::Round($rect.Left+$rect.Width/2)
    $cy=[int][Math]::Round($rect.Top+$rect.Height/2)
    if($rect.Width -lt 8 -or $rect.Height -lt 8 -or
       $cx -lt $windowRect.Left -or $cx -ge $windowRect.Right -or
       $cy -lt $windowRect.Top -or $cy -ge $windowRect.Bottom){
        throw 'SEND_BUTTON_OUTSIDE_CHATGPT_WINDOW_REFUSE'
    }
    if(-not $send.node.Current.IsEnabled -or $send.node.Current.IsOffscreen){
        throw 'SEND_BUTTON_NOT_ENABLED_REFUSE'
    }
    $priorCursor=New-Object DesktopHeartbeatForeground+MousePoint
    if(-not [DesktopHeartbeatForeground]::GetCursorPos([ref]$priorCursor)){
        throw 'CURSOR_POSITION_UNAVAILABLE_REFUSE'
    }
    Assert-OperatorAllowsDesktopSend
    Write-Output 'SENDER_STAGE=CLICK_BEGIN'
    Write-Output 'UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN'
    # Once pointer input begins, delivery may be ambiguous: no retries.
    $script:submitted=$true
    try{
        if(-not [DesktopHeartbeatForeground]::SetCursorPos($cx,$cy)){throw 'SET_SEND_CURSOR_FAILED'}
        [DesktopHeartbeatForeground]::mouse_event([uint32]0x0002,0,0,0,[UIntPtr]::Zero)
        Start-Sleep -Milliseconds 90
        [DesktopHeartbeatForeground]::mouse_event([uint32]0x0004,0,0,0,[UIntPtr]::Zero)
    }finally{
        [void][DesktopHeartbeatForeground]::SetCursorPos($priorCursor.X,$priorCursor.Y)
    }
    Write-Output 'UIA_GUARDED_SEND_BUTTON_CLICK_COMPLETED'
    Write-Output 'SENDER_STAGE=CLICK_COMPLETED'
    $confirmed=$false
    $deadline=[DateTime]::UtcNow.AddSeconds($DeliveryTimeoutSeconds)
    while([DateTime]::UtcNow -lt $deadline){
        Start-Sleep -Milliseconds 300
        try{
            $doc=Get-AnchoredDocument $window $canary
            $composer=Get-Composer $window
            $valueAfter=[string]$composer.pattern.Current.Value
            $composerCleared=($valueAfter.Length -eq 0 -or
                ($valueAfter.Trim() -ceq 'Ask ChatGPT' -and
                 (Test-DisabledSendControlPresent $window)))
            if((Has-Marker $doc $id) -and $composerCleared){
                $confirmed=$true
                break
            }
        }catch{}
    }
    if($confirmed){
        Write-Output 'SENDER_STAGE=CONFIRMED_IN_CONVERSATION'
        Write-Output 'DELIVERY=UIA_CONVERSATION_VISIBLE_AND_COMPOSER_CLEARED'
        Write-Output ('LOCAL_PASS_LEVEL='+$level)
        Write-Output 'GPT_RECEIPT_STILL_REQUIRED_FOR_END_TO_END_PROOF'
        Write-Output 'RESULT=HEARTBEAT_SUBMITTED'
        exit 0
    }
    Write-Output 'DELIVERY=GUARDED_CLICK_ATTEMPTED_ACK_UNCONFIRMED'
    Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
    exit 5
}catch{
    Write-Output ('HEARTBEAT_ERROR='+$_.Exception.Message)
    if($null -ne $window){Try-ClearOwnDraft $window}
    Write-Output 'RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY'
    exit 1
}
