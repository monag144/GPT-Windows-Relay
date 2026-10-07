#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

import windows_relay as relay


class ConsumerMissionQueueTests(unittest.TestCase):
    def test_queue_is_durable_idempotent_and_acknowledged(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "state.json"
            state = relay.State(path)
            result = state.enqueue_mission("consumer-test-1", "mission text")
            self.assertTrue(result["queued"])
            self.assertEqual(state.pending_mission_count(), 1)
            self.assertEqual(state.next_mission()["text"], "mission text")

            duplicate = state.enqueue_mission("consumer-test-1", "mission text")
            self.assertTrue(duplicate["duplicate"])
            self.assertEqual(state.pending_mission_count(), 1)

            restarted = relay.State(path)
            self.assertEqual(restarted.next_mission()["id"], "consumer-test-1")
            self.assertTrue(restarted.ack_mission("consumer-test-1"))
            self.assertEqual(restarted.pending_mission_count(), 0)
            self.assertIsNone(restarted.next_mission())

    def test_mission_journal_persists_key_phases(self):
        with tempfile.TemporaryDirectory() as td:
            state = relay.State(Path(td) / "state.json")
            state.enqueue_mission("consumer-journal-1", "hello", "chrome")
            state.journal_browser_event("consumer_mission_text_set", {"mission_id":"consumer-journal-1","browser_id":"chrome"})
            state.journal_browser_event("consumer_mission_client_sync_divergence", {"mission_id":"consumer-journal-1","browser_id":"chrome"})
            self.assertTrue(state.ack_mission("consumer-journal-1"))
            rows=[__import__("json").loads(x) for x in state.mission_journal_path.read_text(encoding="utf-8").splitlines()]
            phases=[x["phase"] for x in rows]
            self.assertEqual(phases,["CREATED","PROMPT_INJECTED","CLIENT_SYNC_DIVERGENCE","ACKNOWLEDGED"])

    def test_mission_id_collision_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            state = relay.State(Path(td) / "state.json")
            state.enqueue_mission("consumer-test-2", "one")
            with self.assertRaises(relay.RelayError):
                state.enqueue_mission("consumer-test-2", "two")

    def test_queue_capacity_and_text_limit_are_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            state = relay.State(Path(td) / "state.json")
            for i in range(relay.MAX_PENDING_MISSIONS):
                state.enqueue_mission(f"consumer-cap-{i}", "x")
            with self.assertRaises(relay.RelayError):
                state.enqueue_mission("consumer-cap-over", "x")

        with tempfile.TemporaryDirectory() as td:
            state = relay.State(Path(td) / "state.json")
            with self.assertRaises(relay.RelayError):
                state.enqueue_mission("consumer-big-1", "x" * (relay.MAX_MISSION_TEXT + 1))



    def test_browser_targeting_prevents_cross_browser_mission_claims(self):
        with tempfile.TemporaryDirectory() as td:
            state = relay.State(Path(td) / "state.json")
            state.enqueue_mission("consumer-edge-1", "edge mission", "edge")
            state.enqueue_mission("consumer-chrome-1", "chrome mission", "chrome")

            self.assertIsNone(state.next_mission())
            self.assertEqual(state.next_mission("edge")["id"], "consumer-edge-1")
            self.assertEqual(state.next_mission("chrome")["id"], "consumer-chrome-1")
            self.assertEqual(state.pending_mission_count(), 2)

    def test_untargeted_legacy_mission_remains_available_to_browser_pollers(self):
        with tempfile.TemporaryDirectory() as td:
            state = relay.State(Path(td) / "state.json")
            state.enqueue_mission("consumer-legacy-1", "legacy")
            self.assertEqual(state.next_mission("edge")["id"], "consumer-legacy-1")
            self.assertEqual(state.next_mission("chrome")["id"], "consumer-legacy-1")

    def test_duplicate_id_cannot_change_browser_target(self):
        with tempfile.TemporaryDirectory() as td:
            state = relay.State(Path(td) / "state.json")
            state.enqueue_mission("consumer-browser-collision", "same", "edge")
            with self.assertRaises(relay.RelayError):
                state.enqueue_mission("consumer-browser-collision", "same", "chrome")

    def test_invalid_browser_id_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            state = relay.State(Path(td) / "state.json")
            with self.assertRaises(relay.RelayError):
                state.enqueue_mission("consumer-browser-invalid", "x", "../edge")
            with self.assertRaises(relay.RelayError):
                state.next_mission("../edge")


    def test_browser_presence_is_explicit_and_ephemeral(self):
        with tempfile.TemporaryDirectory() as td:
            state = relay.State(Path(td) / "state.json")
            self.assertFalse(state.browser_status("edge")["connected"])
            state.mark_browser_seen("edge", True)
            self.assertTrue(state.browser_status("edge")["connected"])
            state.mark_browser_disconnected("edge")
            self.assertFalse(state.browser_status("edge")["connected"])


    def test_relay_source_is_single_complete_module(self):
        source = (Path(relay.__file__).read_text(encoding="utf-8"))
        self.assertEqual(source.count("#!/usr/bin/env python3"), 1)
        self.assertEqual(source.count("class State:"), 1)
        self.assertEqual(source.count("class Handler("), 1)
        self.assertEqual(source.count("def main():"), 1)
        self.assertEqual(source.count("if __name__=='__main__': raise SystemExit(main())"), 1)
        self.assertIn("GPT_ONE_CLICK_BROWSER_QUEUE_TARGET_V1", source)
        self.assertIn("GPT_ONE_CLICK_BROWSER_STATUS_V1", source)

if __name__ == "__main__":
    unittest.main()
