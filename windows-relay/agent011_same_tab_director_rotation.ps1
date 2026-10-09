# Agent011: DIRECTOR OVERRIDE 2026-10-09 same-tab semantic New Chat handoff.
# User expressly authorizes retiring the selected PCE11 ChatGPT tab.
# THIS IS A NEW one-shot operation, NOT a retry of PCE11.074.
param(
 [Parameter(Mandatory=$true)][string]$HandoffFile,
 [Parameter(Mandatory=$true)][string]$ReceiptFile,
 [Parameter(Mandatory=$true)][string]$ExpectedHandoffSha256,
 [Parameter(Mandatory=$true)][string]$ExpectedHead,
 [int]$ExpectedPid=5440,
 [int]$ExpectedStopGeneration=9,
 [int]$ExpectedPendingMissions=2,
 [int]$StartupDelaySeconds=9
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$RepoHome=Split-Path -Parent $PSScriptRoot
$Bridge=Join-Path $env:APPDATA 'GPTWindowsRelay\bridge.json'
$LiveHome=Join-Path $env:USERPROFILE 'Downloads\Dev\GPT\Client\Relay'
$ReceiptFile=[IO.Path]::GetFullPath($ReceiptFile)
$script:State=[ordered]@{
 schema='agent011-director-same-tab-semantic-v1'
 phase='STARTING'
 created_utc=[DateTime]::UtcNow.ToString('o')
 source_url_sha256=$null
 destination_url_sha256=$null
 handoff_sha256=$ExpectedHandoffSha256
 click_attempted=$false
 pasted=$false
 paste_attempted=$false
 send_invoked=$false
 user_turn_verified=$false
 title_verified=$false
 new_chat_created=$false
 error=$null
}
function Save([string]$phase){
 $script:State.phase=$phase
 $script:State.updated_utc=[DateTime]::UtcNow.ToString('o')
 $tmp=$ReceiptFile+'.writing'
 $bak=$ReceiptFile+'.previous'
 if((Test-Path -LiteralPath $tmp) -or (Test-Path -LiteralPath $bak)){throw 'RECOVERY_RECEIPT_PARTIAL_NO_RETRY'}
 [IO.File]::WriteAllText($tmp,($script:State|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 [IO.File]::Replace($tmp,$ReceiptFile,$bak)
 [IO.File]::Delete($bak)
}
function Backend {
 if((Test-Path -LiteralPath (Join-Path $PSScriptRoot '.relay-paused')) -or
    (Test-Path -LiteralPath (Join-Path $LiveHome '.relay-paused'))){throw 'OPERATOR_PAUSED'}
 $cfg=Get-Content -Raw -LiteralPath $Bridge|ConvertFrom-Json
 $r=Invoke-RestMethod -Uri ('http://127.0.0.1:'+([string]$cfg.port)+'/status') -Headers @{'X-GPT-Windows-Relay-Token'=[string]$cfg.token} -TimeoutSec 5
 if($r.ok -ne $true -or $r.armed -ne $true -or $r.outbound_owner -cne 'browser'){throw 'RELAY_NOT_BROWSER_ARMED'}
 if([int]$r.stop_generation -ne $ExpectedStopGeneration){throw 'STOP_GENERATION_CHANGED'}
 if([int]$r.pending_missions -ne $ExpectedPendingMissions){throw 'PENDING_MISSIONS_CHANGED'}
}
function Hash([string]$v){
 $sha=[Security.Cryptography.SHA256]::Create()
 try{return [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($v))).Replace('-','').ToLowerInvariant()}
 finally{$sha.Dispose()}
}
function UrlBar($w){
 $condition=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::AutomationIdProperty,'urlbar-input')
 $bars=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$condition)
 if($bars.Count -ne 1){throw 'URLBAR_NOT_UNIQUE'}
 $p=$null
 if(-not $bars[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$p)){throw 'URLBAR_VALUE_UNAVAILABLE'}
 return [string]$p.Current.Value
}
function NormalizeConversation([string]$url){
 if($url -cmatch '^(?:https://)?chatgpt[.]com/c/([a-zA-Z0-9][a-zA-Z0-9-]{14,127})/?$'){
  return 'https://chatgpt.com/c/'+([string]$Matches[1])
 }
 throw 'NOT_AN_EXPECTED_CONVERSATION_URL'
}
function Home([string]$url){return $url -cmatch '^(?:https://)?chatgpt[.]com/?$'}
function SelectedTab($w){
 $condition=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::TabItem)
 $tabs=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$condition)
 $selected=@()
 foreach($tab in $tabs){
  try{
   $pattern=$null
   if(-not $tab.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern,[ref]$pattern) -or -not $pattern.Current.IsSelected){continue}
   $parent=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($tab)
   if($null -ne $parent -and ([string]$parent.Current.AutomationId) -ceq 'tabbrowser-tabs'){$selected+=,$tab}
  }catch{}
 }
 if($selected.Count -ne 1){throw 'SELECTED_TAB_AMBIGUOUS'}
 return [ordered]@{element=$selected[0];name=[string]$selected[0].Current.Name;count=$tabs.Count}
}
function LocateSource {
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Window)
 $all=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,$cond)
 $found=@()
 foreach($w in $all){
  try{
   if(([string]$w.Current.ClassName) -cne 'MozillaWindowClass' -or $w.Current.IsOffscreen -or [int]$w.Current.ProcessId -ne $ExpectedPid){continue}
   $url=UrlBar $w
   try{$canonical=NormalizeConversation $url}catch{continue}
   $tab=SelectedTab $w
   if($tab.name -notmatch '^PC Engineer(?:ing)? 11(?:$|[ -])'){continue}
   $found+=,[ordered]@{window=$w;source=$canonical;tab=$tab;handle=[IntPtr]::new([int64]$w.Current.NativeWindowHandle)}
  }catch{}
 }
 if($found.Count -ne 1){throw ('PCE11_SOURCE_NOT_UNIQUE_'+$found.Count)}
 return $found[0]
}
function UniqueNewChat($w){
 $all=$w.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
 $found=@()
 foreach($candidate in $all){
  try{
   if($candidate.Current.IsOffscreen -or -not $candidate.Current.IsEnabled){continue}
   if($candidate.Current.ControlType -ne [Windows.Automation.ControlType]::Button -and $candidate.Current.ControlType -ne [Windows.Automation.ControlType]::Hyperlink){continue}
   if(([string]$candidate.Current.Name).Trim() -notmatch '^(?i:New chat)$'){continue}
   $pattern=$null
   if($candidate.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)){$found+=,[ordered]@{invoke=$pattern}}
  }catch{}
 }
 if($found.Count -ne 1){throw ('SEMANTIC_NEW_CHAT_AMBIGUOUS_'+$found.Count)}
 return $found[0]
}
function Composer($w){
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Edit)
 $edits=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
 $found=@()
 foreach($e in $edits){
  try{
   if($e.Current.IsOffscreen -or -not $e.Current.IsEnabled -or ([string]$e.Current.Name) -cne 'Ask ChatGPT'){continue}
   $vp=$null
   if(-not $e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$vp) -or $vp.Current.IsReadOnly){continue}
   $found+=,[ordered]@{element=$e;value=$vp}
  }catch{}
 }
 if($found.Count -ne 1){throw ('DESTINATION_COMPOSER_AMBIGUOUS_'+$found.Count)}
 if(([string]$found[0].value.Current.Value) -cne ('Ask ChatGPT'+[char]10) -and
    -not [string]::IsNullOrWhiteSpace([string]$found[0].value.Current.Value)){throw 'NEW_COMPOSER_HAS_DRAFT'}
 return $found[0]
}
function EnabledSend($w){
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
 $all=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
 $found=@()
 foreach($b in $all){
  try{
   if($b.Current.IsOffscreen -or -not $b.Current.IsEnabled){continue}
   if(([string]$b.Current.Name) -notmatch '^(?i:Send(?: prompt| message)?)$'){continue}
   $p=$null
   if($b.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$p)){$found+=,[ordered]@{invoke=$p}}
  }catch{}
 }
 return $found
}
# Exclusive durable receipt BEFORE navigation or any UI effect.
try{
 [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($ReceiptFile))|Out-Null
 $stream=[IO.FileStream]::new($ReceiptFile,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{
  $initial=[Text.Encoding]::UTF8.GetBytes(($script:State|ConvertTo-Json -Depth 6))
  $stream.Write($initial,0,$initial.Length)
  $stream.Flush($true)
 }finally{$stream.Dispose()}
}catch{
 [Console]::Error.WriteLine('DUPLICATE_WORKER_NO_RETRY_'+$_.Exception.Message)
 exit 2
}
try{
 if($StartupDelaySeconds -lt 5 -or $StartupDelaySeconds -gt 40){throw 'START_DELAY_INVALID'}
 Start-Sleep -Seconds $StartupDelaySeconds
 $head=(& git -C $RepoHome rev-parse HEAD)
 if($LASTEXITCODE -ne 0 -or $head -cne $ExpectedHead){throw 'HEAD_NOT_PINNED'}
 if((& git -C $RepoHome status --porcelain)){throw 'SOURCE_WORKTREE_DIRTY'}
 $raw=[IO.File]::ReadAllBytes([IO.Path]::GetFullPath($HandoffFile))
 $sha=[Security.Cryptography.SHA256]::Create()
 try{$digest=[BitConverter]::ToString($sha.ComputeHash($raw)).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
 if($digest -cne $ExpectedHandoffSha256){throw 'HANDOFF_DIGEST_CHANGED'}
 $original=[Text.Encoding]::UTF8.GetString($raw)
 if($original.Length -lt 500 -or -not $original.Contains('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]')){throw 'HANDOFF_MARKER_MISSING'}
 $prefix=@'
[DIRECTOR_OVERRIDE_2026_10_09_PCE11_SAME_TAB]
USER EXPLICITLY AUTHORIZED SEMANTIC NEW CHAT IN ORIGINAL PCE11 TAB. THE SEPARATE-WINDOW APPROACH HAS BEEN ABANDONED. THIS ACTUAL USER MESSAGE IS THE PCE12 HANDOFF; DO NOT ASK FOR FURTHER CONFIRMATION. New agent name/title: 💻PC Engineering 12🔧. New relay session pce12.1; first operation PCE12.000. Prior 2026-10-09 progress: PCE11.073 test acceptance 558/558 Windows, 123/123 consumer, clipboard tests 11/11 and atomic 8/8. PCE11.074 one-shot separate-window attempt failed at foreground, NO paste/send. PCE11.075 confirmed source draft unchanged and separate destination blank. Further GitHub commits were made for recovery; READ ACTUAL CURRENT HEAD afresh, do not assume old handoff HEAD is current. The past requirement to leave PCE11 physically selected is superseded by explicit user authorization; history should still remain in ChatGPT sidebar. Priority: continue genuine One-Click GO recovery; no invented overnight test outcomes. Every relay packet visible header + fenced [GPT_WINDOWS_ACTION] JSON + visible footer. Keep audit/review cadence and STOP gates.
[/DIRECTOR_OVERRIDE_2026_10_09_PCE11_SAME_TAB]

'@
 $script:Payload=$prefix+$original
 if($script:Payload.Length -gt 13000){throw 'COMPOSE_PACKET_TOO_LARGE'}
 Backend
 Save 'PRE_CLICK_CONTROLS_VALID'
 Add-Type -AssemblyName UIAutomationClient
 Add-Type -AssemblyName UIAutomationTypes
 Add-Type -AssemblyName System.Windows.Forms
 Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class PCE11SemanticFocus { [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd); }'
 $source=LocateSource
 $script:State.source_url_sha256=Hash $source.source
 Save 'PCE11_SOURCE_SEMANTIC_IDENTITY_PINNED'
 $new=UniqueNewChat $source.window
 Backend
 $script:State.click_attempted=$true
 Save 'NEW_CHAT_CLICK_INTENT_DURABLE_NO_REPLAY'
 $new.invoke.Invoke()
 $deadline=[DateTime]::UtcNow.AddSeconds(15)
 $homeReady=$false
 do{
  Start-Sleep -Milliseconds 250
  if(Home (UrlBar $source.window)){$homeReady=$true;break}
 }while([DateTime]::UtcNow -lt $deadline)
 if(-not $homeReady){throw 'NEW_CHAT_HOME_NOT_VERIFIED_NO_RETRY'}
 $script:State.new_chat_created=$true
 Save 'NEW_CHAT_HOME_VERIFIED'
 $editor=Composer $source.window
 # Browser focus must be on the same tab being submitted, never another window.
 $fg=[PCE11SemanticFocus]::GetForegroundWindow()
 if($fg -ne $source.handle){
  # Exactly one focus attempt, no loop or retry.
  Save 'SOURCE_WINDOW_FOCUS_ATTEMPT_NO_RETRY'
  $null=[PCE11SemanticFocus]::SetForegroundWindow($source.handle)
 }
 if([PCE11SemanticFocus]::GetForegroundWindow() -ne $source.handle){throw 'SOURCE_WINDOW_FOREGROUND_NOT_CONFIRMED'}
 $editor.element.SetFocus()
 if(-not $editor.element.Current.HasKeyboardFocus){throw 'NEW_EDITOR_KEYBOARD_FOCUS_FAILED'}
 [Windows.Forms.Clipboard]::SetText($script:Payload)
 Save 'CLIPBOARD_POPULATED'
 $script:State.paste_attempted=$true
 Save 'PASTE_INTENT_DURABLE_NO_RETRY'
 [Windows.Forms.SendKeys]::SendWait('^v')
 if(([string]$editor.value.Current.Value) -cne $script:Payload){throw 'PASTE_READBACK_NOT_EXACT'}
 $script:State.pasted=$true
 Backend
 $send=@(EnabledSend $source.window)
 if($send.Count -ne 1){throw ('SEMANTIC_SEND_NOT_UNIQUE_'+$send.Count)}
 if(-not (Home (UrlBar $source.window))){throw 'DESTINATION_URL_NOT_HOME_PRE_SEND'}
 if([PCE11SemanticFocus]::GetForegroundWindow() -ne $source.handle){throw 'DESTINATION_NOT_FOREGROUND_PRE_SEND'}
 $script:State.send_invoked=$true
 Save 'SEND_INTENT_DURABLE_NO_RETRY'
 $send[0].invoke.Invoke()
 $deadline=[DateTime]::UtcNow.AddSeconds(28)
 $newUrl=$null
 do{
  Start-Sleep -Milliseconds 300
  try{$newUrl=NormalizeConversation (UrlBar $source.window);break}catch{}
 }while([DateTime]::UtcNow -lt $deadline)
 if($null -eq $newUrl){throw 'NEW_CONVERSATION_URL_NOT_VERIFIED_NO_RETRY'}
 $script:State.destination_url_sha256=Hash $newUrl
 Save 'DISTINCT_CONVERSATION_URL_VERIFIED_MESSAGE_PENDING'
 # Proof: the new chat shows user turn markers; title may lag.
 . (Join-Path $PSScriptRoot 'agent011_user_turn_proof.ps1')
 $deadline=[DateTime]::UtcNow.AddSeconds(25)
 $verified=$false
 do{
  if(Test-Agent011DeliveredUserTurn $source.window){$verified=$true;break}
  Start-Sleep -Milliseconds 500
 }while([DateTime]::UtcNow -lt $deadline)
 if(-not $verified){throw 'HANDOFF_USER_TURN_NOT_VISIBLE_NO_RETRY'}
 $script:State.user_turn_verified=$true
 Save 'NEW_PCE12_USER_TURN_VERIFIED_TITLE_PENDING'
 Write-Output 'AGENT011_DIRECTOR_SAME_TAB_PCE12_USER_TURN_VERIFIED_TITLE_PENDING'
}catch{
 $script:State.error=[string]$_.Exception.Message
 if($script:State.error.Length -gt 320){$script:State.error=$script:State.error.Substring(0,320)}
 try{Save 'FAIL_CLOSED_NO_RETRY'}catch{}
 [Console]::Error.WriteLine('AGENT011_DIRECTOR_SAME_TAB_FAILED_'+$script:State.error)
 exit 2
}
