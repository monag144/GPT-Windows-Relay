"""Native desktop launcher must reuse one disarmed canonical backend."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/'tools'/'Start-ChatGPT-DesktopBackend.ps1').read_text(encoding='utf-8')

class DesktopCanonicalBackendTests(unittest.TestCase):
    def test_reuses_canonical_start(self):
        self.assertIn('START-GPT-WINDOWS-RELAY.bat',SCRIPT)
        self.assertIn('127.0.0.1:8766/status',SCRIPT)
        self.assertIn('CANONICAL_BACKEND_READY=TRUE',SCRIPT)
        self.assertIn('NONCANONICAL_BACKEND_LISTENER_REFUSE_MONITOR',SCRIPT)
        self.assertIn('relay-control.ps1',SCRIPT)
        self.assertIn('CANONICAL_HUD=RUNNING',SCRIPT)
        self.assertIn('CANONICAL_HUD=NOT_RUNNING',SCRIPT)
        self.assertIn('relay-watchdog-loop.ps1',SCRIPT)
        self.assertIn('CANONICAL_WATCHDOG=ALREADY_RUNNING',SCRIPT)

    def test_fail_closed_if_preexisting_backend_armed(self):
        self.assertIn('BACKEND_PERSISTED_ARMED_REFUSE_UNVERIFIED_DESKTOP_INPUT',SCRIPT)
        self.assertIn('BACKEND_RUNNING_ARMED_REFUSE_UNVERIFIED_DESKTOP_INPUT',SCRIPT)
        self.assertIn('CANONICAL_BACKEND_STARTED_ARMED_REFUSE_MONITOR',SCRIPT)
        self.assertNotIn('/arm',SCRIPT)
        self.assertNotIn('/action',SCRIPT)
        self.assertNotIn('GPTWindowsRelayConsumer',SCRIPT)

if __name__=='__main__':
    unittest.main()
