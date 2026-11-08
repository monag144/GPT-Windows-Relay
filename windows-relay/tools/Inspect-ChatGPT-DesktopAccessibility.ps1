# GPT Windows Relay — desktop ChatGPT accessibility preflight
# Read-only. No message text, window screenshots, clipboard, or credentials printed.
# Launched from CMD with: powershell.exe -NoProfile -ExecutionPolicy Bypass -File "..."
$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
} catch {
    Write-Output 'CHATGPT_UIA_ASSEMBLIES=UNAVAILABLE'
    exit 3
}
Write-Output 'RELAY_DESKTOP_PREFLIGHT_V1'
Write-Output 'MODE=READ_ONLY_NO_SCREENSHOT_NO_MESSAGE_CONTENT'
$root = [System.Windows.Automation.AutomationElement]::RootElement
$windows = $root.FindAll(
    [System.Windows.Automation.TreeScope]::Children,
    [System.Windows.Automation.Condition]::TrueCondition
)
$targets = New-Object System.Collections.ArrayList
foreach ($window in $windows) {
    try {
        $processId = [int]$window.Current.ProcessId
        if ($processId -le 0) { continue }
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($null -eq $proc) { continue }
        $name = [string]$proc.ProcessName
        $title = [string]$window.Current.Name
        $isChatGptProcess = $name -match '(?i)chatgpt|openai'
        $isChatGptWindow = $title -match '(?i)chatgpt'
        $excludedBrowser = $name -match '(?i)^(firefox|chrome|msedge|brave|opera|vivaldi)$'
        if (-not $excludedBrowser -and ($isChatGptProcess -or $isChatGptWindow)) {
            [void]$targets.Add(@{ element=$window; process=$name; process_id=$processId })
        }
    } catch { continue }
}
Write-Output ('CHATGPT_DESKTOP_WINDOWS=' + $targets.Count)
if ($targets.Count -eq 0) {
    Write-Output 'RESULT=NO_CHATGPT_DESKTOP_WINDOW_FOUND'
    Write-Output 'NEXT=Open the ChatGPT desktop app in its main window and repeat this check.'
    exit 2
}
foreach ($target in $targets) {
    $element = $target.element
    Write-Output ('CHATGPT_PROCESS=' + $target.process)
    Write-Output ('CHATGPT_PROCESS_ID=' + $target.process_id)
    try {
        $children = $element.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition
        )
        $documents = 0; $editors = 0; $buttons = 0; $textPatterns = 0; $composerCandidates = 0
        $elementsExamined = [Math]::Min([int]$children.Count,3000)
        for ($i=0; $i -lt $elementsExamined; $i++) {
            try {
                $child = $children.Item($i)
                $typeName = [string]$child.Current.ControlType.ProgrammaticName
                if ($typeName -eq 'ControlType.Document') { $documents++ }
                if ($typeName -eq 'ControlType.Edit') {
                    $editors++
                    $accessibilityName = [string]$child.Current.Name
                    if ($accessibilityName -match '(?i)ask chatgpt|prompt|message|chat') {
                        $composerCandidates++
                    }
                }
                if ($typeName -eq 'ControlType.Button') { $buttons++ }
                $pattern = $null
                if ($child.TryGetCurrentPattern(
                    [System.Windows.Automation.TextPattern]::Pattern,[ref]$pattern
                )) { $textPatterns++ }
            } catch { continue }
        }
        Write-Output ('UIA_ELEMENTS_EXAMINED=' + $elementsExamined)
        Write-Output ('UIA_DOCUMENTS=' + $documents)
        Write-Output ('UIA_EDITORS=' + $editors)
        Write-Output ('UIA_BUTTONS=' + $buttons)
        Write-Output ('UIA_TEXT_PATTERN_ELEMENTS=' + $textPatterns)
        Write-Output ('UIA_COMPOSER_CANDIDATES=' + $composerCandidates)
        if ($documents -gt 0 -or $textPatterns -gt 0) {
            Write-Output 'UIA_TEXT_EXTRACTION_CANDIDATE=YES_UNVERIFIED'
        } else {
            Write-Output 'UIA_TEXT_EXTRACTION_CANDIDATE=NONE_VISIBLE'
        }
    } catch {
        Write-Output ('UIA_INSPECTION_ERROR=' + $_.Exception.GetType().Name)
    }
}
Write-Output 'RESULT=PREFLIGHT_COMPLETE_NO_RELAY_EXECUTION'
