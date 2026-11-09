"""Regression for Katana Operation 004 sender PRE_SUBMIT_FAILED retry storm.

No UI clicks or OS commands. Native runner delivery state is exercised with
an authenticated stored result and mocked PowerShell sender output.
"""
from __future__ import annotations
import tempfile
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import windows_relay as wr
import desktop_native_relay as native


class DeliveryFailureHoldTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root=Path(tmp.name)
        for name,value in {
            "HOME":root,"CONFIG":root/"desktop-control.json",
            "STATE":root/"state.json","STATUS":root/"runtime-status.json",
            "OUTBOX":root/"outbox","DELIVERY_HOLDS":root/"delivery-holds",
            "LOCK":root/"desktop-runner.lock"
        }.items():
            patch=mock.patch.object(native,name,value)
            patch.start()
            self.addCleanup(patch.stop)
        native.configuration()
        self.state=wr.State(native.STATE)
        self.state.set_armed(True)
        self.state.data["outbound_owner"]="windows"
        self.state.save()
        self.id="PCE18-NATIVE-SMOKE-20261109-004"
        action=wr.extract("[GPT_WINDOWS_ACTION]\n"
            '{"version":1,"platform":"windows","id":"PCE18-NATIVE-SMOKE-20261109-004",'
            '"action":"EXEC","session":"katana.native","shell":"cmd","command":"echo PCE18_RELAY_SMOKE_004_SUCCESS"}'
            "\n[/GPT_WINDOWS_ACTION]")
        self.state.reserve(action)
        result={"version":1,"platform":"windows","id":self.id,
                "session":"katana.native","action":"EXEC","shell":"cmd",
                "status":"OK","exit_code":0,"cwd":str(root),
                "started_at":wr.now(),"finished_at":wr.now(),"duration_ms":1,
                "stdout":"PCE18_RELAY_SMOKE_004_SUCCESS\n","stderr":""}
        full=wr.save_full_result(self.state,result)
        self.state.mark(action,wr.present_result(action,result,full))

    def test_failed_sender_is_held_and_never_spins(self):
        fake=SimpleNamespace(returncode=1,
            stdout=("HEARTBEAT_ERROR=COMPOSER_NOT_FOCUSED_REFUSE_SENDINPUT\n"
                    "RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY\n"),
            stderr="")
        with mock.patch.object(native.shutil,"which",return_value="powershell.exe"),\
             mock.patch.object(native.subprocess,"run",return_value=fake) as submit:
            native.deliver(self.state,self.id)
            native.deliver(self.state,self.id)
        submit.assert_called_once()
        self.assertTrue(native.delivery_held(self.id))
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"PRE_SUBMIT_FAILED")
        status=native.get_status()
        self.assertTrue(status["delivery_blocked"])
        self.assertEqual(status["last_delivery_error"],"COMPOSER_NOT_FOCUSED_REFUSE_SENDINPUT")
        self.assertEqual(status["phase"],"DELIVERY_BLOCKED")
        # The command result remains safely available; no execution replay.
        self.assertEqual(self.state.lookup(self.id)["status"],"OK")

    def test_explicit_operator_release_allows_one_new_sender_attempt(self):
        failure=SimpleNamespace(returncode=1,
            stdout=("HEARTBEAT_ERROR=COMPOSER_NOT_FOCUSED_REFUSE_SENDINPUT\n"
                    "RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY\n"),stderr="")
        success=SimpleNamespace(returncode=0,
            stdout=("COMPOSER_INPUT=SENDINPUT_UNICODE_ACCEPTED\n"
                    "UIA_GUARDED_SEND_BUTTON_CLICK_COMPLETED\n"
                    "RESULT=HEARTBEAT_SUBMITTED\n"),stderr="")
        with mock.patch.object(native.shutil,"which",return_value="powershell.exe"),\
             mock.patch.object(native.subprocess,"run",side_effect=[failure,success]) as submit:
            native.deliver(self.state,self.id)
            native.release_failed_delivery(self.state,self.id)
            native.deliver(self.state,self.id)
        self.assertEqual(submit.call_count,2)
        self.assertFalse(native.delivery_held(self.id))
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"SUBMITTED")
        self.assertFalse(native.get_status()["delivery_blocked"])

    def test_cannot_replay_execution_or_retry_ambiguous_delivery(self):
        fake=SimpleNamespace(returncode=5,
            stdout=("UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN\n"
                    "RESULT=HEARTBEAT_DELIVERY_UNCERTAIN_DO_NOT_RESEND\n"),stderr="")
        with mock.patch.object(native.shutil,"which",return_value="powershell.exe"),\
             mock.patch.object(native.subprocess,"run",return_value=fake) as submit:
            native.deliver(self.state,self.id)
            native.deliver(self.state,self.id)
        submit.assert_called_once()
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"SUBMIT_UNCERTAIN")
        with self.assertRaisesRegex(RuntimeError,"NOT_SAFELY_RETRYABLE"):
            native.release_failed_delivery(self.state,self.id)

    def test_operator_abort_and_clear_queue_never_change_executed_result(self):
        native.hold_failed_delivery(self.id,"INPUT_BEGIN","TEST")
        native.abort_failed_delivery(self.state,self.id)
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"ABORTED")
        self.assertFalse(native.delivery_held(self.id))
        self.assertEqual(self.state.lookup(self.id)["status"],"OK")
        second="PCE18-NATIVE-SMOKE-20261109-005"
        self.state.data["outbound_deliveries"][second]={"id":second,"phase":"READY"}; self.state.save()
        native.hold_failed_delivery(second,"STARTING","TEST")
        native.clear_pending_deliveries(self.state)
        self.assertIsNone(self.state.outbound_lookup(second))
        self.assertEqual(self.state.lookup(self.id)["status"],"OK")


if __name__=="__main__":
    unittest.main()
