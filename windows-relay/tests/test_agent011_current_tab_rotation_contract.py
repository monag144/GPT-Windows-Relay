"""Regression: PCE12 handoff must follow the originating ChatGPT tab, not another window."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCEDURE = ROOT / "docs" / "relay-sandwich-procedure.md"
TASKS = ROOT / "windows-relay" / "TASKS.md"


class CurrentChatTabRotationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.procedure = PROCEDURE.read_text(encoding="utf-8")
        cls.tasks = TASKS.read_text(encoding="utf-8")

    def test_user_intent_is_same_current_tab(self):
        self.assertIn("SAME CURRENT TAB ONLY", self.procedure)
        self.assertIn("same ChatGPT tab currently originating this relay conversation", self.procedure)
        self.assertIn("THIS CURRENT CHATGPT TAB", self.tasks)

    def test_no_inference_from_tab_count_or_foreground_window(self):
        self.assertIn("11-tab count is **not proof**", self.procedure)
        self.assertIn("do not assume that the 11-tab window is the invoking tab", self.tasks)

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
