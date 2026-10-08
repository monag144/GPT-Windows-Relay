"""Guard Agent011's one-shot semantic rotation against syntax/codepage drift.

Static tests are portable; syntax validation additionally runs on Windows
PowerShell when available. No script is executed and no browser is changed.
"""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"semantic_agent_rotation.ps1"

class SemanticAgentRotationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=SCRIPT.read_bytes()
        cls.src=cls.raw.decode("utf-8")

    def test_powershell_source_is_ascii_only_to_avoid_ps51_ansi_decode(self):
        self.assertTrue(self.raw.isascii())
        self.assertNotIn("💻",self.src)
        self.assertIn("[char]::ConvertFromUtf32(0x1F4BB)",self.src)
        self.assertIn("[char]::ConvertFromUtf32(0x1F527)",self.src)

    def test_one_shot_semantic_new_chat_without_keyboard_shortcuts(self):
        self.assertIn("function NewChatButton(",self.src)
        self.assertIn("ROTATION_NEW_CHAT_SEMANTIC_COUNT_",self.src)
        self.assertIn("$new.invoke.Invoke()",self.src)
        self.assertNotIn("SendWait('^t')",self.src)
        self.assertNotIn("SendWait('^l')",self.src)
        self.assertNotIn("location.assign(",self.src)

    def test_no_retry_after_click_or_sent_handoff(self):
        for token in ("NEW_CHAT_CLICK_UNCERTAIN","HALT_AFTER_CLICK_NO_RETRY",
                      "HANDOFF_SEND_UNCERTAIN","HALT_SUBMISSION_UNCERTAIN",
                      "SOURCE_RESULT_VISIBLE_RECEIPT_NOT_PROVEN"):
            with self.subTest(token=token):
                self.assertIn(token,self.src)
        self.assertLess(self.src.index("$state.click_invoked=$true"),
                        self.src.index("$new.invoke.Invoke()"))
        self.assertLess(self.src.index("$state.send_invoked=$true"),
                        self.src.index("$ip.Invoke()"))

    def test_governance_and_operator_stop_are_gated_before_click(self):
        self.assertIn("ROTATION_OPERATOR_STOP_FILE",self.src)
        self.assertIn("ROTATION_RELAY_UNAVAILABLE_OR_STOPPED",self.src)
        self.assertIn("SOURCE_CONVERSATION_IDENTITY_INVALID",self.src)
        self.assertIn("PENDING_MISSIONS_CHANGED_BEFORE_SEND",self.src)
        self.assertIn("SOURCE_COMPOSER_HAS_DRAFT",self.src)
        self.assertIn("[GPT_ENGINEERING_ROTATION_HANDOFF_V1]",self.src)
        self.assertIn("engineering_preflight",self.src)

    def test_worker_start_receipt_precedes_control_and_ui_checks(self):
        source=self.src
        start=source.index("try{\n # POSITIVE WORKER-START RECEIPT")
        entry=source.index("Save 'WORKER_ENTRY'",start)
        validated=source.index("Save 'HANDOFF_VALIDATED'",entry)
        control=source.index("Save 'CONTROL_GATE_PASSED'",validated)
        selected=source.index("Save 'SOURCE_TAB_RECOGNIZED'",control)
        wait=source.index("Save 'WAITING_FOR_SOURCE_RESULT'",selected)
        click=source.index("Save 'NEW_CHAT_CLICK_UNCERTAIN'",wait)
        self.assertLess(entry,validated)
        self.assertLess(validated,control)
        self.assertLess(control,selected)
        self.assertLess(selected,wait)
        self.assertLess(wait,click)

    def test_delivery_wait_is_bounded_and_first_phase_is_durable(self):
        self.assertIn("$deadline=[DateTime]::UtcNow.AddSeconds(180)",self.src)
        self.assertIn("SOURCE_RESULT_VISIBLE_RECEIPT_NOT_PROVEN",self.src)
        self.assertIn("Save 'WORKER_ENTRY'",self.src)

    def test_worker_script_has_valid_windows_powershell_syntax(self):
        engine=shutil.which("powershell.exe")
        if not engine:
            self.skipTest("Windows PowerShell not installed on this host")
        literal=str(SCRIPT).replace("'","''")
        command=(
            "$t=$null;$e=$null;"
            "[System.Management.Automation.Language.Parser]::ParseFile('"
            +literal+"',[ref]$t,[ref]$e)|Out-Null;"
            "if($e.Count){$e|ForEach-Object{$_.Message};exit 2};"
            "Write-Output 'ROTATION_SCRIPT_PARSE_OK'"
        )
        p=subprocess.run([engine,"-NoProfile","-NonInteractive","-Command",command],
                         capture_output=True,text=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stdout+"\n"+p.stderr)
        self.assertIn("ROTATION_SCRIPT_PARSE_OK",p.stdout)

if __name__=="__main__":
    unittest.main()
