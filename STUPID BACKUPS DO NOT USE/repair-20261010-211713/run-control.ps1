$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$logDir=Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log=Join-Path $logDir 'supervisor.log'
$pause=Join-Path $PSScriptRoot '.relay-paused'
$py=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$server=Join-Path $PSScriptRoot 'windows_relay.py'
function Log([string]$m){Add-Content -LiteralPath $log -Value ((Get-Date -Format o)+' '+$m)}
$created=$false
$mutex=[System.Threading.Mutex]::new($true,'Local\GPTWindowsRelaySupervisor',[ref]$created)
if(-not $created){
  Log ('SUPERVISOR_DUPLICATE_EXIT pid='+$PID)
  Write-Host '[SUPERVISOR] Another supervisor already owns the singleton lock.'
  $mutex.Dispose()
  exit 0
}
try {
  try{$Host.UI.RawUI.WindowTitle='GPT Windows Relay'}catch{}
  Write-Host ''
  Write-Host '========================================'
  Write-Host ' GPT WINDOWS RELAY'
  Write-Host ' Visible supervisor console'
  Write-Host '========================================'
  Write-Host ''
  Log ('SUPERVISOR_START pid='+$PID)
  $crashes=0
  while($true){
    if(Test-Path -LiteralPath $pause){Log 'SUPERVISOR_PAUSED';Write-Host '[SUPERVISOR] Paused.';break}
    try {
      Log ('SERVER_START crashes='+$crashes)
      Write-Host ('[SUPERVISOR] Starting relay - crash count '+$crashes)
      & $py $server server
      $code=$LASTEXITCODE
    } catch {
      $code=1
      Log ('SERVER_EXCEPTION '+$_.Exception.GetType().Name+' '+$_.Exception.Message)
      Write-Host ('[SUPERVISOR] Exception: '+$_.Exception.Message)
    }
    if(Test-Path -LiteralPath $pause){Log ('SERVER_EXIT_PAUSED code='+$code);Write-Host '[SUPERVISOR] Relay stopped while paused.';break}
    $crashes++
    Log ('SERVER_EXIT_UNEXPECTED code='+$code+' restart_in_seconds=2 crash_count='+$crashes)
    Write-Host ('[SUPERVISOR] Relay exited with code '+$code+'. Restarting in 2 seconds...')
    Start-Sleep -Seconds 2
  }
} finally {
  try{$mutex.ReleaseMutex()}catch{}
  $mutex.Dispose()
  Log ('SUPERVISOR_EXIT pid='+$PID)
}
