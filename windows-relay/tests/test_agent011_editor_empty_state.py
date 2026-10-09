"""Source-level and real-PowerShell acceptance for Agent011 placeholder detection.

No browser process, UI automation or message submission occurs in this test.
The exact 12-character Firefox UIA placeholder must not be mistaken for a
user-written draft, while every unknown nonempty value must remain protected.
"""
import base64
import shutil
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "agent011_editor_empty_state.ps1"


class Agent011EmptyEditorContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SCRIPT.read_bytes()
        cls.source = cls.raw.decode("utf-8")

    def test_safe_ascii_source_and_exact_literal_placeholder_only(self):
        self.assertTrue(self.raw.isascii())
        self.assertIn("function Test-Agent011EmptyEditorValue(", self.source)
        self.assertIn("function Test-Agent011DestinationReady(", self.source)
        self.assertIn("'Ask ChatGPT' + [char]10", self.source)
        self.assertIn("[StringComparison]::Ordinal", self.source)
        self.assertNotIn("SetValue(", self.source)
        self.assertNotIn("SendWait(", self.source)
        self.assertNotIn(".Invoke()", self.source)
        self.assertNotIn("Start-Process", self.source)

    def test_destination_identity_and_disabled_send_are_both_required(self):
        self.assertIn("if (-not $HomeIdentityVerified)", self.source)
        self.assertIn("if ($EnabledSendButtonCount -ne 0)", self.source)
        self.assertIn("return (Test-Agent011EmptyEditorValue $Value)", self.source)

    def test_exact_cases_with_real_powershell_without_ui(self):
        powershell = shutil.which("powershell.exe")
        if not powershell:
            self.skipTest("Windows PowerShell not installed")
        snippet = self.source + r"""
$blank=@($null,'',[char]32,[char]9,([char]10),'Ask ChatGPT'+[char]10)
$notBlank=@('Ask ChatGPT','Ask ChatGPT ', 'Ask ChatGPT'+[char]13+[char]10,
 'Ask ChatGPT'+[char]9, 'Ask ChatGPT'+[char]10+'x',
 'ask chatgpt'+[char]10, 'Hello', ' Hello', 'Ask ChatGPT!'+[char]10)
foreach($value in $blank) {
 if(-not (Test-Agent011EmptyEditorValue $value)) { throw 'FALSE_NEGATIVE_EMPTY' }
 if(-not (Test-Agent011DestinationReady $value $true 0)) { throw 'FALSE_NEGATIVE_DESTINATION' }
 if(Test-Agent011DestinationReady $value $false 0) { throw 'IDENTITY_BYPASS' }
 if(Test-Agent011DestinationReady $value $true 1) { throw 'SEND_BUTTON_BYPASS' }
}
foreach($value in $notBlank) {
 if(Test-Agent011EmptyEditorValue $value) { throw 'DRAFT_FALSE_EMPTY' }
 if(Test-Agent011DestinationReady $value $true 0) { throw 'DRAFT_DESTINATION_ACCEPTED' }
}
Write-Output 'AGENT011_EDITOR_PLACEHOLDER_EXACT_ACCEPTANCE_OK'
"""
        encoded = base64.b64encode(snippet.encode("utf-16le")).decode("ascii")
        proc = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=20,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)
        self.assertIn("AGENT011_EDITOR_PLACEHOLDER_EXACT_ACCEPTANCE_OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
