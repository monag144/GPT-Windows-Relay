"""Native ChatGPT desktop smoke: execute only the one fixed echo action.

These are structural checks; the Windows parser gate and operator-side run
provide runtime acceptance. UIA authorship is still unverified.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCAN = (ROOT / "tools" / "Watch-ChatGPT-ActionCandidates.ps1").read_text(encoding="utf-8")
MONITOR = (ROOT / "tools" / "Run-ChatGPT-DesktopMonitor.ps1").read_text(encoding="utf-8")
EXECUTOR = (ROOT / "tools" / "Invoke-ChatGPT-DesktopSafeSmoke.ps1").read_text(encoding="utf-8")
SENDER = (ROOT / "tools" / "Send-ChatGPT-DesktopHeartbeat.ps1").read_text(encoding="utf-8")
ID = "PCE18-KATANA-OPTEST-003"
WORD = "PCE18_OPERATION_003_SUCCESS"

class NativeExactSmokeTests(unittest.TestCase):
    def test_scanner_exact_packet_only(self):
        self.assertIn(ID, SCAN)
        self.assertIn("echo " + WORD, SCAN)
        self.assertIn("$names.Count -eq 7", SCAN)
        self.assertIn("safeSmoke=$data.safeSmoke", SCAN)
        self.assertIn("CANDIDATE_SAFE_SMOKE_MATCH=", SCAN)
        self.assertIn("ASSISTANT_AUTHORSHIP_VERIFIED=NO", SCAN)
        self.assertIn("EXECUTIONS=0", SCAN)

    def test_monitor_permanently_listens_but_only_executes_exact_canary(self):
        self.assertIn("NATIVE_SMOKE_ARMED=EXACT_FIXED_ECHO_ONLY", MONITOR)
        self.assertIn("NATIVE_BROWSER_TRANSPORT=NOT_USED", MONITOR)
        self.assertIn("CANDIDATE_SAFE_SMOKE_MATCH=TRUE", MONITOR)
        self.assertIn("$currentCandidate -ceq '" + ID + "'", MONITOR)
        self.assertIn("Invoke-ChatGPT-DesktopSafeSmoke.ps1", MONITOR)
        self.assertIn("$smokeAttempted=$true", MONITOR)
        self.assertIn("if($EnableLegacyHeartbeat -and", MONITOR)
        self.assertIn("Read-Ledger}else{$null}", MONITOR)
        self.assertIn("WINDOWS_COMMAND_EXECUTION=DISABLED_UNTRUSTED_UIA_ORIGIN", MONITOR)

    def test_executor_uses_only_constant_echo_and_durable_reservation(self):
        self.assertIn(ID, EXECUTOR)
        self.assertIn("System32\\cmd.exe", EXECUTOR)
        self.assertIn("/d /q /c 'echo " + WORD + "'", EXECUTOR)
        self.assertIn("FileMode]::CreateNew", EXECUTOR)
        self.assertIn("SMOKE_RESERVATION_EXISTS_OR_FAILED_REFUSE_REPLAY", EXECUTOR)
        self.assertIn("ConfirmExactCanary", EXECUTOR)
        self.assertIn("SMOKE_CMD_EXECUTION=", EXECUTOR)
        self.assertIn("SMOKE_NO_AUTOMATIC_RETRY=TRUE", EXECUTOR)
        self.assertIn("StopRequested", EXECUTOR)
        self.assertNotIn("Invoke-RestMethod", EXECUTOR)
        self.assertNotIn(" /action", EXECUTOR)
        self.assertNotIn("SetBackendArm", EXECUTOR)
        self.assertNotIn("Invoke-Expression", EXECUTOR)

    def test_smoke_result_reuses_guarded_desktop_send_not_browser(self):
        self.assertIn("[GPT_WINDOWS_RESULT]", SENDER)
        self.assertIn("source_action_id='" + ID + "'", SENDER)
        self.assertIn("EXACT_SMOKE_ALLOWLIST_ONLY", SENDER)
        self.assertIn("origin_authentication='NOT_PROVEN'", SENDER)
        self.assertIn("SmokeResult", SENDER)
        self.assertIn("SmokeExitCode", SENDER)
        self.assertIn("UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN", SENDER)
        self.assertIn("Send-ChatGPT-DesktopHeartbeat.ps1", EXECUTOR)

if __name__ == "__main__":
    unittest.main()
