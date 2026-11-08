"""Static guardrails for the native app UIA detection-only monitor.

Windows UI Automation behavior still requires a Windows acceptance run.
"""
import unittest
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/"tools"/"Watch-ChatGPT-ActionCandidates.ps1").read_text(encoding="utf-8")


class DesktopActionCandidateWatchTests(unittest.TestCase):
    def test_real_chatgpt_app_only(self):
        self.assertIn("$proc.ProcessName -ieq 'ChatGPT'",SOURCE)
        self.assertIn("ControlType.Document",SOURCE)
        self.assertIn("DocumentRange.GetText(-1)",SOURCE)

    def test_full_frames_and_basic_protocol_validation(self):
        self.assertIn("(?m)^[ \\t]*\\[GPT_WINDOWS_ACTION\\]",SOURCE)
        self.assertIn("[regex]::Matches($value,$pattern)",SOURCE)
        self.assertIn("ConvertFrom-Json",SOURCE)
        self.assertIn("command_b64",SOURCE)
        self.assertIn("command_lines",SOURCE)
        self.assertIn("MAX",SOURCE.upper())

    def test_dedupe_and_untrusted_output(self):
        self.assertIn("$seen.Add($key)",SOURCE)
        self.assertIn("BASELINE_UNTRUSTED",SOURCE)
        self.assertIn("NEW_UNTRUSTED",SOURCE)
        self.assertIn("ASSISTANT_AUTHORSHIP_VERIFIED=NO",SOURCE)
        self.assertIn("EXECUTIONS=0",SOURCE)

    def test_never_executes_or_sends_results(self):
        for forbidden in ("Invoke-RestMethod","Invoke-WebRequest","Start-Process",
                          ".Invoke()","SetValue(","Get-Clipboard","Set-Clipboard",
                          "SendKeys","Add-Content","Set-Content","New-Item",
                          "Start-Transcript"):
            self.assertNotIn(forbidden,SOURCE)
        self.assertIn("RESULT=READ_ONLY_DETECTION_COMPLETE",SOURCE)


if __name__=="__main__":
    unittest.main()
