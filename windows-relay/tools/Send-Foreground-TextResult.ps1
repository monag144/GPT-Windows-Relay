# Command Courier foreground UIA destination. No configured input source required.
# Sends the already-owned native result to the focused writable text field.
# App-independent text insertion; Send button activation is only attempted
# when there is a unique explicit Send/Submit button in the same window.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$NativeResultPath,
    [Parameter(Mandatory=$true)][string]$NativeActionId,
    [Parameter(Mandatory=$true)][string]$NativeReceiptMarker,
    [switch]$SubmitExistingOnly,
    [switch]$ManualForceSend
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class CourierForegroundInput {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr handle,out uint processId);
    [StructLayout(LayoutKind.Sequential)] public struct INPUT {public uint type; public INPUTUNION U;}
    [StructLayout(LayoutKind.Explicit)] public struct INPUTUNION {
        [FieldOffset(0)] public MOUSEINPUT mi;
        [FieldOffset(0)] public KEYBDINPUT ki;
    }
    [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT {
        public int dx; public int dy; public uint mouseData; public uint dwFlags;
        public uint time; public UIntPtr dwExtraInfo;
    }
    [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT {
        public ushort wVk; public ushort wScan; public uint dwFlags;
        public uint time; public UIntPtr dwExtraInfo;
    }
    [DllImport("user32.dll", SetLastError=true)]
    public static extern uint SendInput(uint count,INPUT[] inputs,int size);
    public static int InputSize(){return Marshal.SizeOf(typeof(INPUT));}
    public static uint TypeUnicode(string body){
        if(String.IsNullOrEmpty(body)) return 0;
        INPUT[] keys=new INPUT[body.Length*2];
        for(int i=0;i<body.Length;i++){
            keys[i*2].type=1; keys[i*2].U.ki.wScan=body[i];
            keys[i*2].U.ki.dwFlags=0x0004;
            keys[i*2+1].type=1; keys[i*2+1].U.ki.wScan=body[i];
            keys[i*2+1].U.ki.dwFlags=0x0004|0x0002;
        }
        return SendInput((uint)keys.Length,keys,Marshal.SizeOf(typeof(INPUT)));
    }
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT point);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,uint data,UIntPtr extra);
    [StructLayout(LayoutKind.Sequential)] public struct POINT {public int X;public int Y;}
}
'@

function Test-EligibleEditor($window,$node){
    if($null -eq $node){return $false}
    try{
        if(-not $node.Current.IsEnabled -or $node.Current.IsOffscreen -or
           $node.Current.IsPassword){return $false}
        $kind=[string]$node.Current.ControlType.ProgrammaticName
        if($kind -notin @('ControlType.Edit','ControlType.Document')){return $false}
        $bounds=$node.Current.BoundingRectangle
        $root=$window.Current.BoundingRectangle
        if($bounds.Width -lt 8 -or $bounds.Height -lt 8 -or
           $bounds.Left -lt $root.Left -or $bounds.Top -lt $root.Top -or
           $bounds.Right -gt $root.Right -or $bounds.Bottom -gt $root.Bottom){
            return $false
        }
        $walk=[System.Windows.Automation.TreeWalker]::RawViewWalker
        $rootId=($window.GetRuntimeId() -join ',')
        $cursor=$node
        $belongs=$false
        for($depth=0;$depth -lt 60 -and $null -ne $cursor;$depth++){
            if(($cursor.GetRuntimeId() -join ',') -ceq $rootId){
                $belongs=$true
                break
            }
            $cursor=$walk.GetParent($cursor)
        }
        if(-not $belongs){return $false}
        $value=$null
        $text=$null
        $supportsValue=$node.TryGetCurrentPattern(
            [System.Windows.Automation.ValuePattern]::Pattern,[ref]$value)
        $supportsText=$node.TryGetCurrentPattern(
            [System.Windows.Automation.TextPattern]::Pattern,[ref]$text)
        if($supportsValue -and $value.Current.IsReadOnly){return $false}
        return ($supportsValue -or $supportsText)
    }catch{
        return $false
    }
}

function Test-IsSelfOrChild($node,$parent){
    # Focus may live on a child text node inside the writable editor.
    if($null -eq $node -or $null -eq $parent){return $false}
    try{
        $id=($parent.GetRuntimeId() -join ',')
        $walker=[System.Windows.Automation.TreeWalker]::RawViewWalker
        $cursor=$node
        for($depth=0;$depth -lt 60 -and $null -ne $cursor;$depth++){
            if(($cursor.GetRuntimeId() -join ',') -ceq $id){return $true}
            $cursor=$walker.GetParent($cursor)
        }
    }catch{}
    return $false
}

function Test-EditorOwnsFocus($editor){
    try{
        $focused=[System.Windows.Automation.AutomationElement]::FocusedElement
        return ($null -ne $focused -and $focused.Current.HasKeyboardFocus -and
                -not $focused.Current.IsPassword -and
                (Test-IsSelfOrChild $focused $editor))
    }catch{return $false}
}

