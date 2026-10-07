$ErrorActionPreference='SilentlyContinue'
$root=$PSScriptRoot
$log=Join-Path $root 'logs\watchdog.log'
$listener=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if($listener){Add-Content $log ((Get-Date -Format o)+' OK listener PID='+$listener.OwningProcess); exit 0}
$run=Join-Path $root 'run.ps1'
if(Test-Path $run){Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$run+'"')); Start-Sleep -Seconds 2}
$listener=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if($listener){Add-Content $log ((Get-Date -Format o)+' RECOVERED listener PID='+$listener.OwningProcess); exit 0}
Add-Content $log ((Get-Date -Format o)+' FAILED no relay listener'); exit 1
