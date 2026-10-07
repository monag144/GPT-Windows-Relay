param(
  [string]$BrowserId = '',
  [string]$Url = 'https://chatgpt.com/'
)
$ErrorActionPreference='Stop'
$consumerRoot=$PSScriptRoot
$repoRoot=Split-Path -Parent $consumerRoot
$runtimeCandidates=@(
  (Join-Path $consumerRoot 'runtime'),
  (Join-Path $repoRoot 'windows-relay')
)
$runtime=$runtimeCandidates | Where-Object { Test-Path -LiteralPath (Join-Path $_ '.venv\Scripts\python.exe') } | Select-Object -First 1
if(-not $runtime){throw 'One-Click Python runtime not found. Run GO.bat first.'}

$python=Join-Path $runtime '.venv\Scripts\python.exe'
$manager=Join-Path $consumerRoot 'browser_manager.py'
if(-not(Test-Path -LiteralPath $manager)){throw 'Browser manager is missing.'}

$args=@($manager,'launch','--url',$Url)
if($BrowserId){$args += @('--browser',$BrowserId)}
& $python @args
if($LASTEXITCODE -ne 0){throw ('Browser launch failed with exit code '+$LASTEXITCODE)}
