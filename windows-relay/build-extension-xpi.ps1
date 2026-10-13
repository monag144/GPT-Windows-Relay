param([string]$Output = '')
$ErrorActionPreference='Stop'
$src=Join-Path $PSScriptRoot 'extension-persistent'
$manifestPath=Join-Path $src 'manifest.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if($manifest.name -ne 'GPT Windows Relay' -or
   $manifest.browser_specific_settings.gecko.id -ne 'gpt-windows-relay@local'){
  throw 'Persistent Firefox extension identity mismatch; refusing package creation.'
}
$version=[string]$manifest.version
if($version -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$'){throw 'Invalid canonical extension version.'}
# One stable package name prevents old-version artifacts being mistaken for
# the manifest actually packaged. Version is read from source, never hardcoded.
if([string]::IsNullOrWhiteSpace($Output)){
  $Output=Join-Path $PSScriptRoot 'dist\gpt-windows-relay.xpi'
}
$out=[IO.Path]::GetFullPath($Output)
$dir=Split-Path $out -Parent
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$tmp=[IO.Path]::ChangeExtension($out,'.zip')
Remove-Item -LiteralPath $tmp,$out -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $src '*') -DestinationPath $tmp -CompressionLevel Optimal
Move-Item -LiteralPath $tmp -Destination $out -Force
Write-Output ('XPI='+$out)
Write-Output ('SOURCE_VERSION='+$version)
Write-Output 'SOURCE_TREE=extension-persistent'
Write-Output 'LOCAL_BACKUP_CREATED=False'
