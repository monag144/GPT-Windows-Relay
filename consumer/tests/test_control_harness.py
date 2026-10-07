from __future__ import annotations
import tempfile
from pathlib import Path
import unittest
import sys
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE.parent))
import control_harness as ch

class ControlHarnessTests(unittest.TestCase):
    def test_exact_record_dedupe_counts_instead_of_appending(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); a=ch.record_once("capture",b"same bytes",state_root=root); b=ch.record_once("capture",b"same bytes",state_root=root)
            self.assertTrue(a["accepted"]); self.assertFalse(b["accepted"]); self.assertTrue(b["duplicate"]); self.assertEqual(a["sha256"],b["sha256"]); self.assertEqual(b["duplicate_count"],1)
    def test_reflection_is_exactly_deduplicated(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); a=ch.append_reflection("m1","i1","learn","change",["e1"],state_root=root); b=ch.append_reflection("m1","i1","learn","change",["e1"],state_root=root)
            self.assertTrue(a["accepted"]); self.assertTrue(b["duplicate"]); self.assertEqual(len((root/"control-reflections.jsonl").read_text(encoding="utf-8").splitlines()),1)
    def test_incident_file_is_timestamped_and_small_record_style(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); r=ch.write_incident(root,"Example failure",{"Observation":"x","Corrective action":"y"}); name=Path(r["path"]).name
            self.assertTrue(name.startswith("INCIDENT_")); self.assertIn("EXAMPLE_FAILURE",name); self.assertNotIn("CURRENT",name); self.assertNotIn("AUTHORITATIVE",name)
    def test_improvement_gate_fails_closed(self):
        b={"test_failures":0,"canary_success":True,"side_effect_replays":0,"user_rescues":0,"data_loss_events":0,"delivery_success_rate":0.9,"duplicate_bytes_avoided":0,"median_latency_ms":1000}
        good={**b,"delivery_success_rate":0.95,"duplicate_bytes_avoided":100,"target_incident_closed":True}
        bad={**good,"user_rescues":1}
        self.assertTrue(ch.evaluate_improvement(b,good)["promote"]); self.assertFalse(ch.evaluate_improvement(b,bad)["promote"])

    def test_contract_contains_required_methods(self):
        c=ch.build_control_harness_contract("consumer-20261004T000000Z-deadbeef")
        self.assertEqual(c["incident_logging"]["method"],"write_incident"); self.assertEqual(c["reflection"]["method"],"append_reflection"); self.assertEqual(c["data_policy"]["method"],"record_once"); self.assertEqual(c["continuous_improvement"]["method"],"evaluate_improvement"); self.assertIn("live-canary",c["continuous_improvement"]["cycle"])
if __name__=='__main__': unittest.main()
