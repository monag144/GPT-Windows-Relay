#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import browser_manager as bm


class BrowserManagerTests(unittest.TestCase):
    def test_supported_browser_catalog_is_not_edge_only(self):
        by_id = {item["id"]: item for item in bm.BROWSER_DEFS}
        for browser_id in ("edge", "chrome", "brave", "vivaldi", "chromium", "opera"):
            self.assertEqual(by_id[browser_id]["family"], "chromium")
        self.assertEqual(by_id["firefox"]["family"], "firefox")
        self.assertEqual(by_id["chrome"]["setup_mode"], "cdp_auto")
        self.assertEqual(by_id["edge"]["setup_mode"], "cdp_auto")
        self.assertEqual(by_id["firefox"]["setup_mode"], "firefox_temp_auto")

    def test_firefox_setup_is_zero_touch_and_connection_verified(self):
        src = Path(bm.__file__).read_text(encoding="utf-8")
        self.assertIn("GPT_CONSUMER_FIREFOX_ONE_CLICK_TEMP_ADDON_V1", src)
        self.assertIn('"ensure-addon"', src)
        self.assertIn('"--manifest-path"', src)
        self.assertIn('"--profile-path"', src)
        self.assertIn("GPT_CONSUMER_FIREFOX_PROFILE_IDENTITY_V1", src)
        self.assertIn('"close-profile"', src)
        self.assertIn("wait_for_browser_connection", src)
        firefox = next(item for item in bm.BROWSER_DEFS if item["id"] == "firefox")
        self.assertEqual(firefox["setup_mode"], "firefox_temp_auto")

    def test_chrome_setup_is_zero_touch_and_connection_verified(self):
        src = Path(bm.__file__).read_text(encoding="utf-8")
        self.assertIn("chromium_extension_setup.ps1", src)
        self.assertIn("devtools_protocol", src)
        self.assertIn("wait_for_browser_connection", src)
        self.assertNotIn("os.startfile(str(extension))", src)

    def test_chrome_launch_auto_restores_session_integration(self):
        src = Path(bm.__file__).read_text(encoding="utf-8")
        self.assertIn('if browser.get("setup_mode") == "cdp_auto":', src)
        self.assertIn("_automatic_cdp_setup(browser, extension, profile, url)", src)
        self.assertIn("wait_for_browser_connection", src)
        self.assertIn('"setup_method": "devtools_protocol"', src)

    def test_chromium_helper_keeps_successful_session_alive(self):
        helper = bm.HERE / "runtime" / "chromium_extension_setup.ps1"
        if not helper.is_file():
            helper = bm.HERE.parent / "windows-relay" / "chromium_extension_setup.ps1"
        src = helper.read_text(encoding="utf-8")
        self.assertIn("Target.createTarget", src)
        self.assertIn("$setupSucceeded=$true", src)
        self.assertIn("if(-not $setupSucceeded", src)
        self.assertIn("session_loaded=$true", src)

    def test_chromium_helper_recovers_profile_in_use_without_touching_normal_profile(self):
        helper = bm.HERE / "runtime" / "chromium_extension_setup.ps1"
        if not helper.is_file():
            helper = bm.HERE.parent / "windows-relay" / "chromium_extension_setup.ps1"
        src = helper.read_text(encoding="utf-8")
        self.assertIn("Stop-StaleOneClickBrowserProfile", src)
        self.assertIn("Get-OneClickProfileProcesses", src)
        self.assertIn("$browser.ExitCode -eq 21", src)
        self.assertIn("taskkill.exe /PID $proc.ProcessId /T /F", src)

    def test_chromium_helper_quotes_spaced_profile_and_recovers_legacy_bad_launch(self):
        helper = bm.HERE / "runtime" / "chromium_extension_setup.ps1"
        if not helper.is_file():
            helper = bm.HERE.parent / "windows-relay" / "chromium_extension_setup.ps1"
        src = helper.read_text(encoding="utf-8")
        self.assertIn("$profileArg='--user-data-dir=\"'", src)
        self.assertIn("$ProfilePath.Contains(' ')", src)
        self.assertIn("$legacyBrokenProfile", src)
        self.assertIn("$profileArg,", src)
        self.assertNotIn("('--user-data-dir='+$ProfilePath)", src)

    def test_runtime_paths_are_environment_derived_not_username_specific(self):
        manager = Path(bm.__file__).read_text(encoding="utf-8")
        helper = bm.HERE / "runtime" / "chromium_extension_setup.ps1"
        if not helper.is_file():
            helper = bm.HERE.parent / "windows-relay" / "chromium_extension_setup.ps1"
        helper_src = helper.read_text(encoding="utf-8")
        self.assertIn('os.environ.get("LOCALAPPDATA"', manager)
        self.assertIn('os.environ.get("APPDATA"', manager)
        self.assertIn("$ProfilePath", helper_src)
        self.assertNotIn("C:\\Users\\", manager)
        self.assertNotIn("C:\\Users\\", helper_src)

    def test_prepared_extension_has_browser_specific_identity(self):
        old_here, old_appdata, old_local = bm.HERE, bm.APPDATA, bm.LOCALAPPDATA
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                bm.HERE = root / "consumer"
                bm.APPDATA = root / "appdata"
                bm.LOCALAPPDATA = root / "local"

                runtime = bm.HERE / "runtime"
                extension = runtime / "extension"
                extension.mkdir(parents=True)
                (extension / "manifest.json").write_text('{"manifest_version":3}', encoding="utf-8")
                (extension / "service_worker.js").write_text("worker", encoding="utf-8")
                (runtime / "content.js").write_text("canonical-content", encoding="utf-8")

                config_dir = bm.APPDATA / "GPTWindowsRelayConsumer"
                config_dir.mkdir(parents=True)
                (config_dir / "bridge.json").write_text(
                    json.dumps({"version": 1, "host": "127.0.0.1", "port": 8766, "token": "x" * 40}),
                    encoding="utf-8",
                )

                prepared = bm.prepared_extension_path("chrome")
                config = (prepared / "config.js").read_text(encoding="utf-8")
                self.assertIn("RELAY_PORT = 8766", config)
                self.assertIn("RELAY_BROWSER_ID = \"chrome\"", config)
                self.assertEqual((prepared / "content.js").read_text(encoding="utf-8"), "canonical-content")
        finally:
            bm.HERE, bm.APPDATA, bm.LOCALAPPDATA = old_here, old_appdata, old_local

    def test_custom_browser_choice_is_persisted_without_installing_browser(self):
        old_settings = bm.SETTINGS_PATH
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                bm.SETTINGS_PATH = root / "settings.json"
                exe = root / "my-browser.exe"
                exe.write_bytes(b"MZ")
                selected = bm.set_custom_browser(str(exe), "My Browser")
                self.assertTrue(selected["id"].startswith("custom-"))
                saved = json.loads(bm.SETTINGS_PATH.read_text(encoding="utf-8"))
                self.assertEqual(saved["browser_id"], selected["id"])
                self.assertEqual(saved["custom_browser"]["id"], selected["id"])
                self.assertEqual(saved["custom_browser"]["name"], "My Browser")
        finally:
            bm.SETTINGS_PATH = old_settings


    def test_firefox_out_of_band_recovery_prompt_uses_managed_profile(self):
        browser = {"id": "firefox", "family": "firefox", "supported": True}
        with mock.patch.object(bm, "detect_browsers", return_value=[browser]), \
             mock.patch.object(bm, "_run_firefox_adapter", return_value={"ok": True, "action": "send-chatgpt-prompt"}) as run:
            result = bm.send_out_of_band_recovery_prompt("firefox", "RECOVERY TEST")
        self.assertTrue(result["ok"])
        args = run.call_args.args
        self.assertEqual(args[0], "send-chatgpt-prompt")
        self.assertIn("--prompt-b64", args)
        encoded=args[args.index("--prompt-b64")+1]
        self.assertEqual(base64.b64decode(encoded).decode("utf-8"),"RECOVERY TEST")
        self.assertNotIn("--prompt-text", args)
        self.assertIn("--profile-path", args)

    def test_firefox_out_of_band_recovery_readback_uses_managed_profile(self):
        browser = {"id": "firefox", "family": "firefox", "supported": True}
        with mock.patch.object(bm, "detect_browsers", return_value=[browser]), \
             mock.patch.object(bm, "_run_firefox_adapter", return_value={"ok": True, "text": "ADVICE"}) as run:
            text = bm.read_out_of_band_chat("firefox")
        self.assertEqual(text, "ADVICE")
        self.assertEqual(run.call_args.args[0], "read-chatgpt-text")


