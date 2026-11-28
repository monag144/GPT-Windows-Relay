"""Independent native ChatGPT desktop relay acceptance tests (no shell/UIA side effects)."""
from __future__ import annotations
import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import desktop_native_relay as native
import windows_relay as wr


def packet(aid="NATIVE-TEST-001", command="echo harmless"):
    return wr.OPEN + "\n" + json.dumps({
        "version": 1, "platform": "windows", "action": "EXEC",
        "session": "desktop.native", "id": aid,
        "shell": "cmd", "command": command,
    }) + "\n" + wr.CLOSE


class NativeDesktopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        for field, value in {
            "HOME": self.folder,
            "CONFIG": self.folder / "control.json",
            "STATE": self.folder / "state.json",
            "OUTBOX": self.folder / "outbox",
            "STATUS": self.folder / "status.json",
            "LOCK": self.folder / "process.lock",
        }.items():
            patcher = mock.patch.object(native, field, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def state(self):
        state = wr.State(native.STATE)
        state.set_armed(True)
        state.data["outbound_owner"] = "windows"
        state.save()
        return state

    def test_first_install_persistent_native_arming(self):
        first = native.configuration()
        self.assertTrue(first["armed"])
        self.assertFalse(first["trust_visible_desktop_packets"])
        native.update_control("stop")
        self.assertFalse(native.configuration()["armed"])
        self.assertTrue(native.stop_requested())
        native.update_control("arm")
        self.assertTrue(native.configuration()["armed"])
        native.update_control("off")
        self.assertTrue(native.configuration()["off"])

    def test_explicit_output_intake_replaces_transcript_scanner(self):
        state=self.state()
        aid="COURIER-NATIVE-TEST-001"
        for field, value in {
            "OUTPUT_REQUESTS":self.folder/"explicit-output-requests",
            "OUTPUT_RECEIPTS":self.folder/"explicit-output-receipts",
        }.items():
            patch=mock.patch.object(native,field,value)
            patch.start()
            self.addCleanup(patch.stop)
        with mock.patch.object(native,"execute_with_stop") as execute, \
             mock.patch.object(native.subprocess,"run") as process:
            native.queue_explicit_output("Hello independent destination",aid=aid)
            self.assertEqual(native.reconcile_explicit_output_requests(state),1)
        execute.assert_not_called()
        process.assert_not_called()
        self.assertEqual(state.outbound_lookup(aid)["wire_format"],"plain_text")
        self.assertEqual(state.outbound_lookup(aid)["phase"],"READY")
        self.assertNotIn("read_scan(",(Path(native.__file__).read_text(encoding="utf-8")))

    def test_process_persists_once_and_queues_native_result(self):
        state = self.state()
        raw = {
            "version": 1, "platform": "windows", "id": "NATIVE-TEST-001",
            "session": "desktop.native", "action": "EXEC", "shell": "cmd",
            "status": "OK", "exit_code": 0, "cwd": str(self.folder),
            "started_at": wr.now(), "finished_at": wr.now(), "duration_ms": 1,
            "stdout": "harmless", "stderr": "",
        }
        with mock.patch.object(native, "execute_with_stop", return_value=raw) as run:
            native.process_packet(packet(), state)
            native.process_packet(packet(), state)
        run.assert_called_once()
        self.assertEqual(state.lookup("NATIVE-TEST-001")["status"], "OK")
        self.assertEqual(state.outbound_lookup("NATIVE-TEST-001")["phase"], "READY")

    def test_result_delivery_has_unique_receipt_and_marks_submitted(self):
        state = self.state()
        native.configuration()
        raw = {
            "version": 1, "platform": "windows", "id": "NATIVE-TEST-001",
            "session": "desktop.native", "action": "EXEC", "shell": "cmd",
            "status": "OK", "exit_code": 0, "cwd": str(self.folder),
            "started_at": wr.now(), "finished_at": wr.now(), "duration_ms": 1,
            "stdout": "done", "stderr": "",
        }
        with mock.patch.object(native, "execute_with_stop", return_value=raw):
            native.process_packet(packet(), state)
        fake = SimpleNamespace(returncode=0, stdout="RESULT=HEARTBEAT_SUBMITTED\n", stderr="")
        with mock.patch.object(native.shutil, "which", return_value="powershell.exe"), \
             mock.patch.object(native.subprocess, "run", return_value=fake) as call:
            native.deliver(state, "NATIVE-TEST-001")
        self.assertEqual(state.outbound_lookup("NATIVE-TEST-001")["phase"], "SUBMITTED")
        args = call.call_args.args[0]
        self.assertIn("-NativeReceiptMarker", args)
        receipt = args[args.index("-NativeReceiptMarker") + 1]
        self.assertIn(receipt, native.OUTBOX.joinpath("NATIVE-TEST-001.txt").read_text(encoding="utf-8"))

    def test_ambiguous_send_is_never_retried(self):
        state = self.state()
        native.configuration()
        raw = {
            "version": 1, "platform": "windows", "id": "NATIVE-TEST-001",
            "session": "desktop.native", "action": "EXEC", "shell": "cmd",
            "status": "OK", "exit_code": 0, "cwd": str(self.folder),
            "started_at": wr.now(), "finished_at": wr.now(), "duration_ms": 1,
            "stdout": "done", "stderr": "",
        }
        with mock.patch.object(native, "execute_with_stop", return_value=raw):
            native.process_packet(packet(), state)
        result = SimpleNamespace(returncode=5, stdout="UIA_GUARDED_SEND_BUTTON_CLICK_BEGIN\n", stderr="")
        with mock.patch.object(native.shutil, "which", return_value="powershell.exe"), \
             mock.patch.object(native.subprocess, "run", return_value=result) as sender:
            native.deliver(state, "NATIVE-TEST-001")
            native.deliver(state, "NATIVE-TEST-001")
        sender.assert_called_once()
        self.assertEqual(state.outbound_lookup("NATIVE-TEST-001")["phase"], "SUBMIT_UNCERTAIN")


if __name__ == "__main__":
    unittest.main()
