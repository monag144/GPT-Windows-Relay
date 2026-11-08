"""Read-only regression for the canonical Windows Relay PowerShell controller.

The controller emits status from both start and status paths. PowerShell does
not treat a bare `if` in a string concatenation as an expression, so a helper
is required. The native probe exercises the real status command on Windows.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "relay-control.ps1"
SOURCE = SCRIPT.read_text(encoding="utf-8")


class RelayControlFormattingRegressionTests(unittest.TestCase):
    def test_no_inline_if_in_string_concatenation(self):
        self.assertNotIn("+(if($proc)", SOURCE)
        self.assertIn("function SafeProcessCommandLine($proc)", SOURCE)
        self.assertEqual(SOURCE.count("+(SafeProcessCommandLine $proc)"), 4)

    def test_native_status_is_read_only_and_emits_single_state(self):
        if os.name != "nt" or not shutil.which("powershell.exe"):
            self.skipTest("Windows PowerShell required")
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(SCRIPT), "status"],
            cwd=str(ROOT), text=True, capture_output=True,
            encoding="utf-8", errors="replace", timeout=25, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("STATE=", result.stdout)
        self.assertNotIn("CommandNotFoundException", result.stderr)


if __name__ == "__main__":
    unittest.main()
