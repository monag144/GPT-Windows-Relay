#!/usr/bin/env python3
"""One-shot ENTER-only recovery for the already-pasted PCE14->PCE15 handoff.

No New Chat click, no paste, no clipboard access, no relay modifications,
no arbitrary tab switching, no automatic retry. Requires exact draft readback
in uniquely identified, foregrounded Firefox on blank ChatGPT New Chat home.
"""
import csv
import ctypes
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.home() / "Downloads" / "Dev" / "GPT" / "GPT-Windows-Relay"
TEST = Path.home() / "Downloads" / "Dev" / "GPT" / "Client" / "Relay" / "test"
BASE = "a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a"
PROTECTED = "docs/audits/AUDIT_2026-10-09T0808Z_PCE12_OPERATIONS_010_014.md"
EVIDENCE = "3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab"
HANDOFF = "6afc0bd299eb55e1bb892c086ffb7da7f1ee8e8812740db75e00a01bc3de0615"
SCRIPT = "e2ff24ca5b893fa6259bfdc2000872e581a512c13405cdcd6a9bc1c051b9223a"
PREVIOUS_ID = "PCE14-HANDOFF-TO-PCE15-THIRD-ONE-SHOT-20261009"
ACTION = "PCE14-ENTER-ONLY-EXACT-HANDOFF-ONCE-20261009"
ENTER_INTENT = TEST / "PCE14_TO_PCE15_ENTER_ONLY_ONCE.intent.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "MISSING"


def git(*args):
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=15)
    if p.returncode:
        raise RuntimeError("GIT_" + args[0] + "_FAILED")
    return p.stdout.strip()


