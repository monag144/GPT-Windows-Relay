"""HUD sign-in checkbox and gear settings: non-GUI source and worker contracts."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hud
import desktop_native_relay as native

HUD_SOURCE = (ROOT / "hud.py").read_text(encoding="utf-8")


class CourierHudStartupTests(unittest.TestCase):
    def test_checkbox_uses_verified_link_and_runtime_not_persisted_guess(self):
        with mock.patch.object(hud, "courier_hud_cli", side_effect=[
            "COURIER_USER_STARTUP=INSTALLED_OWNED\n",
            "COURIER_RUNTIME=native-desktop\n",
        ]) as calls:
            state = hud.courier_hud_startup_details()
        self.assertEqual(state, {"installed": True, "runtime": "native-desktop"})
        self.assertEqual(calls.call_args_list, [
            mock.call("startup", "status"), mock.call("profile")
        ])

    def test_disable_is_limited_to_owned_startup_link(self):
        with mock.patch.object(hud, "courier_hud_cli", side_effect=[
            "COURIER_USER_STARTUP=REMOVED\n",
            "COURIER_USER_STARTUP=NOT_INSTALLED\n",
            "COURIER_RUNTIME=native-desktop\n",
        ]) as calls:
            result = hud.courier_hud_apply("startup", False)
        self.assertFalse(result["installed"])
        self.assertEqual(calls.call_args_list[0], mock.call("startup", "remove"))
        self.assertEqual(calls.call_args_list[-1], mock.call("profile"))

    def test_enable_installs_owned_link_then_selects_native_runtime(self):
        with mock.patch.object(hud, "courier_hud_cli", side_effect=[
            "COURIER_USER_STARTUP=INSTALLED_OWNED\n",
            "COURIER_RUNTIME_SELECTED=native-desktop\n",
            "COURIER_USER_STARTUP=INSTALLED_OWNED\n",
            "COURIER_RUNTIME=native-desktop\n",
        ]) as calls:
            result = hud.courier_hud_apply("startup", True)
        self.assertTrue(result["installed"])
        self.assertEqual(result["runtime"], "native-desktop")
        self.assertEqual(calls.call_args_list[:2], [
            mock.call("startup", "install"), mock.call("profile", "native-desktop")
        ])

    def test_invalid_link_status_is_not_reported_as_enabled(self):
        with mock.patch.object(hud, "courier_hud_cli", side_effect=[
            "COURIER_USER_STARTUP=UNKNOWN\n",
        ]):
            with self.assertRaisesRegex(RuntimeError, "STATUS_UNRECOGNIZED"):
                hud.courier_hud_startup_details()

    def test_runtime_selection_changes_next_launch_only(self):
        with mock.patch.object(hud, "courier_hud_cli", side_effect=[
            "COURIER_RUNTIME_SELECTED=disabled\n",
            "COURIER_USER_STARTUP=INSTALLED_OWNED\n",
            "COURIER_RUNTIME=disabled\n",
        ]) as calls:
            result = hud.courier_hud_apply("runtime", "disabled")
        self.assertEqual(result["runtime"], "disabled")
        self.assertEqual(calls.call_args_list[0], mock.call("profile", "disabled"))

    def test_gear_and_checkbox_in_existing_window(self):
        self.assertIn('text="⚙"', HUD_SOURCE)
        self.assertIn('text="Start with Windows"', HUD_SOURCE)
        self.assertIn('text="Start HUD and engine with Windows sign-in"', HUD_SOURCE)
        self.assertIn('settings_frame=tk.Frame(panel,bg=PANEL)', HUD_SOURCE)
        self.assertIn('active_frame=settings_frame if settings_open else details_frame', HUD_SOURCE)
        self.assertIn('root.overrideredirect(True)', HUD_SOURCE)
        self.assertIn('W,COMPACT_H,EXPANDED_H=560,184,386', HUD_SOURCE)
        self.assertNotIn('tk.Toplevel(', HUD_SOURCE)

    def test_force_send_button_performs_real_generic_manual_delivery(self):
        self.assertIn('text="FORCE SEND"', HUD_SOURCE)
        self.assertNotIn('text="FOCUS FOR SEND"', HUD_SOURCE)
        self.assertNotIn('text="FORCE RESEND"', HUD_SOURCE)
        self.assertIn('def force_send_selected():', HUD_SOURCE)
        self.assertIn('def remember_external_foreground(last: dict)', HUD_SOURCE)
        self.assertIn('def force_send_to_last_foreground(snap: dict, last: dict)', HUD_SOURCE)
        self.assertIn('native.request_force_send(aid,hwnd)', HUD_SOURCE)
        self.assertIn('force_command_btn.configure(command=force_send_selected)', HUD_SOURCE)
        self.assertIn('remember_external_foreground(last_send_target)', HUD_SOURCE)
        self.assertIn("'force_send_action':force_send_action", HUD_SOURCE)
        self.assertIn("d.get('phase')=='READY'", HUD_SOURCE)
        self.assertIn("d.get('phase')=='SEND_PENDING'", HUD_SOURCE)
        self.assertIn("FORCE CLEAR COMPLETE • no unsent result available", HUD_SOURCE)
        self.assertIn('text="SENDING…" if sending else "FORCE SEND"', HUD_SOURCE)
        self.assertIn('not snap.get("native_off") and not sending else \'disabled\'', HUD_SOURCE)
        self.assertIn('manual_send["id"]=force_send_to_last_foreground(', HUD_SOURCE)
        self.assertIn('FORCE SEND • ', HUD_SOURCE)
        self.assertNotIn('native_delivery_control("force-delivery"', HUD_SOURCE)
        self.assertIn('def reconcile_force_send_requests(state: wr.State)', Path(native.__file__).read_text(encoding="utf-8"))

    def test_force_send_does_not_replay_aborted_result_after_force_clear(self):
        result_id="PCE20-ABORTED-001"
        status={"native_running":True, "native_armed":True, "native_off":False,
                "auto_send":True, "phase":"FORWARDING_NO_CHATGPT",
                "last_action":result_id,"last_result":"FORCE_CLEAR_COMPLETE",
                "delivery_blocked":False}
        journal={"outbound_deliveries":{
            result_id:{"phase":"ABORTED","has_attachments":False,
                       "created_at":"2026-11-27T00:00:00+00:00"}}}
        with mock.patch.object(native,"get_status",return_value=status), \
             mock.patch.object(hud,"read_json",return_value=journal), \
             mock.patch.object(hud,"action_detail",return_value=(None,None)):
            snap=hud.native_snapshot()
        self.assertIsNone(snap["force_send_action"])
        self.assertIn("no unsent result available",snap["phase"])

    def test_force_send_selects_oldest_actual_eligible_unsubmitted_result(self):
        status={"native_running":True, "native_armed":True, "native_off":False,
                "auto_send":False, "phase":"IDLE", "last_action":"STALE",
                "last_result":"FORCE_CLEAR_COMPLETE", "delivery_blocked":False}
        journal={"outbound_deliveries":{
            "DONE":{"phase":"SUBMITTED","has_attachments":False,"created_at":"1"},
            "OLD":{"phase":"READY","has_attachments":False,"created_at":"2"},
            "NEW":{"phase":"SEND_PENDING","submit_only_attempt_count":0,
                   "has_attachments":False,"created_at":"3"},
            "RETRIED":{"phase":"SEND_PENDING","submit_only_attempt_count":1,
                       "has_attachments":False,"created_at":"0"}}}
        with mock.patch.object(native,"get_status",return_value=status), \
             mock.patch.object(hud,"read_json",return_value=journal), \
             mock.patch.object(hud,"action_detail",return_value=(None,None)):
            snap=hud.native_snapshot()
        self.assertEqual(snap["force_send_action"],"OLD")

    def test_hud_toggle_does_not_claim_success_before_worker_receipt(self):
        self.assertIn('def on_startup_check():', HUD_SOURCE)
        self.assertIn('update_courier_settings_widgets()', HUD_SOURCE)
        self.assertIn('start_courier_worker("startup",wanted)', HUD_SOURCE)
        self.assertIn('courier_results.put(("ok",details,None))', HUD_SOURCE)
        self.assertIn('courier_results.put(("error",details,str(exc)[:180]))', HUD_SOURCE)
        self.assertIn('startup_check.configure(state="normal" if editable else "disabled")', HUD_SOURCE)

    def test_live_engine_remains_ready_for_new_commands_while_old_delivery_held(self):
        # Only outbound result 002 is held; the native scanner remains
        # armed for new actions without resending any older result.
        action_id="PCE19-NATIVE-HEALTH-20261122-002"
        status={"native_running":True,"native_armed":True,"native_off":False,
                "auto_send":True,"phase":"DELIVERY_BLOCKED",
                "delivery_blocked":True,"last_action":action_id,
                "last_result":"PRE_SUBMIT_FAILED",
                "last_delivery_error":"COMPOSER_SET_BUT_SEND_NOT_ENABLED"}
        persisted={"outbound_deliveries":{
            action_id:{"phase":"PRE_SUBMIT_FAILED","attempt_count":1}}}
        with mock.patch.object(native,"get_status",return_value=status), \
             mock.patch.object(hud,"read_json",return_value=persisted), \
             mock.patch.object(hud,"action_detail",return_value=(None,None)):
            snap=hud.native_snapshot()
        self.assertEqual(snap["title"],"READY")
        self.assertEqual(snap["title_phase"],"READY")
        self.assertIn("CHATGPT OUTBOX HELD",snap["phase"])
        self.assertEqual(snap["native_delivery_phase"],"PRE_SUBMIT_FAILED")
        self.assertTrue(snap["native_armed"])
        self.assertTrue(snap["online"])
        self.assertIn("DELIVERY BLOCKED:",snap["exact"])

    def test_pending_chat_send_does_not_mislabel_running_engine_stalled(self):
        aid="PCE19-RECOVERABLE-SEND-PENDING-001"
        report={"native_running":True,"native_armed":True,"native_off":False,
                "auto_send":True,"phase":"DELIVERY_UNCERTAIN",
                "delivery_blocked":True,"last_action":aid,"last_result":"SEND_PENDING",
                "last_delivery_error":"SENDER_NO_RECEIPT"}
        persisted={"outbound_deliveries":{
            aid:{"phase":"SEND_PENDING","attempt_count":1}}}
        with mock.patch.object(native,"get_status",return_value=report), \
             mock.patch.object(hud,"read_json",return_value=persisted), \
             mock.patch.object(hud,"action_detail",return_value=(None,None)):
            snap=hud.native_snapshot()
        self.assertEqual(snap["title"],"READY")
        self.assertEqual(snap["outbound_unresolved_count"],1)
        self.assertIn("CHAT SEND PENDING",snap["phase"])
        self.assertNotIn("CHATGPT OUTBOX HELD",snap["phase"])
        self.assertTrue(snap["online"])

    def test_stale_send_pending_status_does_not_override_actual_saved_phase(self):
        aid="PCE19-RECOVERABLE-SEND-PENDING-001"
        report={"native_running":True,"native_armed":True,"native_off":False,
                "auto_send":True,"phase":"DELIVERY_UNCERTAIN",
                "delivery_blocked":True,"last_action":aid,"last_result":"SEND_PENDING",
                "last_delivery_error":"SENDER_NO_RECEIPT"}
        persisted={"outbound_deliveries":{
            aid:{"phase":"SUBMITTED","attempt_count":1}}}
        with mock.patch.object(native,"get_status",return_value=report), \
             mock.patch.object(hud,"read_json",return_value=persisted), \
             mock.patch.object(hud,"action_detail",return_value=(None,None)):
            snap=hud.native_snapshot()
        self.assertNotIn("CHAT SEND PENDING",snap["phase"])
        self.assertEqual(snap["outbound_unresolved_count"],0)

    def test_force_clear_is_journal_only_and_never_touches_chatgpt_or_other_apps(self):
        receipt={"id":"a"*32,"result":"FORCE_CLEAR_COMPLETE",
                 "aborted_count":2,"unresolved_remaining":0}
        with mock.patch.object(native,"request_force_clear_pending",return_value="a"*32) as request, \
             mock.patch.object(native,"wait_force_clear_receipt",return_value=receipt) as waiting, \
             mock.patch.object(hud.subprocess,"run") as send:
            report=hud.native_force_clear_all(composer_focused=True)
        request.assert_called_once_with()
        waiting.assert_called_once_with("a"*32,timeout=15.0)
        send.assert_not_called()
        self.assertEqual(report["composer"],"NOT_TOUCHED")
        self.assertEqual(report["receipt"]["aborted_count"],2)
        source=(ROOT/"hud.py").read_text(encoding="utf-8")
        self.assertNotIn("def native_composer_clear(",source)
        self.assertNotIn("def focus_chatgpt_for_forced_delivery(",source)
        self.assertNotIn("Send-ChatGPT-DesktopHeartbeat.ps1",source)
        self.assertIn("No application's text field will be",source)

    def test_force_clear_requires_confirmed_journal_receipt(self):
        with mock.patch.object(native,"request_force_clear_pending",return_value="b"*32), \\
             mock.patch.object(native,"wait_force_clear_receipt",
                               side_effect=RuntimeError("request pending")):
            with self.assertRaisesRegex(RuntimeError,"request pending"):
                hud.native_force_clear_all()

    def test_native_runtime_never_scans_chatgpt_conversation(self):
        source=(ROOT/"desktop_native_relay.py").read_text(encoding="utf-8")
        runner=source.split("def runner():",1)[1].split("HUD_MODE =",1)[0]
        self.assertIn("reconcile_receipt_requests(state)",runner)
        self.assertIn("reconcile_explicit_output_requests(state)",runner)
        self.assertNotIn("read_scan(",source)
        self.assertNotIn("SCANNING_CHATGPT_APP",source)
        self.assertNotIn("Watch-ChatGPT-ActionCandidates.ps1",source)


if __name__ == "__main__":
    unittest.main()
