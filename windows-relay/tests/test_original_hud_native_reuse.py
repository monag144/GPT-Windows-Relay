"""Ensure native ChatGPT relay reuses the original top-right HUD exclusively."""
from __future__ import annotations
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUD = (ROOT / "hud.py").read_text(encoding="utf-8")
LAUNCH = (ROOT / "START-CHATGPT-DESKTOP-NATIVE.cmd").read_text(encoding="utf-8")
RECONCILE = (ROOT / "tools" / "Reconcile-OriginalDesktopHUD.ps1").read_text(encoding="utf-8")
NATIVE = (ROOT / "desktop_native_relay.py").read_text(encoding="utf-8")

class OriginalHUDReuseTests(unittest.TestCase):
    def test_existing_top_right_layout_retained(self):
        self.assertIn("W,COMPACT_H,EXPANDED_H=560,184,386", HUD)
        self.assertIn("root.overrideredirect(True)", HUD)
        for label in ("START", "STOP", "RESTART", "OFF", "KILL"):
            self.assertIn("text=\""+label+"\"", HUD)
        self.assertIn("OWNER LOCK: ?", HUD)
        self.assertIn("NATIVE_MODE_FILE", HUD)
        self.assertIn("native_snapshot()", HUD)

    def test_native_status_and_buttons_do_not_touch_browser(self):
        self.assertIn("def native_control(action):", HUD)
        self.assertIn("def native_snapshot():", HUD)
        self.assertIn("if native_mode():", HUD)
        self.assertIn("native_control(action)", HUD)
        self.assertIn("OWNER LOCK: N/A", HUD)
        self.assertIn("if native_mode():return", HUD)
        self.assertIn("native_action=", HUD)
        self.assertIn("choices=(\"run\", \"arm\", \"stop\", \"off\", \"restart\", \"kill\"", NATIVE)

    def test_native_hud_exposes_blocked_sender_without_new_window(self):
        self.assertIn("delivery_blocked=bool(report.get('delivery_blocked'))", HUD)
        self.assertIn("DELIVERY BLOCKED", HUD)
        self.assertIn("last_delivery_error", HUD)
        self.assertIn("title='STALLED'", HUD)
        self.assertIn("Auto Send: OFF", HUD)
        self.assertIn("Auto Send: ON", HUD)
        self.assertIn("def native_auto_send(enabled):", HUD)
        self.assertIn("auto-send-on", NATIVE)
        self.assertIn("auto-send-off", NATIVE)
        self.assertIn("FORCE COMMAND", HUD)
        self.assertIn("FORCE ABORT", HUD)
        self.assertIn("CLEAR QUEUE", HUD)
        self.assertIn("abort-delivery", NATIVE)
        self.assertIn("clear-pending-deliveries", NATIVE)

    def test_desktop_launcher_never_starts_mini_hud(self):
        self.assertIn("hud-mode", LAUNCH)
        self.assertIn("Reconcile-OriginalDesktopHUD.ps1", LAUNCH)
        self.assertNotIn("desktop_native_hud.py", LAUNCH)
        self.assertNotIn("START-GPT-WINDOWS-RELAY.bat", LAUNCH)
        self.assertFalse((ROOT / "desktop_native_hud.py").exists())

    def test_reconciliation_affects_only_canonical_hud_files(self):
        self.assertIn("desktop_native_hud.py", RECONCILE)
        self.assertIn("hud.py", RECONCILE)
        self.assertIn("Get-CimInstance Win32_Process", RECONCILE)
        self.assertIn("StringComparison]::OrdinalIgnoreCase", RECONCILE)
        self.assertIn("ORIGINAL_HUD_FILE=hud.py", RECONCILE)
        self.assertIn("ORIGINAL_HUD_TRANSPORT=NATIVE_CHATGPT_APP", RECONCILE)
        self.assertIn("$label+'_ALREADY_EXITED_PID='", RECONCILE)
        self.assertIn("$label+'_STOP_FAILED_PID='", RECONCILE)
        self.assertIn("ORIGINAL_HUD_VISIBLE_WINDOW_COUNT=", RECONCILE)
        self.assertIn("ORIGINAL_HUD_HOST_PROCESS_COUNT=", RECONCILE)
        self.assertNotIn("relay-control.ps1", RECONCILE)
        self.assertNotIn("http://127.0.0.1", RECONCILE)

if __name__ == "__main__":
    unittest.main()
