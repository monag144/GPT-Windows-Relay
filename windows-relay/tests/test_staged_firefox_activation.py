import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

import staged_firefox_activation as activation


class StagedFirefoxActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.live = self.root / "live"
        self.backup = self.root / "backup"
        self.live.mkdir()
        self.backup.mkdir()
        rows = []
        for rel in activation.FILES:
            original = (self.backup / rel)
            staged = (self.live / rel)
            original.parent.mkdir(parents=True, exist_ok=True)
            staged.parent.mkdir(parents=True, exist_ok=True)
            original.write_bytes(b"ORIGINAL CONTENT" + rel.encode())
            staged.write_bytes(b"STAGED CONTENT" + rel.encode())
            rows.append({
                "relative_path": rel,
                "previous_sha256": activation.sha(original),
                "source_sha256": activation.sha(staged),
                "backup": str(original)
            })
        self.manifest = self.backup / "manifest.json"
        self.manifest.write_text(
            json.dumps({"operation": "PCE10.020",
                        "status": "STAGED_AWAITING_EXTENSION_RELOAD",
                        "files": rows}),
            encoding="utf-8"
        )
        (self.live / "firefox_adapter.py").write_text("# adapter", encoding="utf-8")
        (self.live / "extension" / "manifest.json").write_text(
            json.dumps({"name": activation.ADDON}), encoding="utf-8"
        )
        self.fake_python = self.root / "python.exe"
        self.fake_python.write_bytes(b"python")
        self.localappdata = self.root / "local"
        self.events = self.localappdata / "GPTWindowsRelay" / "browser-events.jsonl"
        self.events.parent.mkdir(parents=True)
        (self.events.parent / "state.json").write_text(json.dumps({"armed": True}),encoding="utf-8")
        self.url = "https://chatgpt.com/c/6ac6cf1e-c210-83e8-be8f-77f4b2ca53c1"

    def tearDown(self):
        self.tmp.cleanup()

    def test_preflight_is_bound_to_exact_manifest_and_live_hashes(self):
        self.assertEqual(len(activation.preflight(self.manifest, self.live)["files"]), 3)
        (self.live / "content.js").write_bytes(b"DRIFT")
        with self.assertRaisesRegex(RuntimeError, "STAGED_CONTENT_DRIFT"):
            activation.preflight(self.manifest, self.live)

    def test_fresh_event_requires_exact_url_and_datetime(self):
        old_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        self.events.write_text(json.dumps({"time": old_time,
            "event": "content_script_started", "detail": {"href": self.url}}) + "\n", encoding="utf-8")
        self.assertIsNone(activation.fresh_event(self.events, datetime.now(timezone.utc), self.url))

    def test_positive_activation_produces_canary_pending_without_resend(self):
        def fake_adapter(py, live, action, log, *args):
            if action == "refresh-tab":
                self.events.write_text(json.dumps({
                    "time": datetime.now(timezone.utc).isoformat(),
                    "event": "content_script_started",
                    "detail": {"href": self.url, "runtime": "test-revision"}
                }) + "\n", encoding="utf-8")
                return {"ok": True, "action": action, "invoked": True,
                        "selected_name": "Rename Current Chat", "firefox_pid": 9248}
            return {"ok": True, "action": action, "invoked": True, "firefox_pid": 9248}
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.localappdata)}), \
             patch.object(activation, "call_adapter", side_effect=fake_adapter), \
             patch.object(activation.time, "sleep", return_value=None):
            result = activation.activate(
                self.manifest, self.live, str(self.fake_python),
                self.url, "Rename Current Chat", delay=0, wait=1
            )
        self.assertEqual(result["status"], "ACTIVATED_EVENT_CONFIRMED_CANARY_PENDING")
        self.assertEqual(result["observed"]["href"], self.url)

    def test_operator_stop_blocks_runtime_mutation_even_when_staged(self):
        state_path = self.events.parent / "state.json"
        state_path.write_text(json.dumps({"armed": False}), encoding="utf-8")
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.localappdata)}), \
             patch.object(activation, "call_adapter") as call, \
             patch.object(activation.time, "sleep", return_value=None):
            result = activation.activate(self.manifest, self.live,
                str(self.fake_python), self.url, "Rename Current Chat", delay=0, wait=0)
        self.assertEqual(result["status"], "OPERATOR_STOPPED_NO_ACTION")
        call.assert_not_called()

    def test_failed_refresh_rolls_back_all_bytes(self):
        def fake_adapter(py, live, action, log, *args):
            if action == "refresh-tab":
                raise RuntimeError("REFRESH_FAILED")
            return {"ok": True, "action": action, "invoked": True, "firefox_pid": 9248}
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.localappdata)}), \
             patch.object(activation, "call_adapter", side_effect=fake_adapter), \
             patch.object(activation.time, "sleep", return_value=None):
            result = activation.activate(
                self.manifest, self.live, str(self.fake_python),
                self.url, "Rename Current Chat", delay=0, wait=0
            )
        self.assertEqual(result["status"], "ROLLBACK_FILES_EXACT")
        self.assertFalse(result["runtime_rollback_confirmed"])
        for rel in activation.FILES:
            self.assertEqual(
                activation.sha(self.backup / rel),
                activation.sha(self.live / rel)
            )


if __name__ == "__main__":
    unittest.main()
