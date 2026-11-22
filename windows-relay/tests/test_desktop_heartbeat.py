"""Static gate for native ChatGPT Windows app canned UIA heartbeat."""
import unittest
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/"tools"/"Send-ChatGPT-DesktopHeartbeat.ps1").read_text(encoding="utf-8")

class DesktopHeartbeatTests(unittest.TestCase):
    def test_scoped_app_and_anchored_document(self):
        self.assertIn("$proc.ProcessName -ieq 'ChatGPT'",SOURCE)
        self.assertIn("EXPECTED_ONE_CHATGPT_APP_WINDOW_FOUND",SOURCE)
        self.assertIn("EXPECTED_ONE_DOCUMENT_WITH_CANARY_FOUND",SOURCE)
        self.assertIn("EXPECTED_ONE_VISIBLE_CONVERSATION_DOCUMENT_FOUND",SOURCE)
        self.assertIn("if($NativeResultPath){return Get-ConversationDocument $window}",SOURCE)
        self.assertIn("function Wait-ForComposer",SOURCE)
        self.assertIn("COMPOSER_DISCOVERY_TIMEOUT=",SOURCE)
        self.assertIn("COMPOSER_NOT_EMPTY_REFUSE_TO_OVERWRITE_USER_DRAFT",SOURCE)
        self.assertIn("[switch]$ForceClearComposer", SOURCE)
        self.assertIn("COMPOSER_FORCED_CLEAR=COMPLETED", SOURCE)

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
        self.assertIn("COMPOSER_BASELINE=FOCUSED_PLACEHOLDER_WITH_DISABLED_SEND", SOURCE)
        self.assertIn("COMPOSER_PLACEHOLDER_AMBIGUOUS_SEND_STATE_REFUSE", SOURCE)
        self.assertIn("COMPOSER_NOT_EMPTY_REFUSE_TO_OVERWRITE_USER_DRAFT", SOURCE)

    def test_read_only_probe_never_types_or_clicks(self):
        self.assertIn("[switch]$ProbeComposerOnly", SOURCE)
        segment = SOURCE.split("if($ProbeComposerOnly){", 1)[1].split(
            "    Assert-OperatorAllowsDesktopSend", 1
        )[0]
        for marker in ("UIA_COMPOSER_PROBE=READ_ONLY_NO_INPUT",
                       "PROBE_VALUE_CLASS=", "PROBE_TEXT_CLASS=",
                       "PROBE_DISABLED_SEND=", "PROBE_ENABLED_SEND=",
                       "PROBE_UNNAMED_BUTTONS_NEAR_COMPOSER=",
                       "RESULT=COMPOSER_PROBE_COMPLETED_NO_SEND"):
            self.assertIn(marker, segment)
        for operation in ("SetValue(", "SetFocus(", "mouse_event(",
                          "SetCursorPos(", "SendInput(", "TypeUnicode("):
            self.assertNotIn(operation, segment)
        self.assertIn("exit 0", segment)

    def test_placeholder_fallback_requires_independent_empty_text_and_no_send(self):
        helper=SOURCE.split("function Test-ComposerTextPatternEmpty($composer){",1)[1].split(
            "# A UIA Value can contain",1)[0]
        self.assertIn("TextPattern]::Pattern",helper)
        self.assertIn("GetText(-1)",helper)
        self.assertIn("return ($text.Length -eq 0)",helper)
        self.assertIn("catch{return $false}",helper)
        self.assertNotIn("SetValue(",helper)
        self.assertNotIn("SetFocus(",helper)

        predicate=SOURCE.split("function Test-ComposableEmptyState($window,$composer){",1)[1].split(
            "function Assert-ComposableEmptyState(",1)[0]
        self.assertIn("$trimmed -ceq 'Ask ChatGPT'",predicate)
        self.assertIn("if(-not $looksLikeObservedPlaceholder){return $false}",predicate)
        self.assertIn("if(Test-DisabledSendControlPresent $window){return $true}",predicate)
        self.assertIn("if(-not (Test-ComposerTextPatternEmpty $composer)){return $false}",predicate)
        self.assertIn("return ($null -eq (Get-EnabledSend $window))",predicate)
        self.assertLess(predicate.index("Test-ComposerTextPatternEmpty"),
                        predicate.index("Get-EnabledSend"))

        assertion=SOURCE.split("function Assert-ComposableEmptyState($window,$composer){",1)[1].split(
            "function Clear-ComposerForForcedDelivery",1)[0]
        self.assertIn("COMPOSER_NOT_EMPTY_REFUSE_TO_OVERWRITE_USER_DRAFT",assertion)
        self.assertIn("COMPOSER_PLACEHOLDER_AMBIGUOUS_SEND_STATE_REFUSE",assertion)
        self.assertIn("Test-ComposerTextPatternEmpty $composer",assertion)
        self.assertIn("Get-EnabledSend $window",assertion)
        self.assertIn("PLACEHOLDER_WITH_EMPTY_TEXTPATTERN_NO_ENABLED_SEND",assertion)
        self.assertNotIn("SetValue(",assertion)

    def test_probe_skips_canary_detection_and_reports_draft_safe_evidence(self):
        self.assertIn("if($ProbeComposerOnly){",SOURCE)
        self.assertIn("DETECTION=READ_ONLY_UIA_PROBE",SOURCE)
        self.assertIn("PROBE_INDEPENDENT_TEXTPATTERN_EMPTY=",SOURCE)
        self.assertIn("PROBE_EMPTY_VERIFIED=",SOURCE)
        self.assertIn("RESULT=COMPOSER_PROBE_COMPLETED_NO_SEND",SOURCE)
        self.assertIn("$composerCleared=(Test-ComposableEmptyState $window $composer)",SOURCE)

    def test_force_clear_accepts_empty_placeholder_without_mutation(self):
        # FORCE COMMAND previously required UIA Value.Length == 0 even when
        # ChatGPT had already replaced an empty draft with "Ask ChatGPT".
        start = SOURCE.index("function Clear-ComposerForForcedDelivery(")
        end = SOURCE.index("# UIA ValuePattern may normalize", start)
        function = SOURCE[start:end]
        self.assertIn("if(Test-ComposableEmptyState $window $composer){return $composer}", function)
        self.assertIn("if(Test-ComposableEmptyState $window $current){return $current}", function)
        self.assertLess(function.index("if(Test-ComposableEmptyState $window $composer)"),
                        function.index("$composer.pattern.SetValue('')"))
        self.assertNotIn("Write-Output", function)
        self.assertIn("FORCE_CLEAR_REQUIRES_SAVED_NATIVE_RESULT", SOURCE)
        self.assertIn("COMPOSER_FORCED_CLEAR=COMPLETED", SOURCE)

    def test_sendinput_union_uses_native_win32_input_size(self):
        # Win32 INPUT is 40 bytes on x64, 28 on x86.  A union containing
        # KEYBDINPUT only is too small and SendInput returns ERROR 87.
        self.assertIn("public struct MOUSEINPUT", SOURCE)
        self.assertIn("[FieldOffset(0)] public MOUSEINPUT mi;", SOURCE)
        self.assertIn("[FieldOffset(0)] public KEYBDINPUT ki;", SOURCE)
        self.assertIn("Marshal.SizeOf(typeof(INPUT))", SOURCE)
        self.assertIn("$requiredSize=if([IntPtr]::Size -eq 8){40}else{28}", SOURCE)
        self.assertIn("SENDINPUT_STRUCT_SIZE_INVALID=", SOURCE)
        self.assertIn("WIN32_ERROR=", SOURCE)

    def test_send_attempt_is_reserved_before_side_effect(self):
        mark = SOURCE.index("Write-Output 'UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN'")
        reserved = SOURCE.index("$script:submitted=$true", mark)
        invoke = SOURCE.index("mouse_event([uint32]0x0002", mark)
        self.assertLess(reserved, invoke)

    def test_sender_has_stage_diagnostics_without_payload_echo(self):
        for marker in (
            "SENDER_STAGE=APP_WINDOW_FOUND",
            "SENDER_STAGE=CONVERSATION_DOCUMENT_FOUND",
            "SENDER_STAGE=COMPOSER_DISCOVERY_READY",
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
        self.assertNotIn("ShowWindow(",SOURCE)
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
