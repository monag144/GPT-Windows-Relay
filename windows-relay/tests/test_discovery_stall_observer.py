from __future__ import annotations
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
import io
import contextlib

import discovery_stall_observer as observer


class DiscoveryStallObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.now = datetime(2026, 10, 8, 4, 20, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.temp.cleanup()

    def event(self, name, ident="PCE10.021", seconds_ago=784):
        return {
            "event": name,
            "time": (self.now - timedelta(seconds=seconds_ago)).isoformat(),
            "detail": {"packet_id": ident},
        }

    def test_784_second_discovery_is_flagged_without_backend_execution(self):
        result = observer.latest_unexecuted_discovery(
            [self.event("relay_packet_discovered")], {"processed": {}, "active_action": None},
            self.now)
        self.assertEqual(result["id"], "PCE10.021")
        self.assertEqual(result["age_seconds"], 784)
        self.assertFalse(result["replay_allowed"])

    def test_under_45_seconds_is_not_stalled(self):
        self.assertIsNone(observer.latest_unexecuted_discovery(
            [self.event("relay_packet_discovered", seconds_ago=44)],
            {"processed": {}}, self.now))

    def test_execution_or_durable_result_suppresses_false_stall(self):
        discovery = self.event("relay_packet_discovered")
        self.assertIsNone(observer.latest_unexecuted_discovery(
            [discovery, self.event("relay_action_execution_requested", seconds_ago=780)],
            {"processed": {}}, self.now))
        self.assertIsNone(observer.latest_unexecuted_discovery(
            [discovery], {"active_action": {"id": "PCE10.021"}}, self.now))
        self.assertIsNone(observer.latest_unexecuted_discovery(
            [discovery], {"processed": {"PCE10.021": {"status": "OK"}}}, self.now))

    def test_replay_suppressed_is_not_execution_proof(self):
        self.assertEqual(observer.latest_unexecuted_discovery([
            self.event("relay_packet_discovered"),
            self.event("relay_result_replay_suppressed", seconds_ago=780)],
            {"processed": {}}, self.now)["id"], "PCE10.021")

    def test_latest_packet_wins_and_operator_stop_quiets_watch(self):
        events = [
            self.event("relay_packet_discovered", "PCE10.020", seconds_ago=1000),
            self.event("relay_packet_discovered", "PCE10.021", seconds_ago=10),
        ]
        self.assertIsNone(observer.latest_unexecuted_discovery(events, {"processed": {}}, self.now))
        (self.base / "state.json").write_text(json.dumps({"armed": False}), encoding="utf-8")
        (self.base / "browser-events.jsonl").write_text(
            json.dumps(self.event("relay_packet_discovered")) + "\n", encoding="utf-8"
        )
        self.assertEqual(observer.poll(self.base, self.now)["state"], "PAUSED")

    def test_alert_dedupe_and_no_state_file_mutation(self):
        state = self.base / "state.json"
        state.write_text(json.dumps({"armed": True, "processed": {}}), encoding="utf-8")
        events = self.base / "browser-events.jsonl"
        events.write_text(json.dumps(self.event("relay_packet_discovered")) + "\n", encoding="utf-8")
        latch = self.base / "logs" / "latch.json"
        with patch.object(observer, "poll", return_value={
                "state": "DISCOVERY_STALLED", "id": "PCE10.021",
                "at": self.event("relay_packet_discovered")["time"],
                "age_seconds": 784, "replay_allowed": False
            }):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(observer.main(["--base", str(self.base), "--latch", str(latch)]), 0)
                self.assertEqual(observer.main(["--base", str(self.base), "--latch", str(latch)]), 0)
            self.assertEqual(out.getvalue().count("DISCOVERY_STALLED packet_id="), 1)
        self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["armed"], True)


if __name__ == "__main__":
    unittest.main()