PS = r'''
param(
 [Parameter(Mandatory=$true)][string]$HandoffFile,
 [Parameter(Mandatory=$true)][string]$IntentFile,
 [Parameter(Mandatory=$true)][long]$ExpectedHwnd,
 [Parameter(Mandatory=$true)][string]$ExpectedSha
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class PCE14OneEnterWin32 {
  [StructLayout(LayoutKind.Sequential)] public struct Point {public int X;public int Y;}
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool GetCursorPos(out Point pos);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint x,uint y,uint d,uint extra);
}
"@
function CheckForeground {
 if([int64][PCE14OneEnterWin32]::GetForegroundWindow() -ne $ExpectedHwnd){throw 'FOREGROUND_FIREFOX_CHANGED'}
}
function ReadUrl($w) {
 $condition=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::AutomationIdProperty,'urlbar-input')
 $bars=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$condition)
 if($bars.Count -ne 1){throw ('URL_BAR_MATCH_COUNT_'+$bars.Count)}
 $pattern=$null
 if(-not $bars[0].TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)){throw 'URL_VALUE_PATTERN_UNAVAILABLE'}
 return [string]$pattern.Current.Value
}
function IsBlankChatUrl([string]$value){
 return $value -cmatch '^(?:https://)?chatgpt[.]com/?(?:[?][^#]*)?$'
}
function Record([string]$phase,[string]$message='') {
 $o=[ordered]@{id='PCE14-ENTER-ONLY-EXACT-HANDOFF-ONCE-20261009';phase=$phase;handoff_sha256=$ExpectedSha;hwnd=$ExpectedHwnd;detail=$message;independent_user_role_verified=$false}
 if($phase -eq 'ENTER_INTENT_RESERVED'){
  $bytes=[Text.Encoding]::UTF8.GetBytes(($o|ConvertTo-Json -Compress))
  $stream=[IO.File]::Open($IntentFile,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush()}finally{$stream.Dispose()}
 }else{
  if(Test-Path -LiteralPath $IntentFile) {
   # Preserve exclusive intent: only the exact existing one-shot file is updated.
   $existing=Get-Content -LiteralPath $IntentFile -Raw | ConvertFrom-Json
   if($existing.id -ne $o.id){throw 'ENTER_JOURNAL_ID_CHANGED'}
   [IO.File]::WriteAllText($IntentFile,($o|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))
  }
 }
}
if(Test-Path -LiteralPath $IntentFile){throw 'ENTER_ALREADY_ATTEMPTED_NO_REPLAY'}
if((Get-FileHash -LiteralPath $HandoffFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedSha){throw 'HANDOFF_FILE_SHA_CHANGED'}
$text=[IO.File]::ReadAllText($HandoffFile,[Text.UTF8Encoding]::new($false,$true))
if(-not $text.Contains('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]') -or -not $text.Contains('[END_GPT_ENGINEERING_ROTATION_HANDOFF_V1]')){throw 'HANDOFF_MARKERS_MISSING'}
CheckForeground
$wins=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,(New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Window)))
$targets=@()
foreach($w in $wins){
 try{if(-not $w.Current.IsOffscreen -and $w.Current.ClassName -eq 'MozillaWindowClass' -and [int64]$w.Current.NativeWindowHandle -eq $ExpectedHwnd){$targets+=,$w}}catch{}
}
if($targets.Count -ne 1){throw ('EXACT_FIREFOX_WINDOW_COUNT_'+$targets.Count)}
$w=$targets[0]
$tabCond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::TabItem)
$items=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$tabCond)
$walker=[Windows.Automation.TreeWalker]::ControlViewWalker
$selected=@()
foreach($tab in $items) {
 try{
  $p=$walker.GetParent($tab)
  if($null -eq $p -or $p.Current.ControlType -ne [Windows.Automation.ControlType]::Tab -or $p.Current.AutomationId -ne 'tabbrowser-tabs'){continue}
  $sp=$null
  if($tab.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sp) -and $sp.Current.IsSelected){$selected+=,[ordered]@{tab=$tab;pattern=$sp}}
 }catch{}
}
if($selected.Count -ne 1){throw ('SELECTED_CANONICAL_TAB_COUNT_'+$selected.Count)}
$originalUrl=ReadUrl $w
if(-not (IsBlankChatUrl $originalUrl)){throw 'SELECTED_CHATGPT_TAB_NOT_NEW_CHAT_HOME'}
$editCond=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Edit)
$edits=$w.FindAll([Windows.Automation.TreeScope]::Descendants,$editCond)
$matches=@()
foreach($e in $edits){
 try{
  if(-not $e.Current.IsEnabled -or $e.Current.IsOffscreen -or $e.Current.ClassName -ne 'ProseMirror'){continue}
  $vp=$null
  if(-not $e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$vp)){continue}
  if($vp.Current.IsReadOnly){continue}
  if(([string]$vp.Current.Value) -ceq $text){$matches+=,[ordered]@{edit=$e;pattern=$vp}}
 }catch{}
}
if($matches.Count -ne 1){throw ('EXACT_PASTED_HANDOFF_COMPOSER_COUNT_'+$matches.Count)}
$editor=$matches[0].edit
$vp=$matches[0].pattern
$buttons=$w.FindAll([Windows.Automation.TreeScope]::Descendants,(New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button)))
$send=@()
foreach($b in $buttons){
 try{if($b.Current.IsEnabled -and -not $b.Current.IsOffscreen -and ([string]$b.Current.Name) -match '^(?i:Send(?: prompt| message)?)$'){$send+=,$b}}catch{}
}
if($send.Count -ne 1){throw ('ENABLED_SEMANTIC_SEND_CONTROL_COUNT_'+$send.Count)}
$rect=$editor.Current.BoundingRectangle
$winRect=$w.Current.BoundingRectangle
$cx=[int][Math]::Round($rect.Left + $rect.Width/2)
$cy=[int][Math]::Round($rect.Top + $rect.Height/2)
if($rect.Width -lt 200 -or $rect.Height -lt 18 -or $cx -le $winRect.Left -or $cx -ge $winRect.Right -or $cy -le $winRect.Top -or $cy -ge $winRect.Bottom){throw 'EDITOR_BOUNDS_INVALID'}
CheckForeground
$orig=New-Object PCE14OneEnterWin32+Point
[void][PCE14OneEnterWin32]::GetCursorPos([ref]$orig)
try {
 [void][PCE14OneEnterWin32]::SetCursorPos($cx,$cy)
 [PCE14OneEnterWin32]::mouse_event(2,0,0,0,0)
 [PCE14OneEnterWin32]::mouse_event(4,0,0,0,0)
 Start-Sleep -Milliseconds 125
}finally{[void][PCE14OneEnterWin32]::SetCursorPos($orig.X,$orig.Y)}
CheckForeground
if(-not $selected[0].pattern.Current.IsSelected){throw 'TAB_SELECTION_CHANGED_AFTER_COMPOSER_CLICK'}
if((ReadUrl $w) -cne $originalUrl){throw 'TAB_URL_CHANGED_BEFORE_ENTER'}
if(([string]$vp.Current.Value) -cne $text){throw 'COMPOSER_READBACK_CHANGED_BEFORE_ENTER'}
if(-not $editor.Current.HasKeyboardFocus){throw 'EXACT_COMPOSER_KEYBOARD_FOCUS_NOT_CONFIRMED'}
if(Test-Path -LiteralPath $IntentFile){throw 'ENTER_ALREADY_RESERVED_BEFORE_DISPATCH'}
# Durable no-retry reservation directly before the single keyboard effect.
Record 'ENTER_INTENT_RESERVED'
CheckForeground
try{
 [Windows.Forms.SendKeys]::SendWait('{ENTER}')
}catch{
 Record 'ENTER_DISPATCH_UNCERTAIN' ([string]$_.Exception.Message)
 throw
}
Record 'ONE_ENTER_DISPATCHED_RECEIPT_PENDING'
$changed=$false;$cleared=$false
$deadline=[DateTime]::UtcNow.AddSeconds(8)
do{
 Start-Sleep -Milliseconds 150
 try{
  $url=ReadUrl $w
  if($url -match '^(?:https://)?chatgpt[.]com/c/[a-zA-Z0-9-]+'){$changed=$true}
  if([string]::IsNullOrWhiteSpace([string]$vp.Current.Value)){$cleared=$true}
 }catch{}
}while([DateTime]::UtcNow -lt $deadline -and -not ($changed -and $cleared))
$phase=if($changed -and $cleared){'ONE_ENTER_NAVIGATED_COMPOSER_CLEARED_USER_ROLE_STILL_UNVERIFIED'}else{'ONE_ENTER_DISPATCHED_DELIVERY_UNCERTAIN'}
Record $phase
[ordered]@{ok=$true;phase=$phase;enter_count=1;new_chat_url_observed=$changed;composer_cleared=$cleared;independent_user_role_verified=$false;no_retry=$true}|ConvertTo-Json -Compress
'''


