param(
 [string]$SourceDir = (Join-Path $PSScriptRoot 'extension-persistent'),
 [string]$ArtifactsDir = (Join-Path $PSScriptRoot 'dist\amo-signed')
)
$ErrorActionPreference='Stop'
$manifest=Get-Content -LiteralPath (Join-Path $SourceDir 'manifest.json') -Raw | ConvertFrom-Json
$id=[string]$manifest.browser_specific_settings.gecko.id
$version=[string]$manifest.version
if([string]::IsNullOrEmpty($env:WEB_EXT_API_KEY) -or [string]::IsNullOrEmpty($env:WEB_EXT_API_SECRET)){
 throw 'AMO_SIGNING_CREDENTIALS_MISSING: set WEB_EXT_API_KEY and WEB_EXT_API_SECRET in the automation environment; values are never stored by this script.'
}
$npxCmd=Get-Command npx -ErrorAction SilentlyContinue
if($npxCmd){$npx=$npxCmd.Source}else{
  $candidates=@(
    (Join-Path $env:LOCALAPPDATA 'Programs\nodejs\npx.cmd'),
    'C:\Program Files\nodejs\npx.cmd'
  )
  $npx=$null
  foreach($c in $candidates){if(Test-Path -LiteralPath $c){$npx=$c;break}}
  if(-not $npx){
    $packages=Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    if(Test-Path -LiteralPath $packages){
      $hit=Get-ChildItem -LiteralPath $packages -Filter 'npx.cmd' -File -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.FullName -like '*OpenJS.NodeJS*'} | Select-Object -First 1
      if($hit){$npx=$hit.FullName}
    }
  }
  if(-not $npx){throw 'NPX_NOT_FOUND: install Node.js LTS before AMO signing.'}
}
New-Item -ItemType Directory -Force -Path $ArtifactsDir | Out-Null
& $npx --yes web-ext sign --source-dir $SourceDir --artifacts-dir $ArtifactsDir --channel unlisted --api-key $env:WEB_EXT_API_KEY --api-secret $env:WEB_EXT_API_SECRET
if($LASTEXITCODE -ne 0){throw ('WEB_EXT_SIGN_FAILED_'+$LASTEXITCODE)}
$xp=@(Get-ChildItem -LiteralPath $ArtifactsDir -Filter '*.xpi' -File | Sort-Object LastWriteTimeUtc -Descending)
if($xp.Count -lt 1){throw 'SIGNED_XPI_NOT_PRODUCED'}
$out=Join-Path $PSScriptRoot 'dist\gpt-windows-relay-signed.xpi'
Copy-Item -LiteralPath $xp[0].FullName -Destination $out -Force
Write-Output ('SIGNED_XPI='+[IO.Path]::GetFullPath($out))
Write-Output ('SOURCE_VERSION='+$version)
Write-Output ('EXTENSION_ID='+$id)
Write-Output 'SIGNING_CHANNEL=unlisted'
