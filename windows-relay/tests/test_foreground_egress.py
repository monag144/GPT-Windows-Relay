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
        self.assertEqual(self.state.outbound_lookup(self.aid)["last_sender_error"],
                         "FOREIGN_RESULT_PATH_MISMATCH")
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
        self.assertIn("$focused=[System.Windows.Automation.AutomationElement]::FocusedElement", SENDER)
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

    def test_foreground_target_auto_focus_requires_unique_writable_editor(self):
        # Automatic focus must not depend on a prior click in the composer.
        self.assertIn("function Test-EligibleEditor(", SENDER)
        self.assertIn("function Focus-CandidateEditor(", SENDER)
        self.assertIn("function Get-ForegroundEditable {", SENDER)
        self.assertIn("$window.FindAll(", SENDER)
        self.assertIn("FOREGROUND_EDITOR_AUTOFOCUSED", SENDER)
        self.assertIn("$editor.SetFocus()", SENDER)
        self.assertIn("GetCursorPos", SENDER)
        self.assertIn("SetCursorPos", SENDER)
        self.assertIn("if($named.Count -eq 1)", SENDER)
        self.assertIn("elseif($all.Count -eq 1)", SENDER)
        self.assertIn("else{return $null}  # Ambiguous fields", SENDER)
        self.assertIn("Test-EligibleEditor $window $focused", SENDER)
        self.assertIn("IsPassword", SENDER)
        self.assertIn("Read-EditorText $target", SENDER)
        # A diagnostic from inside a PowerShell function would corrupt its
        # hashtable result. Require script-scoped status to be emitted later.
        self.assertIn("$script:autoFocused=$true", SENDER)
        self.assertNotIn(
            "Write-Output 'SENDER_STAGE=FOREGROUND_EDITOR_AUTOFOCUSED'\n    }\n    if(",
            SENDER)

    def test_chat_send_enter_only_after_unique_enabled_send_control(self):
        self.assertIn("public static uint TypeEnter()", SENDER)
        self.assertIn("keys[0].U.ki.wVk=0x0D", SENDER)
        self.assertIn("function Find-SendButton(", SENDER)
        self.assertIn("$send=if($allowSubmit){Find-SendButton $target}else{$null}", SENDER)
        self.assertIn("if($null -eq $send){", SENDER)
        self.assertIn("RESULT=TEXT_INSERTED_VERIFIED", SENDER)
        self.assertIn("if($kind -eq 'ControlType.Edit'){", SENDER)
        self.assertIn("[CourierForegroundInput]::TypeEnter() -ne [uint32]2", SENDER)
        self.assertIn("UIA_GUARDED_SUBMIT_ENTER_BEGIN", SENDER)
        self.assertIn("SENDER_STAGE=SUBMIT_KEY_COMPLETED", SENDER)
        self.assertLess(SENDER.index("if($null -eq $send){"),
                        SENDER.index("if($kind -eq 'ControlType.Edit'){"))
        self.assertIn("FOREGROUND_SEND_OUTSIDE_ACTIVE_WINDOW", SENDER)
        self.assertIn("UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN", SENDER)
        self.assertIn("RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND", SENDER)

    def test_electron_typing_recognized_without_stale_value_pattern(self):
        self.assertIn("function Test-EditorContainsMarker(", SENDER)
        self.assertIn("function Test-EmptyOrPlaceholder(", SENDER)
        self.assertIn("EDITOR_TEXT_MARKER_VERIFIED", SENDER)
        self.assertIn("EDITOR_SEND_ENABLEMENT_VERIFIED", SENDER)
        self.assertIn("$sendBefore=Find-SendButton $target", SENDER)
        self.assertIn("$null -eq $sendBefore", SENDER)
        self.assertIn("CHAT_EDITOR_HAS_UNRELATED_DRAFT", SENDER)
        self.assertIn("RESULT=FOREGROUND_NO_TARGET", SENDER)
        self.assertIn("Test-TranscriptMarker $target $NativeReceiptMarker", SENDER)
        self.assertIn("Test-EditorContainsMarker $target $NativeReceiptMarker){continue}", SENDER)
        self.assertIn("FOREGROUND_INSERTION_NOT_VERIFIED", SENDER)

    def test_guarded_enter_submitted_receipt_updates_native_journal(self):
        which, process = self.sender(
            "SENDER_STAGE=FOREGROUND_EDITOR_AUTOFOCUSED\n"
            "SENDER_STAGE=EDITOR_SEND_ENABLEMENT_VERIFIED\n"
            "SENDER_STAGE=SUBMIT_KEY_BEGIN\n"
            "UIA_GUARDED_SUBMIT_ENTER_BEGIN\n"
            "SENDER_STAGE=CONFIRMED_IN_CONVERSATION\n"
            "RESULT=HEARTBEAT_SUBMITTED\n"
        )
        with which, process as invoked:
            native.deliver(self.state, self.aid)
        invoked.assert_called_once()
        self.assertEqual(
            self.state.outbound_lookup(self.aid)["phase"], "SUBMITTED"
        )
        self.assertEqual(native.get_status()["last_delivery_stage"],
                         "CONFIRMED_IN_CONVERSATION")

    def test_guarded_enter_unconfirmed_is_not_replayed(self):
        which, process = self.sender(
            "SENDER_STAGE=SUBMIT_KEY_BEGIN\n"
            "UIA_GUARDED_SUBMIT_ENTER_BEGIN\n"
            "RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND\n", 5
        )
        with which, process as invoked:
            native.deliver(self.state, self.aid)
            native.deliver(self.state, self.aid)
        invoked.assert_called_once()
        self.assertEqual(
            self.state.outbound_lookup(self.aid)["phase"], "SUBMIT_UNCERTAIN"
        )
        self.assertEqual(
            self.state.outbound_lookup(self.aid)["attempt_count"], 1
        )

    def test_chat_without_send_button_is_pending_not_successfully_delivered(self):
        self.assertIn("SENDER_STAGE=CHAT_DRAFT_PENDING_SEND", SENDER)
        self.assertIn("RESULT=CHAT_SEND_PENDING", SENDER)
        self.assertIn('phase = "SEND_PENDING"', NATIVE)
        self.assertIn("SEND_PENDING", (ROOT/"hud.py").read_text(encoding="utf-8"))
        self.assertIn("SEND_PENDING", (ROOT/"windows_relay.py").read_text(encoding="utf-8"))
        self.assertIn("def recover_submit_only(state: wr.State, aid: str):", NATIVE)
        self.assertIn('"-SubmitExistingOnly"', NATIVE)

    def test_send_only_recovers_stored_chat_draft_without_exec_or_retyping(self):
        self.state.data["outbound_deliveries"][self.aid]["phase"] = "SEND_PENDING"
        self.state.data["outbound_deliveries"][self.aid]["attempt_count"] = 1
        self.state.save()
        which, process = self.sender(
            "SENDER_STAGE=SUBMIT_ONLY_ATTEMPT_1\n"
            "SENDER_STAGE=CONFIRMED_IN_CONVERSATION\n"
            "RESULT=HEARTBEAT_SUBMITTED\n")
        with which, process as invoked, \
             mock.patch.object(native, "process_packet") as no_exec, \
             mock.patch.object(native, "execute_with_stop") as no_command:
            native.recover_submit_only(self.state, self.aid)
        invoked.assert_called_once()
        no_exec.assert_not_called()
        no_command.assert_not_called()
        args = invoked.call_args.args[0]
        self.assertIn("-SubmitExistingOnly", args)
        self.assertIn(str(native.FOREGROUND_SENDER), args)
        self.assertNotIn(str(native.SENDER), args)
        record = self.state.outbound_lookup(self.aid)
        self.assertEqual(record["phase"], "SUBMITTED")
        self.assertEqual(record["attempt_count"], 1)
        self.assertEqual(record["submit_only_attempt_count"], 1)
        self.assertEqual(record["last_sender_stage"], "CONFIRMED_IN_CONVERSATION")
        self.assertEqual(self.state.lookup(self.aid)["status"], "OK")

    def test_send_only_no_target_defers_without_spending_retry_budget(self):
        self.state.data["outbound_deliveries"][self.aid]["phase"] = "SEND_PENDING"
        self.state.save()
        which, process = self.sender(
            "SENDER_STAGE=SUBMIT_ONLY_NO_OWN_DRAFT\n"
            "RESULT=FOREGROUND_NO_TARGET\n")
        with which, process as invoked:
            native.recover_submit_only(self.state, self.aid)
            native.recover_submit_only(self.state, self.aid)
        self.assertEqual(invoked.call_count, 2)
        delivery = self.state.outbound_lookup(self.aid)
        self.assertEqual(delivery["phase"], "SEND_PENDING")
        self.assertEqual(delivery["submit_only_attempt_count"], 0)
        self.assertEqual(self.state.lookup(self.aid)["status"], "OK")

    def test_send_only_uncertain_is_not_retried_or_reexecuted(self):
        self.state.data["outbound_deliveries"][self.aid]["phase"] = "SUBMIT_UNCERTAIN"
        self.state.save()
        which, process = self.sender(
            "SENDER_STAGE=SUBMIT_ONLY_RETRY_EXHAUSTED\n"
            "RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND\n")
        with which, process as invoked, \
             mock.patch.object(native, "process_packet") as no_exec:
            native.recover_submit_only(self.state, self.aid)
            native.recover_submit_only(self.state, self.aid)
        invoked.assert_called_once()
        no_exec.assert_not_called()
        delivery = self.state.outbound_lookup(self.aid)
        self.assertEqual(delivery["phase"], "SUBMIT_UNCERTAIN")
        self.assertEqual(delivery["submit_only_attempt_count"], 1)

    def test_previously_visible_receipt_does_not_send_duplicate(self):
        self.state.data["outbound_deliveries"][self.aid]["phase"] = "SUBMIT_UNCERTAIN"
        self.state.save()
        which, process = self.sender(
            "SENDER_STAGE=SUBMIT_ONLY_ALREADY_IN_TRANSCRIPT\n"
            "RESULT=HEARTBEAT_SUBMITTED\n")
        with which, process as invoked:
            native.recover_submit_only(self.state, self.aid)
        invoked.assert_called_once()
        record = self.state.outbound_lookup(self.aid)
        self.assertEqual(record["phase"], "SUBMITTED")
        self.assertEqual(record["reconciliation_evidence"],
                         "UIA_EXISTING_TRANSCRIPT_RECEIPT")

    def test_submit_only_mode_is_receipt_bound_and_never_types_payload(self):
        self.assertIn("[switch]$SubmitExistingOnly", SENDER)
        self.assertIn("function Test-ExactOwnDraft(", SENDER)
        self.assertIn("function Test-ChatGPTSubmissionTarget(", SENDER)
        self.assertIn("function Recover-ExistingChatDraft(", SENDER)
        self.assertIn("Test-ConversationReceiptNotComposer $target $marker", SENDER)
        self.assertIn("function Test-ConversationReceiptNotComposer(", SENDER)
        self.assertIn("Test-ExactOwnDraft $target $marker", SENDER)
        self.assertIn("if($SubmitExistingOnly){", SENDER)
        self.assertIn("Recover-ExistingChatDraft $target $NativeReceiptMarker", SENDER)
        self.assertIn("RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND", SENDER)
        self.assertIn("for($attempt=1;$attempt -le 2;$attempt++)", SENDER)
        self.assertIn("Get-Process -Id ([int]$target.window.Current.ProcessId)", SENDER)
        self.assertIn("$proc.ProcessName -ine 'ChatGPT'", SENDER)
        submit_helper = SENDER.split("function Recover-ExistingChatDraft(",1)[1].split(
            "$script:autoFocused=$false",1)[0]
        self.assertNotIn("TypeUnicode(", submit_helper)
        self.assertNotIn("SetValue(", submit_helper)
        self.assertNotIn("ClearFocusedComposer(", submit_helper)
        self.assertNotIn("process_packet(", NATIVE.split("def recover_submit_only(",1)[1].split("def runner():",1)[0])
        self.assertLess(NATIVE.index("state.list_claimable_submit_retries()"),
                        NATIVE.index("for aid in state.list_claimable_outbound_ids():"))

    def test_retry_journal_survives_restart_and_prevents_duplicate_enter(self):
        d=self.state.data["outbound_deliveries"][self.aid]
        d["phase"]="SEND_PENDING"
        d["attempt_count"]=1
        self.state.save()
        self.assertEqual(self.state.list_claimable_submit_retries(),[self.aid])
        self.state.claim_submit_only_retry(self.aid)
        recovered=wr.State(native.STATE)
        record=recovered.outbound_lookup(self.aid)
        self.assertEqual(record["phase"],"SUBMIT_UNCERTAIN")
        self.assertEqual(record["submit_only_attempt_count"],1)
        self.assertEqual(recovered.list_claimable_submit_retries(),[])
        self.assertEqual(recovered.lookup(self.aid)["status"],"OK")

    def test_only_chat_outcomes_are_eligible_for_send_retry(self):
        self.assertEqual(self.state.list_claimable_submit_retries(),[])
        d=self.state.data["outbound_deliveries"][self.aid]
        d["phase"]="TEXT_INSERTED"
        self.state.save()
        self.assertEqual(self.state.list_claimable_submit_retries(),[])
        d["phase"]="SUBMITTED"
        self.state.save()
        self.assertEqual(self.state.list_claimable_submit_retries(),[])
        d["phase"]="SEND_PENDING"
        d["submit_only_attempt_count"]=1
        self.state.save()
        self.assertEqual(self.state.list_claimable_submit_retries(),[])

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
