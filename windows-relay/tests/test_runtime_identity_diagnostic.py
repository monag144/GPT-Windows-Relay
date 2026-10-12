"""Read-only Windows Relay diagnostic safety and parser regression tests."""
from pathlib import Path
import os
import shutil
import subprocess
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "Inspect-Relay-Runtime-Identity.ps1"


class RuntimeIdentityDiagnosticTests(unittest.TestCase):
    def test_read_only_contract_and_diagnostic_coverage(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for marker in (
            "Get-NetTCPConnection",
            "Get-CimInstance",
            "Get-ScheduledTask",
            "RELAY_CONTROL_MARKER=",
            "RELAY_VENV_PYTHON_PRESENT=",
            "SYSTEM_PYTHON_COMMAND_AVAILABLE=",
            "PORT_8767_CONSUMER=",
            "TRIGGER_COUNT=",
            "RELAY_STARTUP_ENTRY KEY=",
            "TARGET=' + $targetType",

            "Get-FileHash",
            "SOURCE_COMPONENT=",
            "FIREFOX_ADDON_REGISTRATION",
            "FIREFOX_SIGNED_POLICY",
            "SIGNED_XPI_PARITY=",
            "gpt-windows-relay-signed.xpi",
            "RELAY_SHORTCUT",
            "FIREFOX_REGISTRATION_IS_NOT_LOADED_CODE_PROOF=True",
            "FIREFOX_LOADED_EXTENSION_IDENTITY=UNKNOWN",
            "RESULT=READ_ONLY_NO_CHANGES",
            "IdentifySource",
        ):
            self.assertIn(marker, source)
        for forbidden in (
            "Start-Process", "Stop-Process", "taskkill ", "Remove-Item ",
            "Set-Content ", "Invoke-RestMethod", "Invoke-WebRequest",
            "Get-Content -LiteralPath $cfg", "Set-ItemProperty",
            "CreateTextFile", "Start-Sleep",
        ):
            self.assertNotIn(forbidden, source)

    def test_offline_startup_observability_is_read_only(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Get-NetTCPConnection -LocalPort 8766", source)
        self.assertIn("Get-NetTCPConnection -LocalPort 8767", source)
        self.assertIn("RELAY_CONTROL_MARKER=", source)
        self.assertIn("RELAY_TASK NAME=", source)
        self.assertIn(" STATE=' + $state", source)
        self.assertIn(" TARGET=' + $targetType", source)
        self.assertIn("RELAY_PROCESS_CANDIDATES=", source)
        self.assertNotIn("Register-ScheduledTask", source)
        self.assertNotIn("Unregister-ScheduledTask", source)
        self.assertNotIn("Disable-ScheduledTask", source)

    def test_addon_regex_and_footer_not_corrupted(self):
        source = SCRIPT.read_text(encoding="utf-8")
        lines = source.splitlines()
        addon_line = "             $addonName -notmatch '^GPT (Windows Relay|One-Click Go Relay)$'){continue}"
        self.assertIn(addon_line, lines)
        self.assertEqual(source.count("RESULT=READ_ONLY_NO_CHANGES"), 1)
        self.assertEqual(source.count("FIREFOX_REGISTRATION_IS_NOT_LOADED_CODE_PROOF=True"), 1)
        self.assertEqual(lines[-1], "Write-Output 'RESULT=READ_ONLY_NO_CHANGES'")
        self.assertEqual(lines.count(addon_line), 1)

    def test_does_not_echo_sensitive_browser_or_pairing_data(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "$registry |", "Write-Output $registry", "Write-Output $addonPath",
            "Write-Output $combined", "Write-Output $cfg",
        ):
            self.assertNotIn(forbidden, source)

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"),
                         "Requires Windows PowerShell parser")
    def test_native_powershell_parser_reports_no_errors(self):
        """Uses the actual Windows PowerShell AST parser without running script."""
        script_path = str(SCRIPT).replace("'", "''")
        command = (
            "$tokens=$null; $parseErrors=$null; "
            "[System.Management.Automation.Language.Parser]::ParseFile('"
            + script_path + "', [ref]$tokens, [ref]$parseErrors) | Out-Null; "
            "if($parseErrors.Count -gt 0) { "
            "$parseErrors | ForEach-Object { Write-Output $_.Message }; exit 1 }; "
            "Write-Output 'POWERSHELL_PARSE_OK'"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("POWERSHELL_PARSE_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