function Resolve-FocusedEditor($window,$focused){
    # Prefer operator-selected field, even with a focused Text/Custom child.
    if($null -eq $focused){return $null}
    try{
        if(-not $focused.Current.HasKeyboardFocus -or $focused.Current.IsPassword -or
           $focused.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button){
            return $null
        }
        $windowId=($window.GetRuntimeId() -join ',')
        $walker=[System.Windows.Automation.TreeWalker]::RawViewWalker
        $cursor=$focused
        for($depth=0;$depth -lt 60 -and $null -ne $cursor;$depth++){
            if(($cursor.GetRuntimeId() -join ',') -ceq $windowId){break}
            if(Test-EligibleEditor $window $cursor){
                # A whole-page Document is not proof that its focused
                # child is an input field.
                $rect=$cursor.Current.BoundingRectangle
                $root=$window.Current.BoundingRectangle
                $pageWide=([string]$cursor.Current.ControlType.ProgrammaticName -eq
                    'ControlType.Document' -and
                    $rect.Width -gt ($root.Width * 0.75) -and
                    $rect.Height -gt ($root.Height * 0.65))
                if(-not $pageWide){return $cursor}
            }
            $cursor=$walker.GetParent($cursor)
        }
    }catch{}
    return $null
}

function Focus-CandidateEditor($window,$editor,[IntPtr]$handle){
    if([CourierForegroundInput]::GetForegroundWindow() -ne $handle){return $false}
    try{
        $editor.SetFocus()
        Start-Sleep -Milliseconds 100
    }catch{}
    if(Test-EditorOwnsFocus $editor){return $true}

    # Some Electron/Scintilla editors do not honor UIA SetFocus. Click the
    # center of the VERIFIED editor, not any screen coordinate guessed from
    # a specific application's geometry or the Enter/Send control.
    if([CourierForegroundInput]::GetForegroundWindow() -ne $handle){return $false}
    $bounds=$editor.Current.BoundingRectangle
    $x=[int][Math]::Round(($bounds.Left+$bounds.Right)/2)
    $y=[int][Math]::Round(($bounds.Top+$bounds.Bottom)/2)
    $root=$window.Current.BoundingRectangle
    if($x -lt $root.Left -or $x -ge $root.Right -or
       $y -lt $root.Top -or $y -ge $root.Bottom){return $false}
    $saved=New-Object CourierForegroundInput+POINT
    if(-not [CourierForegroundInput]::GetCursorPos([ref]$saved)){return $false}
    try{
        if(-not [CourierForegroundInput]::SetCursorPos($x,$y)){return $false}
        [CourierForegroundInput]::mouse_event([uint32]2,0,0,0,[UIntPtr]::Zero)
        Start-Sleep -Milliseconds 45
        [CourierForegroundInput]::mouse_event([uint32]4,0,0,0,[UIntPtr]::Zero)
    }finally{
        [void][CourierForegroundInput]::SetCursorPos($saved.X,$saved.Y)
    }
    Start-Sleep -Milliseconds 120
    if([CourierForegroundInput]::GetForegroundWindow() -ne $handle){return $false}
    return (Test-EditorOwnsFocus $editor)
}

function Get-ForegroundEditable {
    $hwnd=[CourierForegroundInput]::GetForegroundWindow()
    if($hwnd -eq [IntPtr]::Zero){return $null}
    $window=[System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
    if($null -eq $window){return $null}
    # Terminal text panes must not execute result-body code as keystrokes.
    $proc=Get-Process -Id ([int]$window.Current.ProcessId) -ErrorAction SilentlyContinue
    if($proc -and $proc.ProcessName -match
       '^(?i:cmd|powershell|pwsh|windowsterminal|openconsole|conhost|wt)$'){
        return $null
    }
    $focused=[System.Windows.Automation.AutomationElement]::FocusedElement
    $editor=$null
    $editor=Resolve-FocusedEditor $window $focused
    if($null -eq $editor){
        # Do not demand an already-clicked composer. Discover a single
        # visible writable Edit/Document target from the FOREGROUND app.
        $all=New-Object System.Collections.ArrayList
        $named=New-Object System.Collections.ArrayList
        $descendants=$window.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition)
        foreach($node in $descendants){
            if(-not (Test-EligibleEditor $window $node)){continue}
            [void]$all.Add($node)
            $label=([string]$node.Current.Name)+' '+([string]$node.Current.AutomationId)
            if($label -match '(?i)ask chatgpt|ask anything|message|prompt|compose|reply|chat.input|write.*message'){
                [void]$named.Add($node)
            }
        }
        if($named.Count -eq 1){$editor=$named[0]}
        elseif($all.Count -eq 1){$editor=$all[0]}
        else{return $null}  # Ambiguous fields: never type into a guess.
        if(-not (Focus-CandidateEditor $window $editor $hwnd)){return $null}
        $script:autoFocused=$true
    }
    if([CourierForegroundInput]::GetForegroundWindow() -ne $hwnd -or
       -not (Test-EditorOwnsFocus $editor)){return $null}
    $value=$null
    $text=$null
    $hasValue=$editor.TryGetCurrentPattern(
        [System.Windows.Automation.ValuePattern]::Pattern,[ref]$value)
    $hasText=$editor.TryGetCurrentPattern(
        [System.Windows.Automation.TextPattern]::Pattern,[ref]$text)
    if($hasValue -and $value.Current.IsReadOnly){return $null}
    return @{window=$window;editor=$editor;handle=$hwnd;
             runtimeId=($editor.GetRuntimeId() -join ',');
             value=$value;text=$text;hasValue=$hasValue;hasText=$hasText}
}

