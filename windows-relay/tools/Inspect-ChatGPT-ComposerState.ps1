# GPT Windows Relay — read-only ChatGPT app composer diagnosis
# No composer content, access tokens, keyboard, mouse, screenshot, clipboard or HTTP.
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::RootElement
$top=$root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
$windows=New-Object System.Collections.ArrayList
foreach($node in $top){
    try{
        $pidValue=[int]$node.Current.ProcessId
        if($pidValue -le 0){continue}
        $proc=Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        if($proc -and $proc.ProcessName -ieq 'ChatGPT'){[void]$windows.Add($node)}
    }catch{}
}
Write-Output 'CHATGPT_COMPOSER_DIAGNOSTIC_V1'
Write-Output 'MODE=READ_ONLY_NO_DRAFT_CONTENT'
Write-Output ('CHATGPT_WINDOWS='+$windows.Count)
if($windows.Count -ne 1){
    Write-Output 'RESULT=AMBIGUOUS_OR_MISSING_CHATGPT_WINDOW'
    exit 2
}
$nodes=$windows[0].FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$editCount=0
$composerCount=0
for($i=0;$i -lt $nodes.Count;$i++){
    try{
        $node=$nodes.Item($i)
        if([string]$node.Current.ControlType.ProgrammaticName -ne 'ControlType.Edit'){continue}
        $editCount++
        if([string]$node.Current.Name -notmatch '(?i)ask chatgpt|ask anything|message|prompt|chat'){continue}
        $p=$null
        if(-not $node.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$p)){continue}
        if($p.Current.IsReadOnly){continue}
        $composerCount++
        if($composerCount -gt 3){continue}
        $value=[string]$p.Current.Value
        $name=[string]$node.Current.Name
        $textAvailable=$false
        $textLength=-1
        $tp=$null
        if($node.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$tp)){
            try{$textLength=([string]$tp.DocumentRange.GetText(-1)).Length;$textAvailable=$true}catch{}
        }
        $normal=$value.Trim()
        $placeholderLike=($normal -cmatch '^(?i:ask chatgpt|ask anything|message chatgpt|message|send a message|ask a question)[.!?]?$')
        Write-Output ('COMPOSER_'+$composerCount+'_ENABLED='+$node.Current.IsEnabled)
        Write-Output ('COMPOSER_'+$composerCount+'_OFFSCREEN='+$node.Current.IsOffscreen)
        Write-Output ('COMPOSER_'+$composerCount+'_FOCUSED='+$node.Current.HasKeyboardFocus)
        Write-Output ('COMPOSER_'+$composerCount+'_VALUE_LENGTH='+$value.Length)
        Write-Output ('COMPOSER_'+$composerCount+'_TRIMMED_LENGTH='+$normal.Length)
        Write-Output ('COMPOSER_'+$composerCount+'_VALUE_EQUALS_ACCESSIBLE_NAME='+($value -ceq $name))
        Write-Output ('COMPOSER_'+$composerCount+'_MATCHES_COMMON_PLACEHOLDER_WORDING='+$placeholderLike)
        Write-Output ('COMPOSER_'+$composerCount+'_TEXT_PATTERN_AVAILABLE='+$textAvailable)
        Write-Output ('COMPOSER_'+$composerCount+'_TEXT_PATTERN_LENGTH='+$textLength)
    }catch{
        Write-Output 'COMPOSER_ELEMENT_UNREADABLE=TRUE'
    }
}
Write-Output ('EDIT_CONTROLS='+$editCount)
Write-Output ('WRITABLE_COMPOSER_CANDIDATES='+$composerCount)
Write-Output 'NOTE=PLACEHOLDER_LIKE_VALUE_IS_NOT_PROOF_OF_AN_EMPTY_DRAFT'
Write-Output 'RESULT=DIAGNOSTIC_COMPLETE_NO_UI_MUTATION'
