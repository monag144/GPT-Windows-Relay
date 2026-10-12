"""Source checks for the read-only Windows Relay identity diagnostic."""
from pathlib import Path
import unittest
import os
import shutil
import subprocess

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "Inspect-Relay-Runtime-Identity.ps1"

class RuntimeIdentityDiagnosticTests(unittest.TestCase):
    def test_diagnostic_is_read_only_and_does_not_print_tokens(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Get-NetTCPConnection", source)
        self.assertIn("Get-CimInstance", source)
        self.assertIn("Get-ScheduledTask", source)
        self.assertIn("Get-FileHash", source)
        self.assertIn("SOURCE_COMPONENT=", source)
        self.assertIn("FIREFOX_ADDON_REGISTRATION", source)
        self.assertIn("FIREFOX_SIGNED_POLICY", source)
        self.assertIn("SIGNED_XPI_PARITY=", source)
        self.assertIn("gpt-windows-relay-signed.xpi", source)
        self.assertIn("RELAY_SHORTCUT", source)
        self.assertIn("FIREFOX_REGISTRATION_IS_NOT_LOADED_CODE_PROOF=True", source)
        self.assertIn("PROFILE_OR_PACKAGED_EXTENSION", source)
        self.assertIn("IdentifySource", source)
        self.assertIn("FIREFOX_LOADED_EXTENSION_IDENTITY=UNKNOWN", source)
        self.assertIn("RESULT=READ_ONLY_NO_CHANGES", source)
        for forbidden in ("Start-Process", "Stop-Process", "taskkill ", "Remove-Item ", "Set-Content ", "Invoke-RestMethod", "Invoke-WebRequest", "Get-Content -LiteralPath $cfg", "Set-ItemProperty", "CreateTextFile", "Start-Sleep"):
            self.assertNotIn(forbidden, source)

    def test_firefox_addon_regex_is_contiguous_and_footer_is_at_end(self):
        source = SCRIPT.read_text(encoding="utf-8")
        lines = source.splitlines()
        self.assertIn("             $addonName -notmatch '^GPT (Windows Relay|One-Click Go Relay)
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("$registry |", source)
        self.assertNotIn("Write-Output $registry", source)
        self.assertNotIn("Write-Output $addonPath", source)
        self.assertNotIn("Write-Output $combined", source)
        self.assertIn("SOURCE=", source)

if __name__ == "__main__":
    unittest.main()
){continue}", lines)
        self.assertEqual(source.count("RESULT=READ_ONLY_NO_CHANGES"), 1)
        self.assertEqual(source.count("FIREFOX_REGISTRATION_IS_NOT_LOADED_CODE_PROOF=True"), 1)
        self.assertEqual(lines[-1], "Write-Output 'RESULT=READ_ONLY_NO_CHANGES'")
        addon_index = next(i for i, line in enumerate(lines) if "$addonName -notmatch " in line)
        self.assertIn("){continue}", lines[addon_index])
        self.assertNotIn("Write-Output", lines[addon_index])

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"),
                         "Windows PowerShell parser is required")
    def test_native_powershell_parser_reports_zero_errors(self):
        """Parse the entire script as PowerShell without executing it."""
        quoted_path = str(SCRIPT).replace("'", "''")
        command = (
            "$tokens=$null; $errors=$null; "
            "[System.Management.Automation.Language.Parser]::ParseFile('"
            + quoted_path + "',[ref]$tokens,[ref]$errors) | Out-Null; "
            "if($errors.Count -gt 0){$errors | ForEach-Object { Write-Output $_.ToString() }; exit 1}; "
            "Write-Output 'POWERSHELL_PARSE_OK'"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=30, check=False
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("POWERSHELL_PARSE_OK", result.stdout)

    def test_diagnostic_has_no_sensitive_debug_output(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("$registry |", source)
        self.assertNotIn("Write-Output $registry", source)
        self.assertNotIn("Write-Output $addonPath", source)
        self.assertNotIn("Write-Output $combined", source)
        self.assertIn("SOURCE=", source)

if __name__ == "__main__":
    unittest.main()
