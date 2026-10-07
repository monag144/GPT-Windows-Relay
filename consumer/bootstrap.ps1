param(
  [switch]$NoBrowser,
  [switch]$NoGui
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$consumerRoot=$PSScriptRoot
$repoRoot=Split-Path -Parent $consumerRoot
$runtimeCandidates=@(
  (Join-Path $consumerRoot 'runtime'),
  (Join-Path $repoRoot 'windows-relay')
)
$runtime=$runtimeCandidates | Where-Object { Test-Path -LiteralPath (Join-Path $_ 'windows_relay.py') } | Select-Object -First 1
if(-not $runtime){throw 'Consumer relay runtime not found.'}

function Find-Python {
  $candidates=@()
  foreach($name in @('py.exe','python.exe')){
    $cmd=Get-Command $name -ErrorAction SilentlyContinue
    if($cmd){$candidates += $cmd.Source}
  }
  $candidates += @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'),
    (Join-Path $env:ProgramFiles 'Python313\python.exe'),
    (Join-Path $env:ProgramFiles 'Python312\python.exe'),
    (Join-Path $env:ProgramFiles 'Python311\python.exe')
  )
  foreach($candidate in $candidates | Select-Object -Unique){
    if(-not $candidate -or -not(Test-Path -LiteralPath $candidate)){continue}
    try{
      if((Split-Path -Leaf $candidate) -ieq 'py.exe'){
        & $candidate -3 -c "import sys,tkinter; assert sys.version_info >= (3,10)" 2>$null
        if($LASTEXITCODE -eq 0){return [pscustomobject]@{Exe=$candidate;Prefix=@('-3')}}
      }else{
        & $candidate -c "import sys,tkinter; assert sys.version_info >= (3,10)" 2>$null
        if($LASTEXITCODE -eq 0){return [pscustomobject]@{Exe=$candidate;Prefix=@()}}
      }
    }catch{}
  }
  return $null
}

function Install-PythonFallback {
  $version='3.13.16'
  $arch=[string]$env:PROCESSOR_ARCHITECTURE
  if($arch -eq 'ARM64'){
    $file='python-'+$version+'-arm64.exe'
    $sha='696e2226062c6ec3622c13f143d28336a856968518e49cb4f4c62513215a4f5d'
  }elseif($arch -eq 'x86'){
    $file='python-'+$version+'.exe'
    $sha='394ca84150ea428db952cb617c1163c49fbc30e47ec53048c26e6ae44265df07'
  }else{
    $file='python-'+$version+'-amd64.exe'
    $sha='fb4f9f5d438b2396da0086dc70b935c530cb578e37adc6d354f7ad2037fee83b'
  }
  $url='https://www.python.org/ftp/python/'+$version+'/'+$file
  $installer=Join-Path $env:TEMP ('gpt-oneclick-'+$file)
  Write-Host ('Downloading Python '+$version+' from python.org...')
  [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $installer
  $actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $installer).Hash.ToLowerInvariant()
  if($actual -ne $sha){
    Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue
    throw 'Downloaded Python installer failed SHA-256 verification.'
  }
  $args='/quiet InstallAllUsers=0 PrependPath=0 Include_launcher=1 Include_pip=1 Include_tcltk=1 Include_test=0 SimpleInstall=1'
  $proc=Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru
  Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue
  if($proc.ExitCode -ne 0){throw ('Python installer failed with exit code '+$proc.ExitCode)}
}

$python=Find-Python
if(-not $python){
  $winget=Get-Command winget.exe -ErrorAction SilentlyContinue
  if($winget){
    Write-Host 'Installing Python 3.13 for GPT One-Click Go with winget...'
    & $winget.Source install --id Python.Python.3.13 -e --source winget --scope user --silent --accept-package-agreements --accept-source-agreements
    if($LASTEXITCODE -ne 0){
      Write-Host ('winget Python install failed with exit code '+$LASTEXITCODE+'; using verified python.org fallback.')
    }
    $python=Find-Python
  }
  if(-not $python){
    Install-PythonFallback
    $python=Find-Python
  }
  if(-not $python){throw 'Python installation completed but Python 3.10+ with tkinter could not be located.'}
}

$pythonExe=[string]$python.Exe
$pythonPrefix=@($python.Prefix)
$venv=Join-Path $runtime '.venv'
$venvCfg=Join-Path $venv 'pyvenv.cfg'
$venvPy=Join-Path $venv 'Scripts\python.exe'
$venvPyw=Join-Path $venv 'Scripts\pythonw.exe'

function Test-OneClickVenv {
  if(-not(Test-Path -LiteralPath $venvCfg)){return $false}
  if(-not(Test-Path -LiteralPath $venvPy)){return $false}
  if(-not(Test-Path -LiteralPath $venvPyw)){return $false}
  try{
    & $venvPy -c "import json,tkinter,urllib.request,zipfile; import sys; assert sys.version_info >= (3,10)" 2>$null
    return ($LASTEXITCODE -eq 0)
  }catch{return $false}
}

