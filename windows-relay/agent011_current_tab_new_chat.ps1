# Director correction 2026-10-09: invoke New chat ONLY in the relay-ORIGINATING selected ChatGPT tab.
# No new Firefox tab/window, no cross-window destination, no 11-tab count heuristic.
param(
 [Parameter(Mandatory=$true)][string]$SourcePacketId,
 [Parameter(Mandatory=$true)][string]$ReceiptFile,
 [Parameter(Mandatory=$true)][string]$ExpectedHead,
 [int]$ExpectedStopGeneration=9,
 [int]$ExpectedPendingMissions=2,
 [int]$SettleSeconds=8
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$Repo=Split-Path -Parent $PSScriptRoot
$Bridge=Join-Path $env:APPDATA 'GPTWindowsRelay\bridge.json'
$Live=Join-Path $env:USERPROFILE 'Downloads\Dev\GPT\Client\Relay'
$ReceiptFile=[IO.Path]::GetFullPath($ReceiptFile)
$script:State=[ordered]@{
 schema='agent011-current-origin-tab-new-chat-v1'
 phase='WORKER_ENTRY'
 source_packet=$SourcePacketId
 origin_tab_proven=$false
 source_url_sha256=$null
 source_window_handle=$null
 source_tab_runtime_id=$null
 new_chat_click_attempted=$false
 new_chat_clicked=$false
 same_tab_home_verified=$false
 paste_attempted=$false
 send_invoked=$false
 error=$null
}
function Save([string]$phase){
 $script:State.phase=$phase
 $temp=$ReceiptFile+'.writing'
 $backup=$ReceiptFile+'.previous'
 if((Test-Path -LiteralPath $temp) -or (Test-Path -LiteralPath $backup)){throw 'RECEIPT_TRANSITION_UNCERTAIN'}
 [IO.File]::WriteAllText($temp,($script:State|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 [IO.File]::Replace($temp,$ReceiptFile,$backup)
 [IO.File]::Delete($backup)
}
function Guard{
 if((Test-Path (Join-Path $PSScriptRoot '.relay-paused')) -or (Test-Path (Join-Path $Live '.relay-paused'))){throw 'OPERATOR_STOP'}
 $cfg=Get-Content -LiteralPath $Bridge -Raw|ConvertFrom-Json
 $r=Invoke-RestMethod -Uri ('http://127.0.0.1:'+([string]$cfg.port)+'/status') -Headers @{'X-GPT-Windows-Relay-Token'=[string]$cfg.token} -TimeoutSec 5
 if($r.ok -ne $true -or $r.armed -ne $true -or $r.outbound_owner -cne 'browser' -or [int]$r.stop_generation -ne $ExpectedStopGeneration -or [int]$r.pending_missions -ne $ExpectedPendingMissions){throw 'STOP_OWNER_OR_PENDING_CHANGED'}
}
function Hash([string]$s){
 $sha=[Security.Cryptography.SHA256]::Create()
 try{return [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($s))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
}
function Url($w){
 $c=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::AutomationIdProperty,'urlbar-input')
 $bars=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$c)
 if($bars.Count -ne 1){throw 'SOURCE_URLBAR_AMBIGUOUS'}
 $vp=$null
 if(-not $bars[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){throw 'SOURCE_URL_VALUE_UNAVAILABLE'}
 return [string]$vp.Current.Value
}
function IsConversation([string]$address){
 return $address -cmatch '^(?:https://)?chatgpt[.]com/c/[a-zA-Z0-9][a-zA-Z0-9-]{14,127}/?$'
}
function IsHome([string]$address){
 return $address -cmatch '^(?:https://)?chatgpt[.]com/?$'
}
function SelectedTab($w){
 $tc=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::TabItem)
 $tabs=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$tc)
 $selected=@()
 foreach($tab in $tabs){
  try{
   $p=$null
   if(-not $tab.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern,[ref]$p) -or -not $p.Current.IsSelected){continue}
   $parent=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($tab)
   if($null -ne $parent -and ([string]$parent.Current.AutomationId) -ceq 'tabbrowser-tabs'){$selected+=,[ordered]@{element=$tab;pattern=$p}}
  }catch{}
 }
 if($selected.Count -ne 1){throw 'ORIGIN_SELECTED_TAB_AMBIGUOUS'}
 return $selected[0]
}
function RecentSourceResult($w){
 $dc=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Document)
 $docs=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$dc)
 $visible=@()
 foreach($doc in $docs){try{if($doc.Current.IsEnabled -and -not $doc.Current.IsOffscreen){$visible+=,$doc}}catch{}}
 if($visible.Count -ne 1){return $false}
 $tp=$null
 if(-not $visible[0].TryGetCurrentPattern([Windows.Automation.TextPattern]::Pattern,[ref]$tp)){return $false}
 $body=[string]$tp.DocumentRange.GetText(-1)
 $open=$body.LastIndexOf('[GPT_WINDOWS_RESULT]')
 if($open -lt 0){return $false}
 $close=$body.IndexOf('[/GPT_WINDOWS_RESULT]',$open)
 if($close -le $open){return $false}
 $chunk=$body.Substring($open,[Math]::Min(9000,$close-$open))
 return $chunk.Contains($SourcePacketId) -and $chunk.Contains('"status"')
}
function FindOrigin{
 $wc=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Window)
 $all=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,$wc)
 $found=@()
 foreach($w in $all){
  try{
   if(([string]$w.Current.ClassName) -cne 'MozillaWindowClass' -or $w.Current.IsOffscreen){continue}
   $address=Url $w
   if(-not (IsConversation $address)){continue}
   $selected=SelectedTab $w
   if(-not (RecentSourceResult $w)){continue}
   $found+=,[ordered]@{window=$w;url=$address;selected=$selected;handle=[int64]$w.Current.NativeWindowHandle}
  }catch{}
 }
 if($found.Count -ne 1){return $null}
 return $found[0]
}
function NewChat($w){
 $buttons=$w.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
 $found=@()
 foreach($element in $buttons){
  try{
   if($element.Current.IsOffscreen -or -not $element.Current.IsEnabled){continue}
   if($element.Current.ControlType -ne [Windows.Automation.ControlType]::Button -and $element.Current.ControlType -ne [Windows.Automation.ControlType]::Hyperlink){continue}
   if(([string]$element.Current.Name).Trim() -notmatch '^(?i:New chat)$'){continue}
   $invoke=$null
   if($element.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)){$found+=,[ordered]@{invoke=$invoke}}
  }catch{}
 }
 if($found.Count -ne 1){throw ('NEW_CHAT_CONTROL_AMBIGUOUS_'+$found.Count)}
 return $found[0]
}
try{
 [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($ReceiptFile))|Out-Null
 $fs=[IO.FileStream]::new($ReceiptFile,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$bytes=[Text.Encoding]::UTF8.GetBytes(($script:State|ConvertTo-Json -Depth 6));$fs.Write($bytes,0,$bytes.Length);$fs.Flush($true)}finally{$fs.Dispose()}
}catch{[Console]::Error.WriteLine('EXCLUSIVE_RECEIPT_ALREADY_EXISTS_NO_RETRY');exit 2}
try{
 if($SettleSeconds -lt 5 -or $SettleSeconds -gt 25){throw 'SETTLE_DELAY_INVALID'}
 Start-Sleep -Seconds $SettleSeconds
 if((& git -C $Repo rev-parse HEAD) -cne $ExpectedHead -or (& git -C $Repo status --porcelain)){throw 'CANONICAL_SOURCE_CHANGED'}
 Guard
 Add-Type -AssemblyName UIAutomationClient
 Add-Type -AssemblyName UIAutomationTypes
 $deadline=[DateTime]::UtcNow.AddSeconds(45)
 $origin=$null
 do{
  $origin=FindOrigin
  if($null -ne $origin){break}
  Start-Sleep -Milliseconds 500
 }while([DateTime]::UtcNow -lt $deadline)
 if($null -eq $origin){throw 'CURRENT_RELAY_ORIGINATING_TAB_NOT_PROVEN_NO_UI_EFFECT'}
 $script:State.origin_tab_proven=$true
 $script:State.source_url_sha256=Hash $origin.url
 $script:State.source_window_handle=$origin.handle
 $script:State.source_tab_runtime_id=[string]::Join(',',@($origin.selected.element.GetRuntimeId()))
 Save 'EXACT_CURRENT_RELAY_ORIGIN_TAB_VERIFIED'
 $button=NewChat $origin.window
 Guard
 if(-not $origin.selected.pattern.Current.IsSelected -or (Url $origin.window) -cne $origin.url){throw 'SOURCE_TAB_CHANGED_PRE_CLICK'}
 $script:State.new_chat_click_attempted=$true
 Save 'SEMANTIC_NEW_CHAT_CLICK_INTENT_NO_RETRY'
 $button.invoke.Invoke()
 $deadline=[DateTime]::UtcNow.AddSeconds(15)
 $home=$false
 do{
  Start-Sleep -Milliseconds 250
  if(IsHome (Url $origin.window)){$home=$true;break}
 }while([DateTime]::UtcNow -lt $deadline)
 if(-not $home){throw 'SAME_TAB_NEW_CHAT_HOME_NOT_VERIFIED'}
 if(-not $origin.selected.pattern.Current.IsSelected){throw 'SAME_TAB_SELECTION_LOST'}
 if([int64]$origin.window.Current.NativeWindowHandle -ne $origin.handle){throw 'SAME_WINDOW_HANDLE_CHANGED'}
 $script:State.new_chat_clicked=$true
 $script:State.same_tab_home_verified=$true
 Save 'ORIGIN_TAB_SAME_TAB_NEW_CHAT_VERIFIED'
 Write-Output 'AGENT011_CURRENT_TAB_NEW_CHAT_CLICK_VERIFIED_HANDOFF_NOT_SENT'
}catch{
 $script:State.error=[string]$_.Exception.Message
 if($script:State.error.Length -gt 280){$script:State.error=$script:State.error.Substring(0,280)}
 try{Save 'HALT_NO_RETRY'}catch{}
 [Console]::Error.WriteLine('AGENT011_CURRENT_TAB_NEW_CHAT_FAILED_'+$script:State.error)
 exit 2
}
