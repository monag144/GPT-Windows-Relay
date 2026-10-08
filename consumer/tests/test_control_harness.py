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
            self.assertTrue(name.startswith("INCIDENT_")); self.assertIn("EXAMPLE_FAILURE",name); self.assertNotIn("CURRENT",name); self.assertNotIn("AUTHORITATIVE",name); self.assertEqual(Path(r["path"]).parent.name,"incidents")
    def test_improvement_gate_fails_closed(self):
        b={"test_failures":0,"canary_success":True,"side_effect_replays":0,"user_rescues":0,"data_loss_events":0,"delivery_success_rate":0.9,"duplicate_bytes_avoided":0,"median_latency_ms":1000}
        good={**b,"delivery_success_rate":0.95,"duplicate_bytes_avoided":100,"target_incident_closed":True}
        bad={**good,"user_rescues":1}
        self.assertTrue(ch.evaluate_improvement(b,good)["promote"]); self.assertFalse(ch.evaluate_improvement(b,bad)["promote"])

    def test_runtime_source_gate_rejects_consumer_contaminated_main_runner(self):
        bad_main="GPTWindowsRelayConsumer Local\\GPTWindowsRelayConsumerSupervisor --config $config --state-dir $stateDir server"
        consumer_run="GPTWindowsRelayConsumer Local\\GPTWindowsRelayConsumerSupervisor --config $config --state-dir $stateDir server"
        control="$run=Join-Path $root 'run-control.ps1'"
        cutover="rollback_watchdog_started start_watchdog(ns.live) wait_hud_process rollback_hud_ready"
        verdict=ch.validate_windows_runtime_contract(bad_main,consumer_run,control,cutover)
        self.assertFalse(verdict["ok"]); self.assertIn("main_runner_not_consumer",verdict["blockers"])

    def test_runtime_transition_gate_requires_distinct_relays_and_hud(self):
        good=ch.evaluate_runtime_transition({"main_8766":True,"consumer_8767":True,"main_pid":1,"consumer_pid":2,"hud_processes":1,"firefox_runtime":"v17","helper_finalized":True})
        bad=ch.evaluate_runtime_transition({"main_8766":True,"consumer_8767":True,"main_pid":1,"consumer_pid":1,"hud_processes":0,"firefox_runtime":"","helper_finalized":False})
        self.assertTrue(good["ok"]); self.assertFalse(bad["ok"]); self.assertIn("one_hud",bad["blockers"])

    def test_operation_budget_makes_rotation_p0(self):
        x=ch.assess_engineering_operation_budget(77,current_series=8)
        self.assertEqual(x["remaining_after_current"],23)
        self.assertEqual(x["rotation_priority"],"P0")
        self.assertTrue(x["rotation_build_due"])
        self.assertEqual(x["next_chat_title"],"💻PC Engineering 9🔧")

    def test_pce9_rotation_budget_is_p0(self):
        x=ch.assess_engineering_operation_budget(78,current_series=8)
        self.assertEqual(x["rotation_priority"],"P0"); self.assertEqual(x["remaining_after_current"],22); self.assertEqual(x["next_chat_title"],"💻PC Engineering 9🔧")

    def test_current_series_budget_computes_generic_successor(self):
        x=ch.assess_engineering_operation_budget(3,current_series=10)
        self.assertEqual(x["current_series"],10)
        self.assertEqual(x["next_chat_title"],"💻PC Engineering 11🔧")
        self.assertEqual(x["remaining_after_current"],97)

    def test_contract_contains_required_methods(self):
        c=ch.build_control_harness_contract("consumer-20261004T000000Z-deadbeef")
        self.assertEqual(c["version"],3)
        self.assertEqual(c["turn_discipline"]["read_every_turn"],["consumer/control_harness.py","windows-relay/TASKS.md","docs/roadmap/ROADMAP_2026-10-08T0020Z_PCE10_CONTROLLED_RECONCILIATION.md","docs/windows-relay-mission-and-roadmap.md"])
        self.assertEqual(c["turn_discipline"]["canonical_windows_repository"],"monag144/GPT-Windows-Relay")
        self.assertTrue(c["turn_discipline"]["sandwich_required"])
        self.assertEqual(c["turn_discipline"]["audit_every_engineering_turns"],5)
        self.assertIn("repair the harness",c["turn_discipline"]["harness_hole_rule"].lower())
        self.assertEqual(c["test_runtime"]["default_runner"],"unittest")
        self.assertIn("capability-probe",c["test_runtime"]["external_runner_rule"])
        self.assertIn("Executable existence is not proof",c["test_runtime"]["external_runner_rule"])
        self.assertEqual(c["migration_evidence"]["source_repository"],"monag144/GPT-Termux-Relay")
        self.assertEqual(c["migration_evidence"]["source_commit"],"249e3bb46c6ea57968d9ecf5157d73867a7f918d")
        self.assertIn("Git blob SHA",c["migration_evidence"]["verification_rule"])
        self.assertIn("non-manifest whitespace error blocks promotion",c["migration_evidence"]["diff_check_rule"])
        self.assertEqual(c["incident_logging"]["method"],"write_incident"); self.assertEqual(c["runtime_gates"]["source_contract_method"],"validate_windows_runtime_contract"); self.assertEqual(c["runtime_gates"]["browser_discovery_settle"]["settle_ms"],500); self.assertEqual(c["runtime_gates"]["browser_discovery_settle"]["stale_pending_lease_ms"],5000); self.assertIn("re-armed",c["runtime_gates"]["browser_discovery_settle"]["rule"]); self.assertEqual(c["reflection"]["method"],"append_reflection"); self.assertEqual(c["data_policy"]["method"],"record_once"); self.assertEqual(c["continuous_improvement"]["method"],"evaluate_improvement"); self.assertIn("live-canary",c["continuous_improvement"]["cycle"])
if __name__=='__main__': unittest.main()
