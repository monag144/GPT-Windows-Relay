@echo off
setlocal EnableExtensions DisableDelayedExpansion
title PCE12 - Verified New Chat Click
echo PCE12 Windows-only, one-shot New chat recovery
echo No Termux, GitHub Actions, or Windows Relay governance changes.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$raw=[IO.File]::ReadAllText('%~f0'); $marker=':'+'PCE12_EMBEDDED_PS1'; $i=$raw.LastIndexOf($marker); if($i -lt 0){throw 'EMBEDDED_SCRIPT_NOT_FOUND'}; $f=Join-Path $env:TEMP 'PCE12-Verified-NewChat.ps1'; [IO.File]::WriteAllText($f,$raw.Substring($i+$marker.Length),[Text.UTF8Encoding]::new($false)); try { & $f; $rc=if($null -eq $LASTEXITCODE){0}else{$LASTEXITCODE} } finally { Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue }; exit $rc"
set "EXITCODE=%ERRORLEVEL%"
echo.
echo Completed with code %EXITCODE%. Press any key to close.
pause >nul
exit /b %EXITCODE%
:PCE12_EMBEDDED_PS1
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PCE12Input {
 [StructLayout(LayoutKind.Sequential)] public struct Point { public int X; public int Y; }
 [DllImport("user32.dll")] public static extern bool GetCursorPos(out Point p);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,uint data,UIntPtr extra);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr handle);
}
'@
function CursorPosition {
 $p = New-Object PCE12Input+Point
 if(-not [PCE12Input]::GetCursorPos([ref]$p)){throw 'CURSOR_READ_FAILED'}
 return ('{0},{1}' -f $p.X,$p.Y)
}
Write-Host ('CURSOR_BEFORE='+(CursorPosition))
$root=[Windows.Automation.AutomationElement]::RootElement
$windows=$root.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
$hits=New-Object System.Collections.ArrayList
foreach($window in $windows) {
 try {
  if($window.Current.ClassName -ne 'MozillaWindowClass' -or $window.Current.IsOffscreen){continue}
  $desc=$window.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
  foreach($element in $desc) {
   try {
    if($element.Current.Name -cne 'New chat' -or $element.Current.IsOffscreen -or -not $element.Current.IsEnabled){continue}
    $rect=$element.Current.BoundingRectangle
    if($rect.Width -lt 30 -or $rect.Height -lt 12 -or $rect.Left -lt 0 -or $rect.Left -gt 400 -or $rect.Top -lt 80 -or $rect.Top -gt 350){continue}
    $null=$hits.Add([pscustomobject]@{Window=$window; Element=$element; Rect=$rect})
   } catch {}
  }
 } catch {}
}
Write-Host ('NEW_CHAT_VISIBLE_MATCHES='+$hits.Count)
if($hits.Count -ne 1){throw 'ABORT: expected exactly one visible Firefox New chat control; nothing clicked'}
$hit=$hits[0]
$window=$hit.Window
$element=$hit.Element
$rect=$hit.Rect
$x=[int][Math]::Round($rect.Left+$rect.Width/2)
$y=[int][Math]::Round($rect.Top+$rect.Height/2)
$oldTitle=[string]$window.Current.Name
Write-Host ('TARGET_TITLE='+$oldTitle)
Write-Host ('TARGET_CENTER='+$x+','+$y)
$handle=[IntPtr]$window.Current.NativeWindowHandle
if($handle -eq [IntPtr]::Zero){throw 'ABORT: Firefox window handle unavailable'}
[void][PCE12Input]::SetForegroundWindow($handle)
Start-Sleep -Milliseconds 250
if(-not [PCE12Input]::SetCursorPos($x,$y)){throw 'ABORT: cursor move failed'}
Start-Sleep -Milliseconds 160
$position=CursorPosition
Write-Host ('CURSOR_POSITIONED='+$position)
if($position -ne ($x.ToString()+','+$y.ToString())){throw 'ABORT: cursor positioning mismatch'}
$pattern=$null
if($element.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)){
 Write-Host 'CLICK_METHOD=UIA_InvokePattern'
 $pattern.Invoke()
} else {
 Write-Host 'CLICK_METHOD=Verified_Mouse_Center'
 [PCE12Input]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 110
 [PCE12Input]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
Write-Host 'CLICK_DISPATCHED=TRUE'
Start-Sleep -Milliseconds 800
$newTitle=''
try { $newTitle=[string]$window.Current.Name } catch {}
Write-Host ('TITLE_AFTER='+$newTitle)
$proof='UNVERIFIED'
if($newTitle -ne $oldTitle -and $newTitle -match 'ChatGPT'){ $proof='WINDOW_TITLE_CHANGED' }
try {
 $nameCondition=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::NameProperty,'Where should we begin?')
 $welcome=$window.FindAll([Windows.Automation.TreeScope]::Descendants,$nameCondition)
 if($welcome.Count -gt 0){$proof='NEW_CHAT_WELCOME_FOUND'}
} catch {}
Write-Host ('NEW_CHAT_NAVIGATION='+$proof)
Write-Host 'The command was executed outside the relay. No audit gate was altered.'
exit 0
