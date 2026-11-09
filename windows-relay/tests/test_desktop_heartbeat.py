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
        self.assertIn("Set-ComposerTextBySendInput $window $composer $script:wire",SOURCE)
        self.assertIn("COMPOSER_NOT_FOCUSED_REFUSE_SENDINPUT",SOURCE)
        self.assertIn("COMPOSER_CHANGED_BEFORE_SEND",SOURCE)
        self.assertIn("HEARTBEAT_ID_ALREADY_PRESENT_REFUSE_DUPLICATE",SOURCE)
        self.assertIn("UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN",SOURCE)
        self.assertIn("mouse_event([uint32]0x0002",SOURCE)
        self.assertIn("mouse_event([uint32]0x0004",SOURCE)
        self.assertNotIn("$send.pattern.Invoke()",SOURCE)
        self.assertIn("CHATGPT_NOT_FOREGROUND_REFUSE_INPUT",SOURCE)
        self.assertIn("COMPOSER_CHANGED_BEFORE_MOUSE_CLICK",SOURCE)

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
        mark = SOURCE.index("Write-Output 'UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN'")
        reserved = SOURCE.index("$script:submitted=$true", mark)
        invoke = SOURCE.index("mouse_event([uint32]0x0002", mark)
        self.assertLess(reserved, invoke)

    def test_sender_has_stage_diagnostics_without_payload_echo(self):
        for marker in (
            "SENDER_STAGE=APP_WINDOW_FOUND",
            "SENDER_STAGE=CONVERSATION_ANCHOR_FOUND",
            "SENDER_STAGE=COMPOSER_EMPTY_VERIFIED",
            "SENDER_STAGE=NATIVE_RESULT_BOUND",
            "SENDER_STAGE=INPUT_BEGIN",
            "SENDER_STAGE=INPUT_COMPLETED",
            "SENDER_STAGE=SEND_BUTTON_ENABLED",
            "SENDER_STAGE=CLICK_BEGIN",
            "SENDER_STAGE=CLICK_COMPLETED",
            "SENDER_STAGE=CONFIRMED_IN_CONVERSATION",
        ):
            self.assertIn(marker, SOURCE)

    def test_no_command_or_clipboard_transport(self):
        for unsafe in ("Invoke-RestMethod","Invoke-WebRequest","Get-Clipboard",
                       "Set-Clipboard","windows_relay.py","/action",
                       "Set-Content","Add-Content","Remove-Item"):
            self.assertNotIn(unsafe,SOURCE)
        self.assertIn("command_execution='NOT_TESTED'",SOURCE)
        self.assertIn("RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND",SOURCE)
        self.assertIn("Test-DisabledSendControlPresent $window",SOURCE)
        self.assertIn("GetWindowThreadProcessId",SOURCE)
        self.assertIn("HasKeyboardFocus",SOURCE)
        self.assertIn("CANONICAL_OPERATOR_STOP_ACTIVE",SOURCE)
        self.assertIn("SetForegroundWindow",SOURCE)
        self.assertIn("GetCursorPos",SOURCE)
        self.assertIn("SetCursorPos",SOURCE)
        self.assertIn("SEND_BUTTON_OUTSIDE_CHATGPT_WINDOW_REFUSE",SOURCE)
        self.assertIn("SEND_BUTTON_NOT_ENABLED_REFUSE",SOURCE)
        self.assertIn("Test-OwnHeartbeatDraft",SOURCE)
        self.assertIn("COMPOSER_INPUT=SENDINPUT_UNICODE_ACCEPTED",SOURCE)
        self.assertIn("COMPOSER_SENDINPUT_EVENTS=",SOURCE)
        self.assertNotIn("[System.Windows.Forms.SendKeys]",SOURCE)

if __name__=="__main__":
    unittest.main()
