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

    def test_placeholder_exception_requires_independent_disabled_send_gate(self):
        # A real message matching placeholder wording must not be overwritten
        # simply because its text looks like the normal editor placeholder.
        self.assertIn("Assert-ComposableEmptyState $window $composer", SOURCE)
        self.assertIn("$trimmed -ceq 'Ask ChatGPT'", SOURCE)
        self.assertIn("Test-DisabledSendControlPresent $window", SOURCE)
        self.assertIn("$composer.node.Current.HasKeyboardFocus", SOURCE)
        self.assertIn("COMPOSER_PLACEHOLDER_AMBIGUOUS_FOCUSED_REFUSE", SOURCE)
        self.assertIn("COMPOSER_PLACEHOLDER_AMBIGUOUS_SEND_STATE_REFUSE", SOURCE)
        self.assertIn("COMPOSER_NOT_EMPTY_REFUSE_TO_OVERWRITE_USER_DRAFT", SOURCE)

    def test_send_attempt_is_reserved_before_side_effect(self):
        mark = SOURCE.index("Write-Output 'UIA_SEND_INVOKE_BEGIN'")
        reserved = SOURCE.index("$script:submitted=$true", mark)
        invoke = SOURCE.index("$send.pattern.Invoke()", mark)
        self.assertLess(reserved, invoke)

    def test_no_command_or_clipboard_transport(self):
        for unsafe in ("Invoke-RestMethod","Invoke-WebRequest","Get-Clipboard",
                       "Set-Clipboard","SendKeys","windows_relay.py","/action",
                       "Set-Content","Add-Content","Remove-Item"):
            self.assertNotIn(unsafe,SOURCE)
        self.assertIn("command_execution='NOT_TESTED'",SOURCE)
        self.assertIn("RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND",SOURCE)

if __name__=="__main__":
    unittest.main()
