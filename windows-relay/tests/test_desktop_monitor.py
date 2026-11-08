"""Offline checks for automatic native ChatGPT desktop monitor lifecycle."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/"tools"/"Run-ChatGPT-DesktopMonitor.ps1").read_text(encoding="utf-8")
LAUNCH=(ROOT/"START-CHATGPT-DESKTOP-RELAY.cmd").read_text(encoding="utf-8")


class DesktopMonitorTests(unittest.TestCase):
    def test_continuously_scans_after_explicit_start(self):
        self.assertIn("while($true)",SCRIPT)
        self.assertIn("Watch-ChatGPT-ActionCandidates.ps1",SCRIPT)
        self.assertIn("DESKTOP_ACTION_DETECTED=",SCRIPT)
        self.assertIn("DESKTOP_ACTION_STATUS=OBSERVED_NOT_EXECUTED",SCRIPT)
        self.assertIn("CHATGPT_DESKTOP_MONITOR_V2",SCRIPT)

    def test_singleton_and_dedupe(self):
        self.assertIn("Local\\GPTWindowsDesktopMonitor",SCRIPT)
        self.assertIn("$known.Add($id)",SCRIPT)
        self.assertIn("SUBMISSION_ATTEMPTED",SCRIPT)
        self.assertIn("DELIVERY_UNCERTAIN",SCRIPT)
        self.assertIn("BLOCKED_BY_DRAFT",SCRIPT)
        self.assertIn("desktop-heartbeat-ledger-v2.json",SCRIPT)
        self.assertIn("MONITOR_STOP=CANONICAL_OPERATOR_STOP",SCRIPT)
        self.assertIn("UIA_FOCUSED_ENTER_BEGIN",SCRIPT)
        self.assertIn("HEARTBEAT_JOURNAL_UNREADABLE_REFUSE_DUPLICATE",SCRIPT)

    def test_defers_user_draft_and_never_executes_commands(self):
        self.assertIn("COMPOSER_NOT_EMPTY_REFUSE_TO_OVERWRITE_USER_DRAFT",SCRIPT)
        self.assertIn("WINDOWS_COMMAND_EXECUTION=DISABLED_UNTRUSTED_UIA_ORIGIN",SCRIPT)
        for command in ("Invoke-RestMethod", "Invoke-WebRequest", "/action",
                        "windows_relay.py", "Get-Clipboard", "Set-Clipboard"):
            self.assertNotIn(command,SCRIPT)

    def test_cmd_entrypoint_only(self):
        self.assertIn("start \"GPT ChatGPT Desktop Monitor\" powershell.exe",LAUNCH)
        self.assertNotIn("START-GPT-WINDOWS-RELAY.bat",LAUNCH)
        self.assertIn("Start-ChatGPT-DesktopBackend.ps1",LAUNCH)


if __name__=="__main__":
    unittest.main()
