# Native desktop ChatGPT monitor inspection, read-only.
# Separate from the browser extension: never arms or dispatches an action.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$expected=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'Run-ChatGPT-DesktopMonitor.ps1'))
$processes=@(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction Stop)
$running=@()
foreach($p in $processes){
    $line=[string]$p.CommandLine
    if($line.Length -eq 0){continue}
    # Match an exact quoted script path. Do not mistake similarly named files
    # or a terminal window title for an active, canonical monitor.
    if($line.IndexOf(('"'+$expected+'"'),[StringComparison]::OrdinalIgnoreCase) -ge 0){
        $running+=,$p
    }
}
Write-Output 'CHATGPT_DESKTOP_MONITOR_STATUS_V1'
if($running.Count -gt 1){
    Write-Output ('DESKTOP_MONITOR=AMBIGUOUS COUNT='+$running.Count)
    exit 3
}
if($running.Count -eq 1){
    Write-Output ('DESKTOP_MONITOR=RUNNING PID='+$running[0].ProcessId)
    Write-Output 'DESKTOP_MONITOR_CODE_RELOAD=STOP_EXISTING_PROCESS_FIRST'
    Write-Output 'DESKTOP_COMMAND_EXECUTION=LOCKED_UNVERIFIED_UIA_ORIGIN'
    exit 10
}
Write-Output 'DESKTOP_MONITOR=STOPPED'
Write-Output 'DESKTOP_COMMAND_EXECUTION=LOCKED_UNVERIFIED_UIA_ORIGIN'
exit 0
