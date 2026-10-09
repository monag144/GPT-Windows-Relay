# Agent011 PCE11 -> PCE12: one-shot, separate Firefox window ONLY.
# Never run the legacy same-tab semantic_agent_rotation.ps1 for this mission.
# No browser launch, navigation, New Chat click, retries, or source edits.
param(
 [Parameter(Mandatory=$true)][string]$SourcePacketId,
 [Parameter(Mandatory=$true)][string]$HandoffFile,
 [Parameter(Mandatory=$true)][string]$ExpectedHandoffSha256,
 [Parameter(Mandatory=$true)][string]$ExpectedSourceHead,
 [Parameter(Mandatory=$true)][string]$ReceiptFile,
 [int]$ExpectedFirefoxPid=5440,
 [int]$ExpectedPendingMissions=2,
 [int]$ExpectedStopGeneration=9,
 [switch]$ValidateOnly
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$RepoHome=Split-Path -Parent $PSScriptRoot
$LiveHome=Join-Path $env:USERPROFILE 'Downloads\Dev\GPT\Client\Relay'
$BridgeFile=Join-Path $env:APPDATA 'GPTWindowsRelay\bridge.json'
$ReceiptFile=[IO.Path]::GetFullPath($ReceiptFile)
$script:State=[ordered]@{
 schema='agent011-separate-window-handoff-v1'
 source_packet_id=$SourcePacketId
 phase='WORKER_ENTRY'
 created_at=[DateTime]::UtcNow.ToString('o')
 source_url_sha256=$null
 new_url=$null
 firefox_pid=$ExpectedFirefoxPid
 expected_handoff_sha256=$ExpectedHandoffSha256
 focus_attempted=$false
 compose_attempted=$false
 send_invoked=$false
 destination_url_verified=$false
 marker_visible=$false
 user_turn_verified=$false
 title_verified=$false
 source_editor_untouched=$true
 firefox_launched=$false
 new_chat_clicked=$false
 error=$null
}
function Save-Receipt([string]$Phase){
 $script:State.phase=$Phase
 $script:State.updated_at=[DateTime]::UtcNow.ToString('o')
 $tmp=$ReceiptFile+'.writing'
 $backup=$ReceiptFile+'.previous'
 if((Test-Path -LiteralPath $tmp) -or (Test-Path -LiteralPath $backup)){throw 'RECEIPT_TRANSITION_ARTIFACT_EXISTS_NO_RETRY'}
 [IO.File]::WriteAllText($tmp,($script:State|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
 if(-not (Test-Path -LiteralPath $ReceiptFile)){throw 'RECEIPT_DISAPPEARED'}
 # Windows PowerShell/.NET Framework requires a real backup path here.
 # The same-directory replacement is atomic; leftover backup/temp halts replay.
 [IO.File]::Replace($tmp,$ReceiptFile,$backup)
 if(-not (Test-Path -LiteralPath $ReceiptFile)){throw 'RECEIPT_REPLACEMENT_NOT_DURABLE'}
 [IO.File]::Delete($backup)
}
function Assert-Handoff {
 if(-not(Test-Path -LiteralPath $HandoffFile -PathType Leaf)){throw 'HANDOFF_FILE_MISSING'}
 if($ExpectedHandoffSha256 -cnotmatch '^[0-9a-f]{64}$'){throw 'HANDOFF_DIGEST_INVALID'}
 $raw=[IO.File]::ReadAllBytes([IO.Path]::GetFullPath($HandoffFile))
 $hash=[BitConverter]::ToString(([Security.Cryptography.SHA256]::Create()).ComputeHash($raw)).Replace('-','').ToLowerInvariant()
 if($hash -cne $ExpectedHandoffSha256){throw 'HANDOFF_SHA256_MISMATCH'}
 $script:Handoff=[Text.Encoding]::UTF8.GetString($raw)
 if($script:Handoff.Length -lt 300 -or $script:Handoff.Length -gt 14000){throw 'HANDOFF_LENGTH_INVALID'}
 foreach($needle in @('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]','PCE12.000','engineering_preflight','539/539','123/123')){
  if(-not $script:Handoff.Contains($needle)){throw ('HANDOFF_REQUIRED_MARKER_MISSING_'+$needle)}
 }
}
function Read-Backend(){
 if(-not(Test-Path -LiteralPath $BridgeFile)){throw 'RELAY_BRIDGE_CONFIG_MISSING'}
 $cfg=Get-Content -LiteralPath $BridgeFile -Raw|ConvertFrom-Json
 if(([string]$cfg.port) -cnotmatch '^[0-9]{2,5}$' -or [string]::IsNullOrWhiteSpace([string]$cfg.token)){throw 'RELAY_BRIDGE_CONFIG_INVALID'}
 Invoke-RestMethod -Uri ('http://127.0.0.1:'+([string]$cfg.port)+'/status') -Headers @{'X-GPT-Windows-Relay-Token'=[string]$cfg.token} -TimeoutSec 5
}
function Assert-Controls(){
 if((Test-Path -LiteralPath (Join-Path $PSScriptRoot '.relay-paused')) -or (Test-Path -LiteralPath (Join-Path $LiveHome '.relay-paused'))){throw 'OPERATOR_STOP_FILE'}
 $r=Read-Backend
 if($r.ok -ne $true -or $r.armed -ne $true -or $r.outbound_owner -cne 'browser'){throw 'RELAY_NOT_ARMED_OR_NOT_BROWSER_OWNER'}
 if([int]$r.stop_generation -ne $ExpectedStopGeneration){throw 'STOP_EPOCH_CHANGED'}
 if([int]$r.pending_missions -ne $ExpectedPendingMissions){throw 'PENDING_MISSIONS_CHANGED'}
 return $r
}
function Assert-SourceCheckout(){
 $head=(& git -C $RepoHome rev-parse HEAD)
 if($ExpectedSourceHead -cnotmatch '^[0-9a-f]{40}$' -or $LASTEXITCODE -ne 0 -or $head -cne $ExpectedSourceHead){throw 'SOURCE_HEAD_NOT_PINNED'}
 $branch=(& git -C $RepoHome branch --show-current)
 if($LASTEXITCODE -ne 0 -or $branch -cne 'pce11/one-click-go-recovery-and-doc-hygiene'){throw 'SOURCE_BRANCH_NOT_PINNED'}
 if((& git -C $RepoHome status --porcelain)){throw 'SOURCE_WORKTREE_DIRTY'}
}
function Hash-String([string]$Value){
 $bytes=[Text.Encoding]::UTF8.GetBytes($Value)
 return [BitConverter]::ToString(([Security.Cryptography.SHA256]::Create()).ComputeHash($bytes)).Replace('-','').ToLowerInvariant()
}
function Normalize-ChatUrl([string]$Value){
 if($Value -cmatch '^(?:https://)?chatgpt[.]com/c/([a-zA-Z0-9][a-zA-Z0-9-]{14,127})/?$'){
  return 'https://chatgpt.com/c/'+([string]$Matches[1])
 }
 throw 'UNTRUSTED_CONVERSATION_URL'
}
function Is-HomeUrl([string]$Value){
 return ($Value -cmatch '^(?:https://)?chatgpt[.]com/?$')
}
function UrlBar($Window){
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::AutomationIdProperty,'urlbar-input')
 $bars=$Window.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
 if($bars.Count -ne 1){throw 'URLBAR_NOT_UNIQUE'}
 $pattern=$null
 if(-not $bars[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)){throw 'URLBAR_VALUE_UNAVAILABLE'}
 return [string]$pattern.Current.Value
}
function Selected-RealTab($Window){
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::TabItem)
 $tabs=$Window.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
 $selected=@()
 foreach($tab in $tabs){
  try{
   $pattern=$null
   if(-not $tab.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern,[ref]$pattern) -or -not $pattern.Current.IsSelected){continue}
   $parent=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($tab)
   if($null -ne $parent -and $parent.Current.AutomationId -ceq 'tabbrowser-tabs'){$selected+=,$tab}
  }catch{}
 }
 if($selected.Count -ne 1){throw 'SELECTED_REAL_TAB_NOT_UNIQUE'}
 return [ordered]@{name=[string]$selected[0].Current.Name;count=$tabs.Count;element=$selected[0]}
}
function Get-Editor($Window,[bool]$RequireVisible){
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Edit)
 $items=$Window.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
 $found=@()
 foreach($el in $items){
  try{
   if(([string]$el.Current.Name) -cne 'Ask ChatGPT'){continue}
   $value=$null
   if(-not $el.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$value)){continue}
   if(-not $el.Current.IsEnabled -or $value.Current.IsReadOnly){throw 'EDITOR_NOT_WRITABLE'}
   if($RequireVisible -and $el.Current.IsOffscreen){continue}
   if(-not (Test-Agent011EmptyEditorValue ([string]$value.Current.Value))){throw 'EDITOR_CONTAINS_NONPLACEHOLDER_DRAFT'}
   $found+=,[ordered]@{element=$el;pattern=$value}
  }catch{
   if($_.Exception.Message -match '^EDITOR_'){throw}
  }
 }
 if($found.Count -ne 1){throw ('WRITABLE_EDITOR_COUNT_'+$found.Count)}
 return $found[0]
}
function Check-SourceEditors($Window){
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Edit)
 $all=$Window.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
 $count=0
 foreach($e in $all){
  if(([string]$e.Current.Name) -cne 'Ask ChatGPT'){continue}
  $p=$null
  if(-not $e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$p)){throw 'SOURCE_EDITOR_NO_VALUE'}
  if(-not (Test-Agent011EmptyEditorValue ([string]$p.Current.Value))){throw 'SOURCE_COMPOSER_HAS_DRAFT'}
  $count++
 }
 if($count -lt 1){throw 'SOURCE_EDITOR_MISSING'}
}
function Active-SendButtons($Window){
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
 $buttons=$Window.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
 $found=@()
 foreach($b in $buttons){
  try{
   if($b.Current.IsOffscreen -or -not $b.Current.IsEnabled){continue}
   if(([string]$b.Current.Name) -notmatch '^(?i:Send(?: prompt| message)?)$'){continue}
   $ip=$null
   if($b.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$ip)){$found+=,[ordered]@{element=$b;invoke=$ip}}
  }catch{}
 }
 return $found
}
function Inspect-Windows {
 $wc=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Window)
 $all=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,$wc)
 $found=@()
 foreach($w in $all){
  if($w.Current.ClassName -cne 'MozillaWindowClass' -or $w.Current.IsOffscreen){continue}
  if([int]$w.Current.ProcessId -ne $ExpectedFirefoxPid){throw 'FIREFOX_PROCESS_ID_UNEXPECTED'}
  $url=UrlBar $w
  $kind='unknown'
  if(Is-HomeUrl $url){$kind='home'}
  else{try{$url=Normalize-ChatUrl $url;$kind='source'}catch{throw 'UNEXPECTED_FIREFOX_WINDOW_ADDRESS'}}
  $tab=Selected-RealTab $w
  if($kind -eq 'source' -and $tab.name -notmatch '^PC Engineer(?:ing)? 11(?:$|[ -])'){throw 'SOURCE_TAB_TITLE_UNTRUSTED'}
  if($kind -eq 'home' -and $tab.count -ne 1){throw 'DESTINATION_HAS_MULTIPLE_TABS'}
  if($kind -eq 'source'){Check-SourceEditors $w}
  if($kind -eq 'home'){
   $editor=Get-Editor $w $true
   if((Active-SendButtons $w).Count -ne 0){throw 'DESTINATION_HAS_PREEXISTING_SEND'}
  }else{$editor=$null}
  $handle=[IntPtr]::new([int64]$w.Current.NativeWindowHandle)
  if($handle -eq [IntPtr]::Zero){throw 'FIREFOX_WINDOW_HANDLE_MISSING'}
  $found+=,[ordered]@{kind=$kind;window=$w;url=$url;tab=$tab;handle=$handle;editor=$editor}
 }
 if($found.Count -ne 2 -or @($found|Where-Object {$_.kind -eq 'source'}).Count -ne 1 -or @($found|Where-Object {$_.kind -eq 'home'}).Count -ne 1){throw 'SOURCE_DESTINATION_WINDOW_PAIR_NOT_UNIQUE'}
 return $found
}
# WORKER_ENTRY receipt is created before all checks, including missing handoff.
try{
 $folder=[IO.Path]::GetDirectoryName($ReceiptFile)
 [IO.Directory]::CreateDirectory($folder)|Out-Null
 $stream=[IO.FileStream]::new($ReceiptFile,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{
  $first=[Text.Encoding]::UTF8.GetBytes(($script:State|ConvertTo-Json -Depth 7))
  $stream.Write($first,0,$first.Length)
  $stream.Flush($true)
 }finally{$stream.Dispose()}
}catch{
 [Console]::Error.WriteLine('EXCLUSIVE_RECEIPT_NOT_CREATED_'+$_.Exception.Message)
 exit 2
}
try{
 Assert-Handoff
 Save-Receipt 'HANDOFF_SCHEMA_AND_DIGEST_VALIDATED'
 Assert-SourceCheckout
 $null=Assert-Controls
 Save-Receipt 'OFFLINE_CONTROLS_VALIDATED'
 if($ValidateOnly){
  Save-Receipt 'VALIDATE_ONLY_PASSED_NO_UI'
  Write-Output 'AGENT011_HANDOFF_VALIDATE_ONLY_PASS'
  exit 0
 }
 # No UI assemblies or window handling before the negative/offline gates above.
 Add-Type -AssemblyName UIAutomationClient
 Add-Type -AssemblyName UIAutomationTypes
 Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class Agent011AtomicFocus { [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); }'
 . (Join-Path $PSScriptRoot 'agent011_editor_empty_state.ps1')
 . (Join-Path $PSScriptRoot 'agent011_user_turn_proof.ps1')
 $windows=Inspect-Windows
 $source=@($windows|Where-Object {$_.kind -eq 'source'})[0]
 $home=@($windows|Where-Object {$_.kind -eq 'home'})[0]
 if($source.handle -eq $home.handle){throw 'SOURCE_AND_DESTINATION_HWND_IDENTICAL'}
 $sourceUrl=$source.url
 $script:State.source_url_sha256=Hash-String $sourceUrl
 Save-Receipt 'PAIR_AND_EDITORS_VERIFIED'
 $foreground=[Agent011AtomicFocus]::GetForegroundWindow()
 if($foreground -ne $source.handle -and $foreground -ne $home.handle){throw 'UNTRUSTED_FOREGROUND_WINDOW'}
 if($foreground -eq $source.handle){
  $script:State.focus_attempted=$true
  Save-Receipt 'FOCUS_ATTEMPT_UNCERTAIN_NO_RETRY'
  if(-not [Agent011AtomicFocus]::SetForegroundWindow($home.handle)){throw 'SET_FOREGROUND_DECLINED'}
 }
 if([Agent011AtomicFocus]::GetForegroundWindow() -ne $home.handle){throw 'DESTINATION_NOT_FOREGROUND'}
 # Recheck the already pinned URLs, original source editor, selection and STOP.
 if((Normalize-ChatUrl (UrlBar $source.window)) -cne $sourceUrl){throw 'SOURCE_URL_CHANGED_AFTER_FOCUS'}
 if(-not (Is-HomeUrl (UrlBar $home.window))){throw 'DESTINATION_URL_CHANGED_AFTER_FOCUS'}
 if((Selected-RealTab $source.window).name -cne $source.tab.name){throw 'SOURCE_SELECTED_TAB_CHANGED'}
 if((Selected-RealTab $home.window).name -cne $home.tab.name){throw 'DESTINATION_SELECTED_TAB_CHANGED'}
 Check-SourceEditors $source.window
 $editor=Get-Editor $home.window $true
 $null=Assert-Controls
 Save-Receipt 'DESTINATION_FOREGROUND_AND_STOP_VERIFIED'
 # Compose ONLY in the separate home window; no fallback/no retry on uncertainty.
 $script:State.compose_attempted=$true
 Save-Receipt 'COMPOSE_ATTEMPT_UNCERTAIN_NO_RETRY'
 $editor.pattern.SetValue($script:Handoff)
 if(([string]$editor.pattern.Current.Value) -cne $script:Handoff){throw 'HANDOFF_EDITOR_READBACK_MISMATCH'}
 Check-SourceEditors $source.window
 $null=Assert-Controls
 $send=Active-SendButtons $home.window
 if($send.Count -ne 1){throw ('HANDOFF_ENABLED_SEND_COUNT_'+$send.Count)}
 if([Agent011AtomicFocus]::GetForegroundWindow() -ne $home.handle){throw 'DESTINATION_FOCUS_LOST_BEFORE_SEND'}
 if((Normalize-ChatUrl (UrlBar $source.window)) -cne $sourceUrl -or -not(Is-HomeUrl (UrlBar $home.window))){throw 'BROWSER_IDENTITY_CHANGED_BEFORE_SEND'}
 if((Selected-RealTab $home.window).name -cne $home.tab.name){throw 'HOME_TAB_CHANGED_BEFORE_SEND'}
 if(([string]$editor.pattern.Current.Value) -cne $script:Handoff){throw 'HANDOFF_CHANGED_BEFORE_SEND'}
 Save-Receipt 'SEND_GATES_VERIFIED'
 $script:State.send_invoked=$true
 Save-Receipt 'HANDOFF_SEND_UNCERTAIN_NO_RETRY'
 $send[0].invoke.Invoke()
 $deadline=[DateTime]::UtcNow.AddSeconds(30)
 do{
  Start-Sleep -Milliseconds 300
  $newUrl=UrlBar $home.window
  $canonical=$null
  try{$canonical=Normalize-ChatUrl $newUrl}catch{}
  if($null -ne $canonical -and $canonical -cne $sourceUrl){
   $script:State.destination_url_verified=$true
   $script:State.new_url=$canonical
   break
  }
 }while([DateTime]::UtcNow -lt $deadline)
 if(-not $script:State.destination_url_verified){throw 'SEND_URL_CHANGE_NOT_VERIFIED'}
 if((Normalize-ChatUrl (UrlBar $source.window)) -cne $sourceUrl){throw 'SOURCE_URL_CHANGED_AFTER_SEND'}
 Check-SourceEditors $source.window
 $null=Assert-Controls
 # URL only confirms navigation; require delivered user bubble in DESTINATION group.
 # Never retry Invoke. A missing bubble is an uncertain send with no replay.
 Save-Receipt 'DISTINCT_NEW_CONVERSATION_VERIFIED_MESSAGE_PENDING'
 $turnDeadline=[DateTime]::UtcNow.AddSeconds(25)
 $delivered=$false
 do{
  if((Normalize-ChatUrl (UrlBar $home.window)) -cne $script:State.new_url){throw 'DESTINATION_URL_CHANGED_DURING_USER_TURN_CHECK'}
  if(Test-Agent011DeliveredUserTurn $home.window){$delivered=$true;break}
  Start-Sleep -Milliseconds 500
 }while([DateTime]::UtcNow -lt $turnDeadline)
 if(-not $delivered){throw 'DESTINATION_USER_TURN_MARKERS_NOT_VISIBLE_NO_RETRY'}
 if((Normalize-ChatUrl (UrlBar $source.window)) -cne $sourceUrl){throw 'SOURCE_URL_CHANGED_AFTER_USER_TURN_CHECK'}
 Check-SourceEditors $source.window
 $null=Assert-Controls
 $script:State.marker_visible=$true
 $script:State.user_turn_verified=$true
 Save-Receipt 'DISTINCT_NEW_CONVERSATION_USER_TURN_MARKERS_VERIFIED_TITLE_PENDING'
 Write-Output 'AGENT011_DISTINCT_CONVERSATION_USER_TURN_MARKERS_VERIFIED_TITLE_PENDING'
}catch{
 $script:State.error=([string]$_.Exception.Message).Substring(0,[Math]::Min(320,([string]$_.Exception.Message).Length))
 try{
  if($script:State.send_invoked){Save-Receipt 'HALT_SUBMISSION_UNCERTAIN_NO_RETRY'}
  elseif($script:State.compose_attempted){Save-Receipt 'HALT_AFTER_COMPOSE_NO_RETRY'}
  elseif($script:State.focus_attempted){Save-Receipt 'HALT_AFTER_FOCUS_NO_RETRY'}
  else{Save-Receipt 'HALT_BEFORE_UI_MUTATION'}
 }catch{}
 [Console]::Error.WriteLine('AGENT011_FAIL_CLOSED_'+$script:State.error)
 exit 2
}