function Stop-OneClickRuntimeForRepair {
  $pause=Join-Path $runtime '.relay-paused'
  New-Item -ItemType File -Force -Path $pause | Out-Null
  try{
    $escaped=[regex]::Escape([string](Resolve-Path -LiteralPath $runtime))
    $matches=@(
      Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
          $_.CommandLine -and
          ($_.CommandLine -match ($escaped+'.*windows_relay\.py') -or
           $_.CommandLine -match ($escaped+'.*run\.ps1'))
        }
    )
    foreach($proc in $matches){
      Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 500
  }catch{}
}

if(-not(Test-OneClickVenv)){
  if(Test-Path -LiteralPath $venv){
    Write-Host 'Repairing incomplete One-Click Python environment...'
    Stop-OneClickRuntimeForRepair
    $removed=$false
    foreach($attempt in 1..6){
      try{
        Remove-Item -LiteralPath $venv -Recurse -Force -ErrorAction Stop
        $removed=$true
        break
      }catch{
        Start-Sleep -Milliseconds (150*$attempt)
      }
    }
    if(-not $removed){throw 'Could not remove the incomplete local Python environment.'}
  }else{
    Write-Host 'Creating isolated One-Click Python environment...'
  }

  & $pythonExe @pythonPrefix -m venv $venv
  if($LASTEXITCODE -ne 0){throw 'Could not create the local Python environment.'}
  Remove-Item -LiteralPath (Join-Path $runtime '.relay-paused') -Force -ErrorAction SilentlyContinue
}

if(-not(Test-OneClickVenv)){throw 'The One-Click Python environment is incomplete after repair.'}

# The consumer runtime intentionally has zero third-party pip dependencies.
$requirements=Join-Path $consumerRoot 'requirements.txt'
if(Test-Path -LiteralPath $requirements){
  $thirdParty=@(
    Get-Content -LiteralPath $requirements |
      Where-Object { $_.Trim() -and -not $_.Trim().StartsWith('#') }
  )
  if($thirdParty.Count -gt 0){
    Write-Host 'Installing declared Python dependencies...'
    & $venvPy -m pip install --disable-pip-version-check -r $requirements
    if($LASTEXITCODE -ne 0){throw 'Could not install required Python dependencies.'}
  }
}

$configDir=Join-Path $env:APPDATA 'GPTWindowsRelayConsumer'
New-Item -ItemType Directory -Force -Path $configDir | Out-Null
$configPath=Join-Path $configDir 'bridge.json'
$consumerSettings=Join-Path $configDir 'consumer-settings.json'
$legacySettings=Join-Path (Join-Path $env:APPDATA 'GPTWindowsRelay') 'consumer-settings.json'
if((-not(Test-Path -LiteralPath $consumerSettings)) -and (Test-Path -LiteralPath $legacySettings)){
  Copy-Item -LiteralPath $legacySettings -Destination $consumerSettings -Force
}
if(Test-Path -LiteralPath $configPath){
  $cfg=Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
  $token=[string]$cfg.token
  $port=[int]$cfg.port
}else{
  $token=(& $venvPy -c "import secrets; print(secrets.token_urlsafe(32))").Trim()
  $port=8767
  @{version=1;host='127.0.0.1';port=$port;token=$token} |
    ConvertTo-Json |
    Set-Content -LiteralPath $configPath -Encoding UTF8
}

$extension=Join-Path $runtime 'extension'
if(-not(Test-Path -LiteralPath (Join-Path $extension 'manifest.json'))){throw 'Relay browser extension is missing.'}
# Do not mutate tracked extension sources in a Git checkout. browser_manager.py
# creates a browser-specific local copy and overlays canonical content there.

function Relay-Online {
  try{
    $headers=@{'X-GPT-Windows-Relay-Token'=$token}
    $s=Invoke-RestMethod -Uri ('http://127.0.0.1:'+$port+'/status') -Headers $headers -TimeoutSec 1
    return ($s.ok -eq $true)
  }catch{return $false}
}

if(-not(Relay-Online)){
  $run=Join-Path $runtime 'run-consumer.ps1' # GPT_CONSUMER_DEDICATED_RUNNER_V1
  $argumentLine='-NoProfile -ExecutionPolicy Bypass -File "'+$run+'"'
  Start-Process powershell.exe -WindowStyle Hidden -ArgumentList $argumentLine | Out-Null
  $online=$false
  foreach($i in 1..40){
    Start-Sleep -Milliseconds 250
    if(Relay-Online){$online=$true;break}
  }
  if(-not $online){throw ('The local GPT Windows Relay did not start from "'+$run+'".')}
}

if(-not(Relay-Online)){throw 'The local GPT Windows Relay is not responding after bootstrap.'}

Write-Host ('ONECLICK_PYTHON_READY=True exe="'+$venvPy+'"')
Write-Host 'ONECLICK_DEPENDENCIES_READY=True external_python_packages=0'
Write-Host ('ONECLICK_RELAY_READY=True port='+$port)
Write-Host 'ONECLICK_BROWSER_POLICY=user_supplied'
Write-Host 'GPT One-Click Go runtime is ready.'
