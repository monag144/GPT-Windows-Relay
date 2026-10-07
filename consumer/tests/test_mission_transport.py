#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import mission_transport as mt


class MissionTransportTests(unittest.TestCase):
    def test_unicode_and_multiline_round_trip(self):
        mission = "Build this thing.\nUnicode: 🦊 café — 漢字\nCode: print('hello')"
        mission_id = "consumer-20261004T003000Z-deadbeef"
        mid, message = mt.build_mission_message(mission, mission_id)
        self.assertEqual(mid, mission_id)
        self.assertEqual(mt.decode_mission_message(message), mission)
        self.assertIn("Base64", message)
        self.assertNotIn(mission, message)


    def test_first_consumer_prompt_primes_canonical_sandwich_contract(self):
        _, message = mt.build_mission_message(
            "test mission",
            "consumer-20261004T003000Z-acde1234",
        )
        self.assertIn("WINDOWS RELAY RENDERING CONTRACT", message)
        self.assertIn("one FINAL assistant response", message)
        self.assertIn("BARE Markdown fence with no language tag", message)
        self.assertIn("Never put a relay packet in commentary", message)
        self.assertIn("Reply to this with the sandwich technique", message)

    def test_machine_readable_relay_harness_is_always_embedded(self):
        mission_id = "consumer-20261004T003000Z-acde5678"
        _, message = mt.build_mission_message("open notepad", mission_id)
        harness = mt.extract_harness_json(message)
        self.assertEqual(harness["mission_id"], mission_id)
        self.assertEqual(harness["control_harness"]["incident_logging"]["method"], "write_incident")
        self.assertEqual(harness["control_harness"]["reflection"]["method"], "append_reflection")
        self.assertEqual(harness["control_harness"]["data_policy"]["method"], "record_once")
        self.assertEqual(harness["relay_contract"]["platform"], "windows")
        self.assertEqual(harness["relay_contract"]["action"], "EXEC")
        self.assertIn("bare fenced GPT_WINDOWS_ACTION", harness["relay_contract"]["rendering"])
        self.assertEqual(harness["relay_contract"]["stdout_footer"], "Reply to this with the sandwich technique")
        self.assertEqual(harness["relay_contract"]["example"]["platform"], "windows")
        self.assertIn("Worked for X", harness["relay_contract"]["collapse_recovery"]["known_symptom"])
        self.assertEqual(mt.decode_mission_message(message), "open notepad")

    def test_empty_and_oversized_missions_fail(self):
        with self.assertRaises(mt.MissionError):
            mt.build_mission_message("   ")
        with self.assertRaises(mt.MissionError):
            mt.build_mission_message("x" * (mt.MAX_RAW_MISSION + 1))

    def test_invalid_mission_id_fails(self):
        with self.assertRaises(mt.MissionError):
            mt.build_mission_message("do it", "../bad")


if __name__ == "__main__":
    unittest.main()


def test_mission_contract_allows_normal_no_relay_completion():
    mission_id, message = mt.build_mission_message("Hi")
    harness = mt.extract_harness_json(message)
    assert "no_action_valid" in harness["relay_contract"]
    assert "do not fabricate" in message
