"""Command Courier coordinator: regression tests with no Windows or OS side effects."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import command_courier as courier


class CourierCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self._patch("HOME", self.folder)
        self._patch("STARTUP_EVENTS", self.folder / "command-courier-startup-events.jsonl")
        self._patch("PROFILE", self.folder / "command-courier-runtime.json")
        self._patch("HUD_MODE", self.folder / "hud-mode.json")

    def _patch(self, name, value):
        p = mock.patch.object(courier, name, value)
        p.start()
        self.addCleanup(p.stop)

    def test_existing_native_mode_is_inferred_before_profile_creation(self):
        self.assertEqual(courier.runtime_mode(), courier.DISABLED)
        courier.HUD_MODE.write_text('{"transport":"native-chatgpt-app"}', encoding="utf-8")
        self.assertEqual(courier.runtime_mode(), courier.NATIVE)
        self.assertFalse(courier.PROFILE.exists())

    def test_profile_change_does_not_mutate_running_engine(self):
        with mock.patch("builtins.print"):
            courier.select_runtime(courier.NATIVE)
        self.assertEqual(courier.runtime_mode(), courier.NATIVE)
        self.assertEqual(json.loads(courier.PROFILE.read_text())["version"], 1)
        with mock.patch("builtins.print"):
            courier.select_runtime(courier.DISABLED)
        self.assertEqual(courier.runtime_mode(), courier.DISABLED)

    def test_invalid_profile_fails_closed(self):
        courier.PROFILE.write_text('{"version":2,"runtime":"native-desktop"}', encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "COURIER_RUNTIME_PROFILE_INVALID"):
            courier.runtime_mode()

    def test_disabled_runtime_does_not_start_engine_or_hud(self):
        with mock.patch.object(courier, "IS_WINDOWS", True), mock.patch("builtins.print"), \
             mock.patch.object(courier.subprocess, "run") as runner:
            self.assertEqual(courier.start(), 0)
            runner.assert_not_called()

    def test_native_runtime_links_engine_and_existing_hud(self):
        self._patch("PROFILE", self.folder / "profile.json")
        courier.PROFILE.write_text('{"version":1,"runtime":"native-desktop"}', encoding="utf-8")
        fake = SimpleNamespace(returncode=0, stdout="ORIGINAL_HUD_RUNNING_COUNT=1\\n", stderr="")
        with mock.patch.object(courier, "IS_WINDOWS", True), \
             mock.patch("desktop_native_relay.select_original_hud") as select, \
             mock.patch("desktop_native_relay.configuration", return_value={"off": False}), \
             mock.patch("desktop_native_relay.launch_runner_if_absent") as engine, \
             mock.patch("desktop_native_relay.runner_active", return_value=True), \
             mock.patch.object(courier.shutil, "which", return_value="powershell.exe"), \
             mock.patch.object(courier.subprocess, "run", return_value=fake) as start_hud, \
             mock.patch("builtins.print"):
            self.assertEqual(courier.start(), 0)
            select.assert_called_once()
            engine.assert_called_once()
            args = start_hud.call_args.args[0]
            self.assertIn("Reconcile-OriginalDesktopHUD.ps1", str(args))

    def test_native_off_retained_without_rearming(self):
        courier.PROFILE.write_text('{"version":1,"runtime":"native-desktop"}', encoding="utf-8")
        fake = SimpleNamespace(returncode=0, stdout="ORIGINAL_HUD_RUNNING_COUNT=1\\n", stderr="")
        with mock.patch.object(courier, "IS_WINDOWS", True), \
             mock.patch("desktop_native_relay.select_original_hud"), \
             mock.patch("desktop_native_relay.configuration", return_value={"off": True}), \
             mock.patch("desktop_native_relay.launch_runner_if_absent") as engine, \
             mock.patch.object(courier.shutil, "which", return_value="powershell.exe"), \
             mock.patch.object(courier.subprocess, "run", return_value=fake), \
             mock.patch("builtins.print"):
            self.assertEqual(courier.start(), 0)
            engine.assert_not_called()

    def test_engine_start_failure_does_not_prevent_original_hud(self):
        courier.PROFILE.write_text('{"version":1,"runtime":"native-desktop"}', encoding="utf-8")
        fake = SimpleNamespace(returncode=0, stdout="ORIGINAL_HUD_RUNNING_COUNT=1\\n", stderr="")
        with mock.patch.object(courier, "IS_WINDOWS", True), \
             mock.patch("desktop_native_relay.select_original_hud"), \
             mock.patch("desktop_native_relay.configuration", return_value={"off": False}), \
             mock.patch("desktop_native_relay.launch_runner_if_absent",
                        side_effect=RuntimeError("NATIVE_RUNNER_STARTUP_NOT_CONFIRMED")), \
             mock.patch.object(courier.shutil, "which", return_value="powershell.exe"), \
             mock.patch.object(courier.subprocess, "run", return_value=fake) as hud, \
             mock.patch("builtins.print"):
            self.assertEqual(courier.main(["start"]), 1)
        hud.assert_called_once()
        events = [json.loads(line) for line in
                  courier.STARTUP_EVENTS.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([event["event"] for event in events],
                         ["START_REQUESTED", "ORIGINAL_HUD_RUNNING", "START_FAILED"])
        self.assertIn("NATIVE_RUNNER_STARTUP_NOT_CONFIRMED", events[-1]["detail"])

    def test_hud_failure_prevents_engine_start_and_records_event(self):
        courier.PROFILE.write_text('{"version":1,"runtime":"native-desktop"}', encoding="utf-8")
        fail = SimpleNamespace(returncode=1, stdout="ORIGINAL_HUD_VISIBLE_WINDOW_COUNT=0", stderr="")
        with mock.patch.object(courier, "IS_WINDOWS", True), \
             mock.patch("desktop_native_relay.select_original_hud"), \
             mock.patch("desktop_native_relay.launch_runner_if_absent") as engine, \
             mock.patch.object(courier.shutil, "which", return_value="powershell.exe"), \
             mock.patch.object(courier.subprocess, "run", return_value=fail), \
             mock.patch("builtins.print"):
            self.assertEqual(courier.main(["start"]), 1)
        engine.assert_not_called()
        events = [json.loads(line) for line in
                  courier.STARTUP_EVENTS.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([event["event"] for event in events],
                         ["START_REQUESTED", "START_FAILED"])
        self.assertIn("COURIER_HUD_START_FAILED", events[-1]["detail"])

    def test_off_mode_keeps_hud_up_without_false_linked_status(self):
        courier.PROFILE.write_text('{"version":1,"runtime":"native-desktop"}', encoding="utf-8")
        ok = SimpleNamespace(returncode=0, stdout="ORIGINAL_HUD_RUNNING_COUNT=1\\n", stderr="")
        with mock.patch.object(courier, "IS_WINDOWS", True), \
             mock.patch("desktop_native_relay.select_original_hud"), \
             mock.patch("desktop_native_relay.configuration", return_value={"off": True}), \
             mock.patch("desktop_native_relay.launch_runner_if_absent") as engine, \
             mock.patch.object(courier.shutil, "which", return_value="powershell.exe"), \
             mock.patch.object(courier.subprocess, "run", return_value=ok), \
             mock.patch("builtins.print") as output:
            self.assertEqual(courier.start(), 0)
        engine.assert_not_called()
        messages = [str(call.args[0]) for call in output.call_args_list]
        self.assertIn("COURIER_START=HUD_RUNNING_ENGINE_OFF_RETAINED", messages)
        self.assertNotIn("COURIER_START=ENGINE_AND_HUD_LINKED", messages)

    def test_startup_install_is_explicit_and_only_calls_manager(self):
        fake = SimpleNamespace(returncode=0, stdout="COURIER_USER_STARTUP=INSTALLED_OWNED\\n", stderr="")
        with mock.patch.object(courier, "IS_WINDOWS", True), \
             mock.patch.object(courier.shutil, "which", return_value="powershell.exe"), \
             mock.patch.object(courier.subprocess, "run", return_value=fake) as call, \
             mock.patch("builtins.print"):
            self.assertEqual(courier.startup("install"), 0)
            cmd = call.call_args.args[0]
            self.assertIn("-LauncherPath", cmd)
            self.assertIn("Manage-Command-CourierStartup.ps1", str(cmd))
            self.assertIn("install", cmd)

    def test_launcher_and_script_keep_existing_hud_and_user_scope(self):
        cmd = (ROOT / "COMMAND-COURIER.cmd").read_text(encoding="utf-8")
        ps = (ROOT / "tools" / "Manage-Command-CourierStartup.ps1").read_text(encoding="utf-8")
        self.assertIn("command_courier.py", cmd)
        self.assertIn("SpecialFolder]::Startup", ps)
        self.assertIn("Command Courier.lnk", ps)
        self.assertIn("COURIER_STARTUP_FOREIGN_SHORTCUT_REFUSE", ps)
        self.assertNotIn("Register-ScheduledTask", ps)
        self.assertNotIn("New-Service", ps)
        self.assertIn("Reconcile-OriginalDesktopHUD.ps1", (ROOT / "command_courier.py").read_text())


if __name__ == "__main__":
    unittest.main()
