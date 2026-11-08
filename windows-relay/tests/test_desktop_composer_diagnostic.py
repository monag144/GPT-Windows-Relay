"""Guardrails for no-content Windows ChatGPT composer diagnostic."""
from pathlib import Path
import unittest

SRC=(Path(__file__).resolve().parents[1] / "tools" /
     "Inspect-ChatGPT-ComposerState.ps1").read_text(encoding="utf-8")


class DesktopComposerDiagnosticTests(unittest.TestCase):
    def test_only_chatgpt_process(self):
        self.assertIn("$proc.ProcessName -ieq 'ChatGPT'", SRC)
        self.assertIn("ControlType.Edit", SRC)
        self.assertIn("ValuePattern", SRC)

    def test_no_mutation_or_chat_content_output(self):
        for needle in ("Get-Clipboard", "Set-Clipboard", "SetValue(", ".Invoke()",
                       "SendKeys", "Invoke-RestMethod", "Invoke-WebRequest",
                       "Start-Process", "Get-Content", "Add-Content", "Set-Content"):
            self.assertNotIn(needle,SRC)
        self.assertIn("TRIMMED_LENGTH",SRC)
        self.assertIn("MATCHES_COMMON_PLACEHOLDER_WORDING",SRC)
        self.assertIn("NOTE=PLACEHOLDER_LIKE_VALUE_IS_NOT_PROOF_OF_AN_EMPTY_DRAFT",SRC)


if __name__=="__main__":
    unittest.main()
