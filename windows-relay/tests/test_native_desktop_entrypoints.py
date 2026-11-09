"""Native app source and launcher separation acceptance."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCH = (ROOT/"START-CHATGPT-DESKTOP-RELAY.cmd").read_text(encoding="utf-8")
NATIVE_LAUNCH = (ROOT/"START-CHATGPT-DESKTOP-NATIVE.cmd").read_text(encoding="utf-8")
CONTROL = (ROOT/"DESKTOP-NATIVE-CONTROL.cmd").read_text(encoding="utf-8")
SCAN = (ROOT/"tools"/"Watch-ChatGPT-ActionCandidates.ps1").read_text(encoding="utf-8")
SEND = (ROOT/"tools"/"Send-ChatGPT-DesktopHeartbeat.ps1").read_text(encoding="utf-8")
NATIVE = (ROOT/"desktop_native_relay.py").read_text(encoding="utf-8")
HUD = (ROOT/"hud.py").read_text(encoding="utf-8")


class NativeEntrypointTests(unittest.TestCase):
    def test_familiar_launcher_delegates_to_independent_transport(self):
        self.assertIn("START-CHATGPT-DESKTOP-NATIVE.cmd", LAUNCH)
        self.assertNotIn("Start-ChatGPT-DesktopBackend.ps1", LAUNCH)
        self.assertNotIn("8766", NATIVE_LAUNCH)
        self.assertNotIn("START-GPT-WINDOWS-RELAY.bat", NATIVE_LAUNCH)
        self.assertNotIn("extension-persistent", NATIVE_LAUNCH)
        self.assertIn("desktop_native_relay.py", NATIVE_LAUNCH)
        self.assertIn("Reconcile-OriginalDesktopHUD.ps1", NATIVE_LAUNCH)
        self.assertIn("hud-mode", NATIVE_LAUNCH)
        self.assertNotIn("desktop_native_hud.py", NATIVE_LAUNCH)

    def test_native_state_and_full_commands(self):
        self.assertIn("GPTWindowsRelayDesktop", NATIVE)
        self.assertIn('"armed": True', NATIVE)
        self.assertIn("trust_visible_desktop_packets", NATIVE)
        self.assertIn("wr.shell_argv(action)", NATIVE)
        self.assertIn("wr.extract(packet)", NATIVE)
        self.assertIn("state.reserve(action)", NATIVE)
        self.assertIn("state.mark(action, presented)", NATIVE)
        self.assertIn("state.claim_outbound_delivery(aid)", NATIVE)
        self.assertIn("state.finish_outbound_delivery(aid, phase)", NATIVE)
        self.assertIn("stop_requested()", NATIVE)
        self.assertNotIn("127.0.0.1:8766", NATIVE)
        self.assertNotIn("Firefox", NATIVE_LAUNCH)

    def test_default_scanner_redacted_native_transport_opt_in(self):
        self.assertIn("[switch]$EmitPackets", SCAN)
        self.assertIn("if($EmitPackets)", SCAN)
        self.assertIn("CANDIDATE_PACKET_B64=", SCAN)
        self.assertIn("safeSmoke=$data.safeSmoke", SCAN)

    def test_sender_binds_result_path_and_receipt(self):
        self.assertIn("NativeResultPath", SEND)
        self.assertIn("NativeActionId", SEND)
        self.assertIn("NativeReceiptMarker", SEND)
        self.assertIn("NATIVE_RESULT_BINDING_MISMATCH", SEND)
        self.assertIn("[GPT_WINDOWS_RESULT]", SEND)
        self.assertIn("Set-ComposerTextBySendInput", SEND)
        self.assertIn("SendInput", SEND)
        self.assertNotIn("composer.pattern.SetValue($script:wire)", SEND)
        self.assertIn("UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN", SEND)

    def test_native_hud_does_not_arm_browser(self):
        self.assertIn("def native_snapshot():", HUD)
        self.assertIn("def native_control(action):", HUD)
        self.assertIn("OWNER LOCK: N/A", HUD)
        self.assertIn("START", HUD)
        self.assertIn("RESTART", HUD)
        self.assertIn("KILL", HUD)
        self.assertIn("native_mode()", HUD)
        self.assertIn("native_action=", HUD)
        self.assertIn("STOP", HUD)
        self.assertNotIn("http://127.0.0.1:8766", HUD)
        self.assertIn("desktop_native_relay.py", CONTROL)


if __name__ == "__main__":
    unittest.main()
