$ErrorActionPreference='SilentlyContinue'
$root=$PSScriptRoot
$logDir=Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log=Join-Path $logDir 'watchdog.log'
$pause=Join-Path $root '.relay-paused'
$off=Join-Path $root '.relay-off'
$kill=Join-Path $root '.relay-kill'
$run=Join-Path $root 'run-control.ps1'
$hudPy=Join-Path $root '.venv\Scripts\pythonw.exe'
$hud=Join-Path $root 'hud.py'
# GPT_RELAY_WATCHDOG_HUD_RECONCILIATION_V1
# GPT_RELAY_WATCHDOG_OPERATOR_INTENT_V2
function Log([string]$m){Add-Content -LiteralPath $log -Value ((Get-Date -Format o)+' '+$m)}
function Listener {Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1}
function GenuineSupervisors {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^powershell(.exe)?$' -and
    $_.CommandLine -match '(?i)-File\s+"?[^"]*\\run-control\.ps1"?(\s|$)'
  })
}
function GenuineHudProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^pythonw(.exe)?$' -and
    $_.CommandLine -match '(?i)(^|\s)"?[^"]*hud\.py"?(\s|$)'
  })
}
function EnsureHud {
  if(-not (Test-Path -LiteralPath $hudPy) -or -not (Test-Path -LiteralPath $hud)){Log 'HUD_LAUNCH_FILES_MISSING';return}
  if((GenuineHudProcesses).Count -gt 0){return}
  Log 'HUD_MISSING starting HUD'
  Start-Process -FilePath $hudPy -WindowStyle Hidden -WorkingDirectory $root -ArgumentList @(('"' + $hud + '"')) | Out-Null
}
$created=$false
$mutex=[System.Threading.Mutex]::new($true,'Local\GPTWindowsRelayWatchdog',[ref]$created)
if(-not $created){Log ('WATCHDOG_DUPLICATE_EXIT pid='+$PID);$mutex.Dispose();exit 0}
try {
  Log ('WATCHDOG_START pid='+$PID)
  while($true){
    if(Test-Path -LiteralPath $kill){Log 'WATCHDOG_KILL_LATCH_EXIT';break}
    if(Test-Path -LiteralPath $off){Log 'WATCHDOG_OFF_LATCH_EXIT';break}
    EnsureHud # GPT_RELAY_WATCHDOG_HUD_RECONCILE_CALL_V1
    if(Test-Path -LiteralPath $pause){Start-Sleep -Seconds 10;continue}
    if(Listener){Start-Sleep -Seconds 10;continue}
    $sup=GenuineSupervisors
    if($sup.Count -eq 0){
      Log 'NO_LISTENER_NO_SUPERVISOR starting VISIBLE supervisor'
      Start-Process powershell.exe -WindowStyle Normal -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$run+'"')) | Out-Null
      Start-Sleep -Seconds 5
    } else {
      Log ('NO_LISTENER supervisor_present count='+$sup.Count+' waiting_for_internal_recovery')
      Start-Sleep -Seconds 5
    }
  }
} finally {
  try{$mutex.ReleaseMutex()}catch{}
  $mutex.Dispose()
  Log ('WATCHDOG_EXIT pid='+$PID)
}
