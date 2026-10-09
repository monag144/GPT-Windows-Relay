"""Regression: PCE12 handoff must follow the originating ChatGPT tab, not another window."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCEDURE = ROOT / "docs" / "relay-sandwich-procedure.md"
TASKS = ROOT / "windows-relay" / "TASKS.md"


class CurrentChatTabRotationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = (ROOT / 'windows-relay' / 'agent011_current_tab_new_chat.ps1').read_text(encoding='utf-8')
        cls.compat_procedure = PROCEDURE.read_text(encoding="utf-8")
        cls.procedure = cls.compat_procedure + "\n" + (ROOT / "docs" / "architecture" / "CONTRACT_2026-10-09T0636Z_AGENT011_CURRENT_TAB_SEMANTIC_ROTATION.md").read_text(encoding="utf-8")
        cls.tasks = TASKS.read_text(encoding="utf-8")

    def test_actual_worker_proves_current_originating_result(self):
        self.assertIn('function RecentSourceResult', self.worker)
        self.assertIn("LastIndexOf('[GPT_WINDOWS_RESULT]')", self.worker)
        self.assertIn('chunk.Contains($SourcePacketId)', self.worker)
        self.assertIn('CURRENT_RELAY_ORIGINATING_TAB_NOT_PROVEN_NO_UI_EFFECT', self.worker)

    def test_actual_worker_has_exactly_one_semantic_newchat_action(self):
        self.assertEqual(self.worker.count('$button.invoke.Invoke()'), 1)
        self.assertIn('ORIGIN_TAB_SAME_TAB_NEW_CHAT_VERIFIED', self.worker)
        self.assertIn('SAME_TAB_SELECTION_LOST', self.worker)
        self.assertIn('SAME_WINDOW_HANDLE_CHANGED', self.worker)
        self.assertNotIn('--new-window', self.worker)
        self.assertNotIn('--new-tab', self.worker)
        self.assertNotIn('Start-Process', self.worker)

    def test_worker_pastes_and_sends_exactly_once_in_same_originating_tab(self):
        self.assertEqual(self.worker.count("SendWait('^v')"), 1)
        self.assertEqual(self.worker.count('$send[0].invoke.Invoke()'), 1)
        self.assertIn('send_invoked=$false', self.worker)
        self.assertIn('paste_attempted=$false', self.worker)
        self.assertIn('SEMANTIC_NEW_CHAT_CLICK_INTENT_NO_RETRY', self.worker)
        self.assertIn('ONE_ORIGIN_TAB_PASTE_INTENT_NO_RETRY', self.worker)
        self.assertIn('ONE_SAME_ORIGIN_TAB_SEND_INTENT_NO_RETRY', self.worker)
        self.assertIn('PCE12_CURRENT_TAB_USER_MESSAGE_VERIFIED', self.worker)
        self.assertIn('ORIGIN_SELECTION_LOST_BEFORE_COMPOSE', self.worker)
        self.assertIn('ORIGIN_SELECTED_TAB_CHANGED_PRE_SEND', self.worker)
        self.assertNotIn('SetForegroundWindow(', self.worker)

    def test_architecture_contract_is_timestamped_and_compat_pointer_small(self):
        self.assertIn("CONTRACT_2026-10-09T0636Z_AGENT011_CURRENT_TAB_SEMANTIC_ROTATION.md", self.compat_procedure)
        self.assertLessEqual(len(PROCEDURE.read_bytes()), 10240)
        self.assertIn("SAME CURRENT TAB ONLY", self.procedure)

    def test_user_intent_is_same_current_tab(self):
        self.assertIn("SAME CURRENT TAB ONLY", self.procedure)
        self.assertIn("same ChatGPT tab currently originating this relay conversation", self.procedure)
        self.assertIn("THIS CURRENT CHATGPT TAB", self.tasks)

    def test_no_inference_from_tab_count_or_foreground_window(self):
        self.assertIn("11-tab count is **not proof**", self.procedure)
        self.assertIn("assume that the 11-tab window is the invoking tab", self.tasks)

    def test_semantic_new_chat_and_same_tab_send_proven(self):
        self.assertIn("same window HWND and same selected tab", self.procedure)
        self.assertIn("unique **New chat** control", self.procedure)
        self.assertIn("Send **once**", self.procedure)
        self.assertIn("actual **user-role message**", self.procedure)

    def test_previous_other_window_rotators_disabled(self):
        self.assertIn("Do not repeat failed PCE11.074/.076/.083 workers", self.procedure)
        self.assertIn("supersede the distinct-window approach", self.tasks)
        self.assertIn("Do not replay legacy attempts", self.tasks)

    def test_exact_sender_provenance_and_stop_required(self):
        self.assertIn("this exact recent relay action/result exchange", self.procedure)
        self.assertIn("STOP/armed/outbound owner", self.procedure)
        self.assertIn("existing draft", self.procedure)


if __name__ == "__main__":
    unittest.main()
