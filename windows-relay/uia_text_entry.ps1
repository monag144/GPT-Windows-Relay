param(
 [Parameter(Mandatory=$true)][string]$WindowTitle,
 [Parameter(Mandatory=$true)][string]$TextBase64,
 [string]$FieldName='',
 [string]$AutomationId='',
 [int]$ProcessId=0
)
$ErrorActionPreference='Stop'
if([string]::IsNullOrEmpty($FieldName) -and [string]::IsNullOrEmpty($AutomationId)){throw 'FIELD_SELECTOR_REQUIRED'}
$text=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($TextBase64))
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
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
$fields=@()
foreach($e in $desc){
 try{
  if($e.Current.ControlType -ne [System.Windows.Automation.ControlType]::Edit -or $e.Current.IsOffscreen -or -not $e.Current.IsEnabled){continue}
  if(-not [string]::IsNullOrEmpty($FieldName) -and $e.Current.Name -ne $FieldName){continue}
  if(-not [string]::IsNullOrEmpty($AutomationId) -and $e.Current.AutomationId -ne $AutomationId){continue}
  $fields+=,$e
 }catch{}
}
if($fields.Count -ne 1){throw ('FIELD_MATCH_COUNT_'+$fields.Count)}
$field=$fields[0]
$pattern=$null
if(-not $field.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)){throw 'VALUE_PATTERN_UNAVAILABLE'}
if($pattern.Current.IsReadOnly){throw 'FIELD_IS_READ_ONLY'}
$pattern.SetValue($text)
$readback=$pattern.Current.Value
if($readback -ne $text){throw 'FIELD_READBACK_MISMATCH'}
[ordered]@{ok=$true;window_title=$WindowTitle;process_id=$field.Current.ProcessId;field_name=$field.Current.Name;automation_id=$field.Current.AutomationId;chars=$text.Length;readback_match=$true}|ConvertTo-Json -Compress
