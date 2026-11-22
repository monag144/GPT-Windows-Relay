# Native ChatGPT desktop heartbeat V5; operator-invoked; one UIA-targeted physical Send click.
# Never dispatches Windows shell commands or calls the backend executor.
[CmdletBinding()]
param([ValidateRange(2,30)][int]$DetectionSeconds=5,
      [ValidateRange(3,30)][int]$DeliveryTimeoutSeconds=15,
      [switch]$SmokeResult,
      [ValidateSet(0,1)][int]$SmokeExitCode=1,
      [string]$NativeResultPath='',
      [string]$NativeActionId='',
      [string]$NativeReceiptMarker='',
      [switch]$ForceClearComposer,
      [switch]$ProbeComposerOnly,
      [switch]$ClearComposerOnly)
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
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [StructLayout(LayoutKind.Sequential)] public struct MousePoint { public int X; public int Y; }
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out MousePoint pt);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint buttons, UIntPtr extraInfo);
    // SendInput requires the *native* INPUT size (40 bytes on x64, 28 on x86).
    // The union must include MOUSEINPUT: KEYBDINPUT alone makes cbSize too small
    // and SendInput returns zero with ERROR_INVALID_PARAMETER (87).
    [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public INPUTUNION U; }
    [StructLayout(LayoutKind.Explicit)] public struct INPUTUNION {
        [FieldOffset(0)] public MOUSEINPUT mi;
        [FieldOffset(0)] public KEYBDINPUT ki;
    }
    [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT {
        public int dx; public int dy; public uint mouseData; public uint dwFlags;
        public uint time; public UIntPtr dwExtraInfo;
    }
    [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT {
        public ushort wVk; public ushort wScan; public uint dwFlags; public uint time; public UIntPtr dwExtraInfo;
    }
    public static int NativeInputSize() { return Marshal.SizeOf(typeof(INPUT)); }
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
    // Real keyboard edit events are needed: Electron may ignore UIA SetValue
    // for its internal controlled composer even when ValuePattern looks empty.
    // Only call this after verifying the exact ChatGPT focused editor.
    const ushort VK_CONTROL=0x11, VK_A=0x41, VK_BACK=0x08;
    private static INPUT VirtualKey(ushort key, bool up) {
        INPUT input=new INPUT();
        input.type=INPUT_KEYBOARD;
        input.U.ki.wVk=key;
        input.U.ki.dwFlags=up ? KEYEVENTF_KEYUP : 0;
        return input;
    }
    public static uint ClearFocusedComposer() {
        INPUT[] inputs=new INPUT[] {
            VirtualKey(VK_CONTROL,false), VirtualKey(VK_A,false),
            VirtualKey(VK_A,true), VirtualKey(VK_CONTROL,true),
            VirtualKey(VK_BACK,false), VirtualKey(VK_BACK,true)
        };
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
function Get-ConversationDocument($window){
    # A native result's action ID is deliberately new to the conversation until
    # this sender inserts it.  Requiring that ID as a precondition deadlocks
    # result delivery.  The app window is already unique; require exactly one
    # visible text document inside it so we still fail closed on ambiguity.
    $nodes=Descendants $window
    $found=New-Object System.Collections.ArrayList
    for($i=0;$i -lt $nodes.Count;$i++){
        try{
            $node=$nodes.Item($i)
            if([string]$node.Current.ControlType.ProgrammaticName -ne 'ControlType.Document'){continue}
            if($node.Current.IsOffscreen){continue}
            $pattern=$null
            if($node.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$pattern)){
                [void]$found.Add($node)
            }
        }catch{}
    }
    if($found.Count -ne 1){throw ('EXPECTED_ONE_VISIBLE_CONVERSATION_DOCUMENT_FOUND='+$found.Count)}
    return $found[0]
}
function Get-TargetDocument($window,[string]$anchor){
    if($NativeResultPath){return Get-ConversationDocument $window}
    return Get-AnchoredDocument $window $anchor
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
function Wait-ForComposer($window,[int]$TimeoutMilliseconds=3000){
    # ChatGPT can briefly rebuild its UIA tree after a draft is cleared.  This
    # is pre-input discovery only: wait for a unique writable editor rather
    # than consuming a one-time delivery retry on that transient condition.
    $deadline=[DateTime]::UtcNow.AddMilliseconds($TimeoutMilliseconds)
    $last='COMPOSER_DISCOVERY_UNAVAILABLE'
    while([DateTime]::UtcNow -lt $deadline){
        try{return Get-Composer $window}
        catch{$last=$_.Exception.Message}
        Start-Sleep -Milliseconds 150
    }
    throw ('COMPOSER_DISCOVERY_TIMEOUT='+$last)
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
# Allow only the exact Katana-observed "Ask ChatGPT" placeholder with either a
# disabled named Send control, or independently empty TextPattern with no
# enabled named Send control. Focus alone never proves emptiness.
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
# UIA can expose visible placeholder text through ValuePattern while its
# independent TextPattern document range is genuinely empty. This is the only
# fallback when the app does not publish a disabled named Send control.
# Never infer emptiness from placeholder wording alone, TextPattern absence,
# a failed read, or a merely disabled/unfocused editor.
function Test-ComposerTextPatternEmpty($composer){
    $textPattern=$null
    try{
        if(-not $composer.node.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$textPattern)){
            return $false
        }
        if($null -eq $textPattern){return $false}
        $text=[string]$textPattern.DocumentRange.GetText(-1)
        return ($text.Length -eq 0)
    }catch{return $false}
}
# A UIA Value can contain the visible placeholder instead of actual input.
# Keep the state check pure so calls from a function returning a composer do
# not accidentally return diagnostic strings as part of that composer.
function Test-ComposableEmptyState($window,$composer){
    $value=[string]$composer.pattern.Current.Value
    if($value.Length -eq 0){return $true}
    $trimmed=$value.Trim()
    $looksLikeObservedPlaceholder=($trimmed -ceq 'Ask ChatGPT' -and $value.Length -le 16)
    if(-not $looksLikeObservedPlaceholder){return $false}
    if(Test-DisabledSendControlPresent $window){return $true}
    # Require an independent, exact empty TextPattern AND no enabled named
    # Send control. If the provider exposes placeholder text in both patterns,
    # refuse rather than risking a real draft that says "Ask ChatGPT".
    if(-not (Test-ComposerTextPatternEmpty $composer)){return $false}
    return ($null -eq (Get-EnabledSend $window))
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
    $disabledNamedSend=Test-DisabledSendControlPresent $window
    if(-not $disabledNamedSend){
        if(-not (Test-ComposerTextPatternEmpty $composer)){
            throw 'COMPOSER_PLACEHOLDER_AMBIGUOUS_SEND_STATE_REFUSE'
        }
        if($null -ne (Get-EnabledSend $window)){
            throw 'COMPOSER_PLACEHOLDER_AMBIGUOUS_SEND_STATE_REFUSE'
        }
        Write-Output 'COMPOSER_BASELINE=PLACEHOLDER_WITH_EMPTY_TEXTPATTERN_NO_ENABLED_SEND'
        return
    }
    if($composer.node.Current.HasKeyboardFocus){
        Write-Output 'COMPOSER_BASELINE=FOCUSED_PLACEHOLDER_WITH_DISABLED_SEND'
        return
    }
    Write-Output 'COMPOSER_BASELINE=UNFOCUSED_PLACEHOLDER_WITH_DISABLED_SEND'
}
function Clear-ComposerForForcedDelivery($window,$composer){
    # Explicit operator-approved clear only. UIA SetValue('') did not reliably
    # update ChatGPT's controlled editor; a real focused Ctrl+A, Backspace does.
    # Never type a result or press Send here; preserve the saved delivery state.
    if(Test-ComposableEmptyState $window $composer){return $composer}
    Assert-ChatGPTForeground $window
    if($composer.pattern.Current.IsReadOnly){throw 'COMPOSER_READ_ONLY_REFUSE_FORCE_CLEAR'}
    $composer.node.SetFocus()
    Start-Sleep -Milliseconds 120
    Assert-ChatGPTForeground $window
    if(-not $composer.node.Current.HasKeyboardFocus){
        throw 'COMPOSER_CLEAR_NOT_FOCUSED_REFUSE_KEYBOARD'
    }
    $sent=[DesktopHeartbeatForeground]::ClearFocusedComposer()
    if($sent -ne 6){
        throw ('COMPOSER_CLEAR_KEYBOARD_INCOMPLETE='+$sent+'/6')
    }
    for($i=0;$i -lt 20;$i++){
        Start-Sleep -Milliseconds 100
        try{
            $current=Get-Composer $window
            if(Test-ComposableEmptyState $window $current){return $current}
        }catch{
            # The editor may be transiently unavailable while ChatGPT redraws.
        }
    }
    throw 'COMPOSER_FORCE_CLEAR_NOT_CONFIRMED'
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
    # Do not restore, resize, or rearrange the operator's desktop.  The target
    # conversation must already be visible; foreground verification below
    # fails closed if it is not.
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
    $nativeSize=[DesktopHeartbeatForeground]::NativeInputSize()
    $requiredSize=if([IntPtr]::Size -eq 8){40}else{28}
    if($nativeSize -ne $requiredSize){throw ('SENDINPUT_STRUCT_SIZE_INVALID='+$nativeSize+'/'+$requiredSize)}
    Write-Output ('SENDINPUT_STRUCT_SIZE='+$nativeSize)
    $expected=[uint32]($text.Length*2)
    $sent=[DesktopHeartbeatForeground]::TypeUnicode($text)
    if($sent -ne $expected){
        $win32=[Runtime.InteropServices.Marshal]::GetLastWin32Error()
        throw ('SENDINPUT_PARTIAL_INPUT='+$sent+'/'+$expected+';WIN32_ERROR='+$win32)
    }
    Write-Output ('COMPOSER_SENDINPUT_EVENTS='+$sent)
}
function Report-UnsentDraftState($window){
    # If a pre-click submission fails, keep OUR unsent packet in the composer
    # for operator inspection. Force Clear is an explicit separate control;
    # a failed sender must never silently discard a visible result.
    # Report metadata only: never log message text or clipboard contents.
    if($script:submitted -or [string]::IsNullOrEmpty($script:wire)){return}
    try{
        $c=Get-Composer $window
        $value=[string]$c.pattern.Current.Value
        if(Test-OwnHeartbeatDraft $value){
            Write-Output 'OWN_UNSENT_DRAFT=PRESERVED_IN_COMPOSER'
        }elseif(Test-ComposableEmptyState $window $c){
            Write-Output 'OWN_UNSENT_DRAFT=NO_DRAFT_VISIBLE'
        }else{
            Write-Output 'OWN_UNSENT_DRAFT=CHANGED_OR_UNVERIFIED_NO_MUTATION'
        }
    }catch{
        Write-Output 'OWN_UNSENT_DRAFT=COMPOSER_UNREADABLE_NO_MUTATION'
    }
}
Write-Output 'CHATGPT_DESKTOP_SENDER_V4'
Write-Output 'MODE=CHATGPT_DESKTOP_OUTBOUND_ONLY_NO_COMMAND_EXECUTION'
Write-Output ('DETECTION_CANARY='+$canary)
$window=$null
try{
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    if($ClearComposerOnly -and ($NativeResultPath -or $NativeActionId -or
            $NativeReceiptMarker -or $ForceClearComposer -or $ProbeComposerOnly -or
            $SmokeResult)){
        throw 'COMPOSER_CLEAR_INCOMPATIBLE_SEND_OR_PROBE_FLAGS'
    }
    if($ClearComposerOnly){
        $status='NOT_APPLICABLE'
        $level=0
        Write-Output 'DETECTION=OPERATOR_CLEAR_COMPOSER_ONLY'
    }elseif($ProbeComposerOnly){
        # Diagnostics must not run the 5-second command scanner or report the
        # expected absent smoke canary as a spurious delivery failure.
        $status='NOT_APPLICABLE'
        $level=0
        Write-Output 'DETECTION=READ_ONLY_UIA_PROBE'
    }elseif($NativeResultPath){
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
    if($ClearComposerOnly){
        # Dedicated manual action. Require exactly one ChatGPT window,
        # conversation document and writable composer. Do not load a native
        # result, release a delivery hold, type a packet or click Send.
        $null=Get-ConversationDocument $window
        $runtimeFile=Join-Path $env:LOCALAPPDATA 'GPTWindowsRelayDesktop\runtime-status.json'
        if(Test-Path -LiteralPath $runtimeFile -PathType Leaf){
            try{
                $runtimeStatus=Get-Content -LiteralPath $runtimeFile -Raw -Encoding UTF8 | ConvertFrom-Json
            }catch{
                throw 'COMPOSER_CLEAR_RUNTIME_STATUS_UNREADABLE'
            }
            if([string]$runtimeStatus.phase -eq 'DELIVERING'){
                throw 'COMPOSER_CLEAR_REFUSE_DURING_NATIVE_DELIVERY'
            }
        }
        $composer=Wait-ForComposer $window
        if(Test-ComposableEmptyState $window $composer){
            Write-Output 'COMPOSER_CLEAR=ALREADY_EMPTY'
        }else{
            Assert-ChatGPTForeground $window
            $composer=Clear-ComposerForForcedDelivery $window $composer
            Assert-ComposableEmptyState $window $composer
            Write-Output 'COMPOSER_CLEAR=VERIFIED_EMPTY'
        }
        Write-Output 'RESULT=COMPOSER_CLEARED_NO_SEND'
        exit 0
    }
    if($ProbeComposerOnly){
        # Read-only UIA diagnostics. Never focus, clear, type, click, or print
        # draft text. Used to validate ChatGPT's actual accessibility controls.
        $probe=Wait-ForComposer $window
        $value=[string]$probe.pattern.Current.Value
        $valueClass=if($value.Length -eq 0){'EMPTY'}elseif($value.Trim() -ceq 'Ask ChatGPT'){'PLACEHOLDER_CANDIDATE'}else{'NONEMPTY_REDACTED'}
        $textClass='UNAVAILABLE'
        $textLength=-1
        $textPattern=$null
        if($probe.node.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$textPattern)){
            try{
                $textValue=[string]$textPattern.DocumentRange.GetText(-1)
                $textLength=$textValue.Length
                $textClass=if($textLength -eq 0){'EMPTY'}elseif($textValue.Trim() -ceq 'Ask ChatGPT'){'PLACEHOLDER_CANDIDATE'}else{'NONEMPTY_REDACTED'}
            }catch{$textClass='UNREADABLE'}
        }
        $matchingSend=0
        $disabledSend=0
        $enabledSend=0
        $unnamedNearby=0
        $composerRect=$probe.node.Current.BoundingRectangle
        $nodes=Descendants $window
        for($i=0;$i -lt $nodes.Count;$i++){
            try{
                $node=$nodes.Item($i)
                if([string]$node.Current.ControlType.ProgrammaticName -ne 'ControlType.Button' -or $node.Current.IsOffscreen){continue}
                $name=[string]$node.Current.Name
                if($name -match '(?i)^(send|send message|send prompt|submit)(\b|$)'){
                    $matchingSend++
                    if($node.Current.IsEnabled){$enabledSend++}else{$disabledSend++}
                }elseif([string]::IsNullOrEmpty($name)){
                    $rect=$node.Current.BoundingRectangle
                    if($rect.Left -ge ($composerRect.Left-80) -and $rect.Right -le ($composerRect.Right+80) -and
                       $rect.Top -ge ($composerRect.Top-80) -and $rect.Top -le ($composerRect.Bottom+80)){
                        $unnamedNearby++
                    }
                }
            }catch{}
        }
        Write-Output 'UIA_COMPOSER_PROBE=READ_ONLY_NO_INPUT'
        Write-Output ('PROBE_VALUE_CLASS='+$valueClass)
        Write-Output ('PROBE_VALUE_LENGTH='+$value.Length)
        Write-Output ('PROBE_TEXT_CLASS='+$textClass)
        Write-Output ('PROBE_TEXT_LENGTH='+$textLength)
        Write-Output ('PROBE_HAS_KEYBOARD_FOCUS='+$probe.node.Current.HasKeyboardFocus)
        Write-Output ('PROBE_MATCHING_SEND='+$matchingSend)
        Write-Output ('PROBE_DISABLED_SEND='+$disabledSend)
        Write-Output ('PROBE_ENABLED_SEND='+$enabledSend)
        Write-Output ('PROBE_UNNAMED_BUTTONS_NEAR_COMPOSER='+$unnamedNearby)
        Write-Output ('PROBE_INDEPENDENT_TEXTPATTERN_EMPTY='+(Test-ComposerTextPatternEmpty $probe))
        Write-Output ('PROBE_EMPTY_VERIFIED='+(Test-ComposableEmptyState $window $probe))
        Write-Output 'RESULT=COMPOSER_PROBE_COMPLETED_NO_SEND'
        exit 0
    }
    Assert-OperatorAllowsDesktopSend
    $doc=Get-TargetDocument $window $canary
    Write-Output 'SENDER_STAGE=CONVERSATION_DOCUMENT_FOUND'
    $composer=Wait-ForComposer $window
    if($ForceClearComposer){
        if(-not $NativeResultPath){throw 'FORCE_CLEAR_REQUIRES_SAVED_NATIVE_RESULT'}
        $composer=Clear-ComposerForForcedDelivery $window $composer
        # Return one composer object, never a mix of diagnostics and UIA nodes.
        Write-Output 'COMPOSER_FORCED_CLEAR=COMPLETED'
        Write-Output 'SENDER_STAGE=COMPOSER_FORCE_CLEARED'
    }
    Assert-ComposableEmptyState $window $composer
    Write-Output 'SENDER_STAGE=COMPOSER_DISCOVERY_READY'
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
    $draftMatches=$false
    $readFailures=0
    # ChatGPT can rebuild UIA nodes after a long Unicode input. Retry transient
    # discovery without clearing the draft or trying a blind Enter click.
    for($i=0;$i -lt 50;$i++){
        Start-Sleep -Milliseconds 200
        try{$composer=Get-Composer $window}
        catch{
            $readFailures++
            continue
        }
        $draftMatches=Test-OwnHeartbeatDraft ([string]$composer.pattern.Current.Value)
        if(-not $draftMatches){continue}
        # Do not swallow AMBIGUOUS_ENABLED_SEND_BUTTONS or any other unsafe
        # send-control state as a transient editor-discovery error.
        $send=Get-EnabledSend $window
        if($null -ne $send){break}
    }
    if($null -eq $send){
        Write-Output 'SENDER_STAGE=SEND_BUTTON_NOT_READY'
        Write-Output ('UIA_SEND_READY_DRAFT_MATCH='+$draftMatches)
        Write-Output ('UIA_SEND_READY_READ_FAILURES='+$readFailures)
        throw 'COMPOSER_SET_BUT_SEND_NOT_ENABLED'
    }
    Write-Output 'COMPOSER_INPUT=SENDINPUT_UNICODE_ACCEPTED'
    Write-Output 'UIA_SEND_BUTTON=ENABLED'
    Write-Output 'SENDER_STAGE=SEND_BUTTON_ENABLED'
    $doc=Get-TargetDocument $window $canary
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
    $doc=Get-TargetDocument $window $canary
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
            $doc=Get-TargetDocument $window $canary
            $composer=Get-Composer $window
            $valueAfter=[string]$composer.pattern.Current.Value
            $composerCleared=(Test-ComposableEmptyState $window $composer)
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
    if($ClearComposerOnly){
        Write-Output 'RESULT=COMPOSER_CLEAR_FAILED_NO_SEND'
        exit 1
    }
    if($null -ne $window){Report-UnsentDraftState $window}
    Write-Output 'RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY'
    exit 1
}
