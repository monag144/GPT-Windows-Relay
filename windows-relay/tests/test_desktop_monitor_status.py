"""Native ChatGPT desktop monitor singleton status is read-only and scoped."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"tools"/"Get-ChatGPT-DesktopMonitorStatus.ps1").read_text(encoding="utf-8")
LAUNCH=(ROOT/"START-CHATGPT-DESKTOP-RELAY.cmd").read_text(encoding="utf-8")

class DesktopMonitorStatusTests(unittest.TestCase):
    def test_uses_canonical_script_path_and_process_id(self):
        self.assertIn("Run-ChatGPT-DesktopMonitor.ps1",SRC)
        self.assertIn("Get-CimInstance Win32_Process",SRC)
        self.assertIn("StringComparison]::OrdinalIgnoreCase",SRC)
        self.assertIn("DESKTOP_MONITOR=RUNNING PID=",SRC)
        self.assertIn("DESKTOP_MONITOR=STOPPED",SRC)
        self.assertIn("DESKTOP_MONITOR=AMBIGUOUS",SRC)

    def test_launcher_skips_existing_monitor(self):
        self.assertIn('if "%MONITOR_STATUS_RC%"=="10"',LAUNCH)
        self.assertIn("No duplicate window launched.",LAUNCH)

    def test_read_only_and_no_browser_interaction(self):
        for forbidden in ("Invoke-RestMethod","Invoke-WebRequest","Set-Content",
                          "Start-Process","SetValue(","SendKeys",
                          "Get-Clipboard","Set-Clipboard","/action"):
            self.assertNotIn(forbidden,SRC)
        self.assertIn("LOCKED_UNVERIFIED_UIA_ORIGIN",SRC)

if __name__=="__main__":
    unittest.main()
