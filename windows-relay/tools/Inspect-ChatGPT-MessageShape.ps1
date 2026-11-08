# ChatGPT desktop UI Automation: read-only message shape probe.
# Does not print message text, alter controls, use clipboard, or execute commands.
[CmdletBinding()]
param(
    [ValidateLength(8,128)][string]$Marker = 'GPT_RELAY_DESKTOP_UIA_PROBE_20261107',
    [ValidateRange(100,10000)][int]$MaxElements = 5000
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root = [System.Windows.Automation.AutomationElement]::RootElement
$top = $root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$matches = 0
$seen = 0
$errors = 0
Write-Output 'DESKTOP_UIA_MESSAGE_SHAPE_V1'
Write-Output 'MODE=READ_ONLY_NO_TEXT_DUMP_NO_CONTROL_ACTION'
foreach ($window in $top) {
    try {
        $pidValue=[int]$window.Current.ProcessId
        if ($pidValue -le 0) { continue }
        $proc=Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        if (-not $proc -or $proc.ProcessName -ine 'ChatGPT') { continue }
        $bounds=$window.Current.BoundingRectangle
        $nodes=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
        $limit=[Math]::Min([int]$nodes.Count,$MaxElements)
        Write-Output ('CHATGPT_WINDOW_ELEMENTS='+$limit)
        for ($i=0;$i -lt $limit;$i++) {
            try {
                $node=$nodes.Item($i)
                $name=[string]$node.Current.Name
                $source=''
                if ($name.IndexOf($Marker,[StringComparison]::Ordinal) -ge 0) { $source='ACCESSIBLE_NAME' }
                $tp=$null
                if ($node.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$tp)) {
                    try {
                        $found=$tp.DocumentRange.FindText($Marker,$false,$false)
                        if ($null -ne $found) {
                            $source=if ($source) {'BOTH'} else {'TEXT_PATTERN'}
                        }
                    }catch { $errors++ }
                }
                if (-not $source) { continue }
                $seen++
                if ($matches -ge 8) { continue }
                $matches++
                $types=New-Object System.Collections.ArrayList
                $hints=New-Object 'System.Collections.Generic.HashSet[string]'
                $actions=New-Object 'System.Collections.Generic.HashSet[string]'
                $parent=$node
                for ($depth=0;$depth -lt 9 -and $null -ne $parent;$depth++) {
                    try {
                        $t=[string]$parent.Current.ControlType.ProgrammaticName
                        [void]$types.Add($t.Replace('ControlType.',''))
                        $aid=[string]$parent.Current.AutomationId
                        $class=[string]$parent.Current.ClassName
                        $n=[string]$parent.Current.Name
                        $descriptor=($aid+' '+$class)
                        if ($descriptor -match '(?i)(^|[^a-z])assistant([^a-z]|$)' -or $n -match '^(?i:assistant)( message)?$') { [void]$hints.Add('ASSISTANT') }
                        if ($descriptor -match '(?i)(^|[^a-z])user([^a-z]|$)' -or $n -match '^(?i:user)( message)?$') { [void]$hints.Add('USER') }
                        if ($descriptor -match '(?i)(^|[^a-z])message([^a-z]|$)') { [void]$hints.Add('MESSAGE_CONTAINER') }
                        if ($descriptor -match '(?i)(^|[^a-z])turn([^a-z]|$)') { [void]$hints.Add('TURN_CONTAINER') }
                        $children=$parent.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
                        for ($j=0;$j -lt [Math]::Min([int]$children.Count,40);$j++) {
                            $child=$children.Item($j)
                            if ([string]$child.Current.ControlType.ProgrammaticName -ne 'ControlType.Button') { continue }
                            $label=[string]$child.Current.Name
                            if ($label -match '(?i)copy') { [void]$actions.Add('COPY') }
                            if ($label -match '(?i)edit') { [void]$actions.Add('EDIT') }
                            if ($label -match '(?i)read aloud|listen') { [void]$actions.Add('READ_ALOUD') }
                            if ($label -match '(?i)thumbs up|good response') { [void]$actions.Add('POSITIVE_FEEDBACK') }
                            if ($label -match '(?i)thumbs down|bad response') { [void]$actions.Add('NEGATIVE_FEEDBACK') }
                            if ($label -match '(?i)retry|regenerate') { [void]$actions.Add('REGENERATE') }
                        }
                        $parent=$walker.GetParent($parent)
                    }catch { $errors++; break }
                }
                $rect=$node.Current.BoundingRectangle
                $center=-1
                if ($bounds.Width -gt 0 -and $rect.Width -gt 0) {
                    $center=[Math]::Round((($rect.Left + $rect.Width/2 - $bounds.Left)/$bounds.Width)*100)
                }
                Write-Output ('MATCH_'+$matches+'_SOURCE='+$source)
                Write-Output ('MATCH_'+$matches+'_CHAIN='+(@($types) -join '>'))
                Write-Output ('MATCH_'+$matches+'_SEMANTIC_HINTS='+(if($hints.Count){@($hints|Sort-Object) -join ','}else{'NONE'}))
                Write-Output ('MATCH_'+$matches+'_NEARBY_ACTIONS='+(if($actions.Count){@($actions|Sort-Object) -join ','}else{'NONE'}))
                Write-Output ('MATCH_'+$matches+'_CENTER_X_PERCENT='+$center)
            }catch { $errors++ }
        }
    }catch { $errors++ }
}
Write-Output ('MARKER_MATCHES_TOTAL='+$seen)
Write-Output ('STRUCTURAL_ERRORS='+$errors)
Write-Output 'ASSISTANT_ORIGIN_PROVEN=NO'
Write-Output 'RESULT=STRUCTURE_CAPTURE_ONLY_NO_EXECUTION'