function Read-EditorText($target){
    # A UIA ValuePattern can stay stale after Electron processes SendInput.
    # Consult both fresh ValuePattern and TextPattern; prefer a nonempty
    # editable body over placeholder or stale ValuePattern text.
    $node=$target.editor
    $v=$null
    $t=$null
    $value=''
    $doc=''
    if($node.TryGetCurrentPattern(
        [System.Windows.Automation.ValuePattern]::Pattern,[ref]$v)){
        try{$value=[string]$v.Current.Value}catch{}
    }
    if($node.TryGetCurrentPattern(
        [System.Windows.Automation.TextPattern]::Pattern,[ref]$t)){
        try{$doc=[string]$t.DocumentRange.GetText(-1)}catch{}
    }
    if($doc.Length -gt $value.Length){return $doc}
    return $value
}

function Test-EditorContainsMarker($target,[string]$marker){
    # UIA patterns are queried fresh after each input batch; React editors
    # can replace their underlying UIA elements during an update.
    $node=$target.editor
    $items=New-Object System.Collections.ArrayList
    [void]$items.Add($node)
    try{
        $current=[System.Windows.Automation.AutomationElement]::FocusedElement
        if($null -ne $current -and
           ($current.GetRuntimeId() -join ',') -cne $target.runtimeId){
            # A retargeting React editor is only admissible if the focused
            # replacement is still within the same foreground window.
            if(Test-EligibleEditor $target.window $current){[void]$items.Add($current)}
        }
    }catch{}
    foreach($item in $items){
        try{
            $v=$null
            if($item.TryGetCurrentPattern(
                    [System.Windows.Automation.ValuePattern]::Pattern,[ref]$v)){
                if(([string]$v.Current.Value).Contains($marker)){return $true}
            }
        }catch{}
        try{
            $t=$null
            if($item.TryGetCurrentPattern(
                    [System.Windows.Automation.TextPattern]::Pattern,[ref]$t)){
                if($null -ne $t.DocumentRange.FindText($marker,$false,$false)){
                    return $true
                }
            }
        }catch{}
    }
    return $false
}

