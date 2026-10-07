param([ValidateSet('status','start','stop','restart','pause','resume','off','kill')][string]$Action='status')
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$pause=Join-Path $root '.relay-paused'
$off=Join-Path $root '.relay-off'
$kill=Join-Path $root '.relay-kill'
$killHud=Join-Path $root '.relay-kill-hud'
$starting=Join-Path $root '.relay-starting'
$killFailed=Join-Path $root '.relay-kill-failed'
$disconnectReason=Join-Path $root '.relay-disconnect-reason'
$run=Join-Path $root 'run.ps1'
$watchdog=Join-Path $root 'relay-watchdog-loop.ps1'

function Listener {
  Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
}
function GenuineSupervisors {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^powershell(.exe)?$' -and
    $_.CommandLine -match '(?i)-File\s+"?[^"]*\\run\.ps1"?(\s|$)'
  })
}
function GenuineWatchdogs {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^powershell(.exe)?$' -and
    $_.CommandLine -match '(?i)-File\s+"?[^"]*\\relay-watchdog-loop\.ps1"?(\s|$)'
  })
}
function GenuineHudProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^pythonw(.exe)?$' -and
    $_.CommandLine -match '(?i)(^|\s)"?[^"]*hud\.py"?(\s|$)'
  })
}
function GenuineRelayProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -ieq 'GPTWindowsRelay.exe' -or
    ($_.CommandLine -and $_.CommandLine -match '(?i)(^|\s)"?[^"]*windows_relay\.py"?(\s|$)')
  })
}
function KillTree($items) {
  foreach($p in @($items)){
    if($p.ProcessId -and $p.ProcessId -ne $PID){
      taskkill /PID $p.ProcessId /T /F | Out-Null
    }
  }
}
function KillHudOnly {
  foreach($p in @(GenuineHudProcesses)){
    if($p.ProcessId -and $p.ProcessId -ne $PID){
      taskkill /PID $p.ProcessId /F | Out-Null
    }
  }
}
function WriteReason([string]$Text) {
  Set-Content -LiteralPath $disconnectReason -Value $Text -Encoding UTF8
}
function StopBackend {
  New-Item -ItemType File -Force -Path $pause | Out-Null
  $l=Listener
  if($l){taskkill /PID $l.OwningProcess /T /F | Out-Null}
  KillTree (GenuineRelayProcesses)
  KillTree (GenuineSupervisors)
  Start-Sleep -Milliseconds 500
  $after=Listener
  return -not [bool]$after
}
function StartSupervisor {
  if(-not (Listener) -and (GenuineSupervisors).Count -eq 0){
    Start-Process powershell.exe -WindowStyle Normal -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('\"'+$run+'\"')) | Out-Null
  }
}
function StartWatchdog {
  if((GenuineWatchdogs).Count -eq 0 -and (Test-Path -LiteralPath $watchdog)){
    Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('\"'+$watchdog+'\"')) | Out-Null
  }
}
function WaitListener([int]$Seconds=10) {
  $deadline=(Get-Date).AddSeconds($Seconds)
  while((Get-Date) -lt $deadline){
    $l=Listener
    if($l){return $l}
    Start-Sleep -Milliseconds 500
  }
  return $null
}

if($Action -eq 'status'){
  $l=Listener
  if(Test-Path $killFailed){Write-Output ('STATE=KILL_FAILED REASON='+(Get-Content $killFailed -Raw).Trim());exit}
  if(Test-Path $killHud){Write-Output 'STATE=KILLING_HUD';exit}
  if(Test-Path $kill){Write-Output 'STATE=KILLING_RELAY';exit}
  if(Test-Path $off){Write-Output 'STATE=OFF';exit}
  if(Test-Path $pause){Write-Output 'STATE=STOPPED';exit}
  if(Test-Path $starting){Write-Output 'STATE=STARTING';exit}
  if($l){Write-Output ('STATE=RUNNING PID='+$l.OwningProcess);exit}
  Write-Output 'STATE=DISCONNECTED REASON=port 8766 not listening'
  exit
}

if($Action -in @('stop','pause')){
  Remove-Item $off,$kill,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  if(-not (StopBackend)){WriteReason 'port 8766 remained listening after stop';throw 'relay backend did not stop'}
  if($Action -eq 'stop'){Write-Output 'STOPPED'}else{Write-Output 'PAUSED'}
  exit
}

if($Action -eq 'off'){
  Remove-Item $kill,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $off | Out-Null
  if(-not (StopBackend)){WriteReason 'port 8766 remained listening during OFF';throw 'relay backend did not stop'}
  KillTree (GenuineWatchdogs)
  Write-Output 'OFF'
  exit
}

if($Action -eq 'kill'){
  Remove-Item $off,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $pause | Out-Null
  New-Item -ItemType File -Force -Path $kill | Out-Null
  Start-Sleep -Milliseconds 1400
  $backendDead=StopBackend
  KillTree (GenuineWatchdogs)
  Start-Sleep -Milliseconds 300
  $remainingRelay=(GenuineRelayProcesses).Count
  $remainingSup=(GenuineSupervisors).Count
  $remainingWatchdog=(GenuineWatchdogs).Count
  if((-not $backendDead) -or $remainingRelay -gt 0 -or $remainingSup -gt 0 -or $remainingWatchdog -gt 0){
    $liveListener=Listener
    $reason='kill verification failed: listener='+([bool]$liveListener)+' relay='+$remainingRelay+' supervisor='+$remainingSup+' watchdog='+$remainingWatchdog
    Set-Content -LiteralPath $killFailed -Value $reason -Encoding UTF8
    Write-Output ('KILL_FAILED '+$reason)
    exit 1
  }
  New-Item -ItemType File -Force -Path $killHud | Out-Null
  Start-Sleep -Milliseconds 1400
  KillHudOnly
  Write-Output 'KILLED'
  exit
}

if($Action -eq 'restart'){
  Remove-Item $off,$kill,$killHud,$killFailed,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $starting | Out-Null
  [void](StopBackend)
  Remove-Item $pause -Force -ErrorAction SilentlyContinue
  StartWatchdog
  StartSupervisor
  $l=WaitListener 10
  Remove-Item $starting -Force -ErrorAction SilentlyContinue
  if($l){Write-Output ('RUNNING PID='+$l.OwningProcess);exit}
  WriteReason 'port 8766 not listening after restart timeout'
  Write-Output 'DISCONNECTED'
  exit 1
}

if($Action -in @('start','resume')){
  Remove-Item $pause,$off,$kill,$killHud,$killFailed,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $starting | Out-Null
  StartWatchdog
  StartSupervisor
  $l=WaitListener 10
  Remove-Item $starting -Force -ErrorAction SilentlyContinue
  if($l){Write-Output ('RUNNING PID='+$l.OwningProcess);exit}
  WriteReason 'port 8766 not listening after start timeout'
  Write-Output 'DISCONNECTED'
  exit 1
}
