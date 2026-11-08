"""HUD startup should never inherit a hidden startup style."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WATCHDOG=(ROOT/"relay-watchdog-loop.ps1").read_text(encoding="utf-8")
BACKEND=(ROOT/"tools"/"Start-ChatGPT-DesktopBackend.ps1").read_text(encoding="utf-8")

class HUDLaunchVisibilityTests(unittest.TestCase):
    def test_watchdog_launches_visible_hud(self):
        self.assertIn("Start-Process -FilePath $hudPy -WorkingDirectory $root",WATCHDOG)
        self.assertNotIn("Start-Process -FilePath $hudPy -WindowStyle Hidden",WATCHDOG)

    def test_backend_fallback_launches_visible_hud(self):
        self.assertIn("Start-Process -FilePath $hudPython -WorkingDirectory $root",BACKEND)
        self.assertNotIn("Start-Process -FilePath $hudPython -WindowStyle Hidden",BACKEND)

if __name__=="__main__":
    unittest.main()
