param(
 [Parameter(Mandatory=$true)][ValidateSet('list-tabs','select-tab','reload-addon','refresh-tab','ensure-addon','close-profile','send-chatgpt-prompt','read-chatgpt-text')][string]$Action,
 [string]$TabName='',
 [string]$Contains='',
 [string]$AddonName='',
 [string]$ManifestPath='',
 [int]$FirefoxPid=0,
 [string]$ProfilePath='',
 [string]$PromptText=''
)
$ErrorActionPreference='Stop'
if($Action -in @('select-tab','refresh-tab')){
 if(([string]::IsNullOrEmpty($TabName) -and [string]::IsNullOrEmpty($Contains)) -or (-not [string]::IsNullOrEmpty($TabName) -and -not [string]::IsNullOrEmpty($Contains))){throw 'TAB_SELECTOR_REQUIRED_EXACTLY_ONE'}
}
if($Action -in @('reload-addon','ensure-addon') -and [string]::IsNullOrWhiteSpace($AddonName)){throw 'ADDON_NAME_REQUIRED'}
if($Action -eq 'close-profile' -and [string]::IsNullOrWhiteSpace($ProfilePath)){throw 'PROFILE_PATH_REQUIRED'}
if($Action -eq 'send-chatgpt-prompt' -and [string]::IsNullOrWhiteSpace($PromptText)){throw 'PROMPT_TEXT_REQUIRED'}
if($PromptText.Length -gt 12000){throw 'PROMPT_TEXT_TOO_LONG'}
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
}elseif($Action -in @('send-chatgpt-prompt','read-chatgpt-text')){
 # GPT_WINDOWS_FIREFOX_OUT_OF_BAND_PROMPT_V1
 # GPT_WINDOWS_FIREFOX_OUT_OF_BAND_READBACK_V1
 $chatHosts=@()
 foreach($candidate in $fw){
  $candidateTabs=$candidate.FindAll([System.Windows.Automation.TreeScope]::Descendants,$tc)
  foreach($tab in $candidateTabs){
   try{if(([string]$tab.Current.Name) -match '(?i)ChatGPT|PC Engineering'){$chatHosts+=,$candidate;$chatTarget=$tab;break}}catch{}
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
