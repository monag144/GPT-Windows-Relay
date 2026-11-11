"""Black-box read-only host probe regression: safe even when the listener is live."""
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import relay_readonly_surface as surface  # noqa: E402


class EmptySocket:
    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False


class ReadOnlySurfaceTests(unittest.TestCase):
    @mock.patch.object(surface.socket, "create_connection", return_value=EmptySocket())
    @mock.patch.object(surface.urllib.request, "urlopen",
                       side_effect=urllib.error.HTTPError("http://127.0.0.1:8766/status", 401,
                                                         "Unauthorized", {}, None))
    def test_401_is_expected_auth_protection_not_backend_down(self, requested, connected):
        report = surface.listener_status()
        self.assertEqual(report["tcp"], "REACHABLE")
        self.assertEqual(report["http"], "EXPECTED_401")
        request = requested.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIsNone(request.get_header("X-GPT-Windows-Relay-Token"))

    @mock.patch.object(surface.socket, "create_connection", side_effect=OSError("refused"))
    def test_connect_failure_is_not_reported_as_live(self, connected):
        report = surface.listener_status()
        self.assertEqual(report["tcp"], "UNREACHABLE")
        self.assertEqual(report["http"], "UNKNOWN")

    def test_hash_mismatch_exposes_disk_drift_without_claiming_loaded_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            client = Path(tmp) / "client"
            for base, prefix in [(repo / "windows-relay", b"canonical"), (client, b"client")]:
                for name in ("content.js", "extension/content.js", "extension-persistent/content.js"):
                    path = base / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(prefix)
            result = surface.disk_hashes(repo, client)
            self.assertTrue(result["source_mirrors_equal"])
            self.assertTrue(result["client_mirrors_equal"])
            self.assertFalse(result["disk_source_equals_client"])
            self.assertIsNone(result["active_loaded_script_sha256"])
            self.assertEqual(result["active_loaded_script_status"], "NOT_VERIFIED")

    def test_missing_copy_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self.assertFalse(surface.disk_hashes(p, p)["source_mirrors_equal"])

    @mock.patch.object(surface, "listener_status", return_value={
        "tcp": "REACHABLE", "http": "EXPECTED_401", "port": 8766
    })
    @mock.patch.object(surface, "listener_pid", return_value={"state": "UNIQUE", "pid": 21})
    @mock.patch.object(surface, "disk_hashes", return_value={
        "source_mirrors_equal": True, "client_mirrors_equal": True,
        "disk_source_equals_client": False, "active_loaded_script_sha256": None
    })
    def test_scoreboard_does_not_infer_live_script_or_send(self, disk, pid, listener):
        s = surface.observe(Path("a"), Path("b"))
        self.assertEqual(s["capabilities"]["unauthenticated_endpoint_denied"], "PASS")
        self.assertEqual(s["capabilities"]["source_runtime_disk_parity"], "FAIL")
        self.assertEqual(s["capabilities"]["actual_loaded_runtime"], "NOT_RUN")
        self.assertEqual(s["capabilities"]["real_paste_send_and_receipt"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
