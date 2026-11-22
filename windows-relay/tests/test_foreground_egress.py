"""Command Courier app-neutral foreground text-field delivery regression.

Unit tests simulate the PowerShell sender and do NOT type or click in Windows.
The Windows-only AST check parses, but never executes, the sender source.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import windows_relay as wr
import desktop_native_relay as native
import command_courier as courier

SENDER = (ROOT / "tools" / "Send-Foreground-TextResult.ps1").read_text(
    encoding="utf-8")
NATIVE = (ROOT / "desktop_native_relay.py").read_text(encoding="utf-8")


class ForegroundResultTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for field, value in {
            "HOME": root, "CONFIG": root / "desktop-control.json",
            "STATE": root / "state.json", "STATUS": root / "runtime-status.json",
            "OUTBOX": root / "outbox", "DELIVERY_HOLDS": root / "delivery-holds",
            "LOCK": root / "desktop-runner.lock",
        }.items():
            patch = mock.patch.object(native, field, value)
            patch.start()
            self.addCleanup(patch.stop)
        native.configuration()
        self.state = wr.State(native.STATE)
        self.state.set_armed(True)
        self.state.data["outbound_owner"] = "windows"
        self.state.save()
        self.aid = "PCE19-FOREGROUND-TEST-001"
        action = wr.extract(
            wr.OPEN + "\n" + json.dumps({
                "version": 1, "platform": "windows",
                "id": self.aid, "action": "EXEC",
                "session": "katana.native", "shell": "python",
                "command": "print('small test')"
            }) + "\n" + wr.CLOSE)
        self.state.reserve(action)
        result = {
            "version": 1, "platform": "windows", "id": self.aid,
            "session": "katana.native", "action": "EXEC", "shell": "python",
            "status": "OK", "exit_code": 0, "cwd": str(root),
            "started_at": wr.now(), "finished_at": wr.now(),
            "duration_ms": 1, "stdout": "small test\n", "stderr": "",
        }
        saved = wr.save_full_result(self.state, result)
        self.state.mark(action, wr.present_result(action, result, saved))

    def sender(self, stdout, exit_code=0):
        fake = SimpleNamespace(returncode=exit_code, stdout=stdout, stderr="")
        return (mock.patch.object(native.shutil, "which",
                                  return_value="powershell.exe"),
                mock.patch.object(native.subprocess, "run", return_value=fake))

    def test_no_focused_editor_defers_without_hold_or_attempt_inflation(self):
        which, process = self.sender(
            "SENDER_STAGE=AWAITING_FOREGROUND_TEXT_FIELD\n"
            "RESULT=FOREGROUND_NO_TARGET\n")
        with which, process as invoke:
            native.deliver(self.state, self.aid)
            native.deliver(self.state, self.aid)
        self.assertEqual(invoke.call_count, 2)
        delivered = self.state.outbound_lookup(self.aid)
        self.assertEqual(delivered["phase"], "READY")
        self.assertEqual(delivered["attempt_count"], 0)
        self.assertEqual(delivered["last_deferral"], "AWAITING_FOREGROUND_TEXT_FIELD")
        self.assertFalse(native.delivery_held(self.aid))
        self.assertEqual(native.get_status()["phase"], "AWAITING_TEXT_FIELD")
        self.assertEqual(self.state.lookup(self.aid)["status"], "OK")

    def test_notepad_insertion_is_not_falsely_chat_submitted(self):
        which, process = self.sender(
            "SENDER_STAGE=FOREGROUND_TEXT_FIELD_FOUND\n"
            "SENDER_STAGE=TEXT_INSERTION_VERIFIED\n"
            "RESULT=TEXT_INSERTED_VERIFIED\n")
        with which, process as invoke:
            native.deliver(self.state, self.aid)
            native.deliver(self.state, self.aid)
        invoke.assert_called_once()
        self.assertEqual(self.state.outbound_lookup(self.aid)["phase"],
                         "TEXT_INSERTED")
        self.assertEqual(self.state.outbound_lookup(self.aid)["attempt_count"], 1)
        self.assertFalse(native.delivery_held(self.aid))
        self.assertEqual(native.get_status()["last_result"], "TEXT_INSERTED")
        args = invoke.call_args.args[0]
        self.assertIn(str(native.FOREGROUND_SENDER), args)
        self.assertNotIn(str(native.SENDER), args)
        self.assertEqual(native.get_status()["phase"], "IDLE")

    def test_chat_submitted_only_with_send_and_transcript_receipt(self):
        which, process = self.sender(
            "SENDER_STAGE=TEXT_INSERTION_VERIFIED\n"
            "UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN\n"
            "SENDER_STAGE=CONFIRMED_IN_CONVERSATION\n"
            "RESULT=HEARTBEAT_SUBMITTED\n")
        with which, process:
            native.deliver(self.state, self.aid)
        self.assertEqual(self.state.outbound_lookup(self.aid)["phase"],
                         "SUBMITTED")

    def test_focus_loss_after_input_is_uncertain_not_autoreplayed(self):
        which, process = self.sender(
            "SENDER_STAGE=FOREGROUND_INPUT_COMPLETED\n"
            "HEARTBEAT_ERROR=FOCUSED_EDITOR_CHANGED_DURING_INPUT\n"
            "RESULT=FOREGROUND_INSERTION_UNCERTAIN_NO_RETRY\n", 5)
        with which, process as call:
            native.deliver(self.state, self.aid)
            native.deliver(self.state, self.aid)
        call.assert_called_once()
        self.assertEqual(self.state.outbound_lookup(self.aid)["phase"],
                         "SUBMIT_UNCERTAIN")
        self.assertEqual(self.state.outbound_lookup(self.aid)["attempt_count"], 1)
        self.assertFalse(native.delivery_held(self.aid))

    def test_invalid_preinput_result_fails_without_faking_no_target(self):
        which, process = self.sender(
            "HEARTBEAT_ERROR=FOREIGN_RESULT_PATH_MISMATCH\n"
            "RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY\n", 1)
        with which, process as call:
            native.deliver(self.state, self.aid)
            native.deliver(self.state, self.aid)
        call.assert_called_once()
        self.assertEqual(self.state.outbound_lookup(self.aid)["phase"],
                         "PRE_SUBMIT_FAILED")
        self.assertTrue(native.delivery_held(self.aid))

    def test_explicit_legacy_force_resend_remains_charged_to_chatgpt_adapter(self):
        which, process = self.sender("RESULT=HEARTBEAT_SUBMITTED\n")
        native.DELIVERY_HOLDS.mkdir(parents=True, exist_ok=True)
        native.delivery_force_clear_path(self.aid).write_text("{}")
        with which, process as call:
            native.deliver(self.state, self.aid)
        args = call.call_args.args[0]
        self.assertIn(str(native.SENDER), args)
        self.assertIn("-ForceClearComposer", args)
        self.assertNotIn(str(native.FOREGROUND_SENDER), args)

    def test_source_changes_make_output_independent_from_chatgpt_scanner(self):
        owner = NATIVE.split("def runner():", 1)[1].split("HUD_MODE =", 1)[0]
        self.assertIn("FOREGROUND_SENDER", NATIVE)
        self.assertIn("state.defer_outbound_delivery(aid)", NATIVE)
        self.assertIn("next_foreground_probe = time.monotonic() + 2.0", owner)
        self.assertLess(owner.index("for aid in state.list_claimable_outbound_ids()"),
                        owner.index("candidates = read_scan(require_app=True)"))
        self.assertEqual(owner.count("for aid in state.list_claimable_outbound_ids()"), 1)
        self.assertIn("AWAITING_TEXT_FIELD", owner)
        self.assertIn("TEXT_INSERTED", NATIVE)
        self.assertIn("creationflags=getattr(subprocess, \"CREATE_NO_WINDOW\", 0)", NATIVE)
        hud = (ROOT / "hud.py").read_text(encoding="utf-8")
        self.assertIn("Foreground text field • auto-detect • no configured input", hud)
        self.assertIn("OUTPUT QUEUED • waiting for focused text field", hud)
        self.assertIn("elif phase=='AWAITING_TEXT_FIELD': title='READY'", hud)
        cli = (ROOT / "command_courier.py").read_text(encoding="utf-8")
        self.assertIn('"AWAITING_TEXT_FIELD"', cli)

    def test_app_neutral_editor_cannot_blindly_press_enter_or_run_code(self):
        self.assertIn("Get-ForegroundEditable", SENDER)
        self.assertIn("AutomationElement]::FocusedElement", SENDER)
        self.assertIn("ControlType.Edit", SENDER)
        self.assertIn("ControlType.Document", SENDER)
        self.assertIn("Current.IsPassword", SENDER)
        self.assertIn("Assert-CurrentTarget", SENDER)
        self.assertIn("TypeUnicode", SENDER)
        self.assertIn("Find-SendButton", SENDER)
        self.assertIn("Test-TranscriptMarker", SENDER)
        self.assertIn("RESULT=TEXT_INSERTED_VERIFIED", SENDER)
        self.assertIn("RESULT=FOREGROUND_NO_TARGET", SENDER)
        self.assertIn("RESULT=HEARTBEAT_SUBMITTED", SENDER)
        self.assertIn("windowsterminal|openconsole|conhost", SENDER)
        self.assertIn("windowsterminal|openconsole|conhost|wt)$", SENDER)
        self.assertIn("$editor=[System.Windows.Automation.AutomationElement]::FocusedElement", SENDER)
        self.assertIn("$inputText=$script:wire", SENDER)
        self.assertIn('Replace("`r",\' \').Replace("`n",\' \')', SENDER)
        self.assertEqual(SENDER.count("function Read-EditorText"), 1)
        self.assertNotIn("\n}\n){\n", SENDER)
        self.assertIn("AWAITING_TEXT_FIELD", NATIVE)
        self.assertNotIn("Get-ChatGPTWindow", SENDER)
        self.assertNotIn("ProcessName -ieq 'ChatGPT'", SENDER)
        self.assertNotIn("VK_RETURN", SENDER)
        self.assertNotIn("SendKeys", SENDER)
        self.assertNotIn("subprocess.run(", SENDER)

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"),
                         "PowerShell AST parser is Windows-only")
    def test_sender_powershell_ast_is_parseable_without_running_it(self):
        path = str(ROOT / "tools" / "Send-Foreground-TextResult.ps1")
        escaped = path.replace("'", "''")
        command = ("$tokens=$null;$errors=$null;"
                   "[void][System.Management.Automation.Language.Parser]::"
                   "ParseFile('" + escaped + "',[ref]$tokens,[ref]$errors);"
                   "if($errors.Count){$errors | ForEach-Object {Write-Output $_.Message};"
                   "exit 1};Write-Output 'POWERSHELL_AST_PARSE_OK'")
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=20, encoding="utf-8",
            errors="replace")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("POWERSHELL_AST_PARSE_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