def main():
    backup = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GPTWindowsRelay" / "ops" / "GOVSYNC13-AUDIT-RESTORE-20261009-01" / "PCE12_010_014_preserved.md"
    if (git("rev-parse", "HEAD") != BASE
            or git("branch", "--show-current") != "pce11/one-click-go-recovery-and-doc-hygiene"
            or "monag144/gpt-windows-relay" not in git("remote", "get-url", "origin").lower().removesuffix(".git")
            or git("status", "--porcelain", "-uall").splitlines() != ["?? " + PROTECTED]
            or sha(ROOT / PROTECTED) != EVIDENCE or sha(backup) != EVIDENCE):
        raise RuntimeError("CANONICAL_SOURCE_OR_PROTECTED_EVIDENCE_INVALID")
    sys.path.insert(0, str(ROOT))
    from consumer.control_harness import engineering_preflight
    if not engineering_preflight(ROOT, 29, series=14)["ok"]:
        raise RuntimeError("PCE14_GOVERNANCE_PREFLIGHT_FAILED")
    if ENTER_INTENT.exists():
        raise RuntimeError("ENTER_ALREADY_RESERVED_DO_NOT_RETRY")
    handoff = TEST / "Copy Contents.txt"
    original = TEST / "PCE14_TO_PCE15_HANDOFF_ONCE.intent.json"
    if sha(handoff) != HANDOFF or sha(TEST / "Copy-Contents-To-ChatGPT.ps1") != SCRIPT:
        raise RuntimeError("HANDOFF_OR_ORIGINAL_LAUNCHER_CHANGED")
    if not original.is_file():
        raise RuntimeError("PRIOR_WORKER_JOURNAL_NOT_FOUND")
    record = json.loads(original.read_text(encoding="utf-8"))
    if record.get("id") != PREVIOUS_ID:
        raise RuntimeError("WRONG_PREVIOUS_ONE_SHOT")
    allowed = {"SCRIPT_RETURNED_OK_DELIVERY_NOT_INDEPENDENTLY_VERIFIED",
               "SCRIPT_RETURNED_ERROR_SUBMISSION_UNCERTAIN",
               "SCRIPT_OUTCOME_UNCERTAIN"}
    if record.get("phase") not in allowed:
        raise RuntimeError("PREVIOUS_WORKER_NOT_TERMINAL_PHASE_" + str(record.get("phase")))
    if any(p.exists() for p in (ROOT / "windows-relay" / ".relay-paused", TEST.parent / ".relay-paused")):
        raise RuntimeError("OPERATOR_STOP_PRESENT")
    cmd = subprocess.run(["tasklist", "/FI", "PID eq 9544", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=10)
    if cmd.returncode:
        raise RuntimeError("ORIGINAL_WORKER_PROCESS_STATUS_UNKNOWN")
    alive = any(len(row) > 1 and row[1].strip() == "9544" for row in csv.reader(io.StringIO(cmd.stdout)))
    if alive:
        raise RuntimeError("PREVIOUS_WORKER_STILL_RUNNING_NO_PARALLEL_SEND")
    foreground = int(ctypes.windll.user32.GetForegroundWindow())
    ps = "(Get-Process -Name firefox -ErrorAction Stop | Where-Object {$_.MainWindowHandle -ne 0} | Select-Object -First 1).MainWindowHandle"
    fp = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
                        capture_output=True, text=True, timeout=12)
    hwnd = int(fp.stdout.strip()) if fp.returncode == 0 and fp.stdout.strip().isdigit() else 0
    if not hwnd or hwnd != foreground or hwnd != record.get("hwnd"):
        raise RuntimeError("ORIGINAL_FIREFOX_WINDOW_NOT_FOREGROUND")
    # Everything above is read-only. PS file is a temporary executable for exactly one
    # preexisting draft. It creates a journal immediately before pressing one Enter.
    with tempfile.TemporaryDirectory(prefix="pce14_one_enter_") as tmp:
        psfile = Path(tmp) / "one-enter.ps1"
        psfile.write_text(PS, encoding="utf-8")
        p = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(psfile), "-HandoffFile", str(handoff), "-IntentFile",
             str(ENTER_INTENT), "-ExpectedHwnd", str(hwnd), "-ExpectedSha", HANDOFF],
            capture_output=True, text=True, timeout=38,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        stdout = p.stdout.strip().splitlines()
        print("PCE14_ENTER_ONLY_ACTION=" + json.dumps({
            "exit_code": p.returncode,
            "last_stdout": stdout[-1][:800] if stdout else "",
            "journal_reserved": ENTER_INTENT.exists(),
            "journal_phase": (json.loads(ENTER_INTENT.read_text(encoding="utf-8")).get("phase")
                              if ENTER_INTENT.exists() else None),
            "single_enter_only": True,
            "new_chat_or_clipboard_repeated": False,
        }, separators=(",", ":")), flush=True)
        if p.returncode:
            raise RuntimeError("ENTER_ONLY_GUARD_OR_DISPATCH_FAILED:" + p.stderr.strip()[-230:])
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("PCE14_ENTER_ONLY_BLOCKED=" + type(exc).__name__ + ":" + str(exc)[:240], flush=True)
        raise
    finally:
        print("Reply to this with the sandwich technique", flush=True)
