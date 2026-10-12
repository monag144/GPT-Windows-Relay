# Windows Relay: User-launched, read-only source inventory and optional Codex review.
# Writes reports ONLY under %LOCALAPPDATA%\GPTWindowsRelayAnalyses\OneClick-Dev-Inventory-<date>.
# Does not touch process state, tokens, task scheduler, live relay processes or Dev source.
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$dev=Join-Path $env:USERPROFILE 'Downloads\Dev'
if(-not (Test-Path -LiteralPath $dev -PathType Container)) { Write-Host 'Downloads\Dev not found.'; exit 2 }
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$base=Join-Path $env:LOCALAPPDATA 'GPTWindowsRelayAnalyses'
$out=Join-Path $base ('OneClick-Dev-Inventory-'+$stamp)
New-Item -ItemType Directory -Path $out -Force | Out-Null
$report=Join-Path $out 'DEV_INVENTORY.md'
$listing=Join-Path $out 'file-metadata.csv'
$codexOutput=Join-Path $out 'CODEX_MIGRATION_REVIEW.md'
$codexLog=Join-Path $out 'codex-console.log'
$prompt=Join-Path $out 'codex-prompt.txt'
$maxFiles=50000
$skipNames=@('.git','.hg','.svn','node_modules','.venv','venv','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.tox','.next','.cache','Backups','Backup','backups','backup','.idea','target','obj')
$allowedTop=@('GPT-Windows-Relay-Main-Build','Legacy','Prototype')
$privateFilePattern='(?i)(^|[\\/._-])(bridge\.json|state\.json|token|password|secret|private|credential|\.env|keyfile|user-data|profile)([\\/._-]|$)'
$dirs=@(Get-ChildItem -LiteralPath $dev -Directory -Force | Sort-Object Name)
$topNames=@($dirs | ForEach-Object { $_.Name })
$lines=New-Object System.Collections.Generic.List[string]
$lines.Add('# Downloads Dev - read-only migration inventory')
$lines.Add('Generated: '+(Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))
$lines.Add('Root: '+$dev)
$lines.Add('No Dev source files were modified, moved or deleted.')
$lines.Add('')
$lines.Add('## All top-level folders (actual observation)')
foreach($d in $dirs){ $lines.Add('- `'+$d.Name+'`') }
$lines.Add('')
$lines.Add('## Deviations from the intended organization')
$lines.Add('Allowed labels are a heuristic; the actual historic folder structure may use other names.')
foreach($d in $dirs){ if($allowedTop -notcontains $d.Name){$lines.Add('- Other top-level folder: `'+$d.Name+'`')} }
if($topNames -notcontains 'GPT-Windows-Relay-Main-Build'){$lines.Add('- MAIN BUILD FOLDER MISSING')}
$lines.Add('')
$rows=New-Object 'System.Collections.Generic.List[object]'
$skipped=New-Object 'System.Collections.Generic.List[string]'
$scanCount=0
foreach($d in $dirs){
  if(-not ($d.Name -match '(?i)gpt|relay|legacy|prototype|codex')) {continue}
  $lines.Add('## GPT-related source root: `'+$d.Name+'`')
  $stack=New-Object 'System.Collections.Generic.Stack[System.IO.DirectoryInfo]'
  $stack.Push($d)
  $before=$rows.Count
  while($stack.Count -gt 0 -and $scanCount -lt $maxFiles){
    $item=$stack.Pop()
    $children=@()
    try{$children=@(Get-ChildItem -LiteralPath $item.FullName -Force -ErrorAction Stop)}
    catch{$skipped.Add('Access denied or unreadable: '+$item.FullName.Substring($dev.Length).TrimStart('\'));continue}
    foreach($child in $children){
      if($child.PSIsContainer){
        if(($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $skipNames -contains $child.Name){
          $skipped.Add('Skipped directory: '+$child.FullName.Substring($dev.Length).TrimStart('\'))
          continue
        }
        $stack.Push($child)
      } else {
        $scanCount++
        $relative=$child.FullName.Substring($dev.Length).TrimStart('\')
        if($relative -match $privateFilePattern){$skipped.Add('Redacted private-file path');continue}
        $rows.Add([pscustomobject]@{RelativePath=$relative;Bytes=$child.Length;ModifiedLocal=$child.LastWriteTime.ToString('yyyy-MM-dd HH:mm')})
        if($scanCount -ge $maxFiles){break}
      }
    }
  }
  $lines.Add('- Indexed non-private files: '+($rows.Count-$before))
  if($d.Name -eq 'GPT-Windows-Relay-Main-Build'){
    foreach($name in @('windows-relay\windows_relay.py','windows-relay\hud.py','windows-relay\relay-control.ps1','windows-relay\relay-watchdog-loop.ps1','windows-relay\START-GPT-WINDOWS-RELAY.bat','windows-relay\extension-persistent\manifest.json','consumer\control_harness.py')){
      $status=if(Test-Path -LiteralPath (Join-Path $d.FullName $name) -PathType Leaf){'PRESENT'}else{'MISSING'}
      $lines.Add('- '+$status+': `'+$name+'`')
    }
  }
  $lines.Add('')
}
$rows | Export-Csv -LiteralPath $listing -NoTypeInformation -Encoding UTF8
$lines.Add('## Inventory coverage')
$lines.Add('- Total indexed files: '+$rows.Count)
$lines.Add('- Directory traversal/file count limit: '+$maxFiles)
$lines.Add('- Excluded generated/cache/backup directories: '+$skipped.Count)
$lines.Add('- Sensitive-looking file paths are redacted from reports and excluded from file metadata.')
$lines.Add('- This inventory alone is not a content migration certification.')
$lines.Add('')
$lines.Add('## Existing Codex worker guard')
$runCodex=$true
try{
  $active=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.Name -match '^(codex|codex-cli)(\.exe)?$' -or [string]$_.CommandLine -match 'run-codex\.ps1|run-index\.ps1|codex(?:-cli)?\.js|@openai[/\\]codex' })
  if($active.Count -gt 0){$lines.Add('- Codex/related worker currently running: '+$active.Count+'; NOT starting another.');$runCodex=$false}
} catch{$lines.Add('- Could not verify running Codex workers. For safety, NOT starting another.');$runCodex=$false}
$prior=Join-Path $env:LOCALAPPDATA 'GPTWindowsRelayDeployBackups\PCE17-022-CodexCutover'
if((Test-Path -LiteralPath (Join-Path $prior 'run-codex.ps1')) -or (Test-Path -LiteralPath (Join-Path $prior 'codex-output.log'))){
  $lines.Add('- Earlier PCE17.022 Codex artifacts present. For safety, NOT starting another Codex session.')
  $runCodex=$false
}
$codex=Get-Command codex -ErrorAction SilentlyContinue
if(-not $codex){$lines.Add('- Codex CLI unavailable. Baseline inventory finished; no Codex session launched.');$runCodex=$false}
$lines.Add('')
$lines.Add('## Codex result')
Set-Content -LiteralPath $report -Value $lines -Encoding UTF8
$instructions=@'
You are Codex CLI reviewing a Windows developer directory migration. This is strictly a READ-ONLY audit.
Inspect C:\Users\Craig Morgan\Downloads\Dev and its GPT-related folders only. The intended authoritative development build is GPT-Windows-Relay-Main-Build. Legacy and Prototype are archival. The historic Dev\GPT folder may contain unmigrated source, tests, documents or scripts.
1. Enumerate ALL top-level folders in Downloads\Dev, including any unexpected other GPT or relay trees. Create a useful path index of GPT-related source to depth 4, avoiding repeated cache/backup/venv/git trees.
2. Determine whether relevant legacy Dev\GPT code, project docs, tests, HUD, browser extension, CMD/PowerShell launchers and production runtime features have corresponding up-to-date code in the main build. Compare content by safe source hashes and bounded textual diffs, not filenames alone.
3. Explicitly distinguish historical/backup files that should be retained but not migrated into active sources. The one authoritative target is GPT-Windows-Relay-Main-Build\windows-relay plus its related consumer/ and docs/ trees.
4. Summarize missing, divergent, redundant, and safely archiveable items, with exact relative paths (no credential/profile/token content). List the unexpected top-level folders.
5. Report MIGRATION_VERDICT COMPLETE, PARTIAL or UNVERIFIED, with supporting evidence and next suggested actions. Do not move or delete anything.
Privacy: do not open credential stores, .env, bridge.json, state.json, browser profiles, passwords, secrets, token files or private/personal documents. Do not print secrets.
SAFETY: DO NOT modify any file, start/stop a relay, restart any process, change Firefox, run tests which mutate files, call network services, update GitHub, delete archives or install software. Source reading only.
'@
Set-Content -LiteralPath $prompt -Value $instructions -Encoding UTF8
if($runCodex){
  Write-Host 'Running Codex in read-only sandbox. This may take several minutes.'
  try{
    $cmd=$codex.Source
    Get-Content -LiteralPath $prompt -Raw | & $cmd exec --cd $dev --sandbox read-only --skip-git-repo-check --output-last-message $codexOutput - *>&1 | Out-File -LiteralPath $codexLog -Encoding UTF8
    $rc=$LASTEXITCODE
    Add-Content -LiteralPath $report -Value ('- Codex exit code: '+$rc)
    Add-Content -LiteralPath $report -Value ('- Codex report path: '+$codexOutput)
    if($rc -ne 0){Write-Host ('Codex exited with code '+$rc+'. Baseline inventory remains available.')}
  }catch{
    Add-Content -LiteralPath $report -Value ('- Codex invocation error: '+$_.Exception.GetType().Name)
    Write-Host 'Codex did not complete. Baseline inventory remains available.'
  }
}else{
  Add-Content -LiteralPath $report -Value '- Codex launch skipped for safety/availability; baseline inventory completed.'
}
Write-Host 'Inventory report:' $report
Write-Host 'File metadata:' $listing
if(Test-Path -LiteralPath $codexOutput){Write-Host 'Codex migration report:' $codexOutput}
Write-Host 'NO DEV SOURCE CHANGES MADE'
exit 0
