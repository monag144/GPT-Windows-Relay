"""Read-only native runner readiness and error-code regression checks.

These tests mock the Windows process; no local relay is started.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import desktop_native_relay as native


class NativeRunnerReadinessTests(unittest.TestCase):
    def test_existing_runner_is_not_restarted(self):
        with mock.patch.object(native, "runner_active", return_value=True), \
             mock.patch.object(native.subprocess, "Popen") as start:
            native.launch_runner_if_absent()
            start.assert_not_called()

    def test_startup_checks_process_lock_before_reporting_success(self):
        with mock.patch.object(native, "runner_active", side_effect=[False, False, True]), \
             mock.patch.object(native.subprocess, "Popen") as start, \
             mock.patch.object(native.time, "sleep"):
            start.return_value.poll.return_value = None
            native.launch_runner_if_absent()
            start.assert_called_once()

    def test_child_exit_before_lock_is_reported(self):
        with mock.patch.object(native, "runner_active", return_value=False), \
             mock.patch.object(native.subprocess, "Popen") as start:
            start.return_value.poll.return_value = 1
            with self.assertRaisesRegex(RuntimeError, "NATIVE_RUNNER_EXITED_BEFORE_STARTUP"):
                native.launch_runner_if_absent()

    def test_status_supports_loop_error_metadata(self):
        with mock.patch.object(native, "configuration", return_value={"armed": True, "off": False, "auto_send": True}), \
             mock.patch.object(native, "runner_active", return_value=False), \
             mock.patch.object(native.STATUS, "exists", return_value=False):
            status = native.get_status()
        self.assertIn("runner_error_type", status)
        self.assertIn("runner_error_stage", status)
        self.assertFalse(status["native_running"])


if __name__ == "__main__":
    unittest.main()
