"""Static acceptance for read-only ChatGPT Windows desktop UIA probe.

Dynamic UIA and composer behavior require native Windows acceptance evidence.
"""
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "tools" / "Inspect-ChatGPT-DesktopTextRoute.ps1"


class DesktopTextRouteProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HERE.read_text(encoding="utf-8")

    def test_scope_is_real_chatgpt_process_only(self):
        self.assertIn("$proc.ProcessName -ieq 'ChatGPT'", self.source)
        self.assertNotIn("-match '(?i)chatgpt'", self.source)

    def test_marker_is_detected_without_printing_chat_text(self):
        self.assertIn("GPT_RELAY_DESKTOP_UIA_PROBE_20261107", self.source)
        self.assertIn("DocumentRange.FindText($marker,$false,$false)", self.source)
        self.assertIn("PROBE_MARKER_IN_TEXT_PATTERN=", self.source)
        self.assertIn("ASSISTANT_MESSAGE_ATTRIBUTION=NOT_YET_PROVEN", self.source)

    def test_no_execution_or_mutation(self):
        self.assertIn("RESULT=PROBE_COMPLETE_NO_RELAY_EXECUTION", self.source)
        for prohibited in ("Invoke-RestMethod", "Invoke-WebRequest", "Set-Clipboard",
                           "Get-Clipboard", "Start-Process", "SetValue(", ".Invoke()",
                           ".SetFocus(", "SendKeys", "GetText(", "Start-Transcript",
                           "Add-Content", "Set-Content"):
            self.assertNotIn(prohibited, self.source)


if __name__ == "__main__":
    unittest.main()
