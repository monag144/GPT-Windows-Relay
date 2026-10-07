param(
 [Parameter(Mandatory=$true)][ValidateSet('snapshot','execute')][string]$Action,
 [string]$ActionJsonBase64=''
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class WorkdayMouseV2 {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,uint data,UIntPtr extra);
}
public static class WorkdayWindowV2 {
  public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int maxCount);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr hWnd, System.Text.StringBuilder text, int maxCount);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
'@

function Get-FirefoxDocument {
 $fps=@(Get-Process firefox -ErrorAction SilentlyContinue)
 if($fps.Count -lt 1){throw 'FIREFOX_NOT_RUNNING'}
 $root=[System.Windows.Automation.AutomationElement]::RootElement
 $wins=$root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
 $fw=@()
 foreach($w in $wins){
  try{
   if(($fps.Id -contains $w.Current.ProcessId) -and (-not $w.Current.IsOffscreen) -and $w.Current.ClassName -eq 'MozillaWindowClass'){$fw+=,$w}
  }catch{}
 }
 if($fw.Count -ne 1){throw ('FIREFOX_WINDOW_MATCH_COUNT_'+$fw.Count)}
 $docs=@($fw[0].FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition) | Where-Object {
  try{$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Document -and -not $_.Current.IsOffscreen}catch{$false}
 })
 if($docs.Count -lt 1){throw 'FIREFOX_DOCUMENT_NOT_FOUND'}
 if($docs.Count -gt 1){
  $docs=@($docs | Sort-Object -Descending -Property @{Expression={try{$_.Current.BoundingRectangle.Width*$_.Current.BoundingRectangle.Height}catch{0}}})
 }
 return [ordered]@{window=$fw[0];document=$docs[0]}
}

function Get-TypeName($e){
 try{return [string]$e.Current.ControlType.ProgrammaticName}catch{return ''}
}

function Get-NamedGroupPath($e){
 $walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 $out=@();$cur=$e
 for($i=0;$i -lt 10;$i++){
  $cur=$walker.GetParent($cur)
  if($null -eq $cur){break}
  try{
   if((Get-TypeName $cur) -eq 'ControlType.Group' -and -not [string]::IsNullOrWhiteSpace([string]$cur.Current.Name)){
    $out+=,[string]$cur.Current.Name
   }
  }catch{}
 }
 return @($out)
}

function Get-Snapshot {
 $ctx=Get-FirefoxDocument
 $doc=$ctx.document
 $allowed=@(
  'ControlType.Edit','ControlType.Spinner','ControlType.Button','ControlType.CheckBox',
  'ControlType.RadioButton','ControlType.ComboBox','ControlType.ListItem','ControlType.Group','ControlType.Text'
 )
 $controls=@()
 $all=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
 foreach($e in $all){
  try{
   $type=Get-TypeName $e
   if($allowed -notcontains $type){continue}
   $o=[ordered]@{
    type=$type
    id=[string]$e.Current.AutomationId
    name=[string]$e.Current.Name
    enabled=[bool]$e.Current.IsEnabled
    offscreen=[bool]$e.Current.IsOffscreen
    required=[bool]$e.Current.IsRequiredForForm
   }
   try{
    $help=[string]$e.Current.HelpText
    if(-not [string]::IsNullOrWhiteSpace($help)){$o['help_text']=$help}
   }catch{}
   $r=$e.Current.BoundingRectangle
   if(-not $r.IsEmpty){
    $o['top']=[math]::Round($r.Top,1)
    $o['left']=[math]::Round($r.Left,1)
   }
   $gp=@(Get-NamedGroupPath $e)
   if($gp.Count -gt 0){$o['group_path']=$gp}
   $vp=$null
   if($e.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){$o['value']=[string]$vp.Current.Value}
   $tp=$null
   if($e.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern,[ref]$tp)){$o['toggle']=[string]$tp.Current.ToggleState}
   $sp=$null
   if($e.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sp)){$o['selected']=[bool]$sp.Current.IsSelected}
   $ep=$null
   if($e.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$ep)){$o['expand_collapse']=[string]$ep.Current.ExpandCollapseState}
   $selp=$null
   if($e.TryGetCurrentPattern([System.Windows.Automation.SelectionPattern]::Pattern,[ref]$selp)){
    $names=@()
    foreach($selectedElement in @($selp.GetCurrentSelection())){
     try{if(-not [string]::IsNullOrWhiteSpace([string]$selectedElement.Current.Name)){$names+=,[string]$selectedElement.Current.Name}}catch{}
    }
    if($names.Count -gt 0){$o['selection']=$names}
   }
   $controls+=,$o
  }catch{}
 }
 return [ordered]@{
  provider='workday_uia_v2'
  firefox_pid=[int]$ctx.window.Current.ProcessId
  window_name=[string]$ctx.window.Current.Name
  document_name=[string]$doc.Current.Name
  captured_at=[DateTime]::UtcNow.ToString('o')
  controls=$controls
 }
}

