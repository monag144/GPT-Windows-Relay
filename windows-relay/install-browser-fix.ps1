param(
  [string]$RelayRoot = (Join-Path $env:USERPROFILE 'Downloads\Dev\GPT\Client\Relay')
)

$ErrorActionPreference='Stop'
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$bundleRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$fixedContent=Join-Path $bundleRoot 'content.js'

if(-not (Test-Path -LiteralPath $fixedContent)){
  throw "Fixed content.js not found beside installer: $fixedContent"
}
if(-not (Test-Path -LiteralPath $RelayRoot)){
  throw "Relay root not found: $RelayRoot"
}

$backupRoot=Join-Path $RelayRoot ("backups\browser-fix-"+$stamp)
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

foreach($tree in @('extension','extension-persistent')){
  $dir=Join-Path $RelayRoot $tree
  $content=Join-Path $dir 'content.js'
  $manifest=Join-Path $dir 'manifest.json'
  $hud=Join-Path $dir 'hud.js'

  if(-not (Test-Path -LiteralPath $dir)){
    throw "Missing extension tree: $dir"
  }
  if(Test-Path -LiteralPath $content){
    Copy-Item -LiteralPath $content -Destination (Join-Path $backupRoot ($tree+'-content.js.bak')) -Force
  }
  if(Test-Path -LiteralPath $manifest){
    Copy-Item -LiteralPath $manifest -Destination (Join-Path $backupRoot ($tree+'-manifest.json.bak')) -Force
  }
  if(Test-Path -LiteralPath $hud){
    Copy-Item -LiteralPath $hud -Destination (Join-Path $backupRoot ($tree+'-hud.js.bak')) -Force
  }

  Copy-Item -LiteralPath $fixedContent -Destination $content -Force

  if(Test-Path -LiteralPath $manifest){
    $m=Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    foreach($cs in @($m.content_scripts)){
      if($null -ne $cs.js){
        $cs.js=@($cs.js | Where-Object { $_ -ne 'hud.js' })
      }
    }
    [IO.File]::WriteAllText(
      $manifest,
      ($m | ConvertTo-Json -Depth 30),
      [Text.UTF8Encoding]::new($false)
    )
  }

  # Preserve hud.js as evidence/backup, but ensure it cannot be loaded by the manifest.
  if(Test-Path -LiteralPath $hud){
    Move-Item -LiteralPath $hud -Destination ($hud+'.disabled-'+$stamp) -Force
  }
}

$live=Join-Path $RelayRoot 'extension\content.js'
$persistent=Join-Path $RelayRoot 'extension-persistent\content.js'
$liveHash=(Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash
$persistentHash=(Get-FileHash -LiteralPath $persistent -Algorithm SHA256).Hash
$liveManifest=Get-Content -LiteralPath (Join-Path $RelayRoot 'extension\manifest.json') -Raw
$persistentManifest=Get-Content -LiteralPath (Join-Path $RelayRoot 'extension-persistent\manifest.json') -Raw
$src=Get-Content -LiteralPath $live -Raw

Write-Host '=== GPT WINDOWS RELAY BROWSER FIX ==='
Write-Host "BACKUP=$backupRoot"
Write-Host "LIVE_SHA256=$liveHash"
Write-Host "PERSISTENT_SHA256=$persistentHash"
Write-Host "CONTENT_FILES_MATCH=$($liveHash -eq $persistentHash)"
Write-Host "EVENT_DRIVEN_SCANNER_V9=$($src.Contains('GPT_WINDOWS_EVENT_DRIVEN_SCANNER_V9'))"
Write-Host "RECOVERY_SCROLL_V1=$($src.Contains('GPT_WINDOWS_RECOVERY_SCROLL_V1'))"
Write-Host "SMART_AUTOSCROLL_V2=$($src.Contains('GPT_WINDOWS_SMART_AUTOSCROLL_V2'))"
Write-Host "ATTEMPT_HISTORY_BOUNDED=$($src.Contains('MAX_ATTEMPTED=256'))"
Write-Host "OBSERVER_RESCAN_REMOVED=$(-not $src.Contains('conversationRoot.querySelectorAll(ASSISTANT_SELECTOR)'))"
Write-Host "LIVE_MANIFEST_HUD_REMOVED=$(-not $liveManifest.Contains('hud.js'))"
Write-Host "PERSISTENT_MANIFEST_HUD_REMOVED=$(-not $persistentManifest.Contains('hud.js'))"
Write-Host "RECOVERY_SCROLL_CALLS=$(([regex]::Matches($src,'scrollIntoView\s*\(')).Count)"
Write-Host "WINDOW_SCROLL_CALLS=$(([regex]::Matches($src,'window\.scroll(?:By|To)\s*\(')).Count)"
Write-Host 'FIX_APPLIED=True'
Write-Host ''
Write-Host 'Next: Firefox -> about:debugging#/runtime/this-firefox -> Reload GPT Windows Relay, then refresh ChatGPT once.'
