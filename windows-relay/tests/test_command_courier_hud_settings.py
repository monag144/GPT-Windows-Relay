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

    def test_force_clear_runs_only_standalone_powershell_composer_action(self):
        result=SimpleNamespace(returncode=0,stdout=(
            "COMPOSER_CLEAR=VERIFIED_EMPTY\\n"
            "RESULT=COMPOSER_CLEARED_NO_SEND\\n"),stderr="")
        with mock.patch.object(native,"get_status",return_value={"native_running":False,"phase":"IDLE"}), \
             mock.patch.object(hud.subprocess,"run",return_value=result) as run:
            self.assertEqual(hud.native_composer_clear(),"COMPOSER_CLEARED_NO_SEND")
        args=run.call_args.args[0]
        self.assertIn("-ClearComposerOnly",args)
        self.assertIn("-STA",args)
        self.assertNotIn("-NativeResultPath",args)
        self.assertNotIn("-ForceClearComposer",args)
        self.assertNotIn("abort-delivery",args)
        self.assertNotIn("force-delivery",args)
        self.assertNotIn("clear-pending-deliveries",args)
        self.assertEqual(run.call_args.kwargs["check"],False)
        self.assertTrue(run.call_args.kwargs["capture_output"])

    def test_force_clear_refuses_ambiguous_or_failed_composer_result(self):
        result=SimpleNamespace(returncode=1,stdout=(
            "HEARTBEAT_ERROR=EXPECTED_ONE_WRITABLE_COMPOSER_FOUND=2\\n"
            "RESULT=COMPOSER_CLEAR_FAILED_NO_SEND\\n"),stderr="")
        with mock.patch.object(native,"get_status",return_value={"native_running":False,"phase":"IDLE"}), \
             mock.patch.object(hud.subprocess,"run",return_value=result):
            with self.assertRaisesRegex(RuntimeError,"EXPECTED_ONE_WRITABLE_COMPOSER_FOUND=2"):
                hud.native_composer_clear()

    def test_force_clear_does_not_interfere_with_inflight_native_sender(self):
        with mock.patch.object(native,"get_status",return_value={
            "native_running":True,"phase":"DELIVERING"
        }),mock.patch.object(hud.subprocess,"run") as run:
            with self.assertRaisesRegex(RuntimeError,"REFUSE_DURING_NATIVE_DELIVERY"):
                hud.native_composer_clear()
        run.assert_not_called()

    def test_delayed_app_at_login_does_not_form_empty_execution_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            scanner = Path(temp) / "scanner.ps1"
            scanner.touch()
            empty = SimpleNamespace(returncode=0, stdout=(
                "CHATGPT_APP_FOUND=False\nDOCUMENT_READS=0\n"
            ), stderr="")
            ready = SimpleNamespace(returncode=0, stdout=(
                "CHATGPT_APP_FOUND=True\nDOCUMENT_READS=1\n"
            ), stderr="")
            with mock.patch.object(native, "SCANNER", scanner), \
                 mock.patch.object(native.shutil, "which", return_value="powershell.exe"), \
                 mock.patch.object(native.subprocess, "run", side_effect=[empty, ready]):
                with self.assertRaisesRegex(RuntimeError, "NATIVE_CHATGPT_APP_NOT_READY"):
                    native.read_scan(require_app=True)
                self.assertEqual(native.read_scan(require_app=True), [])
        source = (ROOT / "desktop_native_relay.py").read_text(encoding="utf-8")
        self.assertIn("baseline_ready = False", source)
        self.assertIn('phase = ("FORWARDING_NO_CHATGPT" if forward_report["active"]', source)
        self.assertIn('else "WAITING_FOR_CHATGPT_APP")', source)
        self.assertIn('baseline_ready = False', source)
        self.assertIn("candidates = read_scan(require_app=True)", source)


if __name__ == "__main__":
    unittest.main()
