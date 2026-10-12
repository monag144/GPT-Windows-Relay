param(
 [Parameter(Mandatory=$true)][ValidateSet('list-tabs','select-tab','reload-addon','refresh-tab','ensure-addon','close-profile','send-chatgpt-prompt','read-chatgpt-text','send-relay-result','resolve-conversation-tab')][string]$Action,
 [string]$TabName='',
 [string]$Contains='',
 [string]$AddonName='',
 [string]$ManifestPath='',
 [int]$FirefoxPid=0,
 [string]$ProfilePath='',
 [string]$PromptText='',
 [string]$ResultFile='',
 [string]$PacketId='',
 [string]$ExactTabName='',
 [string]$ConversationUrl=''
)
$ErrorActionPreference='Stop'
function Normalize-RelayConversationUrl([string]$Value,[bool]$Strict=$false){
 try{
  if([string]::IsNullOrWhiteSpace($Value)){throw 'invalid'}
  $u=[Uri]$Value
  $parts=@($u.AbsolutePath.Trim('/') -split '/')
  if($u.Scheme -ne 'https' -or $u.Host -ne 'chatgpt.com' -or $parts.Count -ne 2 -or $parts[0] -ne 'c' -or [string]::IsNullOrWhiteSpace($parts[1])){throw 'invalid'}
  return 'https://chatgpt.com/c/'+$parts[1]
 }catch{
  if($Strict){throw 'FIREFOX_CONVERSATION_URL_INVALID'}
  return $null
 }
}
if($Action -in @('select-tab','refresh-tab')){
 if(([string]::IsNullOrEmpty($TabName) -and [string]::IsNullOrEmpty($Contains)) -or (-not [string]::IsNullOrEmpty($TabName) -and -not [string]::IsNullOrEmpty($Contains))){throw 'TAB_SELECTOR_REQUIRED_EXACTLY_ONE'}
}
if($Action -in @('reload-addon','ensure-addon') -and [string]::IsNullOrWhiteSpace($AddonName)){throw 'ADDON_NAME_REQUIRED'}
if($Action -eq 'close-profile' -and [string]::IsNullOrWhiteSpace($ProfilePath)){throw 'PROFILE_PATH_REQUIRED'}
if($Action -eq 'send-chatgpt-prompt' -and [string]::IsNullOrWhiteSpace($PromptText)){throw 'PROMPT_TEXT_REQUIRED'}
if($Action -eq 'resolve-conversation-tab'){$ConversationUrl=Normalize-RelayConversationUrl $ConversationUrl $true}
if($PromptText.Length -gt 12000){throw 'PROMPT_TEXT_TOO_LONG'}
if($Action -eq 'send-relay-result'){
 if([string]::IsNullOrWhiteSpace($ResultFile)){throw 'RELAY_RESULT_FILE_REQUIRED'}
 if([string]::IsNullOrWhiteSpace($PacketId)){throw 'RELAY_RESULT_PACKET_ID_REQUIRED'}
 if([string]::IsNullOrWhiteSpace($ExactTabName)){throw 'RELAY_RESULT_EXACT_TAB_REQUIRED'}
 if([string]::IsNullOrWhiteSpace($ConversationUrl)){throw 'RELAY_RESULT_CONVERSATION_URL_REQUIRED'}
 $ConversationUrl=Normalize-RelayConversationUrl $ConversationUrl $true
 $ResultFile=[IO.Path]::GetFullPath($ResultFile)
 if(-not(Test-Path -LiteralPath $ResultFile -PathType Leaf)){throw 'RELAY_RESULT_FILE_NOT_FOUND'}
 $utf8=New-Object System.Text.UTF8Encoding($false,$true)
 $ResultText=[System.IO.File]::ReadAllText($ResultFile,$utf8)
 if([string]::IsNullOrWhiteSpace($ResultText)){throw 'RELAY_RESULT_TEXT_REQUIRED'}
 if($ResultText.Length -gt 250000){throw 'RELAY_RESULT_TEXT_TOO_LONG'}
 if(-not $ResultText.Contains($PacketId)){throw 'RELAY_RESULT_PACKET_ID_NOT_IN_TEXT'}
}
if(-not [string]::IsNullOrWhiteSpace($ProfilePath)){$ProfilePath=[IO.Path]::GetFullPath($ProfilePath)}
if($Action -eq 'ensure-addon'){
 if([string]::IsNullOrWhiteSpace($ManifestPath)){throw 'MANIFEST_PATH_REQUIRED'}
 $ManifestPath=[IO.Path]::GetFullPath($ManifestPath)
 if(-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)){throw 'MANIFEST_PATH_NOT_FOUND'}
}
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$fps=@(Get-Process firefox -ErrorAction SilentlyContinue)
$allFirefox=@(Get-CimInstance Win32_Process -Filter "Name='firefox.exe'" -ErrorAction SilentlyContinue)
$targetPids=@($fps.Id)
$profileRoots=@()
if(-not [string]::IsNullOrWhiteSpace($ProfilePath)){
 # GPT_WINDOWS_FIREFOX_MANAGED_PROFILE_IDENTITY_V1
 $profileRoots=@($allFirefox|Where-Object{$_.CommandLine -and ([string]$_.CommandLine).Contains($ProfilePath)})
 if($Action -ne 'close-profile' -and $profileRoots.Count -lt 1){throw 'FIREFOX_PROFILE_ROOT_COUNT_0'}
 $targetPids=@($profileRoots|ForEach-Object{[int]$_.ProcessId})
}elseif($FirefoxPid -gt 0){
 # GPT_WINDOWS_FIREFOX_MANAGED_PROCESS_TREE_V1
 $targetPids=@($FirefoxPid)
}
if(-not [string]::IsNullOrWhiteSpace($ProfilePath) -or $FirefoxPid -gt 0){
 $changed=$true
 while($changed){
  $changed=$false
  foreach($proc in $allFirefox){
   if(($targetPids -contains [int]$proc.ParentProcessId) -and -not ($targetPids -contains [int]$proc.ProcessId)){
    $targetPids+=,[int]$proc.ProcessId
    $changed=$true
   }
  }
 }
}
if($Action -eq 'close-profile'){
 # GPT_WINDOWS_FIREFOX_PROFILE_CLOSE_IDEMPOTENT_V1
 # GPT_WINDOWS_FIREFOX_PROFILE_CLOSE_BARRIER_V1
 foreach($procId in @($targetPids|Sort-Object -Descending -Unique)){
  Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
 }
 $deadline=[DateTime]::UtcNow.AddSeconds(5)
 $remaining=@()
 do{
  Start-Sleep -Milliseconds 100
  $remaining=@(Get-CimInstance Win32_Process -Filter "Name='firefox.exe'" -ErrorAction SilentlyContinue|Where-Object{$_.CommandLine -and ([string]$_.CommandLine).Contains($ProfilePath)})
 }while($remaining.Count -gt 0 -and [DateTime]::UtcNow -lt $deadline)
 if($remaining.Count -gt 0){
  $ids=@($remaining|ForEach-Object{[string]$_.ProcessId}) -join ','
  throw ('FIREFOX_PROFILE_CLOSE_TIMEOUT ids='+$ids)
 }
 [ordered]@{ok=$true;action='close-profile';profile_path=$ProfilePath;closed_count=@($targetPids).Count;remaining_count=0}|ConvertTo-Json -Compress
 exit 0
}
$root=[System.Windows.Automation.AutomationElement]::RootElement
$wc=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Window)
$wins=$root.FindAll([System.Windows.Automation.TreeScope]::Children,$wc)
$fw=@()
foreach($w in $wins){try{if(($targetPids -contains $w.Current.ProcessId) -and (-not $w.Current.IsOffscreen) -and $w.Current.ClassName -eq 'MozillaWindowClass'){$fw+=,$w}}catch{}}
if($fw.Count -lt 1){
 # GPT_WINDOWS_FIREFOX_WINDOW_IDENTITY_TELEMETRY_V1
 $visibleMozilla=@()
 foreach($w in $wins){try{if(-not $w.Current.IsOffscreen -and $w.Current.ClassName -eq 'MozillaWindowClass'){$visibleMozilla+=,([string]$w.Current.ProcessId+'|'+(([string]$w.Current.Name)-replace '[|;]',' '))}}catch{}}
 if($visibleMozilla.Count -gt 8){$visibleMozilla=@($visibleMozilla|Select-Object -First 8)}
 $rootIds=@($profileRoots|ForEach-Object{[string]$_.ProcessId}) -join ','
 $targetIds=@($targetPids|ForEach-Object{[string]$_}) -join ','
 throw ('FIREFOX_WINDOW_MATCH_COUNT_0 profile_roots='+$rootIds+' targets='+$targetIds+' visible_mozilla='+($visibleMozilla -join ';'))
}
$tc=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::TabItem)
if($Action -eq 'resolve-conversation-tab'){
 # GPT_WINDOWS_FIREFOX_MANAGED_CONVERSATION_RESOLVER_V1
 $walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 $matches=@();$restore=@();$scanError=$null;$restoreFailed=$false
 try{
  foreach($candidate in $fw){
   $candidateTabs=$candidate.FindAll([System.Windows.Automation.TreeScope]::Descendants,$tc)
   $canonical=@()
   foreach($tab in $candidateTabs){
    try{
     if($tab.Current.IsOffscreen -or -not $tab.Current.IsEnabled){continue}
     $parent=$walker.GetParent($tab)
     if($null -eq $parent -or $parent.Current.ControlType -ne [System.Windows.Automation.ControlType]::Tab -or $parent.Current.AutomationId -ne 'tabbrowser-tabs'){continue}
     $canonical+=,$tab
    }catch{}
   }
   if($canonical.Count -eq 0){continue}
   $selected=@()
   foreach($tab in $canonical){
    try{$sp=$null;if($tab.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sp) -and $sp.Current.IsSelected){$selected+=,$tab}}catch{}
   }
   if($selected.Count -ne 1){throw ('FIREFOX_CONVERSATION_ORIGINAL_SELECTION_COUNT_'+$selected.Count)}
   $restore+=,[ordered]@{tab=$selected[0]}
   foreach($tab in $canonical){
    $sp=$null
    if(-not $tab.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sp)){throw 'FIREFOX_CONVERSATION_TAB_SELECTION_UNAVAILABLE'}
    $sp.Select();Start-Sleep -Milliseconds 180
    if(-not $sp.Current.IsSelected){throw 'FIREFOX_CONVERSATION_TAB_SELECTION_MISMATCH'}
    $aid=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::AutomationIdProperty,'urlbar-input')
    $bars=$candidate.FindAll([System.Windows.Automation.TreeScope]::Descendants,$aid)
    if($bars.Count -ne 1){throw ('FIREFOX_CONVERSATION_URLBAR_COUNT_'+$bars.Count)}
    $vp=$null
    if(-not $bars[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){throw 'FIREFOX_CONVERSATION_URLBAR_VALUE_UNAVAILABLE'}
    $actual=Normalize-RelayConversationUrl ([string]$vp.Current.Value) $false
    if($null -ne $actual -and $actual -eq $ConversationUrl){
     $matches+=,[ordered]@{firefox_pid=[int]$candidate.Current.ProcessId;tab_name=[string]$tab.Current.Name;conversation_url=$actual}
    }
   }
  }
 }catch{$scanError=$_.Exception.Message}
 finally{
  foreach($item in @($restore)){
   try{
    $rsp=$null
    if(-not $item.tab.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$rsp)){throw 'pattern'}
    $rsp.Select();Start-Sleep -Milliseconds 80
    if(-not $rsp.Current.IsSelected){throw 'readback'}
   }catch{$restoreFailed=$true}
  }
 }
 if($restoreFailed){throw 'FIREFOX_CONVERSATION_ORIGINAL_SELECTION_RESTORE_FAILED'}
 if(-not [string]::IsNullOrWhiteSpace($scanError)){throw $scanError}
 if($matches.Count -ne 1){throw ('FIREFOX_CONVERSATION_MATCH_COUNT_'+$matches.Count)}
 $m=$matches[0]
 [ordered]@{ok=$true;action='resolve-conversation-tab';firefox_pid=[int]$m.firefox_pid;tab_name=[string]$m.tab_name;conversation_url=[string]$m.conversation_url;match_count=1}|ConvertTo-Json -Compress
 exit 0
}
$chatTarget=$null
if($Action -in @('reload-addon','ensure-addon')){
 # GPT_WINDOWS_FIREFOX_DEBUG_WINDOW_SEMANTIC_SELECTION_V1
 $debugHosts=@()
 $debugTarget=$null
 foreach($candidate in $fw){
  $candidateTabs=$candidate.FindAll([System.Windows.Automation.TreeScope]::Descendants,$tc)
  foreach($tab in $candidateTabs){
   try{if(([string]$tab.Current.Name) -match '(?i)Debugging.*Runtime|this-firefox'){$debugHosts+=,$candidate;$debugTarget=$tab;break}}catch{}
  }
 }
 if($debugHosts.Count -ne 1){throw ('FIREFOX_DEBUGGING_WINDOW_COUNT_'+$debugHosts.Count)}
 $firefox=$debugHosts[0]
}elseif($Action -in @('send-chatgpt-prompt','read-chatgpt-text','send-relay-result')){
 # GPT_WINDOWS_FIREFOX_OUT_OF_BAND_PROMPT_V1
 # GPT_WINDOWS_FIREFOX_OUT_OF_BAND_READBACK_V1
 # GPT_WINDOWS_FIREFOX_RELAY_RESULT_EXACT_TARGET_V1
 $chatHosts=@()
 $hostWalker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 foreach($candidate in $fw){
  $candidateTabs=$candidate.FindAll([System.Windows.Automation.TreeScope]::Descendants,$tc)
  foreach($tab in $candidateTabs){
   try{
    $tabName=[string]$tab.Current.Name
    if($Action -eq 'send-relay-result'){
     if($tabName -ne $ExactTabName){continue}
     $parent=$hostWalker.GetParent($tab)
     if($null -eq $parent){continue}
     if($parent.Current.ControlType -ne [System.Windows.Automation.ControlType]::Tab){continue}
     if($parent.Current.AutomationId -ne 'tabbrowser-tabs'){continue}
     $chatHosts+=,$candidate;$chatTarget=$tab;break
    }
    if($tabName -match '(?i)ChatGPT|PC Engineering'){$chatHosts+=,$candidate;$chatTarget=$tab;break}
   }catch{}
  }
 }
 if($chatHosts.Count -ne 1){throw ('FIREFOX_CHATGPT_WINDOW_COUNT_'+$chatHosts.Count)}
 $firefox=$chatHosts[0]
}else{
 if($fw.Count -ne 1){throw ('FIREFOX_WINDOW_MATCH_COUNT_'+$fw.Count)}
 $firefox=$fw[0]
}
$all=$firefox.FindAll([System.Windows.Automation.TreeScope]::Descendants,$tc)
$walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
$tabs=@()
foreach($t in $all){
 try{
  if($t.Current.IsOffscreen -or -not $t.Current.IsEnabled){continue}
  $p=$walker.GetParent($t)
  if($null -eq $p){continue}
  if($p.Current.ControlType -ne [System.Windows.Automation.ControlType]::Tab){continue}
  if($p.Current.AutomationId -ne 'tabbrowser-tabs'){continue}
  $tabs+=,$t
 }catch{}
}
function Select-RelayTab([string]$Exact,[string]$Substring){
 $matches=@()
 foreach($t in $tabs){
  $n=[string]$t.Current.Name
  if(-not [string]::IsNullOrEmpty($Exact)){if($n -eq $Exact){$matches+=,$t}}
  elseif($n.Contains($Substring)){$matches+=,$t}
 }
 if($matches.Count -ne 1){throw ('FIREFOX_TAB_MATCH_COUNT_'+$matches.Count)}
 $target=$matches[0];$sp=$null
 if(-not $target.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sp)){throw 'FIREFOX_TAB_SELECTION_PATTERN_UNAVAILABLE'}
 $sp.Select();Start-Sleep -Milliseconds 180
 if(-not $sp.Current.IsSelected){throw 'FIREFOX_TAB_SELECTION_READBACK_MISMATCH'}
 return $target
}
if($Action -eq 'read-chatgpt-text'){
 if($null -eq $chatTarget){throw 'FIREFOX_CHATGPT_TAB_COUNT_0'}
 $chatSelection=$null
 if(-not $chatTarget.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$chatSelection)){throw 'FIREFOX_CHATGPT_TAB_SELECTION_PATTERN_UNAVAILABLE'}
 $chatSelection.Select();Start-Sleep -Milliseconds 120
 $documentType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Document)
 $documents=$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$documentType)
 $visibleDocuments=@()
 foreach($doc in $documents){try{if($doc.Current.IsEnabled -and -not $doc.Current.IsOffscreen){$visibleDocuments+=,$doc}}catch{}}
 if($visibleDocuments.Count -ne 1){throw ('FIREFOX_CHATGPT_DOCUMENT_COUNT_'+$visibleDocuments.Count)}
 $textPattern=$null
 if(-not $visibleDocuments[0].TryGetCurrentPattern([Windows.Automation.TextPattern]::Pattern,[ref]$textPattern)){throw 'FIREFOX_CHATGPT_DOCUMENT_TEXT_PATTERN_UNAVAILABLE'}
 $body=[string]$textPattern.DocumentRange.GetText(-1)
 if($body.Length -gt 24000){$body=$body.Substring($body.Length-24000)}
 [ordered]@{ok=$true;action='read-chatgpt-text';firefox_pid=[int]$firefox.Current.ProcessId;tab_name=[string]$chatTarget.Current.Name;text=$body;text_chars=$body.Length}|ConvertTo-Json -Compress
 exit 0
}
if($Action -eq 'send-relay-result'){
 # GPT_WINDOWS_FIREFOX_RELAY_RESULT_TRANSACTION_V1
 # Clipboard paste is primary. No ValuePattern text insertion and no Enter fallback.
 $pause=Join-Path $PSScriptRoot '.relay-paused'
 $sendInvoked=$false
 $confirmed=$false
 $state='PRE_SUBMIT_FAILED'
 $errorText=''
 $sendName=''
 $insertionMethod='guarded_clipboard_paste'
 $submissionMethod='semantic_send_button'
 try{
  if(Test-Path -LiteralPath $pause){throw 'RELAY_RESULT_OPERATOR_PAUSED'}
  if($null -eq $chatTarget){throw 'FIREFOX_RELAY_RESULT_TAB_COUNT_0'}
  if(([string]$chatTarget.Current.Name) -ne $ExactTabName){throw 'FIREFOX_RELAY_RESULT_TAB_IDENTITY_MISMATCH'}
  $chatSelection=$null
  if(-not $chatTarget.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$chatSelection)){throw 'FIREFOX_RELAY_RESULT_TAB_SELECTION_PATTERN_UNAVAILABLE'}
  $chatSelection.Select();Start-Sleep -Milliseconds 180
  if(-not $chatSelection.Current.IsSelected){throw 'FIREFOX_RELAY_RESULT_TAB_SELECTION_READBACK_MISMATCH'}

  # GPT_WINDOWS_FIREFOX_RELAY_RESULT_URL_BINDING_V1
  $relayUrlCondition=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::AutomationIdProperty,'urlbar-input')
  $relayUrlBars=$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$relayUrlCondition)
  if($relayUrlBars.Count -ne 1){throw ('FIREFOX_RELAY_RESULT_URLBAR_COUNT_'+$relayUrlBars.Count)}
  $relayUrlPattern=$null
  if(-not $relayUrlBars[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$relayUrlPattern)){throw 'FIREFOX_RELAY_RESULT_URLBAR_VALUE_UNAVAILABLE'}
  $relayActualUrl=Normalize-RelayConversationUrl ([string]$relayUrlPattern.Current.Value) $false
  if($null -eq $relayActualUrl -or $relayActualUrl -ne $ConversationUrl){throw 'FIREFOX_RELAY_RESULT_CONVERSATION_URL_MISMATCH'}

  $editType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Edit)
  $edits=$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$editType)
  $composers=@()
  foreach($e in $edits){
   try{
    if($e.Current.IsEnabled -and -not $e.Current.IsOffscreen -and ([string]$e.Current.Name) -eq 'Ask ChatGPT' -and ([string]$e.Current.ClassName) -eq 'ProseMirror'){$composers+=,$e}
   }catch{}
  }
  if($composers.Count -ne 1){throw ('FIREFOX_RELAY_RESULT_COMPOSER_COUNT_'+$composers.Count)}
  $valuePattern=$null
  if(-not $composers[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$valuePattern)){throw 'FIREFOX_RELAY_RESULT_COMPOSER_VALUE_PATTERN_UNAVAILABLE'}
  if($valuePattern.Current.IsReadOnly){throw 'FIREFOX_RELAY_RESULT_COMPOSER_READ_ONLY'}
  if(-not [string]::IsNullOrWhiteSpace([string]$valuePattern.Current.Value)){throw 'FIREFOX_RELAY_RESULT_COMPOSER_NOT_EMPTY'}

  Add-Type -AssemblyName System.Windows.Forms
  $oldClipboard=$null
  $clipboardCaptured=$false
  try{
   try{$oldClipboard=[System.Windows.Forms.Clipboard]::GetDataObject();$clipboardCaptured=$true}catch{}
   if(Test-Path -LiteralPath $pause){throw 'RELAY_RESULT_OPERATOR_PAUSED_BEFORE_PASTE'}
   $composers[0].SetFocus();Start-Sleep -Milliseconds 80
   [System.Windows.Forms.Clipboard]::SetText($ResultText)
   [System.Windows.Forms.SendKeys]::SendWait('^v')
   Start-Sleep -Milliseconds 300
   if(([string]$valuePattern.Current.Value) -ne $ResultText){throw 'FIREFOX_RELAY_RESULT_CLIPBOARD_PASTE_READBACK_MISMATCH'}

   $buttonType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
   $buttons=$firefox.FindAll([System.Windows.Automation.TreeScope]::Descendants,$buttonType)
   $send=@()
   foreach($b in $buttons){
    try{
     if($b.Current.IsEnabled -and -not $b.Current.IsOffscreen -and ([string]$b.Current.Name) -match '(?i)^Send(?: prompt| message)?$'){$send+=,$b}
    }catch{}
   }
   if($send.Count -ne 1){throw ('FIREFOX_RELAY_RESULT_SEND_BUTTON_COUNT_'+$send.Count)}
   $sendInvoke=$null
   if(-not $send[0].TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$sendInvoke)){throw 'FIREFOX_RELAY_RESULT_SEND_INVOKE_UNAVAILABLE'}

   # Final no-send boundary. Anything after sendInvoked becomes fail-closed/uncertain.
   if(Test-Path -LiteralPath $pause){throw 'RELAY_RESULT_OPERATOR_PAUSED_BEFORE_SEND'}
   if(-not $chatSelection.Current.IsSelected){throw 'FIREFOX_RELAY_RESULT_TAB_LOST_BEFORE_SEND'}
   $relayActualUrlBeforeSend=Normalize-RelayConversationUrl ([string]$relayUrlPattern.Current.Value) $false
   if($null -eq $relayActualUrlBeforeSend -or $relayActualUrlBeforeSend -ne $ConversationUrl){throw 'FIREFOX_RELAY_RESULT_CONVERSATION_URL_CHANGED_BEFORE_SEND'}
   if(([string]$valuePattern.Current.Value) -ne $ResultText){throw 'FIREFOX_RELAY_RESULT_COMPOSER_CHANGED_BEFORE_SEND'}
   $sendName=[string]$send[0].Current.Name
   $sendInvoked=$true
   $state='SUBMIT_UNCERTAIN'
   $sendInvoke.Invoke()

   $deadline=[DateTime]::UtcNow.AddSeconds(10)
   do{
    Start-Sleep -Milliseconds 120
    try{
     if([string]::IsNullOrWhiteSpace([string]$valuePattern.Current.Value)){
      $confirmed=$true
      $state='SUBMITTED'
      break
     }
    }catch{}
   }while([DateTime]::UtcNow -lt $deadline)
  }finally{
   if($clipboardCaptured){
    try{
     if($null -ne $oldClipboard){[System.Windows.Forms.Clipboard]::SetDataObject($oldClipboard,$true)}
     else{[System.Windows.Forms.Clipboard]::Clear()}
    }catch{}
   }
  }
 }catch{
  $errorText=[string]$_.Exception.Message
  if($sendInvoked){$state='SUBMIT_UNCERTAIN'}else{$state='PRE_SUBMIT_FAILED'}
 }

 # Always return the transaction phase. Callers may retry PRE_SUBMIT_FAILED only;
 # SUBMITTED and SUBMIT_UNCERTAIN are terminal for automatic delivery.
 [ordered]@{
  ok=$true
  action='send-relay-result'
  state=$state
  packet_id=$PacketId
  firefox_pid=[int]$firefox.Current.ProcessId
  tab_name=[string]$chatTarget.Current.Name
  composer_name=if($composers.Count -eq 1){[string]$composers[0].Current.Name}else{''}
  result_chars=$ResultText.Length
  insertion=$insertionMethod
  submission=$submissionMethod
  send_button=$sendName
  send_invoked=$sendInvoked
  confirmed=$confirmed
  error=$errorText
 }|ConvertTo-Json -Compress
 exit 0
}
if($Action -eq 'send-chatgpt-prompt'){
 if($null -eq $chatTarget){throw 'FIREFOX_CHATGPT_TAB_COUNT_0'}
 $chatSelection=$null
 if(-not $chatTarget.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$chatSelection)){throw 'FIREFOX_CHATGPT_TAB_SELECTION_PATTERN_UNAVAILABLE'}
 $chatSelection.Select();Start-Sleep -Milliseconds 180
 if(-not $chatSelection.Current.IsSelected){throw 'FIREFOX_CHATGPT_TAB_SELECTION_READBACK_MISMATCH'}
 $editType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Edit)
 $edits=$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$editType);$composers=@()
 foreach($e in $edits){try{if($e.Current.IsEnabled -and -not $e.Current.IsOffscreen -and ([string]$e.Current.Name) -eq 'Ask ChatGPT' -and ([string]$e.Current.ClassName) -eq 'ProseMirror'){$composers+=,$e}}catch{}}
 if($composers.Count -ne 1){throw ('FIREFOX_CHATGPT_COMPOSER_COUNT_'+$composers.Count)}
 $valuePattern=$null
 if(-not $composers[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$valuePattern)){throw 'FIREFOX_CHATGPT_COMPOSER_VALUE_PATTERN_UNAVAILABLE'}
 if($valuePattern.Current.IsReadOnly){throw 'FIREFOX_CHATGPT_COMPOSER_READ_ONLY'}
 $valuePattern.SetValue($PromptText);Start-Sleep -Milliseconds 250
 if(([string]$valuePattern.Current.Value) -ne $PromptText){throw 'FIREFOX_CHATGPT_COMPOSER_READBACK_MISMATCH'}
 $buttonType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
 $buttons=$firefox.FindAll([System.Windows.Automation.TreeScope]::Descendants,$buttonType);$send=@()
 foreach($b in $buttons){try{if($b.Current.IsEnabled -and -not $b.Current.IsOffscreen -and ([string]$b.Current.Name) -match '(?i)^Send(?: prompt| message)?$'){$send+=,$b}}catch{}}
 $submissionMethod='semantic_send_button'
 $insertionMethod='uia_value'
 $sendName=''
 if($send.Count -gt 1){throw ('FIREFOX_CHATGPT_SEND_BUTTON_COUNT_'+$send.Count)}
 if($send.Count -eq 0){
  # GPT_WINDOWS_FIREFOX_COMPOSER_CLIPBOARD_FALLBACK_V1
  # ValuePattern can change accessible text without dispatching ChatGPT's DOM input event.
  # This fallback is allowed only after exact tab/composer identity and exact readback above.
  Add-Type -AssemblyName System.Windows.Forms
  $oldClipboard=$null;$clipboardCaptured=$false
  try{
   try{$oldClipboard=[System.Windows.Forms.Clipboard]::GetDataObject();$clipboardCaptured=$true}catch{}
   $valuePattern.SetValue('');Start-Sleep -Milliseconds 80
   $composers[0].SetFocus();Start-Sleep -Milliseconds 80
   [System.Windows.Forms.Clipboard]::SetText($PromptText)
   [System.Windows.Forms.SendKeys]::SendWait('^v')
   Start-Sleep -Milliseconds 300
   if(([string]$valuePattern.Current.Value) -ne $PromptText){throw 'FIREFOX_CHATGPT_CLIPBOARD_PASTE_READBACK_MISMATCH'}
   $buttons=$firefox.FindAll([System.Windows.Automation.TreeScope]::Descendants,$buttonType);$send=@()
   foreach($b in $buttons){try{if($b.Current.IsEnabled -and -not $b.Current.IsOffscreen -and ([string]$b.Current.Name) -match '(?i)^Send(?: prompt| message)?$'){$send+=,$b}}catch{}}
   if($send.Count -gt 1){throw ('FIREFOX_CHATGPT_SEND_BUTTON_COUNT_'+$send.Count)}
   $insertionMethod='guarded_clipboard_paste'
   if($send.Count -eq 0){
    $composers[0].SetFocus();Start-Sleep -Milliseconds 80
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    $submissionMethod='guarded_focused_enter'
    $sendName='keyboard_enter'
   }
  }finally{
   if($clipboardCaptured){
    try{if($null -ne $oldClipboard){[System.Windows.Forms.Clipboard]::SetDataObject($oldClipboard,$true)}else{[System.Windows.Forms.Clipboard]::Clear()}}catch{}
   }
  }
 }
 if($send.Count -eq 1){
  $sendInvoke=$null
  if(-not $send[0].TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$sendInvoke)){throw 'FIREFOX_CHATGPT_SEND_INVOKE_UNAVAILABLE'}
  $sendName=[string]$send[0].Current.Name
  $sendInvoke.Invoke()
 }
 # GPT_WINDOWS_FIREFOX_PROMPT_SUBMIT_CONFIRMATION_V1
 $submitDeadline=[DateTime]::UtcNow.AddSeconds(10);$submitConfirmed=$false
 do{
  Start-Sleep -Milliseconds 120
  try{if([string]::IsNullOrWhiteSpace([string]$valuePattern.Current.Value)){$submitConfirmed=$true;break}}catch{}
 }while([DateTime]::UtcNow -lt $submitDeadline)
 if(-not $submitConfirmed){throw 'FIREFOX_CHATGPT_SUBMIT_NOT_CONFIRMED'}
 [ordered]@{ok=$true;action='send-chatgpt-prompt';firefox_pid=[int]$firefox.Current.ProcessId;tab_name=[string]$chatTarget.Current.Name;composer_name=[string]$composers[0].Current.Name;prompt_chars=$PromptText.Length;send_button=$sendName;insertion=$insertionMethod;submission=$submissionMethod;confirmed=$true}|ConvertTo-Json -Compress
 exit 0
}
if($Action -eq 'list-tabs'){
 $items=@()
 foreach($t in $tabs){$sel=$false;try{$sp=$t.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern);$sel=$sp.Current.IsSelected}catch{};$items+=,[ordered]@{name=[string]$t.Current.Name;selected=$sel;enabled=[bool]$t.Current.IsEnabled}}
 [ordered]@{ok=$true;action='list-tabs';firefox_pid=[int]$firefox.Current.ProcessId;window_name=[string]$firefox.Current.Name;tab_count=$items.Count;tabs=$items}|ConvertTo-Json -Compress -Depth 5
 exit 0
}
if($Action -eq 'select-tab'){
 $target=Select-RelayTab $TabName $Contains
 [ordered]@{ok=$true;action='select-tab';firefox_pid=[int]$firefox.Current.ProcessId;selected_name=[string]$target.Current.Name;selected=$true}|ConvertTo-Json -Compress
 exit 0
}
if($Action -eq 'refresh-tab'){
 $target=Select-RelayTab $TabName $Contains
 $buttonType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
 $buttons=$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$buttonType)
 $reload=@()
 foreach($b in $buttons){try{if($b.Current.IsEnabled -and $b.Current.AutomationId -eq 'reload-button'){$reload+=,$b}}catch{}}
 if($reload.Count -ne 1){throw ('FIREFOX_CHROME_RELOAD_BUTTON_COUNT_'+$reload.Count)}
 $ip=$null
 if(-not $reload[0].TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$ip)){throw 'FIREFOX_CHROME_RELOAD_INVOKE_UNAVAILABLE'}
 $ip.Invoke()
 [ordered]@{ok=$true;action='refresh-tab';firefox_pid=[int]$firefox.Current.ProcessId;selected_name=[string]$target.Current.Name;reload_button_id=[string]$reload[0].Current.AutomationId;invoked=$true}|ConvertTo-Json -Compress
 exit 0
}
if($null -eq $debugTarget){throw 'FIREFOX_DEBUGGING_TAB_COUNT_0'}
$debug=$debugTarget
$debugSelection=$null
if(-not $debug.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$debugSelection)){throw 'FIREFOX_DEBUGGING_TAB_SELECTION_PATTERN_UNAVAILABLE'}
$debugSelection.Select();Start-Sleep -Milliseconds 180
if(-not $debugSelection.Current.IsSelected){throw 'FIREFOX_DEBUGGING_TAB_SELECTION_READBACK_MISMATCH'}
$listType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::ListItem)
$listItems=$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$listType)
$cards=@()
foreach($item in $listItems){try{if($item.Current.IsEnabled -and ([string]$item.Current.Name).StartsWith($AddonName+' ')){$cards+=,$item}}catch{}}
if($Action -eq 'ensure-addon' -and $cards.Count -eq 0){
 $buttonType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
 $allButtons=$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$buttonType)
 $loadButtons=@()
 foreach($b in $allButtons){try{if($b.Current.IsEnabled -and -not $b.Current.IsOffscreen -and ([string]$b.Current.Name) -like 'Load Temporary Add-on*'){$loadButtons+=,$b}}catch{}}
 if($loadButtons.Count -ne 1){throw ('FIREFOX_LOAD_TEMP_ADDON_BUTTON_COUNT_'+$loadButtons.Count)}
 $loadInvoke=$null
 if(-not $loadButtons[0].TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$loadInvoke)){throw 'FIREFOX_LOAD_TEMP_ADDON_INVOKE_UNAVAILABLE'}
 $loadInvoke.Invoke()
 $dialog=$null;$deadline=[DateTime]::UtcNow.AddSeconds(6)
 do{
  Start-Sleep -Milliseconds 100
  $nowWins=$root.FindAll([System.Windows.Automation.TreeScope]::Children,$wc)
  $dialogs=@()
  foreach($w in $nowWins){try{if($w.Current.ProcessId -eq $firefox.Current.ProcessId -and -not $w.Current.IsOffscreen -and $w.Current.ClassName -eq '#32770'){$dialogs+=,$w}}catch{}}
  if($dialogs.Count -eq 1){$dialog=$dialogs[0]}
 }while($null -eq $dialog -and [DateTime]::UtcNow -lt $deadline)
 if($null -eq $dialog){
  # GPT_WINDOWS_FIREFOX_NESTED_FILE_PICKER_V1
  $nestedWindowType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Window)
  $nestedWindows=$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$nestedWindowType)
  foreach($w in $nestedWindows){
   try{
    if($w.Current.IsEnabled -and $w.Current.ClassName -eq '#32770' -and ([string]$w.Current.Name) -match '(?i)manifest|add-on|file|open'){$dialog=$w;break}
   }catch{}
  }
 }
 if($null -eq $dialog){
  # GPT_WINDOWS_FIREFOX_FILE_DIALOG_TELEMETRY_V1
  $seen=@()
  foreach($w in $nowWins){
   try{
    if($w.Current.IsOffscreen){continue}
    $n=([string]$w.Current.Name)-replace '[|;]',' '
    $cl=([string]$w.Current.ClassName)-replace '[|;]',' '
    if($cl -eq '#32770' -or $n -match '(?i)manifest|add-on|file|open|firefox'){
     $seen+=,([string]$w.Current.ProcessId+'|'+$cl+'|'+$n)
    }
   }catch{}
  }
  if($seen.Count -gt 8){$seen=@($seen|Select-Object -First 8)}
  throw ('FIREFOX_ADDON_FILE_DIALOG_NOT_FOUND candidates='+($seen -join ';'))
 }
 $editType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Edit)
 $edits=$dialog.FindAll([Windows.Automation.TreeScope]::Descendants,$editType)
 $fileEdits=@()
 foreach($e in $edits){try{if($e.Current.IsEnabled -and ($e.Current.AutomationId -eq '1148' -or ([string]$e.Current.Name) -match '(?i)file name')){$fileEdits+=,$e}}catch{}}
 if($fileEdits.Count -eq 0 -and $edits.Count -eq 1){$fileEdits=@($edits[0])}
 if($fileEdits.Count -ne 1){throw ('FIREFOX_ADDON_FILE_NAME_EDIT_COUNT_'+$fileEdits.Count)}
 $vp=$null
 if(-not $fileEdits[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){throw 'FIREFOX_ADDON_FILE_NAME_VALUE_UNAVAILABLE'}
 $vp.SetValue($ManifestPath)
 $dialogButtons=$dialog.FindAll([Windows.Automation.TreeScope]::Descendants,$buttonType)
 $openButtons=@()
 foreach($b in $dialogButtons){try{if($b.Current.IsEnabled -and ($b.Current.AutomationId -eq '1' -or ([string]$b.Current.Name) -match '(?i)^&?Open')){$openButtons+=,$b}}catch{}}
 if($openButtons.Count -ne 1){throw ('FIREFOX_ADDON_FILE_OPEN_BUTTON_COUNT_'+$openButtons.Count)}
 $openInvoke=$null
 if(-not $openButtons[0].TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$openInvoke)){throw 'FIREFOX_ADDON_FILE_OPEN_INVOKE_UNAVAILABLE'}
 $openInvoke.Invoke()
 $cards=@();$deadline=[DateTime]::UtcNow.AddSeconds(6)
 do{
  Start-Sleep -Milliseconds 150
  $listItems=$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$listType)
  $cards=@()
  foreach($item in $listItems){try{if($item.Current.IsEnabled -and ([string]$item.Current.Name).StartsWith($AddonName+' ')){$cards+=,$item}}catch{}}
 }while($cards.Count -eq 0 -and [DateTime]::UtcNow -lt $deadline)
 if($cards.Count -ne 1){throw ('FIREFOX_ADDON_CARD_POSTINSTALL_COUNT_'+$cards.Count)}
 [ordered]@{ok=$true;action='ensure-addon';firefox_pid=[int]$firefox.Current.ProcessId;debug_tab=[string]$debug.Current.Name;addon_name=$AddonName;manifest_path=$ManifestPath;setup_method='temporary_addon_install';invoked=$true}|ConvertTo-Json -Compress
 exit 0
}
if($cards.Count -ne 1){throw ('FIREFOX_ADDON_CARD_COUNT_'+$cards.Count)}
$buttonType=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)
$cardButtons=$cards[0].FindAll([Windows.Automation.TreeScope]::Descendants,$buttonType)
$reload=@()
foreach($b in $cardButtons){try{if($b.Current.IsEnabled -and $b.Current.Name -eq 'Reload'){$reload+=,$b}}catch{}}
if($reload.Count -ne 1){throw ('FIREFOX_ADDON_RELOAD_BUTTON_COUNT_'+$reload.Count)}
$ip=$null
if(-not $reload[0].TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$ip)){throw 'FIREFOX_ADDON_RELOAD_INVOKE_UNAVAILABLE'}
$ip.Invoke()
[ordered]@{ok=$true;action=$Action;firefox_pid=[int]$firefox.Current.ProcessId;debug_tab=[string]$debug.Current.Name;addon_name=$AddonName;setup_method='existing_addon_reload';reload_button_count=1;invoked=$true}|ConvertTo-Json -Compress
