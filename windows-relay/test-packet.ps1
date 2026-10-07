$ErrorActionPreference='Stop'; Set-Location $PSScriptRoot
$py=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'; if(-not(Test-Path $py)){ & .\install.ps1 }
@'
[GPT_WINDOWS_ACTION]
{"version":1,"platform":"windows","action":"EXEC","id":"windows-relay-test-1","session":"default","shell":"powershell","cwd":"%USERPROFILE%","timeout":30,"command":"Write-Output 'Windows relay executor is alive'; Get-Date"}
[/GPT_WINDOWS_ACTION]
'@ | & $py windows_relay.py stdin
