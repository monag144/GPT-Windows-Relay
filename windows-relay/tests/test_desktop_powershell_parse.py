"""Native PowerShell parser gate for every critical Windows desktop relay entrypoint.

Existing source-text assertions did not catch malformed quoted expressions
in the HUD recovery path. This suite adds an actual PowerShell AST syntax check
before a launcher is ever exercised. Parsing is read-only and executes no script.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = (
    ROOT / "tools" / "Start-ChatGPT-DesktopBackend.ps1",
    ROOT / "tools" / "Send-ChatGPT-DesktopHeartbeat.ps1",
    ROOT / "tools" / "Run-ChatGPT-DesktopMonitor.ps1",
    ROOT / "tools" / "Get-ChatGPT-DesktopMonitorStatus.ps1",
    ROOT / "relay-control.ps1",
    ROOT / "relay-watchdog-loop.ps1",
)


class DesktopPowerShellSyntaxTests(unittest.TestCase):
    def test_canonical_hud_recovery_source_is_not_garbled(self):
        code = ENTRIES[0].read_text(encoding="utf-8")
        self.assertIn("function Test-CanonicalProcess(", code)
        self.assertIn("$watchdogNames=@(", code)
        self.assertIn("$hudNames=@(", code)
        self.assertNotIn("Has-CanonicalProcess $hud '^python(w)?(.exe)?", code)
        self.assertEqual(code.count("Write-Output 'CANONICAL_BACKEND_READY=TRUE'"), 1)
        self.assertEqual(code.count("Write-Output 'DESKTOP_AUTOMATIC_COMMAND_EXECUTION=DISABLED_PENDING_ASSISTANT_ATTRIBUTION'"), 1)

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "Windows PowerShell parser required")
    def test_windows_powershell_ast_parses_every_entrypoint(self):
        for path in ENTRIES:
            with self.subTest(path=path.name):
                quoted = str(path).replace("'", "''")
                command = (
                    "$tokens=$null; $parseErrors=$null; "
                    "[void][System.Management.Automation.Language.Parser]::ParseFile("
                    + "'" + quoted + "',[ref]$tokens,[ref]$parseErrors); "
                    "foreach($issue in $parseErrors){[Console]::Error.WriteLine($issue.ToString())}; "
                    "if($parseErrors.Count -gt 0){exit 12}"
                )
                result = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    timeout=25, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
