param([string]$Output = (Join-Path $PSScriptRoot 'dist\gpt-windows-relay-0.3.17.xpi'))
$ErrorActionPreference='Stop'
$src=Join-Path $PSScriptRoot 'extension-persistent'
$out=[IO.Path]::GetFullPath($Output)
$dir=Split-Path $out -Parent
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$tmp=[IO.Path]::ChangeExtension($out,'.zip')
Remove-Item $tmp,$out -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $src '*') -DestinationPath $tmp -CompressionLevel Optimal
Move-Item $tmp $out
Write-Output ('XPI='+$out)
