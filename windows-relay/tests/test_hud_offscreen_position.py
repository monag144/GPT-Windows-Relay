"""Regression: retain HUD visibility after moving the Windows Relay between PCs."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"hud.py").read_text(encoding="utf-8")

class HUDOffscreenRestoreTests(unittest.TestCase):
    def test_saved_position_is_checked_against_active_windows_monitor(self):
        self.assertIn('u32.MonitorFromPoint',SOURCE)
        self.assertIn('x=max(12,sw-W-18); y=18',SOURCE)
        self.assertIn('HUDPoint(x+W//2,y+COMPACT_H//2)',SOURCE)
        self.assertIn('root.geometry(f"{W}x{COMPACT_H}+{x}+{y}")',SOURCE)

if __name__=="__main__":
    unittest.main()
