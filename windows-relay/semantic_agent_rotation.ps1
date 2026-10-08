# Director-authorized one-shot Agent011 semantic chat rotation.
# Operational action; no extension code deployment, refresh or replay.
param(
 [Parameter(Mandatory=$true)][string]$SourcePacketId,
 [Parameter(Mandatory=$true)][string]$HandoffFile,
 [Parameter(Mandatory=$true)][string]$ReceiptFile
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$RelayHome=Join-Path $env:LOCALAPPDATA 'GPTWindowsRelay'
$Bridge=Join-Path $env:APPDATA 'GPTWindowsRelay\bridge.json'
$LiveHome=Join-Path $env:USERPROFILE 'Downloads\Dev\GPT\Client\Relay'
$state=[ordered]@{
 schema='agent011-semantic-rotation-v1';phase='STARTED';source_packet_id=$SourcePacketId
 target_title=([char]::ConvertFromUtf32(0x1F4BB)+'PC Engineering 12'+[char]::ConvertFromUtf32(0x1F527));target_session='pce12.1';first_operation='PCE12.000'
 started_at=[DateTime]::UtcNow.ToString('o');source_url=$null;new_url=$null
 source_tab=$null;firefox_pid=$null;send_invoked=$false;click_invoked=$false
 handoff_visible=$false;title_verified=$false;operator_stopped=$false;error=$null
}
function Save([string]$Phase,[string]$Detail=''){
 $state.phase=$Phase;$state.updated_at=[DateTime]::UtcNow.ToString('o')
 if($Detail){$state.detail=$Detail.Substring(0,[Math]::Min(250,$Detail.Length))}
 $target=[IO.Path]::GetFullPath($ReceiptFile)
 [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))|Out-Null
 $tmp=$target+'.writing'
 [IO.File]::WriteAllText($tmp,($state|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
 Move-Item -LiteralPath $tmp -Destination $target -Force
}
function ReadBackend([string]$Path){
 $cfg=Get-Content -LiteralPath $Bridge -Raw|ConvertFrom-Json
 $uri="http://127.0.0.1:$($cfg.port)$Path"
 Invoke-RestMethod -Uri $uri -Headers @{'X-GPT-Windows-Relay-Token'=[string]$cfg.token} -TimeoutSec 4
}
function CheckControls(){
 if((Test-Path -LiteralPath (Join-Path $PSScriptRoot '.relay-paused')) -or
    (Test-Path -LiteralPath (Join-Path $LiveHome '.relay-paused'))){throw 'ROTATION_OPERATOR_STOP_FILE'}
 $r=ReadBackend '/status'
 if($r.ok -ne $true -or $r.armed -ne $true -or $r.outbound_owner -ne 'browser'){throw 'ROTATION_RELAY_UNAVAILABLE_OR_STOPPED'}
 return $r
}
$aut=[Windows.Automation.AutomationElement]
$ct=[Windows.Automation.ControlType]
$ts=[Windows.Automation.TreeScope]
$wc=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Window)
$tc=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::TabItem)
function SelectedSource {
 $windows=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,$wc)
 $found=@()
 foreach($w in $windows){
  try{
   if($w.Current.IsOffscreen -or $w.Current.ClassName -ne 'MozillaWindowClass'){continue}
   $tabs=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$tc)
   foreach($tab in $tabs){
    try{
     if(-not $tab.Current.IsEnabled){continue}
     $sp=$null
     if(-not $tab.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sp) -or -not $sp.Current.IsSelected){continue}
     if(([string]$tab.Current.Name) -notmatch '^PC Engineer(?:ing)? 11(?:\b|[ -])'){continue}
     $parent=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($tab)
     if($null -eq $parent -or $parent.Current.AutomationId -ne 'tabbrowser-tabs'){continue}
     $found+=,[ordered]@{window=$w;tab=$tab;selection=$sp}
    }catch{}
   }
  }catch{}
 }
 if($found.Count -ne 1){throw ('ROTATION_SOURCE_TAB_COUNT_'+$found.Count)}
 return $found[0]
}
function UrlBar($window){
 $cond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::AutomationIdProperty,'urlbar-input')
 $bars=$window.FindAll([Windows.Automation.TreeScope]::Descendants,$cond)
 if($bars.Count -ne 1){throw ('ROTATION_URLBAR_COUNT_'+$bars.Count)}
 $vp=$null
 if(-not $bars[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){throw 'ROTATION_URLBAR_NO_VALUE'}
 return [string]$vp.Current.Value
}
function DocumentBody($window){
 $dc=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Document)
 $docs=$window.FindAll([Windows.Automation.TreeScope]::Descendants,$dc);$visible=@()
 foreach($d in $docs){try{if($d.Current.IsEnabled -and -not $d.Current.IsOffscreen){$visible+=,$d}}catch{}}
 if($visible.Count -ne 1){return ''}
 $p=$null
 if(-not $visible[0].TryGetCurrentPattern([Windows.Automation.TextPattern]::Pattern,[ref]$p)){return ''}
 return [string]$p.DocumentRange.GetText(-1)
}
function NewChatButton($window){
 $buttons=$window.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
 $hits=@()
 foreach($b in $buttons){
  try{
   if($b.Current.IsOffscreen -or -not $b.Current.IsEnabled){continue}
   if($b.Current.ControlType -ne [Windows.Automation.ControlType]::Button -and $b.Current.ControlType -ne [Windows.Automation.ControlType]::Hyperlink){continue}
   $name=([string]$b.Current.Name).Trim()
   if($name -notmatch '^(?i:New chat)$'){continue}
   $ip=$null
   if($b.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$ip)){$hits+=,[ordered]@{element=$b;invoke=$ip}}
  }catch{}
 }
 if($hits.Count -ne 1){throw ('ROTATION_NEW_CHAT_SEMANTIC_COUNT_'+$hits.Count)}
 return $hits[0]
}
function Composer($window){
 $edits=$window.FindAll([Windows.Automation.TreeScope]::Descendants,(New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Edit)))
 $matching=@()
 foreach($e in $edits){
  try{
   if($e.Current.IsOffscreen -or -not $e.Current.IsEnabled){continue}
   if(([string]$e.Current.Name) -eq 'Ask ChatGPT' -and ([string]$e.Current.ClassName) -eq 'ProseMirror'){$matching+=,$e}
  }catch{}
 }
 if($matching.Count -ne 1){throw ('ROTATION_COMPOSER_COUNT_'+$matching.Count)}
 $vp=$null
 if(-not $matching[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$vp) -or $vp.Current.IsReadOnly){throw 'ROTATION_COMPOSER_VALUE_UNAVAILABLE'}
 return @{element=$matching[0];value=$vp}
}
try{
 # POSITIVE WORKER-START RECEIPT: record execution before control/UI reads.
 Save 'WORKER_ENTRY'
 if(-not(Test-Path -LiteralPath $HandoffFile -PathType Leaf)){throw 'HANDOFF_FILE_MISSING'}
 $text=[IO.File]::ReadAllText([IO.Path]::GetFullPath($HandoffFile),[Text.Encoding]::UTF8)
 if($text.Length -lt 200 -or $text.Length -gt 12000 -or
    -not $text.Contains('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]') -or
    -not $text.Contains('PCE12.000') -or -not $text.Contains('engineering_preflight')){throw 'HANDOFF_SCHEMA_REJECTED'}
 Save 'HANDOFF_VALIDATED'
 $baseline=CheckControls
 Save 'CONTROL_GATE_PASSED'
 $initialPending=$baseline.pending_missions
 $source=SelectedSource
 Save 'SOURCE_TAB_RECOGNIZED'
 $window=$source.window;$tab=$source.tab;$selected=$source.selection
 $url=UrlBar $window
 if($url -notmatch '^https://chatgpt\.com/c/[^/?#]+/?$'){throw 'SOURCE_CONVERSATION_IDENTITY_INVALID'}
 $state.source_url=$url;$state.source_tab=[string]$tab.Current.Name
 $state.firefox_pid=[int]$window.Current.ProcessId
 Save 'WAITING_FOR_SOURCE_RESULT'
 $deadline=[DateTime]::UtcNow.AddSeconds(105)
 $confirmed=$false
 do{
  Start-Sleep -Milliseconds 500
  if(-not $selected.Current.IsSelected -or (UrlBar $window) -ne $url){throw 'SOURCE_TAB_CHANGED_DURING_DELIVERY'}
  $body=DocumentBody $window
  $open=$body.LastIndexOf('[GPT_WINDOWS_RESULT]')
  if($open -ge 0){
   $close=$body.IndexOf('[/GPT_WINDOWS_RESULT]',$open)
   if($close -gt $open){
    $span=$body.Substring($open,[Math]::Min(8000,$close-$open))
    if($span.Contains($SourcePacketId) -and $span.Contains('"status"')){$confirmed=$true;break}
   }
  }
 }while([DateTime]::UtcNow -lt $deadline)
 if(-not $confirmed){throw 'SOURCE_RESULT_VISIBLE_RECEIPT_NOT_PROVEN'}
 Save 'SOURCE_RESULT_VISIBLE'
 $status=CheckControls
 if($status.pending_missions -ne $initialPending){throw 'PENDING_MISSIONS_CHANGED'}
 if(-not $selected.Current.IsSelected -or (UrlBar $window) -ne $url){throw 'SOURCE_IDENTITY_LOST'}
 $oldComposer=Composer $window
 if(-not [string]::IsNullOrWhiteSpace([string]$oldComposer.value.Current.Value)){throw 'SOURCE_COMPOSER_HAS_DRAFT'}
 $new=NewChatButton $window
 $state.click_invoked=$true
 Save 'NEW_CHAT_CLICK_UNCERTAIN'
 $new.invoke.Invoke()
 Save 'NEW_CHAT_INVOKED'
 $until=[DateTime]::UtcNow.AddSeconds(18);$newUrl=''
 do{
  Start-Sleep -Milliseconds 300
  $newUrl=UrlBar $window
  if($newUrl -match '^https://chatgpt\.com/?(?:\?.*)?$'){break}
 }while([DateTime]::UtcNow -lt $until)
 if($newUrl -notmatch '^https://chatgpt\.com/?(?:\?.*)?$'){throw 'NEW_CHAT_EMPTY_CONVERSATION_NOT_VERIFIED'}
 if(-not $selected.Current.IsSelected){throw 'SOURCE_TAB_SELECTION_CHANGED'}
 $state.new_url=$newUrl
 Save 'NEW_EMPTY_CHAT_VERIFIED'
 $controls=CheckControls
 if($controls.pending_missions -ne $initialPending){throw 'PENDING_MISSIONS_CHANGED_BEFORE_SEND'}
 $comp=Composer $window
 if(-not [string]::IsNullOrWhiteSpace([string]$comp.value.Current.Value)){throw 'NEW_COMPOSER_NOT_EMPTY'}
 $comp.value.SetValue($text)
 Start-Sleep -Milliseconds 200
 if([string]$comp.value.Current.Value -ne $text){throw 'HANDOFF_TEXT_READBACK_FAILED'}
 $buttonCond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
 $buttons=$window.FindAll([Windows.Automation.TreeScope]::Descendants,$buttonCond)
 $send=@()
 foreach($b in $buttons){try{if($b.Current.IsEnabled -and -not $b.Current.IsOffscreen -and ([string]$b.Current.Name) -match '^Send(?: prompt| message)?$'){$send+=,$b}}catch{}}
 if($send.Count -ne 1){
  # ChatGPT may require a real DOM input event; guarded focus/paste only.
  Add-Type -AssemblyName System.Windows.Forms
  $oldClipboard=[System.Windows.Forms.Clipboard]::GetDataObject()
  try{
   $comp.value.SetValue('')
   $comp.element.SetFocus()
   [System.Windows.Forms.Clipboard]::SetText($text)
   [System.Windows.Forms.SendKeys]::SendWait('^v')
   Start-Sleep -Milliseconds 300
  }finally{
   try{if($null -ne $oldClipboard){[System.Windows.Forms.Clipboard]::SetDataObject($oldClipboard,$true)}else{[System.Windows.Forms.Clipboard]::Clear()}}catch{}
  }
  if([string]$comp.value.Current.Value -ne $text){throw 'HANDOFF_PASTE_READBACK_FAILED'}
  $buttons=$window.FindAll([Windows.Automation.TreeScope]::Descendants,$buttonCond);$send=@()
  foreach($b in $buttons){try{if($b.Current.IsEnabled -and -not $b.Current.IsOffscreen -and ([string]$b.Current.Name) -match '^Send(?: prompt| message)?$'){$send+=,$b}}catch{}}
 }
 if($send.Count -ne 1){throw ('HANDOFF_SEND_BUTTON_COUNT_'+$send.Count)}
 $ip=$null
 if(-not $send[0].TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$ip)){throw 'HANDOFF_SEND_INVOKE_NOT_AVAILABLE'}
 if(-not $selected.Current.IsSelected -or (UrlBar $window) -eq $url){throw 'NEW_CHAT_IDENTITY_LOST_BEFORE_SEND'}
 $state.send_invoked=$true
 Save 'HANDOFF_SEND_UNCERTAIN'
 $ip.Invoke()
 $until=[DateTime]::UtcNow.AddSeconds(28)
 do{
  Start-Sleep -Milliseconds 300
  $newUrl=UrlBar $window
  if($newUrl -match '^https://chatgpt\.com/c/[^/?#]+/?$' -and $newUrl -ne $url){
   $body=DocumentBody $window
   if($body.Contains('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]') -and $body.Contains('PCE12.000')){
    $state.new_url=$newUrl
    $state.handoff_visible=$true
    break
   }
  }
 }while([DateTime]::UtcNow -lt $until)
 if(-not $state.handoff_visible){throw 'HANDOFF_SENT_BUT_VISIBLE_RECEIPT_OR_NEW_ID_UNCONFIRMED'}
 if((CheckControls).pending_missions -ne $initialPending){throw 'PENDING_MISSIONS_CHANGED_AFTER_SEND'}
 # Rename not asserted: receiving agent is mandated to verify/rename before
 # executing PCE12.000. Do not repeat a successfully submitted handoff.
 Save 'NEW_CHAT_HANDOFF_VERIFIED_TITLE_PENDING' 'Distinct new chat and handoff visible; successor governance and title pending positive proof'
}catch{
 $state.error=([string]$_.Exception.Message).Substring(0,[Math]::Min(400,([string]$_.Exception.Message).Length))
 if($state.send_invoked){Save 'HALT_SUBMISSION_UNCERTAIN' $state.error}
 elseif($state.click_invoked){Save 'HALT_AFTER_CLICK_NO_RETRY' $state.error}
 else{Save 'HALT_BEFORE_CLICK' $state.error}
 exit 2
}
