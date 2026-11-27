"""FORCE SEND is an explicit app-neutral dispatch, not a duplicate resend.

All tests operate on temporary files and a mocked foreground window.
No UI, power shell, keyboard, command execution, or real message is touched.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import desktop_native_relay as native
import windows_relay as wr


class ManualForceSendTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        home = Path(tmp.name)
        for field, value in {
            "HOME": home,
            "CONFIG": home / "desktop-control.json",
            "STATE": home / "state.json",
            "STATUS": home / "runtime-status.json",
            "FORCE_SEND_REQUESTS": home / "force-send-requests",
            "FORCE_SEND_RECEIPTS": home / "force-send-receipts",
            "DELIVERY_HOLDS": home / "delivery-holds",
        }.items():
            p = mock.patch.object(native, field, value)
            p.start()
            self.addCleanup(p.stop)
        self.aid = "PCE20-FORCE-SEND-SYNTHETIC-001"
        self.hwnd = 91011
        native.configuration()  # Auto Send intentionally defaults OFF.
        self.state = wr.State(native.STATE)
        self.state.set_armed(True)
        self.state.data["outbound_owner"] = "windows"
        self.state.data["outbound_deliveries"][self.aid] = {
            "phase": "READY", "has_attachments": False, "created_at": wr.now(),
            "attempt_count": 0, "submit_only_attempt_count": 0,
        }
        self.state.save()

    def request(self):
        with mock.patch.object(native, "runner_active", return_value=True):
            return native.request_force_send(self.aid, self.hwnd)

    def receipt(self, rid):
        return json.loads((native.FORCE_SEND_RECEIPTS / (rid + ".json")).read_text(encoding="utf-8"))

    def test_auto_send_off_still_allows_explicit_manual_request(self):
        self.assertFalse(native.configuration()["auto_send"])
        rid = self.request()
        data = json.loads((native.FORCE_SEND_REQUESTS / (rid + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(data["action_id"], self.aid)
        self.assertEqual(data["foreground_hwnd"], self.hwnd)
        self.assertEqual(data["kind"], "FORCE_SEND")

    def test_ready_output_calls_existing_delivery_owner_once(self):
        rid = self.request()
        with mock.patch.object(native, "current_foreground_hwnd", return_value=self.hwnd), \
             mock.patch.object(native, "deliver") as dispatch, \
             mock.patch.object(native, "recover_submit_only") as recover:
            self.assertEqual(native.reconcile_force_send_requests(self.state), 1)
        dispatch.assert_called_once_with(self.state, self.aid, manual=True)
        recover.assert_not_called()
        self.assertEqual(self.receipt(rid)["result"], "READY")
        self.assertFalse((native.FORCE_SEND_REQUESTS / (rid + ".json")).exists())
        self.assertEqual(native.reconcile_force_send_requests(self.state), 0)

    def test_pending_draft_calls_send_only_not_reinsertion(self):
        self.state.data["outbound_deliveries"][self.aid]["phase"] = "SEND_PENDING"
        self.state.save()
        rid = self.request()
        with mock.patch.object(native, "current_foreground_hwnd", return_value=self.hwnd), \
             mock.patch.object(native, "deliver") as dispatch, \
             mock.patch.object(native, "recover_submit_only") as recover:
            self.assertEqual(native.reconcile_force_send_requests(self.state), 1)
        recover.assert_called_once_with(self.state, self.aid, manual=True)
        dispatch.assert_not_called()
        self.assertEqual(self.receipt(rid)["action_id"], self.aid)

    def test_foreground_change_blocks_injection(self):
        rid = self.request()
        with mock.patch.object(native, "current_foreground_hwnd", return_value=self.hwnd + 1), \
             mock.patch.object(native, "deliver") as dispatch:
            native.reconcile_force_send_requests(self.state)
        dispatch.assert_not_called()
        self.assertEqual(self.receipt(rid)["result"], "WINDOW_CHANGED_NO_SEND")

    def test_force_clear_aborted_result_is_not_replayed(self):
        self.state.data["outbound_deliveries"][self.aid]["phase"] = "ABORTED"
        self.state.save()
        rid = self.request()
        with mock.patch.object(native, "current_foreground_hwnd", return_value=self.hwnd), \
             mock.patch.object(native, "deliver") as dispatch, \
             mock.patch.object(native, "recover_submit_only") as recover:
            native.reconcile_force_send_requests(self.state)
        dispatch.assert_not_called()
        recover.assert_not_called()
        self.assertEqual(self.receipt(rid)["result"], "NO_ELIGIBLE_RESULT")

    def test_uncertain_or_already_submitted_result_never_resent(self):
        for phase in ("SUBMIT_UNCERTAIN", "SUBMITTED", "TEXT_INSERTED"):
            self.state.data["outbound_deliveries"][self.aid]["phase"] = phase
            self.state.save()
            rid = self.request()
            with mock.patch.object(native, "current_foreground_hwnd", return_value=self.hwnd), \
                 mock.patch.object(native, "deliver") as dispatch, \
                 mock.patch.object(native, "recover_submit_only") as recover:
                native.reconcile_force_send_requests(self.state)
            dispatch.assert_not_called()
            recover.assert_not_called()
            self.assertEqual(self.receipt(rid)["result"], "NO_ELIGIBLE_RESULT")

    def test_pending_draft_second_click_budget_is_not_reused(self):
        delivery=self.state.data["outbound_deliveries"][self.aid]
        delivery.update(phase="SEND_PENDING",submit_only_attempt_count=1)
        self.state.save()
        rid = self.request()
        with mock.patch.object(native, "current_foreground_hwnd", return_value=self.hwnd), \
             mock.patch.object(native, "recover_submit_only") as recover:
            native.reconcile_force_send_requests(self.state)
        recover.assert_not_called()
        self.assertEqual(self.receipt(rid)["result"], "NO_ELIGIBLE_RESULT")

    def test_target_lost_or_expired_request_makes_no_delivery_attempt(self):
        rid=self.request()
        req=native.FORCE_SEND_REQUESTS / (rid + ".json")
        data=json.loads(req.read_text(encoding="utf-8"))
        data["expires_epoch"]=1.0
        req.write_text(json.dumps(data),encoding="utf-8")
        with mock.patch.object(native, "deliver") as dispatch:
            native.reconcile_force_send_requests(self.state)
        dispatch.assert_not_called()
        self.assertEqual(self.receipt(rid)["result"], "EXPIRED_NO_SEND")

    def test_request_refused_without_active_arm_or_valid_window(self):
        with mock.patch.object(native, "runner_active", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "RUNNING_SINGLETON"):
                native.request_force_send(self.aid,self.hwnd)
        with mock.patch.object(native, "runner_active", return_value=True):
            with self.assertRaisesRegex(ValueError, "WINDOW_INVALID"):
                native.request_force_send(self.aid,0)


if __name__ == "__main__":
    unittest.main()
