"""Regression for Katana Operation 004 sender PRE_SUBMIT_FAILED retry storm.

No UI clicks or OS commands. Native runner delivery state is exercised with
an authenticated stored result and mocked PowerShell sender output.
"""
from __future__ import annotations
import json
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
            "RECEIPT_REQUESTS":root/"receipt-reconciliations",
            "FORCE_CLEAR_REQUESTS":root/"force-clear-requests",
            "FORCE_CLEAR_RECEIPTS":root/"force-clear-receipts",
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

    def test_placeholder_ambiguity_is_held_before_click_without_reexecution(self):
        fake=SimpleNamespace(returncode=1,
            stdout=("SENDER_STAGE=APP_WINDOW_FOUND\n"
                    "SENDER_STAGE=CONVERSATION_DOCUMENT_FOUND\n"
                    "HEARTBEAT_ERROR=COMPOSER_PLACEHOLDER_AMBIGUOUS_SEND_STATE_REFUSE\n"
                    "RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY\n"),
            stderr="")
        before=self.state.lookup(self.id).copy()
        with mock.patch.object(native.shutil,"which",return_value="powershell.exe"), \
             mock.patch.object(native.subprocess,"run",return_value=fake) as submit:
            native.deliver(self.state,self.id)
            native.deliver(self.state,self.id)
        submit.assert_called_once()
        delivery=self.state.outbound_lookup(self.id)
        self.assertEqual(delivery["phase"],"PRE_SUBMIT_FAILED")
        self.assertTrue(native.delivery_held(self.id))
        self.assertEqual(self.state.lookup(self.id)["status"],before["status"])
        status=native.get_status()
        self.assertEqual(status["last_delivery_error"],
                         "COMPOSER_PLACEHOLDER_AMBIGUOUS_SEND_STATE_REFUSE")
        self.assertEqual(status["last_delivery_stage"],"CONVERSATION_DOCUMENT_FOUND")

    def test_unsent_owned_draft_preserved_after_send_button_not_ready(self):
        # A verified native packet was typed into the ChatGPT composer, but
        # the Send button did not become eligible. Preserve the draft and hold
        # the saved result; do not replay the Windows command or auto-retry.
        fake=SimpleNamespace(returncode=1,
            stdout=("SENDER_STAGE=INPUT_COMPLETED\n"
                    "SENDER_STAGE=SEND_BUTTON_NOT_READY\n"
                    "UIA_SEND_READY_DRAFT_MATCH=True\n"
                    "UIA_SEND_READY_READ_FAILURES=2\n"
                    "HEARTBEAT_ERROR=COMPOSER_SET_BUT_SEND_NOT_ENABLED\n"
                    "OWN_UNSENT_DRAFT=PRESERVED_IN_COMPOSER\n"
                    "RESULT=HEARTBEAT_FAILED_NO_CONFIRMED_DELIVERY\n"),
            stderr="")
        before=self.state.lookup(self.id).copy()
        with mock.patch.object(native.shutil,"which",return_value="powershell.exe"), \
             mock.patch.object(native.subprocess,"run",return_value=fake) as sender:
            native.deliver(self.state,self.id)
            native.deliver(self.state,self.id)
        sender.assert_called_once()
        result=self.state.outbound_lookup(self.id)
        self.assertEqual(result["phase"],"PRE_SUBMIT_FAILED")
        self.assertEqual(self.state.lookup(self.id)["status"],before["status"])
        self.assertTrue(native.delivery_held(self.id))
        status=native.get_status()
        self.assertEqual(status["last_delivery_stage"],"SEND_BUTTON_NOT_READY")
        self.assertEqual(status["last_delivery_error"],"COMPOSER_SET_BUT_SEND_NOT_ENABLED")
        self.assertTrue(status["delivery_blocked"])

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

    def test_plain_retry_cannot_inherit_stale_force_clear_authorization(self):
        delivery = self.state.data["outbound_deliveries"][self.id]
        delivery["phase"] = "PRE_SUBMIT_FAILED"
        self.state.save()
        native.hold_failed_delivery(self.id, "STARTING", "TEST")
        marker = native.delivery_force_clear_path(self.id)
        marker.write_text('{"authorized_utc":"OLD"}', encoding="utf-8")
        native.release_failed_delivery(self.state, self.id)
        self.assertFalse(marker.exists())
        self.assertFalse(native.delivery_held(self.id))
        self.assertEqual(self.state.lookup(self.id)["status"], "OK")

    def test_operator_confirmed_receipt_reconciles_without_retry_or_evidence_loss(self):
        outbox, receipt = native.outbox_result(self.state, self.id)
        self.assertTrue(outbox.is_file())
        record = self.state.data["outbound_deliveries"][self.id]
        record["phase"] = "PRE_SUBMIT_FAILED"
        record["attempt_count"] = 46
        self.state.save()
        native.hold_failed_delivery(self.id, "CONVERSATION_DOCUMENT_FOUND", "PLACEHOLDER")
        hold = native.delivery_hold_path(self.id)
        original_hold = hold.read_bytes()
        original_outbox = outbox.read_bytes()
        native.update_control("off")
        with mock.patch.object(native, "runner_active", return_value=False), \
             mock.patch.object(native.subprocess, "run") as never_send:
            acknowledged = native.acknowledge_confirmed_receipt(self.id, receipt)
            again = native.acknowledge_confirmed_receipt(self.id, receipt)
        never_send.assert_not_called()
        self.assertEqual(acknowledged["phase"], "SUBMITTED")
        self.assertEqual(again["phase"], "SUBMITTED")
        self.assertEqual(acknowledged["attempt_count"], 46)
        self.assertEqual(hold.read_bytes(), original_hold)
        self.assertEqual(outbox.read_bytes(), original_outbox)
        current = wr.State(native.STATE)
        self.assertEqual(current.outbound_lookup(self.id)["phase"], "SUBMITTED")
        self.assertEqual(current.lookup(self.id)["status"], "OK")
        self.assertNotIn(self.id, current.list_claimable_outbound_ids())
        self.assertEqual(native.get_status()["last_result"], "SUBMITTED")
        self.assertFalse(native.get_status()["delivery_blocked"])

    def test_live_runner_applies_confirmed_receipt_without_retry_or_state_race(self):
        outbox, receipt = native.outbox_result(self.state,self.id)
        delivery=self.state.data["outbound_deliveries"][self.id]
        delivery["phase"]="PRE_SUBMIT_FAILED"
        delivery["attempt_count"]=2
        self.state.save()
        native.hold_failed_delivery(self.id,"SEND_BUTTON_ENABLED",
                                    "HEARTBEAT_ID_ALREADY_PRESENT_REFUSE_DUPLICATE")
        hold=native.delivery_hold_path(self.id)
        original_hold=hold.read_bytes()
        original_result=self.state.lookup(self.id).copy()
        with mock.patch.object(native,"runner_active",return_value=True), \
             mock.patch.object(native.subprocess,"run") as no_send:
            queued=native.request_confirmed_receipt(self.id,receipt)
            self.assertEqual(queued,"QUEUED")
            self.assertEqual(native.request_confirmed_receipt(self.id,receipt),
                             "ALREADY_QUEUED")
            self.assertEqual(self.state.outbound_lookup(self.id)["phase"],
                             "PRE_SUBMIT_FAILED")
            self.assertEqual(native.reconcile_receipt_requests(self.state),1)
            self.assertEqual(native.reconcile_receipt_requests(self.state),0)
        no_send.assert_not_called()
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"SUBMITTED")
        self.assertEqual(self.state.outbound_lookup(self.id)["attempt_count"],2)
        self.assertEqual(self.state.lookup(self.id),original_result)
        self.assertEqual(hold.read_bytes(),original_hold)
        self.assertTrue(outbox.is_file())
        self.assertEqual(native.get_status()["last_delivery_stage"],
                         "OPERATOR_RECEIPT_RECONCILED")
        self.assertFalse(native.get_status()["delivery_blocked"])
        self.assertEqual(list(native.RECEIPT_REQUESTS.glob("*.json")),[])

    def test_queued_receipt_is_idempotent_when_native_sender_already_submitted(self):
        _,receipt=native.outbox_result(self.state,self.id)
        record=self.state.data["outbound_deliveries"][self.id]
        record["phase"]="SUBMITTED"
        self.state.save()
        native.request_confirmed_receipt(self.id,receipt)
        original=self.state.outbound_lookup(self.id)
        self.assertEqual(native.reconcile_receipt_requests(self.state),1)
        self.assertEqual(self.state.outbound_lookup(self.id),original)
        self.assertEqual(list(native.RECEIPT_REQUESTS.glob("*.json")),[])

    def test_queued_receipt_rejects_wrong_nonce_without_tampering_with_history(self):
        _, receipt=native.outbox_result(self.state,self.id)
        before=native.STATE.read_bytes()
        with self.assertRaisesRegex(RuntimeError,"BINDING_MISMATCH"):
            native.request_confirmed_receipt(self.id,
                "NATIVE-RECEIPT-"+("0"*32))
        self.assertEqual(native.STATE.read_bytes(),before)
        self.assertFalse(native.RECEIPT_REQUESTS.is_dir())
        delivery=self.state.data["outbound_deliveries"][self.id]
        delivery["phase"]="PRE_SUBMIT_FAILED"
        self.state.save()
        native.request_confirmed_receipt(self.id,receipt)
        request_files=list(native.RECEIPT_REQUESTS.glob("*.json"))
        self.assertEqual(len(request_files),1)
        request_files[0].write_text('{"id":"WRONG-ID","receipt":"not-a-nonce"}',
                                    encoding="utf-8")
        self.assertEqual(native.reconcile_receipt_requests(self.state),0)
        self.assertTrue(request_files[0].is_file())
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],
                         "PRE_SUBMIT_FAILED")

    def test_live_receipt_request_cannot_make_unsent_ready_result_submitted(self):
        _,receipt=native.outbox_result(self.state,self.id)
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"READY")
        native.request_confirmed_receipt(self.id,receipt)
        self.assertEqual(native.reconcile_receipt_requests(self.state),0)
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"READY")
        self.assertTrue(list(native.RECEIPT_REQUESTS.glob("*.json")))

    def test_receipt_mismatch_and_running_engine_fail_without_mutation(self):
        _, receipt = native.outbox_result(self.state, self.id)
        record = self.state.data["outbound_deliveries"][self.id]
        record["phase"] = "PRE_SUBMIT_FAILED"
        self.state.save()
        native.update_control("off")
        original = native.STATE.read_bytes()
        different = "NATIVE-RECEIPT-" + ("0" * 32)
        with mock.patch.object(native, "runner_active", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "BINDING_MISMATCH"):
                native.acknowledge_confirmed_receipt(self.id, different)
        self.assertEqual(original, native.STATE.read_bytes())
        with mock.patch.object(native, "runner_active", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "STOPPED_DISARMED_RUNNER"):
                native.acknowledge_confirmed_receipt(self.id, receipt)
        self.assertEqual(original, native.STATE.read_bytes())

    def test_ready_result_cannot_be_falsely_reconciled(self):
        _, receipt = native.outbox_result(self.state, self.id)
        native.update_control("off")
        with mock.patch.object(native, "runner_active", return_value=False):
            with self.assertRaisesRegex(wr.RelayError, "not reconcilable"):
                native.acknowledge_confirmed_receipt(self.id, receipt)
        self.assertEqual(wr.State(native.STATE).outbound_lookup(self.id)["phase"], "READY")

    def test_receipt_request_processed_before_any_chatgpt_uia_scan(self):
        source=(ROOT/"desktop_native_relay.py").read_text(encoding="utf-8")
        self.assertIn('"queue-confirmed-receipt"',source)
        self.assertIn("request_confirmed_receipt(args.action_id, args.receipt)",source)
        self.assertIn("reconcile_receipt_requests(state)",source)
        runner=source.split("def runner():",1)[1].split("HUD_MODE =",1)[0]
        self.assertLess(runner.index("reconcile_receipt_requests(state)"),
                        runner.index("candidates = read_scan(require_app=True)"))
        reconcile=source.split("def reconcile_receipt_requests(state: wr.State):",1)[1].split(
            "def acknowledge_confirmed_receipt",1)[0]
        self.assertNotIn("subprocess.run(",reconcile)
        self.assertNotIn("deliver(",reconcile)
        self.assertIn("state.reconcile_outbound_receipt(aid, receipt)",reconcile)

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

    def test_force_clear_terminally_disposes_unresolved_and_preserves_history(self):
        held="PCE19-NATIVE-E2E-20261122-001"
        unsure="PCE19-NATIVE-HEALTH-20261122-002"
        pending="PCE19-CHAT-SEND-PENDING-20261122-009"
        delivered="PCE19-FOREGROUND-E2E-20261122-005"
        deliveries=self.state.data["outbound_deliveries"]
        deliveries[self.id]["phase"]="READY"
        deliveries[held]={"id":held,"phase":"PRE_SUBMIT_FAILED","attempt_count":2,
                          "saved_result_path":"saved-held"}
        deliveries[unsure]={"id":unsure,"phase":"SUBMIT_UNCERTAIN","attempt_count":1,
                            "saved_result_path":"saved-uncertain"}
        deliveries[pending]={"id":pending,"phase":"SEND_PENDING","attempt_count":1,
                             "saved_result_path":"saved-pending"}
        deliveries[delivered]={"id":delivered,"phase":"SUBMITTED",
                               "attempt_count":1,"saved_result_path":"saved-sent"}
        self.state.save()
        snapshot={k:dict(v) for k,v in deliveries.items()}
        affected=self.state.force_clear_unresolved_deliveries("a"*32,{
            held:{"stage":"INPUT_BEGIN","reason":"COMPOSER_NOT_READY",
                  "held_utc":"2026-11-22T03:00:00Z"}})
        self.assertCountEqual(affected,[self.id,held,unsure,pending])
        for key in affected:
            item=self.state.outbound_lookup(key)
            self.assertEqual(item["phase"],"ABORTED")
            self.assertEqual(item.get("attempt_count",0),
                             snapshot[key].get("attempt_count",0))
            self.assertEqual(item["saved_result_path"],snapshot[key]["saved_result_path"])
            self.assertEqual(item["force_clear_request_id"],"a"*32)
            self.assertEqual(item["force_clear_disposition"],
                             "OPERATOR_DISCARDED_UNVERIFIED_DELIVERY")
        self.assertEqual(self.state.outbound_lookup(held)["force_clear_hold_evidence"]["reason"],
                         "COMPOSER_NOT_READY")
        self.assertEqual(self.state.outbound_lookup(delivered),snapshot[delivered])
        self.assertEqual(self.state.lookup(self.id)["status"],"OK")
        # Crash-after-journal-before-receipt replay must not change the state.
        unchanged=self.state.outbound_lookup(held)
        self.assertCountEqual(self.state.force_clear_unresolved_deliveries("a"*32),
                              affected)
        self.assertEqual(self.state.outbound_lookup(held),unchanged)
        self.assertEqual(self.state.list_claimable_outbound_ids(),[])

    def test_runner_force_clear_request_is_durable_once_and_removes_holds(self):
        native.hold_failed_delivery(self.id,"COMPOSER_SET","TEST_NOT_SENT")
        self.state.data["outbound_deliveries"][self.id]["phase"]="PRE_SUBMIT_FAILED"
        self.state.data["outbound_deliveries"][self.id]["attempt_count"]=2
        self.state.save()
        with mock.patch.object(native,"runner_active",return_value=True):
            request_id=native.request_force_clear_pending()
        with mock.patch.object(native.subprocess,"run") as never_send:
            self.assertEqual(native.reconcile_force_clear_requests(self.state),1)
            self.assertEqual(native.reconcile_force_clear_requests(self.state),0)
        never_send.assert_not_called()
        receipt=native.wait_force_clear_receipt(request_id,timeout=0.1)
        self.assertEqual(receipt["result"],"FORCE_CLEAR_COMPLETE")
        self.assertEqual(receipt["aborted_ids"],[self.id])
        self.assertEqual(receipt["aborted_count"],1)
        self.assertEqual(receipt["unresolved_remaining"],0)
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"ABORTED")
        self.assertEqual(self.state.outbound_lookup(self.id)["attempt_count"],2)
        self.assertEqual(self.state.lookup(self.id)["status"],"OK")
        self.assertEqual(self.state.outbound_lookup(self.id)
                         ["force_clear_hold_evidence"]["reason"],"TEST_NOT_SENT")
        self.assertFalse(native.delivery_held(self.id))
        self.assertEqual(list(native.FORCE_CLEAR_REQUESTS.glob("*.json")),[])

    def test_force_clear_does_not_touch_actively_submitting_record(self):
        self.state.claim_outbound_delivery(self.id)
        self.state.force_clear_unresolved_deliveries("b"*32)
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"SUBMITTING")
        self.assertEqual(self.state.outbound_lookup(self.id)["attempt_count"],1)
        self.state.finish_outbound_delivery(self.id,"SUBMITTED")
        self.assertEqual(self.state.force_clear_unresolved_deliveries("c"*32),[])
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"SUBMITTED")

    def test_malformed_force_clear_request_is_held_without_mutation(self):
        native.FORCE_CLEAR_REQUESTS.mkdir(parents=True,exist_ok=True)
        (native.FORCE_CLEAR_REQUESTS/("a"*32+".json")).write_text(
            json.dumps({"id":"b"*32,"kind":"FORCE_CLEAR_PENDING"}),encoding="utf-8")
        with mock.patch.object(native.subprocess,"run") as never_send:
            self.assertEqual(native.reconcile_force_clear_requests(self.state),0)
        never_send.assert_not_called()
        self.assertEqual(self.state.outbound_lookup(self.id)["phase"],"READY")
        self.assertTrue(list(native.FORCE_CLEAR_REQUESTS.glob("*.json")))
        self.assertFalse(native.FORCE_CLEAR_RECEIPTS.exists())

    def test_force_clear_only_runner_updates_saved_outbox(self):
        source=Path(native.__file__).read_text(encoding="utf-8")
        run_section=source.split("def runner():",1)[1]
        self.assertLess(run_section.index("reconcile_force_clear_requests(state)"),
                        run_section.index("for aid in state.list_claimable_outbound_ids():"))
        self.assertIn('request_force_clear_pending()',source)
        self.assertIn('wait_force_clear_receipt(',source)
        reset=source.split("def reconcile_force_clear_requests(state: wr.State)",1)[1].split(
            "def request_confirmed_receipt",1)[0]
        self.assertIn("state.force_clear_unresolved_deliveries(request_id, holds)",reset)
        self.assertNotIn("wr.State(",reset)
        self.assertNotIn("deliver(",reset)
        self.assertNotIn("process_packet(",reset)


if __name__=="__main__":
    unittest.main()