if __name__ == "__main__":
    unittest.main()

def test_r27_edge_uses_cdp_auto_setup():
    edge = next(item for item in bm.BROWSER_DEFS if item["id"] == "edge")
    assert edge["setup_mode"] == "cdp_auto"


def test_r27_cdp_helper_is_used_for_edge(monkeypatch, tmp_path):
    browser = {"id":"edge","name":"Microsoft Edge","family":"chromium","setup_mode":"cdp_auto","path":"edge.exe","supported":True,"reason":""}
    monkeypatch.setattr(bm, "select_browser", lambda browser_id: browser)
    monkeypatch.setattr(bm, "profile_path", lambda browser_id: tmp_path / "profile")
    monkeypatch.setattr(bm, "prepared_extension_path", lambda browser_id: tmp_path / "extension")
    called = {}
    def fake_setup(b, extension, profile, url):
        called["browser"] = b["id"]
        return {"pid":1234,"extension_id":"edge-test"}
    monkeypatch.setattr(bm, "_automatic_cdp_setup", fake_setup)
    monkeypatch.setattr(bm, "wait_for_browser_connection", lambda browser_id, timeout=20.0: True)
    result = bm.open_extension_setup("edge")
    assert called["browser"] == "edge"
    assert result["setup_method"] == "devtools_protocol"
    assert result["connected"] is True