function Find-Control($doc,$target,[string]$forceType=''){
 $all=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
 $matches=@()
 foreach($e in $all){
  try{
   if(-not $e.Current.IsEnabled){continue}
   if($forceType -and (Get-TypeName $e) -ne $forceType){continue}
   if($target.control_type -and (Get-TypeName $e) -ne [string]$target.control_type){continue}
   if($target.automation_id -and $e.Current.AutomationId -ne [string]$target.automation_id){continue}
   if($target.name -and $e.Current.Name -ne [string]$target.name){continue}
   if($target.group_name){
    $gp=@(Get-NamedGroupPath $e)
    if($gp -notcontains [string]$target.group_name){continue}
   }
   $matches+=,$e
  }catch{}
 }
 if($matches.Count -ne 1){throw ('CONTROL_MATCH_COUNT_'+$matches.Count)}
 return $matches[0]
}

function Scroll-Control($e){
 try{
  $sp=$null
  if($e.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$sp)){$sp.ScrollIntoView();Start-Sleep -Milliseconds 100}
 }catch{}
}

function Click-Control($e){
 Scroll-Control $e
 $r=$e.Current.BoundingRectangle
 if($r.IsEmpty -or $r.Width -le 1 -or $r.Height -le 1){throw 'CONTROL_HAS_NO_CLICK_RECT'}
 $x=[int]($r.Left+($r.Width/2));$y=[int]($r.Top+($r.Height/2))
 [WorkdayMouseV2]::SetCursorPos($x,$y)|Out-Null
 Start-Sleep -Milliseconds 80
 [WorkdayMouseV2]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 [WorkdayMouseV2]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
 return [ordered]@{x=$x;y=$y}
}

function Get-SelectedPills($doc){
 $items=@()
 $all=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
 foreach($e in $all){
  try{
   if((Get-TypeName $e) -eq 'ControlType.ListItem' -and $e.Current.Name -like '*, press delete to clear value.'){$items+=,$e}
  }catch{}
 }
 return $items
}

function Get-FileUploadDialog {
 $firefoxIds=@(Get-Process firefox -ErrorAction SilentlyContinue | ForEach-Object {[uint32]$_.Id})
 $found=New-Object System.Collections.ArrayList
 $callback=[WorkdayWindowV2+EnumWindowsProc]{
  param([IntPtr]$hWnd,[IntPtr]$lParam)
  try{
   if(-not [WorkdayWindowV2]::IsWindowVisible($hWnd)){return $true}
   [uint32]$pid=0
   [WorkdayWindowV2]::GetWindowThreadProcessId($hWnd,[ref]$pid)|Out-Null
   if($firefoxIds -notcontains $pid){return $true}
   $titleBuilder=New-Object Text.StringBuilder 512
   $classBuilder=New-Object Text.StringBuilder 256
   [WorkdayWindowV2]::GetWindowText($hWnd,$titleBuilder,$titleBuilder.Capacity)|Out-Null
   [WorkdayWindowV2]::GetClassName($hWnd,$classBuilder,$classBuilder.Capacity)|Out-Null
   $title=$titleBuilder.ToString();$class=$classBuilder.ToString()
   if($title -eq 'File Upload' -and $class -eq '#32770'){
    [void]$found.Add([pscustomobject]@{hwnd=$hWnd;pid=$pid;title=$title;class=$class})
   }
  }catch{}
  return $true
 }
 [WorkdayWindowV2]::EnumWindows($callback,[IntPtr]::Zero)|Out-Null
 if($found.Count -eq 1){return $found[0]}
 if($found.Count -gt 1){throw ('FILE_UPLOAD_DIALOG_MATCH_COUNT_'+$found.Count)}
 return $null
}

function Test-DocumentName([string]$name){
 $ctx=Get-FirefoxDocument
 $all=$ctx.document.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
 foreach($e in $all){try{if([string]$e.Current.Name -eq $name){return $true}}catch{}}
 return $false
}

