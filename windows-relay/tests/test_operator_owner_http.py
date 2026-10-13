"""Isolated localhost HTTP tests: no production process, shell, or Firefox."""
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import windows_relay as wr  # noqa: E402


def packet(action_id="OWNER-HTTP-001"):
    return wr.OPEN + "\n" + json.dumps({
        "version": 1, "platform": "windows", "action": "EXEC",
        "id": action_id, "session": "default", "shell": "python",
        "command": "print('NO_REAL_EXECUTION')", "timeout": 10,
    }) + "\n" + wr.CLOSE


def metadata(pkt):
    import hashlib
    aid = wr.extract(pkt).id
    return {
        "issuance": {"id": aid, "session": "default",
                     "packet_hash": hashlib.sha256(pkt.encode("utf-8")).hexdigest()},
        "owner": {"conversation_key": "https://chatgpt.com/c/native-test",
                  "session": "default", "tab_id": 29},
    }


class OperatorBindingHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = wr.State(Path(self.temp.name) / "state.json")
        self.state.set_armed(True)
        self.server = wr.Server(("127.0.0.1", 0), "test-only-bearer", self.state)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup_server)

    def cleanup_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def post(self, path, body, token="test-only-bearer"):
        req = urllib.request.Request(
            "http://127.0.0.1:" + str(self.server.server_address[1]) + path,
            data=json.dumps(body).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json",
                     "X-GPT-Windows-Relay-Token": token},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as r:
            return r.code, json.loads(r.read().decode())

    def test_unpaired_request_cannot_trigger_prompt(self):
        with mock.patch.object(wr, "confirm_owner_on_windows_desktop",
                               side_effect=AssertionError("must not prompt")):
            code, response = self.post("/owner-bind-request",
                                       {"owner": metadata(packet())["owner"]}, token="incorrect")
        self.assertEqual((code, response["error"]), (401, "unauthorized"))

    def test_denied_operator_confirmation_does_not_execute(self):
        pkt = packet()
        with mock.patch.object(wr, "confirm_owner_on_windows_desktop", return_value=False):
            code, response = self.post("/owner-bind-request",
                                       {"owner": metadata(pkt)["owner"]})
        self.assertEqual((code, response["detail"]), (400, "operator_confirmation_declined"))
        with mock.patch.object(wr, "execute", side_effect=AssertionError("must not run")):
            code, response = self.post("/action", {"packet": pkt, **metadata(pkt)})
        self.assertEqual((code, response["detail"]), (400, "conversation_owner_mismatch"))
        self.assertFalse(self.state.data["processed"])

    def test_approved_owner_runs_mocked_action_only_once(self):
        pkt = packet("OWNER-HTTP-ONCE")
        m = metadata(pkt)
        with mock.patch.object(wr, "confirm_owner_on_windows_desktop", return_value=True):
            code, response = self.post("/owner-bind-request", {"owner": m["owner"]})
        self.assertEqual(code, 200, response)
        self.assertEqual(self.state.data["conversation_owner"]["authorization"], "operator")
        action = wr.extract(pkt)
        raw = {
            "version": 1, "platform": "windows", "id": action.id,
            "session": "default", "action": "EXEC", "shell": "python",
            "status": "OK", "exit_code": 0, "cwd": self.temp.name,
            "started_at": wr.now(), "finished_at": wr.now(), "duration_ms": 1,
            "stdout": "MOCKED_CANARY_OK", "stderr": "",
        }
        with mock.patch.object(wr, "execute", return_value=raw) as exec_mock:
            code, first = self.post("/action", {"packet": pkt, **m})
            code2, second = self.post("/action", {"packet": pkt, **m})
        self.assertEqual((code, code2), (200, 200))
        self.assertIn("MOCKED_CANARY_OK", first["result"])
        self.assertIn("MOCKED_CANARY_OK", second["result"])
        self.assertIn('"replayed": true', second["result"].lower())
        exec_mock.assert_called_once()

    def test_concurrent_operator_prompt_is_refused(self):
        self.server.operator_prompt_lock.acquire()
        try:
            with mock.patch.object(wr, "confirm_owner_on_windows_desktop",
                                   side_effect=AssertionError("no second prompt")):
                code, response = self.post("/owner-bind-request",
                                           {"owner": metadata(packet())["owner"]})
        finally:
            self.server.operator_prompt_lock.release()
        self.assertEqual((code, response["detail"]), (400, "operator_confirmation_busy"))


if __name__ == "__main__":
    unittest.main()
