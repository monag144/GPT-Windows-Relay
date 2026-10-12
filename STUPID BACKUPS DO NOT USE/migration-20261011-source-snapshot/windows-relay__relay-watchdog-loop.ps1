$ErrorActionPreference='SilentlyContinue'
$root=$PSScriptRoot
$logDir=Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log=Join-Path $logDir 'watchdog.log'
$pause=Join-Path $root '.relay-paused'
$run=Join-Path $root 'run.ps1'
$hud=Join-Path $root 'hud.py'
if(Test-Path (Join-Path $root '.venv\Scripts\pythonw.exe')){$hudPy=Join-Path $root '.venv\Scripts\pythonw.exe'}else{$hudPy=(Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source;if([string]::IsNullOrWhiteSpace($hudPy)){$hudPy=(Get-Command python.exe -ErrorAction SilentlyContinue).Source}}
# GPT_RELAY_WATCHDOG_HUD_RECONCILIATION_V1
function Log([string]$m){Add-Content -LiteralPath $log -Value ((Get-Date -Format o)+' '+$m)}
function Listener {Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1}
function ProcessForListener($l){if($l){Get-CimInstance Win32_Process -Filter ('ProcessId='+$l.OwningProcess) -ErrorAction SilentlyContinue}}
function IsCanonicalProcess($proc,[string]$relative){
  if($null -eq $proc){return $false}
  $expected=[IO.Path]::GetFullPath((Join-Path $root $relative)); $quoted='"'+$expected+'"'
  return ([string]$proc.CommandLine).IndexOf($quoted,[StringComparison]::OrdinalIgnoreCase) -ge 0
}
function CanonicalListener {$l=Listener;if(-not $l){return $null};$p=ProcessForListener $l;if(IsCanonicalProcess $p 'windows_relay.py'){return $l};return $null}
function GenuineSupervisors {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^powershell(.exe)?$' -and
    (IsCanonicalProcess $_ 'run.ps1')
  })
}
function GenuineHudProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^python(w)?(.exe)?$' -and
    (IsCanonicalProcess $_ 'hud.py')
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
    if(Test-Path -LiteralPath $pause){Start-Sleep -Seconds 10;continue}
    if(CanonicalListener){Start-Sleep -Seconds 10;continue}
    if(Listener){Log 'FOREIGN_LISTENER not touching existing backend';Start-Sleep -Seconds 10;continue}
    EnsureHud # GPT_RELAY_WATCHDOG_HUD_RECONCILE_CALL_V1
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