function Test-EmptyOrPlaceholder([string]$value){
    if([string]::IsNullOrWhiteSpace($value)){return $true}
    return ($value.Trim() -match
            '^(?i:ask chatgpt|ask anything|ask a question|message(?:\s+(?:[#@][^\r\n]{1,70}|in\s+[^\r\n]{1,70}))?|type a message|send a message|write a message)(?:\.\.\.)?$'
}

function Assert-CurrentTarget($target){
    if([CourierForegroundInput]::GetForegroundWindow() -ne $target.handle){
        throw 'FOREGROUND_TARGET_CHANGED_DURING_INPUT'
    }
    $fresh=[System.Windows.Automation.AutomationElement]::FocusedElement
    if($null -eq $fresh -or -not (Test-EditorOwnsFocus $target.editor)){
        throw 'FOCUSED_EDITOR_CHANGED_DURING_INPUT'
    }
    if($fresh.Current.IsPassword -or -not $fresh.Current.IsEnabled){
        throw 'FOCUSED_EDITOR_BECAME_PROTECTED'
    }
}

function Find-SendButton($target){
    # Generic Send capability: Name, HelpText or AutomationId on a visible
    # enabled button. An icon-only Custom control requires InvokePattern.
    # No guessing when several controls qualify.
    $candidates=New-Object System.Collections.ArrayList
    $nodes=$target.window.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    foreach($node in $nodes){
        try{
            $role=[string]$node.Current.ControlType.ProgrammaticName
            if($role -notin @('ControlType.Button','ControlType.Custom')){continue}
            if($node.Current.IsOffscreen -or -not $node.Current.IsEnabled){continue}
            $label=([string]$node.Current.Name).Trim()
            $help=([string]$node.Current.HelpText).Trim()
            $id=([string]$node.Current.AutomationId).Trim()
            $named=($label -match '^(?i:send(?: a)?(?: message| prompt| reply| now)?|submit(?: message)?|post message)(?:\s*\([^)]*\))?$' -or
                    $help -match '^(?i:send(?: a)?(?: message| prompt| reply| now)?|submit(?: message)?|post message)(?:\s*\([^)]*\))?$')
            $identified=($id -match '^(?i:send(?:[-_]?(?:button|message|prompt|reply))?|message[-_]?send(?:[-_]?button)?|chat[-_]?send(?:[-_]?button)?|submit[-_]?button)$')
            if(-not ($named -or $identified)){continue}
            if($role -eq 'ControlType.Custom'){
                $invoke=$null
                if(-not $node.TryGetCurrentPattern(
                    [System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)){continue}
            }
            $bounds=$node.Current.BoundingRectangle
            if($bounds.Width -lt 8 -or $bounds.Height -lt 8){continue}
            [void]$candidates.Add($node)
        }catch{}
    }
    if($candidates.Count -eq 1){return $candidates[0]}
    return $null
}

function Test-TranscriptMarker($target,$nonce){
    # Never confuse the editor or its document ancestors with sent messages.
    return (Test-ConversationReceiptNotComposer $target $nonce)
}

function Assert-RunnerAllowed {
    $root=Split-Path -Parent $PSScriptRoot
    foreach($stop in @('.relay-paused','.relay-off','.relay-kill','.relay-kill-hud')){
        if(Test-Path -LiteralPath (Join-Path $root $stop)){
            throw 'OPERATOR_STOP_ACTIVE'
        }
    }
    $configPath=Join-Path $env:LOCALAPPDATA 'GPTWindowsRelayDesktop\desktop-control.json'
    $config=Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if(-not $config.armed -or $config.off -or
       (-not $config.auto_send -and -not $ManualForceSend)){
        throw 'OPERATOR_AUTO_SEND_NOT_ARMED'
    }
}


function Test-ConversationReceiptNotComposer($target,[string]$marker){
    # Chat messages may appear as Text nodes or Document controls.
    # Exclude editor, descendants and ancestors from receipt evidence.
    $nodes=$target.window.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    foreach($node in $nodes){
        try{
            $role=[string]$node.Current.ControlType.ProgrammaticName
            if($role -notin @('ControlType.Document','ControlType.Text')){continue}
            if($node.Current.IsOffscreen){continue}
            if((Test-IsSelfOrChild $node $target.editor) -or
               (Test-IsSelfOrChild $target.editor $node)){continue}
            if($role -eq 'ControlType.Text' -and
               ([string]$node.Current.Name).Contains($marker)){return $true}
            $pattern=$null
            if($node.TryGetCurrentPattern(
                [System.Windows.Automation.TextPattern]::Pattern,[ref]$pattern) -and
               $null -ne $pattern.DocumentRange.FindText($marker,$false,$false)){
                return $true
            }
        }catch{}
    }
    return $false
}

function Test-ExactOwnDraft($target,[string]$marker){
    if(-not (Test-EditorContainsMarker $target $marker)){return $false}
    # Do not submit a mixed human draft: both frame delimiters and the
    # matching unique receipt must be visible in the same writable editor.
    try{
        $body=Read-EditorText $target
        if(-not $body.Contains($marker) -or
           -not $body.Contains('[GPT_WINDOWS_RESULT]') -or
           -not $body.Contains('[/GPT_WINDOWS_RESULT]')){return $false}
        # A nonce embedded in a user's mixed/edited draft isn't permission
        # to hit Enter. Match the exact saved frame, permitting only line
        # wrapping/whitespace normalization of the UIA representation.
        $observed=($body -replace '\s+',' ').Trim()
        $expected=($script:wire -replace '\s+',' ').Trim()
        return ($observed -ceq $expected)
    }catch{return $false}
}

function Test-MessagingComposerTarget($target){
    # Message field semantics, not app branding, enable saved-draft recovery.
    try{
        $label=([string]$target.editor.Current.Name)+' '+
               ([string]$target.editor.Current.AutomationId)+' '+
               ([string]$target.editor.Current.HelpText)
        if($label -match '(?i)ask chatgpt|ask anything|message|reply|chat.?input|compose|prompt|write.*message'){
            return $true
        }
        # Compatibility with ChatGPT's unnamed editor, not the primary rule.
        $proc=Get-Process -Id ([int]$target.window.Current.ProcessId) -ErrorAction Stop
        return ($proc.ProcessName -ieq 'ChatGPT' -and
                [string]::IsNullOrWhiteSpace([string]$target.editor.Current.Name))
    }catch{return $false}
}

function Invoke-ExistingDraftSubmit($target,$send){
    Assert-RunnerAllowed
    Assert-CurrentTarget $target
    # A recovered result may ONLY use ChatGPT's explicit, unique Send control.
    # Enter is not a Send-button substitute and must never create another post.
    if($null -eq $send){throw 'SUBMIT_ONLY_SEND_CONTROL_NOT_IDENTIFIED'}
    if(-not $send.Current.IsEnabled -or $send.Current.IsOffscreen){
        throw 'SUBMIT_ONLY_SEND_CONTROL_NOT_READY'
    }
    $bounds=$send.Current.BoundingRectangle
    $root=$target.window.Current.BoundingRectangle
    $x=[int][Math]::Round(($bounds.Left+$bounds.Right)/2)
    $y=[int][Math]::Round(($bounds.Top+$bounds.Bottom)/2)
    if($x -lt $root.Left -or $x -ge $root.Right -or
       $y -lt $root.Top -or $y -ge $root.Bottom){
        throw 'SUBMIT_ONLY_BUTTON_OUTSIDE_WINDOW'
    }
    $cursor=New-Object CourierForegroundInput+POINT
    if(-not [CourierForegroundInput]::GetCursorPos([ref]$cursor)){
        throw 'SUBMIT_ONLY_CURSOR_UNAVAILABLE'
    }
    Write-Output 'SENDER_STAGE=SUBMIT_ONLY_CLICK_BEGIN'
    try{
        if(-not [CourierForegroundInput]::SetCursorPos($x,$y)){
            throw 'SUBMIT_ONLY_CURSOR_MOVE_FAILED'
        }
        Assert-RunnerAllowed
        Assert-CurrentTarget $target
        [CourierForegroundInput]::mouse_event([uint32]2,0,0,0,[UIntPtr]::Zero)
        Start-Sleep -Milliseconds 70
        [CourierForegroundInput]::mouse_event([uint32]4,0,0,0,[UIntPtr]::Zero)
    }finally{
        [void][CourierForegroundInput]::SetCursorPos($cursor.X,$cursor.Y)
    }
    Write-Output 'SENDER_STAGE=SUBMIT_ONLY_CLICK_COMPLETED'
}

function Recover-ExistingChatDraft($target,[string]$marker){
    # Only a recognized message field or explicitly exposed Send control
    # qualifies; no text reinsertion, command replay or Enter fallback.
    if(-not (Test-MessagingComposerTarget $target) -and
       $null -eq (Find-SendButton $target)){
        Write-Output 'SENDER_STAGE=SUBMIT_ONLY_NOT_NATIVE_CHAT_COMPOSER'
        Write-Output 'RESULT=FOREGROUND_NO_TARGET'
        return
    }
    # Read-only receipt reconciliation happens BEFORE any keyboard event.
    if(-not (Test-EditorContainsMarker $target $marker)){
        if(Test-ConversationReceiptNotComposer $target $marker){
            Write-Output 'SENDER_STAGE=SUBMIT_ONLY_ALREADY_IN_TRANSCRIPT'
            Write-Output 'RESULT=HEARTBEAT_SUBMITTED'
        }else{
            Write-Output 'SENDER_STAGE=SUBMIT_ONLY_NO_OWN_DRAFT'
            Write-Output 'RESULT=FOREGROUND_NO_TARGET'
        }
        return
    }
    if(-not (Test-ExactOwnDraft $target $marker)){
        Write-Output 'SENDER_STAGE=SUBMIT_ONLY_DRAFT_NOT_EXACT'
        Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
        return
    }
    # Before another Enter, allow a previously initiated send to settle.
    # A slow ChatGPT response must not trigger an immediate duplicate.
    for($settle=0;$settle -lt 10;$settle++){
        Start-Sleep -Milliseconds 250
        if(-not (Test-EditorContainsMarker $target $marker)){
            if(Test-ConversationReceiptNotComposer $target $marker){
                Write-Output 'SENDER_STAGE=SUBMIT_ONLY_ALREADY_IN_TRANSCRIPT'
                Write-Output 'RESULT=HEARTBEAT_SUBMITTED'
            }else{
                Write-Output 'SENDER_STAGE=SUBMIT_ONLY_DRAFT_DISAPPEARED_UNCONFIRMED'
                Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
            }
            return
        }
    }
    # At most ONE actual Send-button activation for this saved result.
    # Any unconfirmed outcome stays uncertain; never auto-press Send again.
    for($attempt=1;$attempt -le 1;$attempt++){
        if(-not (Test-ExactOwnDraft $target $marker)){
            Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
            return
        }
        if(Test-ConversationReceiptNotComposer $target $marker){
            # Transcript may still include composer; never click if both
            # show the same receipt, because server state is ambiguous.
            Write-Output 'SENDER_STAGE=SUBMIT_ONLY_TRANSCRIPT_AMBIGUOUS'
            Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
            return
        }
        $send=Find-SendButton $target
        if($null -eq $send){
            # No Send click occurred; keep SEND_PENDING and try only after
            # the application exposes one verified Send control.
            Write-Output 'SENDER_STAGE=SUBMIT_ONLY_SEND_CONTROL_NOT_IDENTIFIED'
            Write-Output 'RESULT=FOREGROUND_NO_TARGET'
            return
        }
        Write-Output ('SENDER_STAGE=SUBMIT_ONLY_ATTEMPT_'+$attempt)
        Invoke-ExistingDraftSubmit $target $send
        for($tick=0;$tick -lt 45;$tick++){
            Start-Sleep -Milliseconds 200
            try{
                $draftPresent=Test-EditorContainsMarker $target $marker
                if(-not $draftPresent -and (Test-ConversationReceiptNotComposer $target $marker)){
                    Write-Output 'SENDER_STAGE=CONFIRMED_IN_CONVERSATION'
                    Write-Output 'RESULT=HEARTBEAT_SUBMITTED'
                    return
                }
                if(-not $draftPresent){
                    # Draft cleared but UIA transcript not yet caught up:
                    # this is uncertain, and another Enter may create a
                    # duplicate or send an unrelated draft.
                    Write-Output 'SENDER_STAGE=SUBMIT_ONLY_DRAFT_CLEARED_UNCONFIRMED'
                    Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
                    return
                }
            }catch{
                Write-Output 'SENDER_STAGE=SUBMIT_ONLY_VERIFICATION_UNAVAILABLE'
                Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
                return
            }
        }
        # The send-control activation has an ambiguous outcome. Do not
        # retry, even when UIA still shows the draft and no receipt.
    }
    Write-Output 'SENDER_STAGE=SUBMIT_ONLY_RETRY_EXHAUSTED'
    Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
}

$script:autoFocused=$false
$inputStarted=$false
$submitStarted=$false
$script:wire=''
try{
    if($NativeActionId -notmatch '^[A-Za-z0-9._:-]{1,128}$' -or
       $NativeReceiptMarker -cnotmatch '^NATIVE-RECEIPT-[0-9a-f]{32}$'){
        throw 'FOREIGN_RESULT_BINDING_INVALID'
    }
    $expected=Join-Path $env:LOCALAPPDATA ('GPTWindowsRelayDesktop\outbox\'+
                                          ($NativeActionId -replace '[^A-Za-z0-9._-]','_')+'.txt')
    if([IO.Path]::GetFullPath($NativeResultPath) -ine [IO.Path]::GetFullPath($expected)){
        throw 'FOREIGN_RESULT_PATH_MISMATCH'
    }
    $raw=[IO.File]::ReadAllBytes($NativeResultPath)
    if($raw.Length -lt 30 -or $raw.Length -gt 180000){
        throw 'FOREIGN_RESULT_SIZE_INVALID'
    }
    $utf8=New-Object System.Text.UTF8Encoding($false,$true)
    $script:wire=$utf8.GetString($raw)
    if(-not $script:wire.StartsWith('[GPT_WINDOWS_RESULT]') -or
       -not $script:wire.TrimEnd().EndsWith('[/GPT_WINDOWS_RESULT]')){
        throw 'FOREIGN_RESULT_FRAME_INVALID'
    }
    $payload=$script:wire.Substring('[GPT_WINDOWS_RESULT]'.Length)
    $payload=$payload.Substring(0,$payload.LastIndexOf('[/GPT_WINDOWS_RESULT]')) | ConvertFrom-Json
    if($payload.id -cne $NativeActionId -or
       $payload.native_delivery_receipt -cne $NativeReceiptMarker){
        throw 'FOREIGN_RESULT_ID_RECEIPT_MISMATCH'
    }
    Assert-RunnerAllowed
    # An unavailable or non-UIA window is simply not an eligible text field.
    # The result stays queued; it must not become a permanent failed delivery.
    try{$target=Get-ForegroundEditable}
    catch{$target=$null}
    if($null -eq $target){
        Write-Output 'SENDER_STAGE=AWAITING_FOREGROUND_TEXT_FIELD'
        Write-Output 'RESULT=FOREGROUND_NO_TARGET'
        exit 0
    }
    if($script:autoFocused){Write-Output 'SENDER_STAGE=FOREGROUND_EDITOR_AUTOFOCUSED'}
    Write-Output 'SENDER_STAGE=FOREGROUND_TEXT_FIELD_FOUND'
    if($SubmitExistingOnly){
        Recover-ExistingChatDraft $target $NativeReceiptMarker
        exit 0
    }
    $before=Read-EditorText $target
    $sendBefore=Find-SendButton $target
    if(Test-EditorContainsMarker $target $NativeReceiptMarker){
        Write-Output 'SENDER_STAGE=RESULT_ALREADY_IN_EDIT_FIELD'
        if(Test-MessagingComposerTarget $target){
            # A restored unsent ChatGPT draft is NOT a delivered message.
            # Recovery can only submit it after a strict saved-frame check.
            Write-Output 'SENDER_STAGE=CHAT_DRAFT_PENDING_SEND'
            Write-Output 'RESULT=CHAT_SEND_PENDING'
        }else{
            Write-Output 'RESULT=TEXT_INSERTED_VERIFIED'
        }
        exit 0
    }
    # A permanently enabled Send button does NOT prove the editor contains
    # someone else's draft (Telegram/Discord and icon buttons may stay
    # enabled). Inspect the actual selected editor instead; never mix with
    # a nonempty existing draft before writing a saved result.
    $allowSubmit=Test-EmptyOrPlaceholder $before
    if($target.hasText){
        try{
            $allowSubmit=($allowSubmit -and
                         (Test-EmptyOrPlaceholder ([string]$target.text.DocumentRange.GetText(-1))))
        }catch{}
    }
    if($null -ne $sendBefore -and -not $allowSubmit){
        Write-Output 'SENDER_STAGE=CHAT_EDITOR_HAS_UNRELATED_DRAFT'
        Write-Output 'RESULT=FOREGROUND_NO_TARGET'
        exit 0
    }
    # For a named chat composer, a busy draft isn't an output target. The
    # unrelated text must not be submitted with our result.
    $isChatComposer=(([string]$target.editor.Current.Name -match
                     '(?i)ask chatgpt|ask anything|message|prompt|compose|chat') -or
                     (Test-MessagingComposerTarget $target))
    if($isChatComposer -and -not $allowSubmit){
        Write-Output 'SENDER_STAGE=CHAT_EDITOR_HAS_UNRELATED_DRAFT'
        Write-Output 'RESULT=FOREGROUND_NO_TARGET'
        exit 0
    }
    $requiredSize=if([IntPtr]::Size -eq 8){40}else{28}
    if([CourierForegroundInput]::InputSize() -ne $requiredSize){
        throw 'FOREGROUND_INPUT_STRUCT_SIZE_INVALID'
    }
    # CR/LF keystrokes can submit partial results in rich chat editors.
    # Insert one compact line regardless of which foreground app is selected.
    $inputText=$script:wire.Replace("`r",' ').Replace("`n",' ')
    Assert-CurrentTarget $target
    $inputStarted=$true
    # Chunk large Unicode writes while checking exact focused editor.
    for($offset=0;$offset -lt $inputText.Length;$offset+=2048){
        Assert-RunnerAllowed
        Assert-CurrentTarget $target
        $chunk=$inputText.Substring($offset,[Math]::Min(2048,$inputText.Length-$offset))
        $written=[CourierForegroundInput]::TypeUnicode($chunk)
        if($written -ne [uint32]($chunk.Length*2)){
            throw 'FOREGROUND_PARTIAL_KEYBOARD_INPUT'
        }
    }
    Write-Output 'SENDER_STAGE=FOREGROUND_INPUT_COMPLETED'
    $matched=$false
    $send=$null
    for($i=0;$i -lt 40;$i++){
        Start-Sleep -Milliseconds 150
        try{
            if(Test-EditorContainsMarker $target $NativeReceiptMarker){
                $matched=$true
                Write-Output 'SENDER_STAGE=EDITOR_TEXT_MARKER_VERIFIED'
                break
            }
            # Electron can render the exact typed body while returning an
            # old placeholder through UIA. A previously DISABLED Send
            # control becoming ENABLED after our own SendInput is a
            # second, event-driven indication that typing reached it.
            if($allowSubmit -and $null -eq $sendBefore){
                $send=Find-SendButton $target
                if($null -ne $send){
                    $matched=$true
                    Write-Output 'SENDER_STAGE=EDITOR_SEND_ENABLEMENT_VERIFIED'
                    break
                }
            }
        }catch{}
    }
    if(-not $matched){throw 'FOREGROUND_INSERTION_NOT_VERIFIED'}
    Write-Output 'SENDER_STAGE=TEXT_INSERTION_VERIFIED'
    $send=if($allowSubmit){Find-SendButton $target}else{$null}
    $isChatComposer=($isChatComposer -or $null -ne $send)
    if($null -eq $send){
        if($isChatComposer){
            # In a known chat composer, typed != submitted. The native
            # runner schedules a SEND ONLY recovery with this same nonce.
            Write-Output 'SENDER_STAGE=CHAT_DRAFT_PENDING_SEND'
            Write-Output 'RESULT=CHAT_SEND_PENDING'
        }else{
            Write-Output 'RESULT=TEXT_INSERTED_VERIFIED'
        }
        exit 0
    }
    Assert-RunnerAllowed
    Assert-CurrentTarget $target
    # Every application's Send is guarded by an exact saved frame and an
    # independently absent posted receipt; never blind-press Enter.
    if(-not (Test-ExactOwnDraft $target $NativeReceiptMarker)){
        Write-Output 'SENDER_STAGE=CHAT_DRAFT_WAITING_FOR_EXACT_FRAME'
        Write-Output 'RESULT=CHAT_SEND_PENDING'
        exit 0
    }
    if(Test-ConversationReceiptNotComposer $target $NativeReceiptMarker){
        Write-Output 'SENDER_STAGE=CHAT_TRANSCRIPT_ALREADY_HAS_RECEIPT'
        Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
        exit 5
    }
    # Initial submission and send-only recovery use the same explicit
    # Send control.  Never treat Enter as a substitute for clicking Send.
    $box=$send.Current.BoundingRectangle
    $rootBox=$target.window.Current.BoundingRectangle
    $cx=[int][Math]::Round(($box.Left+$box.Right)/2)
    $cy=[int][Math]::Round(($box.Top+$box.Bottom)/2)
    if($cx -lt $rootBox.Left -or $cx -ge $rootBox.Right -or
       $cy -lt $rootBox.Top -or $cy -ge $rootBox.Bottom){
        throw 'FOREGROUND_SEND_OUTSIDE_ACTIVE_WINDOW'
    }
    $cursor=New-Object CourierForegroundInput+POINT
    if(-not [CourierForegroundInput]::GetCursorPos([ref]$cursor)){
        throw 'FOREGROUND_CURSOR_UNAVAILABLE'
    }
    Write-Output 'SENDER_STAGE=CLICK_BEGIN'
    Write-Output 'UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN'
    $submitStarted=$true
    try{
        if(-not [CourierForegroundInput]::SetCursorPos($cx,$cy)){
            throw 'FOREGROUND_SEND_CURSOR_FAILURE'
        }
        Assert-CurrentTarget $target
        [CourierForegroundInput]::mouse_event([uint32]2,0,0,0,[UIntPtr]::Zero)
        Start-Sleep -Milliseconds 70
        [CourierForegroundInput]::mouse_event([uint32]4,0,0,0,[UIntPtr]::Zero)
    }finally{
        [void][CourierForegroundInput]::SetCursorPos($cursor.X,$cursor.Y)
    }
    Write-Output 'UIA_GUARDED_SEND_BUTTON_CLICK_COMPLETED'
    Write-Output 'SENDER_STAGE=CLICK_COMPLETED'
    $confirmed=$false
    for($i=0;$i -lt 50;$i++){
        Start-Sleep -Milliseconds 200
        try{
            # Conversation documents may include an UNSENT composer.
            # Confirm the draft marker disappeared before marking submitted.
            if(Test-EditorContainsMarker $target $NativeReceiptMarker){continue}
            if((Test-TranscriptMarker $target $NativeReceiptMarker) -and
               $null -eq (Find-SendButton $target)){
                $confirmed=$true
                break
            }
        }catch{}
    }
    if($confirmed){
        Write-Output 'SENDER_STAGE=CONFIRMED_IN_CONVERSATION'
        Write-Output 'RESULT=HEARTBEAT_SUBMITTED'
        exit 0
    }
    Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
    exit 5
}catch{
    $reason=$_.Exception.Message
    if($reason -notmatch '^[A-Z0-9_]{3,90}$'){$reason='FOREGROUND_UNCLASSIFIED_ERROR'}
    Write-Output ('HEARTBEAT_ERROR='+$reason)
    if(-not $inputStarted){
        # These failures occur before ANY mouse-down, so a later attempt
        # may still click this same verified draft without risking a retry
        # of a click that might already have reached ChatGPT.
        if($SubmitExistingOnly -and $reason -in @(
            'SUBMIT_ONLY_SEND_CONTROL_NOT_IDENTIFIED',
            'SUBMIT_ONLY_SEND_CONTROL_NOT_READY',
            'SUBMIT_ONLY_BUTTON_OUTSIDE_WINDOW',
            'SUBMIT_ONLY_CURSOR_UNAVAILABLE',
            'SUBMIT_ONLY_CURSOR_MOVE_FAILED')){
            Write-Output 'SENDER_STAGE=SUBMIT_ONLY_NO_CLICK_CONFIRMED'
            Write-Output 'RESULT=FOREGROUND_NO_TARGET'
            exit 0
        }
        if($reason -in @('FOREGROUND_TARGET_CHANGED_DURING_INPUT',
                        'FOCUSED_EDITOR_CHANGED_DURING_INPUT',
                        'OPERATOR_AUTO_SEND_NOT_ARMED',
                        'OPERATOR_STOP_ACTIVE')){
            Write-Output 'RESULT=FOREGROUND_NO_TARGET'
            exit 0
        }
        Write-Output 'RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY'
        exit 1
    }
    if($submitStarted){
        Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
        exit 5
    }
    # Input may be partially visible; never automatically replay this frame.
    Write-Output 'RESULT=FOREGROUND_INSERTION_UNCERTAIN_NO_RETRY'
    exit 5
}
