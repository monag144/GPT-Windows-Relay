param(
  [Parameter(Mandatory=$true)][string]$BrowserExe,
  [Parameter(Mandatory=$true)][string]$ProfilePath,
  [Parameter(Mandatory=$true)][string]$ExtensionPath,
  [string]$Url='https://chatgpt.com/'
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'

if(-not(Test-Path -LiteralPath $BrowserExe)){throw 'Browser executable not found.'}
if(-not(Test-Path -LiteralPath (Join-Path $ExtensionPath 'manifest.json'))){throw 'Prepared extension is missing manifest.json.'}
New-Item -ItemType Directory -Force -Path $ProfilePath | Out-Null

$ProfilePath=[IO.Path]::GetFullPath($ProfilePath)
$browserName=[IO.Path]::GetFileName($BrowserExe)
$activePort=Join-Path $ProfilePath 'DevToolsActivePort'
$profileArg='--user-data-dir="'+$ProfilePath.Replace('"','\"')+'"'
$legacyBrokenProfile=$null
if($ProfilePath.Contains(' ')){
  $legacyBrokenProfile='--user-data-dir='+$ProfilePath.Substring(0,$ProfilePath.IndexOf(' '))
}

function Get-OneClickProfileProcesses {
  @(
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object {
        if($_.Name -ine $browserName -or -not $_.CommandLine){return $false}
        $full=$_.CommandLine.IndexOf($ProfilePath,[StringComparison]::OrdinalIgnoreCase) -ge 0
        $legacy=$false
        if($legacyBrokenProfile){
          $legacy=$_.CommandLine.IndexOf($legacyBrokenProfile,[StringComparison]::OrdinalIgnoreCase) -ge 0
        }
        $full -or $legacy
      }
  )
}

function Stop-StaleOneClickBrowserProfile {
  $matches=@(Get-OneClickProfileProcesses)
  foreach($proc in $matches){
    taskkill.exe /PID $proc.ProcessId /T /F | Out-Null
  }
  if($matches.Count -gt 0){
    foreach($i in 1..40){
      Start-Sleep -Milliseconds 200
      if(@(Get-OneClickProfileProcesses).Count -eq 0){break}
    }
  }
  if(@(Get-OneClickProfileProcesses).Count -gt 0){
    throw 'Could not release the dedicated One-Click browser profile.'
  }
}

# Start-Process joins -ArgumentList values into one command line. Any Windows
# profile path containing spaces must therefore be quoted before Chromium sees
# it. This is derived entirely from the runtime-supplied ProfilePath; no Windows
# account name, home directory, or machine-specific path is hardcoded here.
Stop-StaleOneClickBrowserProfile
Remove-Item -LiteralPath $activePort -Force -ErrorAction SilentlyContinue

$browser=$null
$setupSucceeded=$false
try {
  foreach($launchAttempt in 1..2){
    Remove-Item -LiteralPath $activePort -Force -ErrorAction SilentlyContinue
    $browser=Start-Process -FilePath $BrowserExe -ArgumentList @(
      '--no-first-run',
      '--no-default-browser-check',
      '--new-window',
      $profileArg,
      '--remote-debugging-port=0',
      '--enable-unsafe-extension-debugging',
      'about:blank'
    ) -PassThru

    $retryProfile=$false
    foreach($i in 1..80){
      if(Test-Path -LiteralPath $activePort){break}
      if($browser.HasExited){
        if($browser.ExitCode -eq 21 -and $launchAttempt -eq 1){
          $retryProfile=$true
          break
        }
        throw ('Browser exited during automatic extension setup with code '+$browser.ExitCode)
      }
      Start-Sleep -Milliseconds 250
    }

    if($retryProfile){
      Stop-StaleOneClickBrowserProfile
      Start-Sleep -Milliseconds 500
      continue
    }
    if(Test-Path -LiteralPath $activePort){break}
    if($launchAttempt -eq 2){throw 'Browser did not expose the temporary setup channel.'}
    Stop-StaleOneClickBrowserProfile
  }

  if(-not(Test-Path -LiteralPath $activePort)){throw 'Browser did not expose the temporary setup channel.'}

  $lines=@(Get-Content -LiteralPath $activePort)
  if($lines.Count -lt 2){throw 'Browser setup channel metadata is incomplete.'}
  $port=[int]$lines[0]
  $path=[string]$lines[1]

  $ws=[System.Net.WebSockets.ClientWebSocket]::new()
  try {
    $ct=[Threading.CancellationToken]::None
    $ws.ConnectAsync([Uri]('ws://127.0.0.1:'+$port+$path),$ct).GetAwaiter().GetResult() | Out-Null

    function Invoke-Cdp([int]$Id,[string]$Method,[hashtable]$Params,[string]$SessionId=''){
      $request=@{id=$Id;method=$Method;params=$Params}
      if(-not [string]::IsNullOrWhiteSpace($SessionId)){$request.sessionId=$SessionId}
      $payload=$request|ConvertTo-Json -Compress
      $bytes=[Text.Encoding]::UTF8.GetBytes($payload)
      $ws.SendAsync(
        [ArraySegment[byte]]::new($bytes),
        [Net.WebSockets.WebSocketMessageType]::Text,
        $true,
        $ct
      ).GetAwaiter().GetResult() | Out-Null

      while($true){
        $buffer=New-Object byte[] 65536
        $stream=[IO.MemoryStream]::new()
        do {
          $received=$ws.ReceiveAsync([ArraySegment[byte]]::new($buffer),$ct).GetAwaiter().GetResult()
          if($received.MessageType -eq [Net.WebSockets.WebSocketMessageType]::Close){
            throw 'Browser closed the automatic setup channel.'
          }
          $stream.Write($buffer,0,$received.Count)
        } until($received.EndOfMessage)
        $response=[Text.Encoding]::UTF8.GetString($stream.ToArray()) | ConvertFrom-Json
        if([int]$response.id -eq $Id){return $response}
      }
    }

    $resolvedExtension=[string](Resolve-Path -LiteralPath $ExtensionPath)

    # GPT_CHROMIUM_FRESH_UNPACKED_RELOAD_V1
    # Extensions.loadUnpacked may reuse an existing unpacked installation without
    # restarting its MV3 service worker. If that worker predates an update, Chrome
    # can keep executing stale JavaScript even though the files on disk are newer.
    # Remove only the extension whose persisted path exactly matches our prepared
    # One-Click directory, then load that same path fresh.
    $existing=Invoke-Cdp 1 'Extensions.getExtensions' @{}
    if(-not $existing.error){
      foreach($entry in @($existing.result.extensions)){
        $entryPath=[string]$entry.path
        if([string]::IsNullOrWhiteSpace($entryPath)){continue}
        try{$entryFull=[IO.Path]::GetFullPath($entryPath)}catch{$entryFull=$entryPath}
        if($entryFull.TrimEnd('\') -ieq $resolvedExtension.TrimEnd('\')){
          $existingId=[string]$entry.id
          if(-not [string]::IsNullOrWhiteSpace($existingId)){
            $removed=Invoke-Cdp 2 'Extensions.uninstall' @{id=$existingId}
            if($removed.error){
              throw ('Browser could not refresh the existing One-Click extension: '+($removed.error|ConvertTo-Json -Compress))
            }
          }
          break
        }
      }
    }

    $loaded=Invoke-Cdp 3 'Extensions.loadUnpacked' @{path=$resolvedExtension}
    if($loaded.error){
      throw ('Browser rejected automatic extension installation: '+($loaded.error|ConvertTo-Json -Compress))
    }
    $extensionId=[string]$loaded.result.id
    if([string]::IsNullOrWhiteSpace($extensionId)){throw 'Browser did not return an extension id.'}

    $created=Invoke-Cdp 4 'Target.createTarget' @{url=$Url}
    if($created.error -or [string]::IsNullOrWhiteSpace([string]$created.result.targetId)){
      throw 'Browser could not open ChatGPT after extension setup.'
    }

    # GPT_CHROMIUM_POSTLOAD_RELOAD_V1
    $attached=Invoke-Cdp 5 'Target.attachToTarget' @{targetId=[string]$created.result.targetId;flatten=$true}
    if($attached.error -or [string]::IsNullOrWhiteSpace([string]$attached.result.sessionId)){
      throw 'Browser could not attach to ChatGPT for One-Click activation.'
    }
    Start-Sleep -Milliseconds 750
    $reloaded=Invoke-Cdp 6 'Page.reload' @{ignoreCache=$false} ([string]$attached.result.sessionId)
    if($reloaded.error){throw ('Browser could not activate One-Click integration: '+($reloaded.error|ConvertTo-Json -Compress))}

    $targets=Invoke-Cdp 7 'Target.getTargets' @{}
    if(-not $targets.error){
      foreach($target in @($targets.result.targetInfos)){
        if(
          [string]$target.type -eq 'page' -and
          [string]$target.url -eq 'about:blank' -and
          [string]$target.targetId -ne [string]$created.result.targetId
        ){
          try{Invoke-Cdp 8 'Target.closeTarget' @{targetId=[string]$target.targetId}|Out-Null}catch{}
          break
        }
      }
    }
  } finally {
    try{$ws.Dispose()}catch{}
  }

  $setupSucceeded=$true
  [ordered]@{
    ok=$true
    extension_id=$extensionId
    pid=[int]$browser.Id
    profile=[string](Resolve-Path -LiteralPath $ProfilePath)
    extension=[string](Resolve-Path -LiteralPath $ExtensionPath)
    url=$Url
    setup_channel_port=$port
    session_loaded=$true
  } | ConvertTo-Json -Compress
} finally {
  if(-not $setupSucceeded -and $browser -and -not $browser.HasExited){
    taskkill.exe /PID $browser.Id /T /F | Out-Null
  }
}
