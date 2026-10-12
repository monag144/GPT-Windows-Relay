# Read-only Windows Relay source/launch identity inspection.
# Does not execute a relay action, bind ownership, print tokens, or change any file.
$ErrorActionPreference = 'Stop'
$relayRoot = Split-Path -Parent $PSScriptRoot
$checkout = Split-Path -Parent $relayRoot
$legacy = Join-Path $env:USERPROFILE 'Downloads\Dev\GPT\Client\Relay'
$mainBuild = Join-Path $env:USERPROFILE 'Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay'
$oldIndicator = 'Downloads\Dev\GPT\Client\Relay'
$newIndicator = 'Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay'
function IdentifySource([string]$commandLine) {
  if([string]::IsNullOrWhiteSpace($commandLine)){return 'UNKNOWN'}
  # Handles Windows command lines and file:/// extension install URLs alike.
  try {$normalized=([Uri]::UnescapeDataString($commandLine)).Replace('/','\')}
  catch {$normalized=$commandLine.Replace('/','\')}
  if($normalized.IndexOf($newIndicator,[StringComparison]::OrdinalIgnoreCase) -ge 0){return 'MAIN_BUILD'}
  if($normalized.IndexOf($oldIndicator,[StringComparison]::OrdinalIgnoreCase) -ge 0){return 'OLD_CLIENT'}
  if($normalized -match 'windows_relay\.py|relay-watchdog|relay-control|run\.ps1|hud\.py'){return 'OTHER_RELAY_PATH'}
  return 'NOT_RELAY'
}
Write-Output '=== GPT WINDOWS RELAY READ-ONLY IDENTITY ==='
Write-Output ('SOURCE_ROOT=' + $relayRoot)
Write-Output ('CHECKOUT_ROOT=' + $checkout)
Write-Output ('MAIN_BUILD_SOURCE_PRESENT=' + (Test-Path -LiteralPath (Join-Path $mainBuild 'windows_relay.py')))
Write-Output ('OLD_CLIENT_PATH_PRESENT=' + (Test-Path -LiteralPath $legacy))
$sourceFile=Join-Path $relayRoot 'windows_relay.py'
if(Test-Path -LiteralPath $sourceFile){
  Write-Output ('MAIN_SOURCE_SHA256=' + (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash)
}
# Compare every critical source element with the old installation, not just the launcher.
# Source hashes prove disk differences; they do not prove which binary Firefox loaded.
$components=@(
  'windows_relay.py','run.ps1','relay-control.ps1','relay-watchdog-loop.ps1',
  'hud.py','START-GPT-WINDOWS-RELAY.bat',
  'extension-persistent/manifest.json','extension-persistent/content.js',
  'extension-persistent/service_worker.js','extension-persistent/popup.js'
)
foreach($relative in $components){
  $mainItem=Join-Path $mainBuild $relative
  $oldItem=Join-Path $legacy $relative
  $mainPresent=Test-Path -LiteralPath $mainItem -PathType Leaf
  $oldPresent=Test-Path -LiteralPath $oldItem -PathType Leaf
  $same='UNVERIFIED'
  if($mainPresent -and $oldPresent){
    $mainHash=(Get-FileHash -LiteralPath $mainItem -Algorithm SHA256).Hash
    $oldHash=(Get-FileHash -LiteralPath $oldItem -Algorithm SHA256).Hash
    $same=if($mainHash -eq $oldHash){'IDENTICAL'}else{'DIFFERENT'}
  }elseif(-not $oldPresent){$same='OLD_MISSING'}
  elseif(-not $mainPresent){$same='MAIN_MISSING'}
  Write-Output ('SOURCE_COMPONENT=' + $relative + ' MAIN_PRESENT=' + $mainPresent + ' OLD_PRESENT=' + $oldPresent + ' COMPARISON=' + $same)
}

try {
  $git = Get-Command git.exe -ErrorAction Stop
  $head=(& $git.Source -C $checkout rev-parse HEAD 2>$null)
  $branch=(& $git.Source -C $checkout branch --show-current 2>$null)
  $dirty=@(& $git.Source -C $checkout status --porcelain 2>$null)
  Write-Output ('GIT_HEAD=' + $head)
  Write-Output ('GIT_BRANCH=' + $branch)
  Write-Output ('GIT_DIRTY_ENTRY_COUNT=' + $dirty.Count)
} catch { Write-Output 'GIT_IDENTITY=UNAVAILABLE' }
$cfg=Join-Path $env:APPDATA 'GPTWindowsRelay\bridge.json'
Write-Output ('BRIDGE_CONFIG_EXISTS=' + (Test-Path -LiteralPath $cfg))
# STOP/OFF markers may explain why a configured watchdog is not recovering.
foreach($entry in @(
  @{label='PAUSED'; name='.relay-paused'},
  @{label='OFF'; name='.relay-off'},
  @{label='KILL'; name='.relay-kill'},
  @{label='STARTING'; name='.relay-starting'},
  @{label='KILL_FAILED'; name='.relay-kill-failed'}
)){
  Write-Output ('RELAY_CONTROL_MARKER=' + $entry.label + ' PRESENT=' +
    (Test-Path -LiteralPath (Join-Path $mainBuild $entry.name) -PathType Leaf))
}
# Check available interpreters without launching an installer or changing PATH.
$pythonExe=Join-Path $mainBuild '.venv\Scripts\python.exe'
Write-Output ('RELAY_VENV_PYTHON_PRESENT=' + (Test-Path -LiteralPath $pythonExe -PathType Leaf))
$globalPython=Get-Command python.exe -ErrorAction SilentlyContinue
Write-Output ('SYSTEM_PYTHON_COMMAND_AVAILABLE=' + [bool]$globalPython)
# Never read or print pairing credentials.
$processes=@()
try { $processes=@(Get-CimInstance Win32_Process -ErrorAction Stop) }
catch { Write-Output 'PROCESS_ENUMERATION=UNAVAILABLE' }
try {
  $listeners=@(Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalAddress -eq '127.0.0.1' })
  if($listeners.Count -eq 0){Write-Output 'PORT_8766=NOT_LISTENING'}
  foreach($l in $listeners){
    $proc=@($processes | Where-Object { $_.ProcessId -eq $l.OwningProcess } | Select-Object -First 1)
    $cmd=if($proc.Count){[string]$proc[0].CommandLine}else{''}
    Write-Output ('PORT_8766=LISTENING PID=' + $l.OwningProcess + ' SOURCE=' + (IdentifySource $cmd))
  }
} catch {
  Write-Output ('PORT_8766=UNVERIFIED ' + $_.Exception.GetType().Name)
}
# The separate One-Click Go consumer can use 8767; keep it distinct from Main-Build.
try {
  $consumerListeners=@(Get-NetTCPConnection -LocalPort 8767 -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalAddress -eq '127.0.0.1' })
  if($consumerListeners.Count -eq 0){Write-Output 'PORT_8767_CONSUMER=NOT_LISTENING'}
  foreach($l in $consumerListeners){
    $proc=@($processes | Where-Object { $_.ProcessId -eq $l.OwningProcess } | Select-Object -First 1)
    $cmd=if($proc.Count){[string]$proc[0].CommandLine}else{''}
    Write-Output ('PORT_8767_CONSUMER=LISTENING PID=' + $l.OwningProcess + ' SOURCE=' + (IdentifySource $cmd))
  }
} catch {Write-Output 'PORT_8767_CONSUMER=UNVERIFIED'}
$relayProcesses=@($processes | Where-Object {
  $_.Name -match '^(pythonw?\.exe|powershell\.exe|pwsh\.exe|cmd\.exe)$' -and
  [string]$_.CommandLine -match 'windows_relay\.py|relay-control|relay-watchdog|hud\.py|GPTWindowsRelay'
})
Write-Output ('RELAY_PROCESS_CANDIDATES=' + $relayProcesses.Count)
foreach($p in $relayProcesses){
  Write-Output ('RELAY_PROCESS PID=' + $p.ProcessId + ' NAME=' + $p.Name + ' SOURCE=' + (IdentifySource ([string]$p.CommandLine)))
}
try {
  $tasks=@(Get-ScheduledTask -ErrorAction Stop)
  $found=0
  foreach($t in $tasks){
    foreach($a in @($t.Actions)){
      $command=[string]$a.Execute+' '+[string]$a.Arguments
      if($command -match 'GPTWindowsRelay|GPT-Windows-Relay|windows_relay\.py|relay-watchdog|relay-control|GPT\\Client\\Relay'){
        $found++
        $actionExe=[IO.Path]::GetFileName(([string]$a.Execute).Trim('"'))
        $state=if($null -ne $t.State){[string]$t.State}else{'UNKNOWN'}
        Write-Output ('RELAY_TASK NAME=' + $t.TaskName + ' SOURCE=' + (IdentifySource $command) +
          ' STATE=' + $state + ' EXE=' + $actionExe +
          ' TRIGGER_COUNT=' + @($t.Triggers).Count)
      }
    }
  }
  Write-Output ('RELAY_SCHEDULED_ACTION_COUNT=' + $found)
} catch {Write-Output 'SCHEDULED_TASK_INSPECTION=UNAVAILABLE'}
foreach($key in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\Microsoft\Windows\CurrentVersion\Run')){
  try {
    $values=Get-ItemProperty -LiteralPath $key -ErrorAction Stop
    foreach($prop in $values.PSObject.Properties){
      if($prop.Name -match '^PS'){continue}
      $value=[string]$prop.Value
      if($value -match 'GPTWindowsRelay|GPT-Windows-Relay|windows_relay\.py|relay-watchdog|GPT\\Client\\Relay'){
        $targetType=if($value -match 'relay-watchdog-loop\.ps1'){'WATCHDOG_LOOP'}
          elseif($value -match 'relay-control\.ps1'){'CONTROLLER'}
          elseif($value -match 'run\.ps1'){'SUPERVISOR'}
          elseif($value -match 'windows_relay\.py'){'BACKEND'}
          else{'UNIDENTIFIED_RELAY_TARGET'}
        Write-Output ('RELAY_STARTUP_ENTRY KEY=' + $key + ' NAME=' + $prop.Name +
          ' SOURCE=' + (IdentifySource $value) + ' TARGET=' + $targetType)
      }
    }
  }catch{}
}
$firefox=@(Get-Process -Name firefox -ErrorAction SilentlyContinue)
Write-Output ('FIREFOX_PROCESS_COUNT=' + $firefox.Count)
# These are on-disk extension registration hints, NOT proof of loaded browser code.
# Never emit browser profile paths, private addon metadata, or pairing secrets.
$ffProfiles=Join-Path $env:APPDATA 'Mozilla\Firefox\Profiles'
$matchingAddonRecords=0
if(Test-Path -LiteralPath $ffProfiles){
  try {
    foreach($ffProfileEntry in @(Get-ChildItem -LiteralPath $ffProfiles -Directory -ErrorAction Stop)){
      $extRegistry=Join-Path $ffProfileEntry.FullName 'extensions.json'
      if(-not (Test-Path -LiteralPath $extRegistry)){continue}
      try {
        $registry=Get-Content -LiteralPath $extRegistry -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        foreach($addon in @($registry.addons)){
          $addonId=[string]$addon.id
          $addonName=[string]$addon.defaultLocale.name
          if($addonId -ne 'gpt-windows-relay@local' -and
             $addonName -notmatch '^GPT (Windows Relay|One-Click Go Relay)$'){continue}
          $matchingAddonRecords++
          $addonPath=[string]$addon.path
          if(-not $addonPath){$addonPath=[string]$addon.rootURI}
          $sourceLabel=IdentifySource $addonPath
          if($sourceLabel -eq 'NOT_RELAY'){$sourceLabel='PROFILE_OR_PACKAGED_EXTENSION'}
          $packageParity='UNKNOWN'
          $canonicalSigned=Join-Path $mainBuild 'dist\gpt-windows-relay-signed.xpi'
          if(($addonPath -like '*.xpi') -and (Test-Path -LiteralPath $addonPath -PathType Leaf) -and
             (Test-Path -LiteralPath $canonicalSigned -PathType Leaf)){
            try {
              $installedDigest=(Get-FileHash -LiteralPath $addonPath -Algorithm SHA256).Hash
              $canonicalDigest=(Get-FileHash -LiteralPath $canonicalSigned -Algorithm SHA256).Hash
              $packageParity=if($installedDigest -eq $canonicalDigest){'IDENTICAL'}else{'DIFFERENT'}
            }catch{$packageParity='HASH_UNAVAILABLE'}
          }
          Write-Output ('FIREFOX_ADDON_REGISTRATION ID=' + $addonId + ' VERSION=' + [string]$addon.version +
            ' ACTIVE_IN_REGISTRY=' + [string]$addon.active + ' SOURCE=' + $sourceLabel +
            ' SIGNED_XPI_PARITY=' + $packageParity)
        }
      } catch {Write-Output 'FIREFOX_ADDON_REGISTRY_PARSE=UNAVAILABLE'}
    }
  } catch {Write-Output 'FIREFOX_ADDON_REGISTRY_SCAN=UNAVAILABLE'}
}
Write-Output ('FIREFOX_MATCHING_ADDON_REGISTRATIONS=' + $matchingAddonRecords)
$firefoxExeCandidates=@('C:\Program Files\Mozilla Firefox','C:\Program Files (x86)\Mozilla Firefox')
foreach($ffDir in $firefoxExeCandidates){
  $policyFile=Join-Path $ffDir 'distribution\policies.json'
  if(-not (Test-Path -LiteralPath $policyFile)){continue}
  try {
    $pol=Get-Content -LiteralPath $policyFile -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
    $extSettings=$pol.policies.ExtensionSettings
    $target=$null
    if($null -ne $extSettings){
      $p=$extSettings.PSObject.Properties['gpt-windows-relay@local']
      if($null -ne $p){$target=$p.Value}
    }
    if($null -ne $target){
      Write-Output ('FIREFOX_SIGNED_POLICY MODE=' + [string]$target.installation_mode +
        ' INSTALL_SOURCE=' + (IdentifySource ([string]$target.install_url)))
    }else{Write-Output 'FIREFOX_SIGNED_POLICY=NO_RELAY_ENTRY'}
  } catch { Write-Output 'FIREFOX_SIGNED_POLICY=UNREADABLE' }
}
# Relevant Windows shortcuts can still target an outdated Client even when
# the checked-in launcher is self-relative. Resolve them without opening them.
$shortcutGroups=@(
  @{kind='USER_DESKTOP'; path=[Environment]::GetFolderPath('Desktop')},
  @{kind='PUBLIC_DESKTOP'; path=[Environment]::GetFolderPath('CommonDesktopDirectory')},
  @{kind='USER_START_MENU'; path=[Environment]::GetFolderPath('StartMenu')},
  @{kind='COMMON_START_MENU'; path=[Environment]::GetFolderPath('CommonStartMenu')}
)
$shortcuts=0
try {
  $shell=New-Object -ComObject WScript.Shell
  foreach($folder in $shortcutGroups){
    if(-not $folder.path -or -not (Test-Path -LiteralPath $folder.path)){continue}
    foreach($file in @(Get-ChildItem -LiteralPath $folder.path -Filter '*.lnk' -File -Recurse -ErrorAction SilentlyContinue)){
      try {
        $lnk=$shell.CreateShortcut($file.FullName)
        $combined=[string]$lnk.TargetPath+' '+[string]$lnk.Arguments
        if($file.BaseName -notmatch 'GPT.*Relay|Windows.*Relay|Relay.*GPT' -and
           $combined -notmatch 'GPTWindowsRelay|GPT-Windows-Relay|GPT\\Client\\Relay|windows_relay\.py'){continue}
        $shortcuts++
        Write-Output ('RELAY_SHORTCUT LOCATION=' + $folder.kind + ' SOURCE=' + (IdentifySource $combined))
      } catch {}
    }
  }
} catch {Write-Output 'RELAY_SHORTCUT_SCAN=UNAVAILABLE'}
Write-Output ('RELAY_SHORTCUT_COUNT=' + $shortcuts)
Write-Output 'FIREFOX_LOADED_EXTENSION_IDENTITY=UNKNOWN_FROM_PROCESS_INSPECTION'
Write-Output 'FIREFOX_REGISTRATION_IS_NOT_LOADED_CODE_PROOF=True'
Write-Output 'FIREFOX_NEXT_CHECK=about:debugging#/runtime/this-firefox'
Write-Output 'RESULT=READ_ONLY_NO_CHANGES'
