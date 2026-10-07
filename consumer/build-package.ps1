param(
  [string]$Output = (Join-Path $PSScriptRoot 'dist\GPT-OneClick-Go.zip')
)
$ErrorActionPreference='Stop'
$consumerRoot=$PSScriptRoot
$repoRoot=Split-Path -Parent $consumerRoot
$relay=Join-Path $repoRoot 'windows-relay'
if(-not(Test-Path -LiteralPath $relay)){throw 'windows-relay source folder not found.'}

$dist=Split-Path -Parent $Output
if(-not $dist){$dist=(Get-Location).Path}
New-Item -ItemType Directory -Force -Path $dist | Out-Null

# Never stage beside the output archive. A consumer may have a live installation
# named GPT-OneClick-Go in that directory. Staging there would destroy it.
$buildRoot=Join-Path ([System.IO.Path]::GetTempPath()) ('GPT-OneClick-Go-build-'+[guid]::NewGuid().ToString('N'))
$stage=Join-Path $buildRoot 'GPT-OneClick-Go'
try {
  New-Item -ItemType Directory -Force -Path $stage | Out-Null
  $runtime=Join-Path $stage 'runtime'
  New-Item -ItemType Directory -Force -Path $runtime | Out-Null

  foreach($name in @('GO.bat','bootstrap.ps1','launch_chatgpt.ps1','consumer_app.py','mission_transport.py','control_harness.py','browser_manager.py','recovery_supervisor.py','updater.py','release.json','requirements.txt','README.txt')){
    Copy-Item -LiteralPath (Join-Path $consumerRoot $name) -Destination (Join-Path $stage $name) -Force
  }
  foreach($name in @(
    'windows_relay.py','run.ps1','run-consumer.ps1','content.js','chromium_extension_setup.ps1','firefox_adapter.py','firefox_tab_adapter.ps1','screenshot_capture.ps1',
    'uia_control_action.ps1','uia_text_entry.ps1','windows_tools.py','windows_workflow.py',
    'relay-control.ps1','hud.py'
  )){
    $src=Join-Path $relay $name
    if(Test-Path -LiteralPath $src){Copy-Item -LiteralPath $src -Destination (Join-Path $runtime $name) -Force}
  }
  Copy-Item -LiteralPath (Join-Path $relay 'extension') -Destination (Join-Path $runtime 'extension') -Recurse -Force
  # GPT_CONSUMER_CANONICAL_CONTENT_SOURCE_V1
  # The consumer extension tree is authoritative. Keep runtime/content.js only as
  # a compatibility copy derived from that canonical consumer extension file.
  Copy-Item -LiteralPath (Join-Path $relay 'extension\content.js') -Destination (Join-Path $runtime 'content.js') -Force
  Remove-Item -LiteralPath (Join-Path $runtime 'extension\config.js') -Force -ErrorAction SilentlyContinue

  Remove-Item -LiteralPath $Output -Force -ErrorAction SilentlyContinue
  Compress-Archive -LiteralPath $stage -DestinationPath $Output -CompressionLevel Optimal
} finally {
  Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host ('PACKAGE='+$Output)
Write-Host 'JOB_APPLICATION_MODULES_INCLUDED=False'
