param([ValidateSet('status','start','stop','restart','pause','resume','retry')][string]$Action='status')
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$pause=Join-Path $root '.relay-paused'
$run=Join-Path $root 'run.ps1'
function Listener {Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1}
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
  $l=Listener;$p=Test-Path $pause
  if($l){Write-Output ('RUNNING PID='+$l.OwningProcess+' PAUSED='+$p)}else{Write-Output ('STOPPED PAUSED='+$p)}
  exit
}
if($Action -in @('stop','pause')){
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
if($Action -eq 'restart'){
  New-Item -ItemType File -Force -Path $pause | Out-Null
  $l=Listener
  if($l){taskkill /PID $l.OwningProcess /T /F | Out-Null}
  Start-Sleep -Seconds 2
  Remove-Item $pause -Force -ErrorAction SilentlyContinue
  StartSupervisor
} elseif($Action -in @('start','resume')) {
  Remove-Item $pause -Force -ErrorAction SilentlyContinue
  StartSupervisor
}
$l=Listener
if($l){Write-Output ('RUNNING PID='+$l.OwningProcess+' PAUSED=False')}else{Write-Output 'STOPPED PAUSED=False'}