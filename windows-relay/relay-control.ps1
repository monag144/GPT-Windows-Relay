param([ValidateSet('status','start','stop','restart','pause','resume','retry','off','kill')][string]$Action='status')
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$pause=Join-Path $root '.relay-paused'
$off=Join-Path $root '.relay-off'
$kill=Join-Path $root '.relay-kill'
$killHud=Join-Path $root '.relay-kill-hud'
$starting=Join-Path $root '.relay-starting'
$killFailed=Join-Path $root '.relay-kill-failed'
$disconnectReason=Join-Path $root '.relay-disconnect-reason'
$run=Join-Path $root 'run-control.ps1'
$watchdog=Join-Path $root 'relay-watchdog-loop.ps1'
function Listener {Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1}
function GenuineSupervisors {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -match '^powershell(.exe)?$' -and $_.CommandLine -match '(?i)-File\s+"?[^\"]*\\run-control\.ps1"?(\s|$)'})
}
function GenuineWatchdogs {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -match '^powershell(.exe)?$' -and $_.CommandLine -match '(?i)-File\s+"?[^\"]*\\relay-watchdog-loop\.ps1"?(\s|$)'})
}
function GenuineHudProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -match '^pythonw(.exe)?$' -and $_.CommandLine -match '(?i)(^|\s)"?[^\"]*hud\.py"?(\s|$)'})
}
function GenuineRelayProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -ieq 'GPTWindowsRelay.exe' -or ($_.CommandLine -and $_.CommandLine -match '(?i)(^|\s)"?[^\"]*windows_relay\.py"?(\s|$)')})
}
function KillTree($items){foreach($proc in @($items)){if($proc.ProcessId -and $proc.ProcessId -ne $PID){taskkill /PID $proc.ProcessId /T /F | Out-Null}}}
function KillHudOnly {foreach($proc in @(GenuineHudProcesses)){if($proc.ProcessId -and $proc.ProcessId -ne $PID){taskkill /PID $proc.ProcessId /F | Out-Null}}}
function WriteReason([string]$Text){Set-Content -LiteralPath $disconnectReason -Value $Text -Encoding UTF8}
function GetBackendConfig([int]$listenerPort){
  $configs=@()
  foreach($bridge in @(
    (Join-Path $env:APPDATA 'GPTWindowsRelay\bridge.json'),
    (Join-Path $env:APPDATA 'GPTWindowsRelayConsumer\bridge.json')
  )){
    if(-not(Test-Path -LiteralPath $bridge)){continue}
    try{$candidate=Get-Content -LiteralPath $bridge -Raw | ConvertFrom-Json}catch{continue}
    if([int]$candidate.port -eq $listenerPort -and -not [string]::IsNullOrWhiteSpace([string]$candidate.token)){$configs+=,$candidate}
  }
  if($configs.Count -ne 1){return $null}
  return $configs[0]
}
function SetBackendArm([bool]$armed,[int]$listenerPort){
  try{
    $cfg=GetBackendConfig $listenerPort
    if($null -eq $cfg){return $null}
    $headers=@{'X-GPT-Windows-Relay-Token'=[string]$cfg.token}
    $body=@{armed=$armed}|ConvertTo-Json -Compress
    return Invoke-RestMethod -Uri ('http://127.0.0.1:'+([int]$cfg.port)+'/arm') -Method Post -Headers $headers -ContentType 'application/json' -Body $body -TimeoutSec 2
  }catch{return $null}
}
function WaitBrowserQuiesced([int]$listenerPort,[long]$generation,[int]$timeoutMs=5000){
  if($generation -le 0){return $false}
  $cfg=GetBackendConfig $listenerPort
  if($null -eq $cfg){return $false}
  $headers=@{'X-GPT-Windows-Relay-Token'=[string]$cfg.token}
  $deadline=[DateTime]::UtcNow.AddMilliseconds($timeoutMs)
  while([DateTime]::UtcNow -lt $deadline){
    try{
      $st=Invoke-RestMethod -Uri ('http://127.0.0.1:'+([int]$cfg.port)+'/status') -Headers $headers -TimeoutSec 1
      if((-not [bool]$st.armed) -and [long]$st.stop_generation -eq $generation -and [long]$st.browser_quiesced_generation -eq $generation){return $true}
    }catch{}
    Start-Sleep -Milliseconds 100
  }
  return $false
}
function StartSupervisor {
  if(-not (Listener)){
    Start-Process powershell.exe -WindowStyle Normal -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$run+'"')) | Out-Null
    Start-Sleep -Seconds 2
  }
}
function StartWatchdog {
  if((GenuineWatchdogs).Count -eq 0 -and (Test-Path -LiteralPath $watchdog)){
    $args='-NoProfile -ExecutionPolicy Bypass -File "'+$watchdog+'"'
    Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $root -ArgumentList $args | Out-Null
  }
}
function StopBackend {
  New-Item -ItemType File -Force -Path $pause | Out-Null
  $l=Listener
  if($l){
    $arm=SetBackendArm $false ([int]$l.LocalPort)
    if($null -ne $arm -and [long]$arm.stop_generation -gt 0){[void](WaitBrowserQuiesced ([int]$l.LocalPort) ([long]$arm.stop_generation) 5000)}
    taskkill /PID $l.OwningProcess /T /F | Out-Null
  }
  KillTree (GenuineRelayProcesses); KillTree (GenuineSupervisors); Start-Sleep -Milliseconds 500
  return -not [bool](Listener)
}
if($Action -eq 'retry'){
  $py=Join-Path $root '.venv\Scripts\python.exe'
  $adapter=Join-Path $root 'firefox_adapter.py'
  $raw=& $py $adapter list-tabs
  if($LASTEXITCODE -ne 0){throw 'Firefox tab discovery failed'}
  $tabs=$raw|ConvertFrom-Json
  $selected=@($tabs.tabs|Where-Object{$_.selected -eq $true -and $_.name -match 'PC Engineering'})
  if($selected.Count -ne 1){throw ('Expected one selected PC Engineering tab, found '+$selected.Count)}
  & $py $adapter refresh-tab --tab-name ([string]$selected[0].name) | Out-Null
  if($LASTEXITCODE -ne 0){throw 'Firefox retry refresh failed'}
  Write-Output ('RETRY_REQUESTED TAB='+[string]$selected[0].name)
  exit
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
  Write-Output 'STATE=DISCONNECTED REASON=port 8766 not listening';exit
}
if($Action -in @('stop','pause')){
  Remove-Item $off,$kill,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $pause | Out-Null
  $l=Listener
  $stopGeneration=0
  $verified=$false
  if($l){
    $arm=SetBackendArm $false ([int]$l.LocalPort)
    if($null -ne $arm -and [long]$arm.stop_generation -gt 0){
      $stopGeneration=[long]$arm.stop_generation
      $verified=WaitBrowserQuiesced ([int]$l.LocalPort) $stopGeneration 5000
    }
    taskkill /PID $l.OwningProcess /T /F | Out-Null
  }
  $q=if($verified){'VERIFIED'}else{'UNVERIFIED'}
  if($Action -eq 'stop'){Write-Output ('STOPPED BROWSER_QUIESCENCE='+$q+' GENERATION='+$stopGeneration)}else{Write-Output ('PAUSED BROWSER_QUIESCENCE='+$q+' GENERATION='+$stopGeneration)}
  exit
}
if($Action -eq 'off'){
  Remove-Item $kill,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $off | Out-Null
  if(-not (StopBackend)){WriteReason 'port 8766 remained listening during OFF';throw 'relay backend did not stop'}
  KillTree (GenuineWatchdogs); Write-Output 'OFF'; exit
}
if($Action -eq 'kill'){
  Remove-Item $off,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $pause | Out-Null
  New-Item -ItemType File -Force -Path $kill | Out-Null
  Start-Sleep -Milliseconds 1400
  $backendDead=StopBackend
  KillTree (GenuineWatchdogs); Start-Sleep -Milliseconds 300
  $remainingRelay=(GenuineRelayProcesses).Count; $remainingSup=(GenuineSupervisors).Count; $remainingWatchdog=(GenuineWatchdogs).Count
  if((-not $backendDead) -or $remainingRelay -gt 0 -or $remainingSup -gt 0 -or $remainingWatchdog -gt 0){
    $reason='kill verification failed: listener='+([bool](Listener))+' relay='+$remainingRelay+' supervisor='+$remainingSup+' watchdog='+$remainingWatchdog
    Set-Content -LiteralPath $killFailed -Value $reason -Encoding UTF8; Write-Output ('KILL_FAILED '+$reason); exit 1
  }
  New-Item -ItemType File -Force -Path $killHud | Out-Null; Start-Sleep -Milliseconds 1400; KillHudOnly; Write-Output 'KILLED'; exit
}

if($Action -eq 'restart'){
  Remove-Item $off,$kill,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $starting | Out-Null
  New-Item -ItemType File -Force -Path $pause | Out-Null
  $l=Listener
  if($l){taskkill /PID $l.OwningProcess /T /F | Out-Null}
  Start-Sleep -Seconds 2
  Remove-Item $pause -Force -ErrorAction SilentlyContinue
  StartWatchdog
  StartSupervisor
  Remove-Item $starting -Force -ErrorAction SilentlyContinue
} elseif($Action -in @('start','resume')) {
  Remove-Item $pause,$off,$kill,$killHud,$killFailed,$starting,$disconnectReason -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force -Path $starting | Out-Null
  StartWatchdog
  StartSupervisor
  Remove-Item $starting -Force -ErrorAction SilentlyContinue
}
$l=Listener
if($l){Write-Output ('RUNNING PID='+$l.OwningProcess+' PAUSED=False')}else{Write-Output 'STOPPED PAUSED=False'}