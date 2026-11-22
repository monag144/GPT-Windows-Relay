# Command Courier foreground UIA destination. No configured input source required.
# Sends the already-owned native result to the focused writable text field.
# App-independent text insertion; Send button activation is only attempted
# when there is a unique explicit Send/Submit button in the same window.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$NativeResultPath,
    [Parameter(Mandatory=$true)][string]$NativeActionId,
    [Parameter(Mandatory=$true)][string]$NativeReceiptMarker
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

function Get-ForegroundEditable {
    $hwnd=[CourierForegroundInput]::GetForegroundWindow()
    if($hwnd -eq [IntPtr]::Zero){return $null}
    $window=[System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
    if($null -eq $window){return $null}
    $editor=[System.Windows.Automation.AutomationElement]::FocusedElement
    if($null -eq $editor){return $null}
    if(-not $editor.Current.IsEnabled -or $editor.Current.IsOffscreen -or
       $editor.Current.IsPassword -or -not $editor.Current.HasKeyboardFocus){return $null}
    $control=[string]$editor.Current.ControlType.ProgrammaticName
    if($control -notin @('ControlType.Edit','ControlType.Document')){return $null}
    $walker=[System.Windows.Automation.TreeWalker]::RawViewWalker
    $node=$editor
    $inside=$false
    for($i=0;$i -lt 60 -and $null -ne $node;$i++){
        if([System.Windows.Automation.Automation]::Compare($node,$window)){
            $inside=$true
            break
        }
        $node=$walker.GetParent($node)
    }
    if(-not $inside){return $null}
    $box=$editor.Current.BoundingRectangle
    $rootBox=$window.Current.BoundingRectangle
    if($box.Width -lt 8 -or $box.Height -lt 8 -or
       $box.Left -lt $rootBox.Left -or $box.Top -lt $rootBox.Top -or
       $box.Right -gt $rootBox.Right -or $box.Bottom -gt $rootBox.Bottom){
        return $null
    }
    $v=$null
    $t=$null
    $hasValue=$editor.TryGetCurrentPattern(
        [System.Windows.Automation.ValuePattern]::Pattern,[ref]$v)
    $hasText=$editor.TryGetCurrentPattern(
        [System.Windows.Automation.TextPattern]::Pattern,[ref]$t)
    if($hasValue -and $v.Current.IsReadOnly){return $null}
    if(-not $hasValue -and -not $hasText){return $null}
    $rid=($editor.GetRuntimeId() -join ',')
    return @{window=$window;editor=$editor;handle=$hwnd;runtimeId=$rid;
             value=$v;text=$t;hasValue=$hasValue;hasText=$hasText}
}

function Read-EditorText($target){
    if($target.hasValue){
        return [string]$target.value.Current.Value
    }
    return [string]$target.text.DocumentRange.GetText(-1)
}

function Assert-CurrentTarget($target){
    if([CourierForegroundInput]::GetForegroundWindow() -ne $target.handle){
        throw 'FOREGROUND_TARGET_CHANGED_DURING_INPUT'
    }
    $fresh=[System.Windows.Automation.AutomationElement]::FocusedElement
    if($null -eq $fresh -or -not $fresh.Current.HasKeyboardFocus -or
       ($fresh.GetRuntimeId() -join ',') -cne $target.runtimeId){
        throw 'FOCUSED_EDITOR_CHANGED_DURING_INPUT'
    }
    if($fresh.Current.IsPassword -or -not $fresh.Current.IsEnabled){
        throw 'FOCUSED_EDITOR_BECAME_PROTECTED'
    }
}

function Find-SendButton($target){
    $candidates=New-Object System.Collections.ArrayList
    $nodes=$target.window.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    foreach($node in $nodes){
        try{
            if($node.Current.ControlType -ne
               [System.Windows.Automation.ControlType]::Button){continue}
            if($node.Current.IsOffscreen -or -not $node.Current.IsEnabled){continue}
            if([string]$node.Current.Name -notmatch '^(?i:send|send message|send prompt|submit)$'){
                continue
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
    $nodes=$target.window.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    foreach($node in $nodes){
        try{
            if($node.Current.ControlType -ne
               [System.Windows.Automation.ControlType]::Document){continue}
            if($node.Current.IsOffscreen){continue}
            $pattern=$null
            if(-not $node.TryGetCurrentPattern(
                    [System.Windows.Automation.TextPattern]::Pattern,[ref]$pattern)){continue}
            if($null -ne $pattern.DocumentRange.FindText($nonce,$false,$false)){
                return $true
            }
        }catch{}
    }
    return $false
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
    if(-not $config.armed -or $config.off -or -not $config.auto_send){
        throw 'OPERATOR_AUTO_SEND_NOT_ARMED'
    }
}

$inputStarted=$false
$clickStarted=$false
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
    $target=Get-ForegroundEditable
    if($null -eq $target){
        Write-Output 'SENDER_STAGE=AWAITING_FOREGROUND_TEXT_FIELD'
        Write-Output 'RESULT=FOREGROUND_NO_TARGET'
        exit 0
    }
    Write-Output 'SENDER_STAGE=FOREGROUND_TEXT_FIELD_FOUND'
    $before=Read-EditorText $target
    if($before.Contains($NativeReceiptMarker)){
        Write-Output 'SENDER_STAGE=RESULT_ALREADY_IN_EDIT_FIELD'
        Write-Output 'RESULT=TEXT_INSERTED_VERIFIED'
        exit 0
    }
    # An existing draft must never be submitted together with an unrelated
    # result. The text may still be inserted at the current cursor position.
    $allowSubmit=[string]::IsNullOrWhiteSpace($before)
    if($target.hasText){
        try{
            $textBefore=[string]$target.text.DocumentRange.GetText(-1)
            $allowSubmit=[string]::IsNullOrWhiteSpace($textBefore)
        }catch{}
    }
    $requiredSize=if([IntPtr]::Size -eq 8){40}else{28}
    if([CourierForegroundInput]::InputSize() -ne $requiredSize){
        throw 'FOREGROUND_INPUT_STRUCT_SIZE_INVALID'
    }
    Assert-CurrentTarget $target
    $inputStarted=$true
    # SendInput Unicode accepts UTF-16 units; chunks constrain resource use
    # and let us abort if the user changes foreground apps while typing.
    for($offset=0;$offset -lt $script:wire.Length;$offset+=128){
        Assert-RunnerAllowed
        Assert-CurrentTarget $target
        $chunk=$script:wire.Substring($offset,[Math]::Min(128,$script:wire.Length-$offset))
        $written=[CourierForegroundInput]::TypeUnicode($chunk)
        if($written -ne [uint32]($chunk.Length*2)){
            throw 'FOREGROUND_PARTIAL_KEYBOARD_INPUT'
        }
    }
    Write-Output 'SENDER_STAGE=FOREGROUND_INPUT_COMPLETED'
    $matched=$false
    for($i=0;$i -lt 25;$i++){
        Start-Sleep -Milliseconds 120
        try{
            if((Read-EditorText $target).Contains($NativeReceiptMarker)){
                $matched=$true
                break
            }
        }catch{}
    }
    if(-not $matched){throw 'FOREGROUND_INSERTION_NOT_VERIFIED'}
    Write-Output 'SENDER_STAGE=TEXT_INSERTION_VERIFIED'
    # Explicit chat Send control is optional. Without it, e.g. Notepad,
    # successful text insertion is a terminal result (not a remote receipt).
    $send=if($allowSubmit){Find-SendButton $target}else{$null}
    if($null -eq $send){
        Write-Output 'RESULT=TEXT_INSERTED_VERIFIED'
        exit 0
    }
    Assert-RunnerAllowed
    Assert-CurrentTarget $target
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
    $clickStarted=$true
    try{
        if(-not [CourierForegroundInput]::SetCursorPos($cx,$cy)){
            throw 'FOREGROUND_SEND_CURSOR_FAILURE'
        }
        [CourierForegroundInput]::mouse_event([uint32]2,0,0,0,[UIntPtr]::Zero)
        Start-Sleep -Milliseconds 70
        [CourierForegroundInput]::mouse_event([uint32]4,0,0,0,[UIntPtr]::Zero)
    }finally{
        [void][CourierForegroundInput]::SetCursorPos($cursor.X,$cursor.Y)
    }
    Write-Output 'SENDER_STAGE=CLICK_COMPLETED'
    $confirmed=$false
    for($i=0;$i -lt 50;$i++){
        Start-Sleep -Milliseconds 200
        try{
            if((Read-EditorText $target).Contains($NativeReceiptMarker)){continue}
            if(Test-TranscriptMarker $target $NativeReceiptMarker){
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
        Write-Output 'RESULT=FOREGROUND_NO_TARGET'
        exit 0
    }
    if($clickStarted){
        Write-Output 'RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND'
        exit 5
    }
    # Input may be partially visible; never automatically replay this frame.
    Write-Output 'RESULT=FOREGROUND_INSERTION_UNCERTAIN_NO_RETRY'
    exit 5
}
