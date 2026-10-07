param(
  [string]$SignedXpi = (Join-Path $PSScriptRoot 'dist\gpt-windows-relay-signed.xpi'),
  [string]$FirefoxRoot = 'C:\Program Files\Mozilla Firefox'
)
$ErrorActionPreference='Stop'
$extensionId='gpt-windows-relay@local'

if(-not (Test-Path -LiteralPath $SignedXpi)){throw "Signed XPI not found: $SignedXpi"}
if(-not (Test-Path -LiteralPath (Join-Path $FirefoxRoot 'firefox.exe'))){throw "Firefox not found: $FirefoxRoot"}

$dest=Join-Path $PSScriptRoot 'dist\gpt-windows-relay-signed.xpi'
if([IO.Path]::GetFullPath($SignedXpi) -ne [IO.Path]::GetFullPath($dest)){
  Copy-Item -LiteralPath $SignedXpi -Destination $dest -Force
}
$dest=[IO.Path]::GetFullPath($dest)
$installUrl=([Uri]$dest).AbsoluteUri

$dist=Join-Path $FirefoxRoot 'distribution'
New-Item -ItemType Directory -Force -Path $dist | Out-Null
$pol=Join-Path $dist 'policies.json'
$backup=$null

if(Test-Path -LiteralPath $pol){
  $backup=$pol+'.bak-'+(Get-Date -Format yyyyMMddHHmmss)
  Copy-Item -LiteralPath $pol -Destination $backup -Force
  $doc=Get-Content -LiteralPath $pol -Raw | ConvertFrom-Json
}else{
  $doc=[pscustomobject]@{}
}

if(-not $doc.PSObject.Properties['policies']){
  $doc | Add-Member -NotePropertyName policies -NotePropertyValue ([pscustomobject]@{})
}
if($null -eq $doc.policies){
  $doc.policies=[pscustomobject]@{}
}
if(-not $doc.policies.PSObject.Properties['ExtensionSettings']){
  $doc.policies | Add-Member -NotePropertyName ExtensionSettings -NotePropertyValue ([pscustomobject]@{})
}
if($null -eq $doc.policies.ExtensionSettings){
  $doc.policies.ExtensionSettings=[pscustomobject]@{}
}

$entry=[pscustomobject]@{
  installation_mode='force_installed'
  install_url=$installUrl
}
$doc.policies.ExtensionSettings | Add-Member -NotePropertyName $extensionId -NotePropertyValue $entry -Force

$json=$doc | ConvertTo-Json -Depth 50
[IO.File]::WriteAllText($pol,$json,[Text.UTF8Encoding]::new($false))

$verify=Get-Content -LiteralPath $pol -Raw | ConvertFrom-Json
$v=$verify.policies.ExtensionSettings.PSObject.Properties[$extensionId].Value
if($null -eq $v){throw 'Policy verification failed: extension entry missing'}
if([string]$v.installation_mode -ne 'force_installed'){throw 'Policy verification failed: extension is not force_installed'}
if([string]$v.install_url -ne $installUrl){throw 'Policy verification failed: install_url mismatch'}

Write-Output ('POLICY_INSTALLED='+$pol)
if($backup){Write-Output ('POLICY_BACKUP='+$backup)}
Write-Output ('EXTENSION_ID='+$extensionId)
Write-Output ('INSTALLATION_MODE='+$v.installation_mode)
Write-Output ('INSTALL_URL='+$v.install_url)
Write-Output 'EXISTING_POLICIES_PRESERVED=True'
Write-Output 'Restart Firefox once to activate the persistent signed extension.'
