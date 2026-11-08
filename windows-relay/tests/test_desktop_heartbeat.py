"""Static gate for native ChatGPT Windows app canned UIA heartbeat."""
import unittest
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/"tools"/"Send-ChatGPT-DesktopHeartbeat.ps1").read_text(encoding="utf-8")

class DesktopHeartbeatTests(unittest.TestCase):
    def test_scoped_app_and_anchored_document(self):
        self.assertIn("$proc.ProcessName -ieq 'ChatGPT'",SOURCE)
        self.assertIn("EXPECTED_ONE_CHATGPT_APP_WINDOW_FOUND",SOURCE)
        self.assertIn("EXPECTED_ONE_DOCUMENT_WITH_CANARY_FOUND",SOURCE)
        self.assertIn("COMPOSER_NOT_EMPTY_REFUSE_TO_OVERWRITE_USER_DRAFT",SOURCE)

    def test_ui_gates_before_send(self):
        self.assertIn("Watch-ChatGPT-ActionCandidates.ps1",SOURCE)
        self.assertIn("[GPT_WINDOWS_HEARTBEAT]",SOURCE)
        self.assertIn("pass_percent_if_received",SOURCE)
        self.assertIn("$composer.pattern.SetValue($script:wire)",SOURCE)
        self.assertIn("COMPOSER_CHANGED_BEFORE_SEND",SOURCE)
        self.assertIn("HEARTBEAT_ID_ALREADY_PRESENT_REFUSE_DUPLICATE",SOURCE)
        self.assertIn("$send.pattern.Invoke()",SOURCE)

    def test_no_command_or_clipboard_transport(self):
        for unsafe in ("Invoke-RestMethod","Invoke-WebRequest","Get-Clipboard",
                       "Set-Clipboard","SendKeys","windows_relay.py","/action",
                       "Set-Content","Add-Content","Remove-Item"):
            self.assertNotIn(unsafe,SOURCE)
        self.assertIn("command_execution='NOT_TESTED'",SOURCE)
        self.assertIn("RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND",SOURCE)

if __name__=="__main__":
    unittest.main()
