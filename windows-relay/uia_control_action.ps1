param(
 [Parameter(Mandatory=$true)][string]$WindowTitle,
 [Parameter(Mandatory=$true)][ValidateSet('inspect','invoke','select','set-toggle')][string]$Action,
 [string]$ControlType='',
 [string]$ControlName='',
 [string]$AutomationId='',
 [int]$ProcessId=0,
 [ValidateSet('','on','off')][string]$DesiredState='',
 [int]$MaxResults=50
)
$ErrorActionPreference='Stop'
if($MaxResults -lt 1 -or $MaxResults -gt 200){throw 'MAX_RESULTS_OUT_OF_RANGE'}
if($Action -ne 'inspect' -and [string]::IsNullOrEmpty($ControlType)){throw 'CONTROL_TYPE_REQUIRED'}
if($Action -ne 'inspect' -and [string]::IsNullOrEmpty($ControlName) -and [string]::IsNullOrEmpty($AutomationId)){throw 'CONTROL_SELECTOR_REQUIRED'}
if($Action -eq 'set-toggle' -and [string]::IsNullOrEmpty($DesiredState)){throw 'DESIRED_STATE_REQUIRED'}
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
function Resolve-ControlType([string]$name){
 if([string]::IsNullOrEmpty($name)){return $null}
 switch($name){
  'Button'{return [System.Windows.Automation.ControlType]::Button}
  'CheckBox'{return [System.Windows.Automation.ControlType]::CheckBox}
  'RadioButton'{return [System.Windows.Automation.ControlType]::RadioButton}
  'ComboBox'{return [System.Windows.Automation.ControlType]::ComboBox}
  'ListItem'{return [System.Windows.Automation.ControlType]::ListItem}
  'TabItem'{return [System.Windows.Automation.ControlType]::TabItem}
  'MenuItem'{return [System.Windows.Automation.ControlType]::MenuItem}
  'Hyperlink'{return [System.Windows.Automation.ControlType]::Hyperlink}
  'TreeItem'{return [System.Windows.Automation.ControlType]::TreeItem}
  default{throw 'UNSUPPORTED_CONTROL_TYPE'}
 }
}
$wantType=Resolve-ControlType $ControlType
$root=[System.Windows.Automation.AutomationElement]::RootElement
$allWindows=$root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
$wins=@()
foreach($e in $allWindows){
 try{
  if($e.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window){continue}
  if($e.Current.Name -ne $WindowTitle -or $e.Current.IsOffscreen){continue}
  if($ProcessId -gt 0 -and $e.Current.ProcessId -ne $ProcessId){continue}
  $wins+=,$e
 }catch{}
}
if($wins.Count -ne 1){throw ('WINDOW_MATCH_COUNT_'+$wins.Count)}
$window=$wins[0]
$desc=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$matches=@()
foreach($e in $desc){
 try{
  if($e.Current.IsOffscreen){continue}
  if($null -ne $wantType -and $e.Current.ControlType -ne $wantType){continue}
  if(-not [string]::IsNullOrEmpty($ControlName) -and $e.Current.Name -ne $ControlName){continue}
  if(-not [string]::IsNullOrEmpty($AutomationId) -and $e.Current.AutomationId -ne $AutomationId){continue}
  if($Action -ne 'inspect' -and -not $e.Current.IsEnabled){continue}
  $matches+=,$e
 }catch{}
}
if($Action -eq 'inspect'){
 $items=@();$take=[Math]::Min($matches.Count,$MaxResults)
 for($i=0;$i -lt $take;$i++){
  $e=$matches[$i]
  # GPT_WINDOWS_UIA_INSPECT_VALUE_READBACK_V1
  $vp=$null;$value=$null
  try{if($e.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){$value=[string]$vp.Current.Value}}catch{}
  $items+=,[ordered]@{name=[string]$e.Current.Name;automation_id=[string]$e.Current.AutomationId;control_type=[string]$e.Current.ControlType.ProgrammaticName;process_id=[int]$e.Current.ProcessId;enabled=[bool]$e.Current.IsEnabled;offscreen=[bool]$e.Current.IsOffscreen;value=$value}
 }
 [ordered]@{ok=$true;action='inspect';window_title=$WindowTitle;match_count=$matches.Count;truncated=($matches.Count -gt $take);matches=$items}|ConvertTo-Json -Compress -Depth 5
 exit 0
}
if($matches.Count -ne 1){throw ('CONTROL_MATCH_COUNT_'+$matches.Count)}
$control=$matches[0]
$result=[ordered]@{ok=$true;action=$Action;window_title=$WindowTitle;process_id=[int]$control.Current.ProcessId;control_name=[string]$control.Current.Name;automation_id=[string]$control.Current.AutomationId;control_type=[string]$control.Current.ControlType.ProgrammaticName}
if($Action -eq 'invoke'){
 $p=$null
 if(-not $control.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$p)){throw 'INVOKE_PATTERN_UNAVAILABLE'}
 $p.Invoke();$result['invoked']=$true
}elseif($Action -eq 'select'){
 $p=$null
 if(-not $control.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$p)){throw 'SELECTION_ITEM_PATTERN_UNAVAILABLE'}
 $p.Select();Start-Sleep -Milliseconds 100
 if(-not $p.Current.IsSelected){throw 'SELECTION_READBACK_MISMATCH'}
 $result['selected']=$true
}elseif($Action -eq 'set-toggle'){
 $p=$null
 if(-not $control.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern,[ref]$p)){throw 'TOGGLE_PATTERN_UNAVAILABLE'}
 $target=if($DesiredState -eq 'on'){[System.Windows.Automation.ToggleState]::On}else{[System.Windows.Automation.ToggleState]::Off}
 for($i=0;$i -lt 3 -and $p.Current.ToggleState -ne $target;$i++){$p.Toggle();Start-Sleep -Milliseconds 75}
 if($p.Current.ToggleState -ne $target){throw 'TOGGLE_READBACK_MISMATCH'}
 $result['toggle_state']=[string]$p.Current.ToggleState
}
$result|ConvertTo-Json -Compress
