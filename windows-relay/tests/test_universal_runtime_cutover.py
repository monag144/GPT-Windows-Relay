"""Universal Courier deployment and PowerShell syntax contracts.

No runtime reboot or GUI execution: source checks plus PowerShell AST parsing.
"""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
CUTOVER=(ROOT/"tools"/"Activate-UniversalCourier-PR34.ps1").read_text(encoding="utf-8")
SENDER=(ROOT/"tools"/"Send-Foreground-TextResult.ps1").read_text(encoding="utf-8")
RECONCILE=(ROOT/"tools"/"Reconcile-OriginalDesktopHUD.ps1").read_text(encoding="utf-8")


class UniversalCutoverTests(unittest.TestCase):
    def test_cutover_is_guarded_by_test_pass_and_exact_source_hash(self):
        self.assertIn("SOURCE_HEAD_MISMATCH",CUTOVER)
        self.assertIn("TRACKED_WORKTREE_DIRTY_REFUSE_ACTIVATION",CUTOVER)
        self.assertIn("WIN_RELAY_SUITE_FAILED_NO_RESTART",CUTOVER)
        self.assertIn("CONSUMER_SUITE_FAILED_NO_RESTART",CUTOVER)
        self.assertIn("INFLIGHT_DELIVERY_REFUSE_RESTART",CUTOVER)
        self.assertIn("OLD_NATIVE_STOPPED=TRUE",CUTOVER)
        self.assertIn("NEW_NATIVE_SOURCE_HASH=",CUTOVER)
        self.assertIn("NEW_CANONICAL_HUD_COUNT=1",CUTOVER)
        self.assertIn("NO_MAIN_WORKTREE_MUTATION=TRUE",CUTOVER)
        self.assertIn("AUTO_SEND=OFF_PRIOR_UNSENT_RESULT_REVIEW_REQUIRED_COUNT=",CUTOVER)
        self.assertNotRegex(CUTOVER,r"(?im)^\s*(?:&\s*)?git\s+reset\b")
        self.assertNotRegex(CUTOVER,r"(?im)^\s*(?:&\s*)?git\s+clean\b")
        self.assertNotIn("Remove-Item",CUTOVER)
        self.assertNotIn("taskkill",CUTOVER.lower())

    def test_sender_is_based_on_field_category_not_provider_executable(self):
        self.assertIn("function Get-EditorCategory($target)",SENDER)
        self.assertIn("DESTINATION_CATEGORY=",SENDER)
        self.assertIn("MESSAGE_COMPOSER",SENDER)
        self.assertIn("TEXT_EDITOR",SENDER)
        self.assertNotIn("ProcessName -ieq 'ChatGPT'",SENDER)
        self.assertNotIn("ask chatgpt",SENDER.lower())
        self.assertIn("Test-EditorIsCertainlyEmpty $target",SENDER)
        self.assertIn("OPERATOR_AUTO_SEND_NOT_ARMED",SENDER)
        self.assertIn("[switch]$ManualForceSend",SENDER)

    def test_reconcile_identifies_generic_foreground_transport(self):
        self.assertIn("ORIGINAL_HUD_TRANSPORT=NATIVE_FOREGROUND",RECONCILE)
        self.assertNotIn("ORIGINAL_HUD_TRANSPORT=NATIVE_CHATGPT_APP",RECONCILE)

    @unittest.skipUnless(os.name=="nt" and shutil.which("powershell.exe"),
                         "PowerShell AST parsing requires Windows")
    def test_all_changed_powershell_scripts_parse(self):
        for relative in (
            "tools/Activate-UniversalCourier-PR34.ps1",
            "tools/Send-Foreground-TextResult.ps1",
            "tools/Reconcile-OriginalDesktopHUD.ps1",
        ):
            with self.subTest(relative=relative):
                path=str(ROOT/relative).replace("'","''")
                code=("$tok=$null;$err=$null;"
                      "[void][System.Management.Automation.Language.Parser]::"
                      "ParseFile('"+path+"',[ref]$tok,[ref]$err);"
                      "if($err.Count){$err | ForEach-Object {Write-Output $_.Message};"
                      "exit 1};Write-Output 'AST_OK'")
                result=subprocess.run(
                    ["powershell.exe","-NoProfile","-NonInteractive",
                     "-Command",code],capture_output=True,text=True,
                    encoding="utf-8",errors="replace",timeout=20)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn("AST_OK",result.stdout)


if __name__=="__main__":
    unittest.main()
