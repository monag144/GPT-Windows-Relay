"""Source checks for the read-only Windows Relay identity diagnostic."""
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "Inspect-Relay-Runtime-Identity.ps1"

class RuntimeIdentityDiagnosticTests(unittest.TestCase):
    def test_diagnostic_is_read_only_and_does_not_print_tokens(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Get-NetTCPConnection", source)
        self.assertIn("Get-CimInstance", source)
        self.assertIn("Get-ScheduledTask", source)
        self.assertIn("FIREFOX_LOADED_EXTENSION_IDENTITY=UNKNOWN", source)
        self.assertIn("RESULT=READ_ONLY_NO_CHANGES", source)
        for forbidden in ("Start-Process", "Stop-Process", "taskkill ", "Remove-Item ", "Set-Content ", "Invoke-RestMethod", "Invoke-WebRequest", "Get-Content -LiteralPath $cfg"):
            self.assertNotIn(forbidden, source)

if __name__ == "__main__":
    unittest.main()
