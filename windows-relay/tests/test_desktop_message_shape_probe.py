"""Static safety assertions for the Windows ChatGPT UIA message-shape probe."""
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1] / "tools" / "Inspect-ChatGPT-MessageShape.ps1")


class DesktopMessageShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=SCRIPT.read_text(encoding="utf-8")

    def test_app_scope_and_bounded_examination(self):
        self.assertIn("$proc.ProcessName -ine 'ChatGPT'",self.code)
        self.assertIn("[Math]::Min([int]$nodes.Count,$MaxElements)",self.code)
        self.assertIn("if ($matches -ge 8)",self.code)

    def test_read_only_and_no_raw_content_output(self):
        for forbidden in ("Get-Clipboard","Set-Clipboard","GetText(","Invoke-RestMethod",
                          ".SetValue(",".Invoke()","SendKeys","Set-Content","Add-Content",
                          "Start-Process","[GPT_WINDOWS_ACTION]"):
            self.assertNotIn(forbidden,self.code)
        self.assertIn("ASSISTANT_ORIGIN_PROVEN=NO",self.code)
        self.assertIn("RESULT=STRUCTURE_CAPTURE_ONLY_NO_EXECUTION",self.code)


if __name__=="__main__":
    unittest.main()