function Test-OptionListAncestor($e){
 $walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 $cur=$e
 for($i=0;$i -lt 12;$i++){
  $cur=$walker.GetParent($cur)
  if($null -eq $cur){break}
  try{
   $type=Get-TypeName $cur
   $name=[string]$cur.Current.Name
   if($type -eq 'ControlType.List' -and ($name -eq 'Options Expanded' -or $name -like '*Options*')){return $true}
  }catch{}
 }
 return $false
}

function Get-ControlSemanticSelection($e){
 $out=[ordered]@{value='';selection=@()}
 try{
  $vp=$null
  if($e.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){$out.value=[string]$vp.Current.Value}
 }catch{}
 try{
  $sp=$null
  if($e.TryGetCurrentPattern([System.Windows.Automation.SelectionPattern]::Pattern,[ref]$sp)){
   $names=@()
   foreach($item in @($sp.GetCurrentSelection())){
    try{if(-not [string]::IsNullOrWhiteSpace([string]$item.Current.Name)){$names+=,[string]$item.Current.Name}}catch{}
   }
   $out.selection=@($names)
  }
 }catch{}
 return $out
}

function Find-AncestorGroup($e,[string]$name){
 $walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 $cur=$e
 for($i=0;$i -lt 10;$i++){
  $cur=$walker.GetParent($cur)
  if($null -eq $cur){break}
  try{
   if((Get-TypeName $cur) -eq 'ControlType.Group' -and $cur.Current.Name -eq $name){return $cur}
  }catch{}
 }
 return $null
}

