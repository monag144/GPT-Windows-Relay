#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
CONSUMER = HERE.parent


class ConsumerAppContractTests(unittest.TestCase):
    def test_gui_is_the_consumer_control_center(self):
        src = (CONSUMER / "consumer_app.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.1.0"', src)
        self.assertIn('text="GO"', src)
        self.assertIn('text="Open ChatGPT"', src)
        self.assertIn('text="Setup Browser"', src)
        self.assertIn('text="Update"', src)
        self.assertIn("self.browser_combo", src)
        self.assertIn("choose_custom_browser", src)
        self.assertIn("updater.perform_update()", src)
        self.assertIn("APP_DISPLAY_VERSION", src)
        self.assertIn("oneclick-browser-setup", src)
        self.assertIn("No manual extension setup is required.", src)
        self.assertNotIn("Turn on Developer mode", src)
        self.assertNotIn("Choose Load unpacked", src)

    def test_layout_contract_keeps_go_and_update_visible(self):
        src = (CONSUMER / "consumer_app.py").read_text(encoding="utf-8")
        self.assertIn("frame.rowconfigure(5, weight=1, minsize=90)", src)
        self.assertIn('text="One-click GO upon entering prompt"', src)
        self.assertIn('settings_row.grid(row=6, column=0, sticky="ew"', src)
        self.assertIn('self.one_click_check.pack(side="left")', src)
        self.assertIn('text="Send on Enter"', src)
        self.assertIn('self.send_on_enter_check.pack(side="left"', src)
        self.assertIn('self.button_bar.grid(row=7, column=0, sticky="ew"', src)
        self.assertIn('"go_visible": visible(self.go_button)', src)
        self.assertIn('"setup_visible": visible(self.setup_button)', src)
        self.assertIn('"update_visible": visible(self.update_button)', src)

    def test_go_targets_the_selected_browser(self):
        src = (CONSUMER / "consumer_app.py").read_text(encoding="utf-8")
        self.assertIn('"target_browser": browser["id"]', src)
        self.assertIn("browser_manager.select_browser(browser[\"id\"])", src)
        self.assertIn("that browser's active ChatGPT tab", src)
        self.assertIn("browser-status?browser_id=", src)
        self.assertIn("if not self._browser_connected(browser)", src)

    def test_recovery_supervisor_obligation_is_visible_in_control_center(self):
        src = (CONSUMER / "consumer_app.py").read_text(encoding="utf-8")
        self.assertIn("GPT_CONSUMER_RECOVERY_STATUS_VISIBLE_V1", src)
        self.assertIn("recovery-supervisor.json", src)
        self.assertIn("OOB_WAITING_ADVICE", src)
        self.assertIn("RECOVERY STALLED", src)
        self.assertIn("RECOVERY FAILED", src)
        self.assertIn("recovery_status_line()", src)

    def test_bootstrap_provisions_runtime_but_does_not_choose_browser(self):
        src = (CONSUMER / "bootstrap.ps1").read_text(encoding="utf-8")
        self.assertIn("ONECLICK_PYTHON_READY=True", src)
        self.assertIn("ONECLICK_DEPENDENCIES_READY=True", src)
        self.assertIn("ONECLICK_RELAY_READY=True", src)
        self.assertIn("ONECLICK_BROWSER_POLICY=user_supplied", src)
        self.assertNotIn("Microsoft Edge is missing", src)
        self.assertNotIn("launch_chatgpt.ps1') -RestartExisting", src)
        self.assertIn("Install-PythonFallback", src)
        self.assertIn("https://www.python.org/ftp/python/", src)
        self.assertIn("Get-FileHash -Algorithm SHA256", src)
        self.assertIn("external_python_packages=0", src)
        self.assertIn("pyvenv.cfg", src)
        self.assertIn("Test-OneClickVenv", src)
        self.assertIn("Repairing incomplete One-Click Python environment", src)
        self.assertIn("Stop-OneClickRuntimeForRepair", src)

    def test_go_batch_bootstraps_then_launches_gui_directly(self):
        src = (CONSUMER / "GO.bat").read_text(encoding="utf-8")
        self.assertIn("bootstrap.ps1", src)
        self.assertIn("-NoBrowser -NoGui", src)
        self.assertIn('set "RUNTIME=%~dp0runtime"', src)
        self.assertIn('set "RUNTIME=%~dp0..\\windows-relay"', src)
        self.assertIn(".venv\\Scripts\\pythonw.exe", src)
        self.assertIn("consumer_app.py", src)

    def test_legacy_browser_wrapper_delegates_to_browser_manager(self):
        src = (CONSUMER / "launch_chatgpt.ps1").read_text(encoding="utf-8")
        self.assertIn("browser_manager.py", src)
        self.assertIn("'launch'", src)
        self.assertNotIn("Microsoft\\Edge", src)


    def test_windows_gui_has_named_single_instance_guard(self):
        src = (CONSUMER / "consumer_app.py").read_text(encoding="utf-8")
        self.assertIn('Local\\GPTOneClickGoConsumerGui', src)
        self.assertIn("def acquire_single_instance()", src)
        self.assertIn("CreateMutexW", src)
        self.assertIn("ERROR_ALREADY_EXISTS", src)
        self.assertIn("if not acquire_single_instance():", src)
        self.assertIn("release_single_instance()", src)


    def test_update_restart_releases_singleton_before_relaunch(self):
        src = (CONSUMER / "consumer_app.py").read_text(encoding="utf-8")
        self.assertIn("time.sleep(1.5)", src)
        self.assertIn("[sys.executable, \"-c\", restart_code, go]", src)
        self.assertIn("DETACHED_PROCESS", src)
        self.assertIn("self.root.destroy()", src)
        self.assertNotIn("os.startfile(str(HERE / \"GO.bat\"))", src)


    def test_package_builder_uses_isolated_temp_staging(self):
        src = (CONSUMER / "build-package.ps1").read_text(encoding="utf-8")
        self.assertIn("[System.IO.Path]::GetTempPath()", src)
        self.assertIn("GPT-OneClick-Go-build-", src)
        self.assertIn("$stage=Join-Path $buildRoot 'GPT-OneClick-Go'", src)
        self.assertNotIn("$stage=Join-Path $dist 'GPT-OneClick-Go'", src)
        self.assertIn("Remove-Item -LiteralPath $buildRoot", src)

    @unittest.skipUnless(
        sys.platform == "win32" and os.environ.get("CI", "").lower() != "true",
        "Interactive Windows GUI layout probe",
    )
    def test_windows_layout_probe_reports_visible_controls(self):
        proc = subprocess.run(
            [sys.executable, str(CONSUMER / "consumer_app.py"), "--layout-probe"],
            cwd=CONSUMER,
            text=True,
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertTrue(payload["ok"], payload)
        self.assertEqual(payload["version"], "1.1.0")
        self.assertGreaterEqual(payload["revision"], 10)
        self.assertIn("r", payload["display_version"])
        self.assertTrue(all(item["go_visible"] for item in payload["results"]))
        self.assertTrue(all(item["setup_visible"] for item in payload["results"]))
        self.assertTrue(all(item["update_visible"] for item in payload["results"]))


if __name__ == "__main__":
    unittest.main()
