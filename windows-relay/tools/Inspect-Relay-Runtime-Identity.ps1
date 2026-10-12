# Read-only Windows Relay source/launch identity inspection.
# Does not execute a relay action, bind ownership, print tokens, or change any file.
$ErrorActionPreference = 'Stop'
$relayRoot = Split-Path -Parent $PSScriptRoot
$checkout = Split-Path -Parent $relayRoot
$legacy = Join-Path $env:USERPROFILE 'Downloads\Dev\GPT\Client\Relay'
$mainBuild = Join-Path $env:USERPROFILE 'Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay'
$oldIndicator = 'Downloads\Dev\GPT\Client\Relay'
$newIndicator = 'Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay'
function IdentifySource([string]$commandLine) {
  if([string]::IsNullOrWhiteSpace($commandLine)){return 'UNKNOWN'}
  if($commandLine.IndexOf($newIndicator,[StringComparison]::OrdinalIgnoreCase) -ge 0){return 'MAIN_BUILD'}
  if($commandLine.IndexOf($oldIndicator,[StringComparison]::OrdinalIgnoreCase) -ge 0){return 'OLD_CLIENT'}
  if($commandLine -match 'windows_relay\.py|relay-watchdog|relay-control|run\.ps1|hud\.py'){return 'OTHER_RELAY_PATH'}
  return 'NOT_RELAY'
}
Write-Output '=== GPT WINDOWS RELAY READ-ONLY IDENTITY ==='
Write-Output ('SOURCE_ROOT=' + $relayRoot)
Write-Output ('CHECKOUT_ROOT=' + $checkout)
Write-Output ('MAIN_BUILD_SOURCE_PRESENT=' + (Test-Path -LiteralPath (Join-Path $mainBuild 'windows_relay.py')))
Write-Output ('OLD_CLIENT_PATH_PRESENT=' + (Test-Path -LiteralPath $legacy))
$sourceFile=Join-Path $relayRoot 'windows_relay.py'
if(Test-Path -LiteralPath $sourceFile){
  Write-Output ('MAIN_SOURCE_SHA256=' + (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash)
}
try {
  $git = Get-Command git.exe -ErrorAction Stop
  $head=(& $git.Source -C $checkout rev-parse HEAD 2>$null)
  $branch=(& $git.Source -C $checkout branch --show-current 2>$null)
  $dirty=@(& $git.Source -C $checkout status --porcelain 2>$null)
  Write-Output ('GIT_HEAD=' + $head)
  Write-Output ('GIT_BRANCH=' + $branch)
  Write-Output ('GIT_DIRTY_ENTRY_COUNT=' + $dirty.Count)
} catch { Write-Output 'GIT_IDENTITY=UNAVAILABLE' }
$cfg=Join-Path $env:APPDATA 'GPTWindowsRelay\bridge.json'
Write-Output ('BRIDGE_CONFIG_EXISTS=' + (Test-Path -LiteralPath $cfg))
# Never read or print pairing credentials.
$processes=@()
try { $processes=@(Get-CimInstance Win32_Process -ErrorAction Stop) }
catch { Write-Output 'PROCESS_ENUMERATION=UNAVAILABLE' }
try {
  $listeners=@(Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalAddress -eq '127.0.0.1' })
  if($listeners.Count -eq 0){Write-Output 'PORT_8766=NOT_LISTENING'}
  foreach($l in $listeners){
    $proc=@($processes | Where-Object { $_.ProcessId -eq $l.OwningProcess } | Select-Object -First 1)
    $cmd=if($proc.Count){[string]$proc[0].CommandLine}else{''}
    Write-Output ('PORT_8766=LISTENING PID=' + $l.OwningProcess + ' SOURCE=' + (IdentifySource $cmd))
  }
} catch {
  Write-Output ('PORT_8766=UNVERIFIED ' + $_.Exception.GetType().Name)
}
$relayProcesses=@($processes | Where-Object {
  $_.Name -match '^(pythonw?\.exe|powershell\.exe|pwsh\.exe|cmd\.exe)$' -and
  [string]$_.CommandLine -match 'windows_relay\.py|relay-control|relay-watchdog|hud\.py|GPTWindowsRelay'
})
Write-Output ('RELAY_PROCESS_CANDIDATES=' + $relayProcesses.Count)
foreach($p in $relayProcesses){
  Write-Output ('RELAY_PROCESS PID=' + $p.ProcessId + ' NAME=' + $p.Name + ' SOURCE=' + (IdentifySource ([string]$p.CommandLine)))
}
try {
  $tasks=@(Get-ScheduledTask -ErrorAction Stop)
  $found=0
  foreach($t in $tasks){
    foreach($a in @($t.Actions)){
      $command=[string]$a.Execute+' '+[string]$a.Arguments
      if($command -match 'GPTWindowsRelay|GPT-Windows-Relay|windows_relay\.py|relay-watchdog|relay-control|GPT\\Client\\Relay'){
        $found++
        Write-Output ('RELAY_TASK NAME=' + $t.TaskName + ' SOURCE=' + (IdentifySource $command))
      }
    }
  }
  Write-Output ('RELAY_SCHEDULED_ACTION_COUNT=' + $found)
} catch {Write-Output 'SCHEDULED_TASK_INSPECTION=UNAVAILABLE'}
foreach($key in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\Microsoft\Windows\CurrentVersion\Run')){
  try {
    $values=Get-ItemProperty -LiteralPath $key -ErrorAction Stop
    foreach($prop in $values.PSObject.Properties){
      if($prop.Name -match '^PS'){continue}
      $value=[string]$prop.Value
      if($value -match 'GPTWindowsRelay|GPT-Windows-Relay|windows_relay\.py|relay-watchdog|GPT\\Client\\Relay'){
        Write-Output ('RELAY_STARTUP_ENTRY KEY=' + $key + ' NAME=' + $prop.Name + ' SOURCE=' + (IdentifySource $value))
      }
    }
  }catch{}
}
$firefox=@(Get-Process -Name firefox -ErrorAction SilentlyContinue)
Write-Output ('FIREFOX_PROCESS_COUNT=' + $firefox.Count)
Write-Output 'FIREFOX_LOADED_EXTENSION_IDENTITY=UNKNOWN_FROM_PROCESS_INSPECTION'
Write-Output 'FIREFOX_NEXT_CHECK=about:debugging#/runtime/this-firefox'
Write-Output 'RESULT=READ_ONLY_NO_CHANGES'