function Execute-Intent($intent){
 $ctx=Get-FirefoxDocument;$doc=$ctx.document
 $op=[string]$intent.op
 $target=$intent.target
 if($null -eq $target){$target=[pscustomobject]@{}}
 if($op -eq 'set_text'){
  $c=Find-Control $doc $target
  Scroll-Control $c
  $vp=$null
  if(-not $c.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){throw 'VALUE_PATTERN_UNAVAILABLE'}
  if($vp.Current.IsReadOnly){throw 'FIELD_IS_READ_ONLY'}
  $value=[string]$intent.value
  $vp.SetValue($value);Start-Sleep -Milliseconds 250
  $ctx2=Get-FirefoxDocument;$c2=Find-Control $ctx2.document $target
  $vp2=$null
  if(-not $c2.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$vp2)){throw 'VALUE_PATTERN_UNAVAILABLE_AFTER_SET'}
  if([string]$vp2.Current.Value -ne $value){throw 'FIELD_READBACK_MISMATCH'}
  return [ordered]@{ok=$true;op=$op;value=$value}
 }
 if($op -eq 'set_toggle'){
  $c=Find-Control $doc $target 'ControlType.CheckBox'
  Scroll-Control $c
  $tp=$null
  if(-not $c.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern,[ref]$tp)){throw 'TOGGLE_PATTERN_UNAVAILABLE'}
  $want=if([bool]$intent.checked){[System.Windows.Automation.ToggleState]::On}else{[System.Windows.Automation.ToggleState]::Off}
  for($i=0;$i -lt 3 -and $tp.Current.ToggleState -ne $want;$i++){$tp.Toggle();Start-Sleep -Milliseconds 150}
  $ctx2=Get-FirefoxDocument;$c2=Find-Control $ctx2.document $target 'ControlType.CheckBox'
  $tp2=$null
  if(-not $c2.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern,[ref]$tp2)){throw 'TOGGLE_PATTERN_UNAVAILABLE_AFTER_SET'}
  if($tp2.Current.ToggleState -ne $want){throw 'TOGGLE_READBACK_MISMATCH'}
  return [ordered]@{ok=$true;op=$op;toggle=[string]$tp2.Current.ToggleState}
 }
 if($op -eq 'inspect_options'){
  $c=Find-Control $doc $target
  Scroll-Control $c
  $before=Get-ControlSemanticSelection $c
  $ep=$null;$startedCollapsed=$false;$openedByFallback=$false
  if($c.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$ep)){
   $expandState=$ep.Current.ExpandCollapseState
   if($expandState -eq [System.Windows.Automation.ExpandCollapseState]::Collapsed){
    $startedCollapsed=$true
    $ep.Expand();Start-Sleep -Milliseconds 350
   } elseif($expandState -ne [System.Windows.Automation.ExpandCollapseState]::Expanded -and $expandState -ne [System.Windows.Automation.ExpandCollapseState]::PartiallyExpanded){
    $openedByFallback=$true
    Click-Control $c|Out-Null;Start-Sleep -Milliseconds 350
   }
  } else {
   $openedByFallback=$true
   Click-Control $c|Out-Null;Start-Sleep -Milliseconds 350
  }

  $ctxOpen=Get-FirefoxDocument
  $all=$ctxOpen.document.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  $names=New-Object System.Collections.Generic.List[string]
  foreach($e in $all){
   try{
    if($e.Current.IsOffscreen){continue}
    $type=Get-TypeName $e
    if($type -notin @('ControlType.ListItem','ControlType.RadioButton','ControlType.MenuItem')){continue}
    if(-not (Test-OptionListAncestor $e)){continue}
    $name=[string]$e.Current.Name
    if([string]::IsNullOrWhiteSpace($name)){continue}
    if($name.EndsWith(' not checked')){$name=$name.Substring(0,$name.Length-12)}
    if(-not [string]::IsNullOrWhiteSpace($name) -and -not $names.Contains($name)){$names.Add($name)}
   }catch{}
  }

  $ctxClose=Get-FirefoxDocument
  $cClose=Find-Control $ctxClose.document $target
  if($startedCollapsed){
   $epClose=$null
   if($cClose.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$epClose)){
    if($epClose.Current.ExpandCollapseState -eq [System.Windows.Automation.ExpandCollapseState]::Expanded -or $epClose.Current.ExpandCollapseState -eq [System.Windows.Automation.ExpandCollapseState]::PartiallyExpanded){
     $epClose.Collapse();Start-Sleep -Milliseconds 250
    }
   } else {
    [System.Windows.Forms.SendKeys]::SendWait('{ESC}');Start-Sleep -Milliseconds 200
   }
  } elseif($openedByFallback) {
   [System.Windows.Forms.SendKeys]::SendWait('{ESC}');Start-Sleep -Milliseconds 150
  }

  $ctx2=Get-FirefoxDocument;$c2=Find-Control $ctx2.document $target
  $after=Get-ControlSemanticSelection $c2
  $beforeSel=@($before.selection) -join [char]31
  $afterSel=@($after.selection) -join [char]31
  if([string]$before.value -ne [string]$after.value -or $beforeSel -ne $afterSel){throw 'OPTION_PROBE_CHANGED_SELECTION'}
  if($names.Count -lt 1){throw 'OPTION_PROBE_FOUND_NO_OPTIONS'}
  return [ordered]@{ok=$true;op=$op;options=@($names);value=[string]$after.value;selection=@($after.selection);selection_unchanged=$true}
 }
 if($op -eq 'select_option'){
  $optionName=[string]$intent.value
  if([string]::IsNullOrWhiteSpace($optionName)){throw 'OPTION_VALUE_REQUIRED'}
  $c=Find-Control $doc $target
  Scroll-Control $c
  $ep=$null
  if($c.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$ep)){
   $state=$ep.Current.ExpandCollapseState
   if($state -eq [System.Windows.Automation.ExpandCollapseState]::Collapsed){
    $ep.Expand();Start-Sleep -Milliseconds 350
   } elseif($state -ne [System.Windows.Automation.ExpandCollapseState]::Expanded -and $state -ne [System.Windows.Automation.ExpandCollapseState]::PartiallyExpanded){
    Click-Control $c|Out-Null;Start-Sleep -Milliseconds 350
   }
  } else {
   $ip=$null
   if($c.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$ip)){$ip.Invoke()}
   else{Click-Control $c|Out-Null}
   Start-Sleep -Milliseconds 350
  }
  $ctxOpen=Get-FirefoxDocument
  $all=$ctxOpen.document.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  $matches=@()
  foreach($e in $all){
   try{
    if($e.Current.IsOffscreen){continue}
    $type=Get-TypeName $e
    if($type -notin @('ControlType.ListItem','ControlType.RadioButton','ControlType.MenuItem','ControlType.Text')){continue}
    $name=[string]$e.Current.Name
    if($name -eq $optionName -or $name -eq ($optionName+' not checked')){$matches+=,$e}
   }catch{}
  }
  if($matches.Count -lt 1){throw ('OPTION_EXACT_MATCH_COUNT_'+$matches.Count)}
  # Prefer actionable semantic wrappers over Text descendants.
  $candidate=@($matches | Where-Object {(Get-TypeName $_) -ne 'ControlType.Text'}) | Select-Object -First 1
  if($null -eq $candidate){$candidate=$matches[0]}
  Scroll-Control $candidate
  $selected=$false
  $sip=$null
  if($candidate.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sip)){
   try{$sip.Select();$selected=$true}catch{}
  }
  if(-not $selected){
   $iip=$null
   if($candidate.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$iip)){$iip.Invoke()}
   else{Click-Control $candidate|Out-Null}
  }
  Start-Sleep -Milliseconds 350
  $ctx2=Get-FirefoxDocument;$c2=Find-Control $ctx2.document $target
  $verified=$false
  $vp2=$null
  if($c2.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$vp2)){
   if([string]$vp2.Current.Value -eq $optionName){$verified=$true}
  }
  if(-not $verified){
   $sel2=$null
   if($c2.TryGetCurrentPattern([System.Windows.Automation.SelectionPattern]::Pattern,[ref]$sel2)){
    foreach($selectedElement in @($sel2.GetCurrentSelection())){
     try{if([string]$selectedElement.Current.Name -eq $optionName){$verified=$true;break}}catch{}
    }
   }
  }
  if(-not $verified){throw 'OPTION_SELECTION_NOT_VERIFIED'}
  return [ordered]@{ok=$true;op=$op;option=$optionName;selected=$true}
 }
 if($op -eq 'select_choice'){
  $groupName=[string]$target.group_name
  $optionName=[string]$target.name
  if([string]::IsNullOrWhiteSpace($groupName) -or [string]::IsNullOrWhiteSpace($optionName)){throw 'CHOICE_TARGET_INCOMPLETE'}
  $all=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  $matches=@()
  foreach($e in $all){
   try{
    if((Get-TypeName $e) -ne 'ControlType.RadioButton' -or -not $e.Current.IsEnabled -or $e.Current.Name -ne $optionName){continue}
    $gp=@(Get-NamedGroupPath $e)
    if($gp -contains $groupName){$matches+=,$e}
   }catch{}
  }
  if($matches.Count -ne 1){throw ('CHOICE_MATCH_COUNT_'+$matches.Count)}
  $c=$matches[0];Scroll-Control $c
  $sp=$null
  if($c.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sp)){$sp.Select()}
  else{
   $ip=$null
   if($c.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$ip)){$ip.Invoke()}
   else{Click-Control $c|Out-Null}
  }
  Start-Sleep -Milliseconds 300
  $ctx2=Get-FirefoxDocument;$all2=$ctx2.document.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  $verified=$false
  foreach($e in $all2){
   try{
    if((Get-TypeName $e) -ne 'ControlType.RadioButton' -or $e.Current.Name -ne $optionName){continue}
    $gp=@(Get-NamedGroupPath $e);if($gp -notcontains $groupName){continue}
    $sp2=$null;if($e.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sp2) -and $sp2.Current.IsSelected){$verified=$true;break}
   }catch{}
  }
  if(-not $verified){throw 'CHOICE_SELECTION_NOT_VERIFIED'}
  return [ordered]@{ok=$true;op=$op;group_name=$groupName;option=$optionName;selected=$true}
 }
 if($op -eq 'upload_file'){
  $filePath=[string]$intent.path
  $expected=[string]$intent.expected_filename
  $successText=[string]$intent.success_text
  if([string]::IsNullOrWhiteSpace($filePath) -or -not (Test-Path -LiteralPath $filePath -PathType Leaf)){throw 'UPLOAD_FILE_NOT_FOUND'}
  if([string]::IsNullOrWhiteSpace($expected)){throw 'UPLOAD_EXPECTED_FILENAME_REQUIRED'}
  if([IO.Path]::GetFileName($filePath) -ne $expected){throw 'UPLOAD_FILENAME_MISMATCH'}
  if([string]::IsNullOrWhiteSpace($successText)){$successText='Successfully Uploaded!'}
  if((Test-DocumentName $expected) -and (Test-DocumentName $successText)){
   return [ordered]@{ok=$true;op=$op;already_uploaded=$true;expected_filename=$expected}
  }
  $c=Find-Control $doc $target
  Scroll-Control $c
  $ip=$null
  if($c.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$ip)){$ip.Invoke()}
  else{Click-Control $c|Out-Null}
  $dialog=$null
  for($i=0;$i -lt 20 -and $null -eq $dialog;$i++){Start-Sleep -Milliseconds 250;$dialog=Get-FileUploadDialog}
  if($null -eq $dialog){throw 'FILE_UPLOAD_DIALOG_NOT_FOUND'}
  [WorkdayWindowV2]::SetForegroundWindow([IntPtr]$dialog.hwnd)|Out-Null
  Start-Sleep -Milliseconds 250
  $hadClipboard=[System.Windows.Forms.Clipboard]::ContainsText()
  $oldClipboard=if($hadClipboard){[System.Windows.Forms.Clipboard]::GetText()}else{$null}
  try{
   [System.Windows.Forms.SendKeys]::SendWait('%n')
   Start-Sleep -Milliseconds 100
   [System.Windows.Forms.Clipboard]::SetText($filePath)
   [System.Windows.Forms.SendKeys]::SendWait('^v')
   Start-Sleep -Milliseconds 100
   [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  }finally{
   Start-Sleep -Milliseconds 100
   if($hadClipboard){[System.Windows.Forms.Clipboard]::SetText($oldClipboard)}else{[System.Windows.Forms.Clipboard]::Clear()}
  }
  $verified=$false
  for($i=0;$i -lt 30;$i++){
   Start-Sleep -Milliseconds 350
   if((Test-DocumentName $expected) -and (Test-DocumentName $successText)){$verified=$true;break}
  }
  if(-not $verified){throw 'UPLOAD_VERIFICATION_FAILED'}
  return [ordered]@{ok=$true;op=$op;expected_filename=$expected;success_text=$successText;uploaded=$true}
 }
 if($op -eq 'invoke'){
  $c=Find-Control $doc $target
  Scroll-Control $c
  $ip=$null
  if($c.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$ip)){$ip.Invoke()}
  else{$c.SetFocus();[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')}
  return [ordered]@{ok=$true;op=$op;invoked=$true}
 }
 if($op -eq 'select_hierarchy'){
  $path=@($intent.path)
  if($path.Count -lt 1){throw 'HIERARCHY_PATH_EMPTY'}
  $field=Find-Control $doc $target 'ControlType.Edit'
  $terminal=[string]$path[$path.Count-1]
  $already=@(Get-SelectedPills $doc | Where-Object {$_.Current.Name -eq ($terminal+', press delete to clear value.')})
  if($already.Count -eq 1){return [ordered]@{ok=$true;op=$op;already_selected=$true;terminal=$terminal}}
  $group=$null
  if($target.name){$group=Find-AncestorGroup $field ([string]$target.name)}
  if($null -ne $group){
   $inside=$group.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
   foreach($e in $inside){
    try{
     if((Get-TypeName $e) -eq 'ControlType.ListItem' -and $e.Current.Name -like '*, press delete to clear value.'){
      $e.SetFocus();[System.Windows.Forms.SendKeys]::SendWait('{DELETE}');Start-Sleep -Milliseconds 350
     }
    }catch{}
   }
  }
  $ctx=Get-FirefoxDocument;$field=Find-Control $ctx.document $target 'ControlType.Edit'
  $field.SetFocus();[System.Windows.Forms.SendKeys]::SendWait('^a');[System.Windows.Forms.SendKeys]::SendWait('{BACKSPACE}');Start-Sleep -Milliseconds 150
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}');Start-Sleep -Milliseconds 650
  for($i=0;$i -lt $path.Count;$i++){
   $segment=[string]$path[$i]
   $ctx=Get-FirefoxDocument
   $all=$ctx.document.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
   $matches=@()
   foreach($e in $all){
    try{
     if(-not $e.Current.IsOffscreen -and (Get-TypeName $e) -eq 'ControlType.ListItem' -and $e.Current.Name -eq ($segment+' not checked')){$matches+=,$e}
    }catch{}
   }
   if($matches.Count -ne 1){throw ('HIERARCHY_OPTION_MATCH_COUNT_'+$segment+'_'+$matches.Count)}
   $click=Click-Control $matches[0]
   Start-Sleep -Milliseconds 700
  }
  $ctx=Get-FirefoxDocument
  $final=@(Get-SelectedPills $ctx.document | Where-Object {$_.Current.Name -eq ($terminal+', press delete to clear value.')})
  if($final.Count -ne 1){throw 'HIERARCHY_TERMINAL_PILL_NOT_VERIFIED'}
  return [ordered]@{ok=$true;op=$op;terminal=$terminal;selected=$true}
 }
 throw ('UNSUPPORTED_INTENT_'+$op)
}

if($Action -eq 'snapshot'){
 (Get-Snapshot)|ConvertTo-Json -Compress -Depth 8
 exit 0
}
if([string]::IsNullOrEmpty($ActionJsonBase64)){throw 'ACTION_JSON_REQUIRED'}
$json=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($ActionJsonBase64))
$intent=$json|ConvertFrom-Json
(Execute-Intent $intent)|ConvertTo-Json -Compress -Depth 8
