# GPT Windows Relay — native ChatGPT desktop UIA route inspection
# READ ONLY: no clipboard, screenshots, control invocation, process execution or chat content output.
# Launch from CMD using powershell.exe -NoProfile -ExecutionPolicy Bypass -File "...ps1"
# This probe does not start/arm/execute the relay.
[CmdletBinding()]
param([ValidateRange(100,10000)][int]$MaxElements=5000)
$ErrorActionPreference='Stop'
$marker='GPT_RELAY_DESKTOP_UIA_PROBE_20261107'
try {
    Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
    Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop
} catch {
    Write-Output 'RESULT=UIA_NOT_AVAILABLE'
    exit 3
}
Write-Output 'RELAY_DESKTOP_TEXT_ROUTE_PROBE_V1'
Write-Output 'MODE=READ_ONLY_NO_SCREENSHOT_NO_CLIPBOARD_NO_MESSAGE_CONTENT_NO_CONTROL_ACTION'
$root=[System.Windows.Automation.AutomationElement]::RootElement
$top=$root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
$windows=New-Object System.Collections.ArrayList
foreach($element in $top){
    try {
        $pidValue=[int]$element.Current.ProcessId
        if($pidValue -le 0){continue}
        $proc=Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        if($proc -and $proc.ProcessName -ieq 'ChatGPT'){
            [void]$windows.Add($element)
        }
    }catch{continue}
}
Write-Output ('CHATGPT_PROCESS_WINDOWS='+$windows.Count)
if($windows.Count -eq 0){
    Write-Output 'RESULT=CHATGPT_APP_WINDOW_NOT_FOUND'
    exit 2
}
$globalDocuments=0
$globalText=0
$globalNames=0
$globalComposer=0
$globalWritable=0
$globalSend=0
$globalStop=0
$globalErrors=0
$globalTruncated=0
$roleSignals=New-Object 'System.Collections.Generic.HashSet[string]'
$walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
foreach($window in $windows){
    try{
        $nodes=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
    }catch{
        $globalErrors++
        continue
    }
    $count=[Math]::Min([int]$nodes.Count,$MaxElements)
    if($nodes.Count -gt $MaxElements){$globalTruncated++}
    Write-Output ('WINDOW_UIA_ELEMENTS_EXAMINED='+$count)
    for($i=0;$i -lt $count;$i++){
        try{
            $node=$nodes.Item($i)
            $type=[string]$node.Current.ControlType.ProgrammaticName
            $name=[string]$node.Current.Name
            if($type -eq 'ControlType.Document'){$globalDocuments++}
            if($type -eq 'ControlType.Edit'){
                if($name -match '(?i)ask chatgpt|ask anything|message|prompt|chat'){
                    $globalComposer++
                    $vp=$null
                    if($node.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){
                        if(-not $vp.Current.IsReadOnly){$globalWritable++}
                    }
                }
            }
            if($type -eq 'ControlType.Button'){
                if($name -match '(?i)^(send|send message|send prompt|submit)(\b|$)'){$globalSend++}
                if($name -match '(?i)stop generating|stop response'){$globalStop++}
            }
            $matched=$false
            if($name -and $name.IndexOf($marker,[StringComparison]::Ordinal) -ge 0){
                $globalNames++
                $matched=$true
            }
            $tp=$null
            if($node.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$tp)){
                try {
                    $found=$tp.DocumentRange.FindText($marker,$false,$false)
                    if($null -ne $found){
                        $globalText++
                        $matched=$true
                    }
                }catch{$globalErrors++}
            }
            if($matched){
                # Only structural role signals, never the message text/accessible name.
                $parent=$node
                for($depth=0;$depth -lt 7 -and $null -ne $parent;$depth++){
                    try {
                        $id=[string]$parent.Current.AutomationId
                        $class=[string]$parent.Current.ClassName
                        $candidate=($id+' '+$class)
                        if($candidate -match '(?i)(^|[^a-z])assistant([^a-z]|$)'){
                            [void]$roleSignals.Add('ASSISTANT_AUTOMATION_ID_OR_CLASS')
                        }
                        if($candidate -match '(?i)(^|[^a-z])user([^a-z]|$)'){
                            [void]$roleSignals.Add('USER_AUTOMATION_ID_OR_CLASS')
                        }
                        $exact=[string]$parent.Current.Name
                        if($exact -match '^(?i:assistant)( message)?$'){
                            [void]$roleSignals.Add('ASSISTANT_EXACT_ACCESSIBILITY_NAME')
                        }
                        if($exact -match '^(?i:user)( message)?$'){
                            [void]$roleSignals.Add('USER_EXACT_ACCESSIBILITY_NAME')
                        }
                        $parent=$walker.GetParent($parent)
                    }catch{break}
                }
            }
        }catch{$globalErrors++}
    }
}
Write-Output ('UIA_DOCUMENTS='+$globalDocuments)
Write-Output ('PROBE_MARKER_IN_TEXT_PATTERN='+$globalText)
Write-Output ('PROBE_MARKER_IN_ACCESSIBILITY_NAME='+$globalNames)
Write-Output ('COMPOSER_CANDIDATES='+$globalComposer)
Write-Output ('COMPOSER_VALUE_WRITABLE='+$globalWritable)
Write-Output ('SEND_BUTTON_CANDIDATES='+$globalSend)
Write-Output ('STOP_BUTTON_CANDIDATES='+$globalStop)
$signals=if($roleSignals.Count){@($roleSignals | Sort-Object) -join ','}else{'NONE'}
Write-Output ('STRUCTURAL_ROLE_SIGNALS='+$signals)
Write-Output ('UIA_ENUMERATION_ERRORS='+$globalErrors)
Write-Output ('WINDOWS_TRUNCATED_BY_CAP='+$globalTruncated)
Write-Output 'ASSISTANT_MESSAGE_ATTRIBUTION=NOT_YET_PROVEN'
Write-Output 'COMPOSER_WRITE_AND_SEND=NOT_ATTEMPTED'
Write-Output 'RESULT=PROBE_COMPLETE_NO_RELAY_EXECUTION'
