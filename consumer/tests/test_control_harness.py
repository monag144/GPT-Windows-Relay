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

    def test_runtime_source_gate_rejects_consumer_contaminated_main_runner(self):
        bad_main="GPTWindowsRelayConsumer Local\\GPTWindowsRelayConsumerSupervisor --config $config --state-dir $stateDir server"
        consumer_run="GPTWindowsRelayConsumer Local\\GPTWindowsRelayConsumerSupervisor --config $config --state-dir $stateDir server"
        control="$run=Join-Path $root 'run.ps1'"
        cutover="rollback_watchdog_started start_watchdog(ns.live) wait_hud_process rollback_hud_ready"
        verdict=ch.validate_windows_runtime_contract(bad_main,consumer_run,control,cutover)
        self.assertFalse(verdict["ok"]); self.assertIn("main_runner_not_consumer",verdict["blockers"])

    def test_runtime_transition_gate_requires_distinct_relays_and_hud(self):
        good=ch.evaluate_runtime_transition({"main_8766":True,"consumer_8767":True,"main_pid":1,"consumer_pid":2,"hud_processes":1,"firefox_runtime":"v17","helper_finalized":True})
        bad=ch.evaluate_runtime_transition({"main_8766":True,"consumer_8767":True,"main_pid":1,"consumer_pid":1,"hud_processes":0,"firefox_runtime":"","helper_finalized":False})
        self.assertTrue(good["ok"]); self.assertFalse(bad["ok"]); self.assertIn("one_hud",bad["blockers"])

    def test_operation_budget_stops_without_automatic_switching(self):
        early=ch.assess_engineering_operation_budget(77)
        self.assertEqual(early["remaining_after_current"],23)
        self.assertFalse(early["automatic_switching_allowed"])
        self.assertFalse(early["manual_handoff_required_after_current"])
        final=ch.assess_engineering_operation_budget(100)
        self.assertEqual(final["remaining_after_current"],0)
        self.assertTrue(final["manual_handoff_required_after_current"])
        self.assertIn("STOP",final["action_at_limit"])
        self.assertNotIn("next_chat_title",final)
        with self.assertRaises(ch.ControlHarnessError):
            ch.assess_engineering_operation_budget(101)

    def test_no_local_backup_rule_is_advisory_and_explicit(self):
        c = ch.build_control_harness_contract("PCE19")
        policy = c["local_backup_policy"]
        self.assertEqual(policy["mode"], "NO_ON_DEVICE_BACKUPS")
        self.assertEqual(policy["effective_date"], "2026-10-12")
        self.assertIn("Never create on-device", policy["rule"])
        self.assertIn("GitHub", policy["history"])
        self.assertIn("operator disposition", policy["irreplaceable_data"])
        self.assertIn("never a relay action authorization", policy["execution_policy"])
        self.assertNotIn("local_backup_policy", c["execution_policy"])
        self.assertTrue(ch.engineering_preflight("PCE19", 5)["ok"])

    def test_contract_uses_only_approved_script_for_handoff(self):
        c=ch.build_control_harness_contract("PCE16")
        self.assertEqual(c["agent_handoff"]["mode"],"user_requested_one_shot_only")
        self.assertIn("Run-Copy-Contents.cmd",c["agent_handoff"]["transport"])
        self.assertIn("next PCE series",c["agent_handoff"]["procedure"])
        self.assertNotIn("capture_policy",c)
        self.assertNotIn("rotation",c)

    def test_contract_contains_no_governance_gate(self):
        c=ch.build_control_harness_contract("PCE16")
        self.assertNotIn("github_audit_checkpoint", c)
        self.assertNotIn("twenty_operation_review", c)
        self.assertFalse(c["engineering_notes"]["required_every_issued_pce_operation"])
        self.assertIn("No GitHub audit", c["execution_policy"]["rule"])

    def test_operator_ownership_and_push_before_pull_workflow_is_advisory(self):
        c=ch.build_control_harness_contract("PCE18")
        owner=c["engineering_owner"]
        self.assertEqual(owner["primary"], "ChatGPT")
        self.assertEqual(owner["repository"], "monag144/GPT-Windows-Relay")
        self.assertIn("wip/windows-relay-rebuilt-resynced-2047-101026", owner["working_branch"])
        self.assertIn("pull --ff-only origin", owner["git_pull_cmd"])
        self.assertIn("verify and push remote commit", owner["delivery_sequence"])
        self.assertIn("major", owner["codex"].lower())
        self.assertIn("never a command admission gate", owner["non_governance"])
        self.assertTrue(ch.engineering_preflight("PCE18", 5)["ok"])
        self.assertEqual(ch.engineering_preflight("PCE18", 5)["blockers"], [])

    def test_contract_contains_required_methods(self):
        c=ch.build_control_harness_contract("consumer-20261004T000000Z-deadbeef")
        self.assertEqual(c["incident_logging"]["method"],"write_incident"); self.assertEqual(c["runtime_gates"]["source_contract_method"],"validate_windows_runtime_contract"); self.assertEqual(c["reflection"]["method"],"append_reflection"); self.assertEqual(c["data_policy"]["method"],"record_once"); self.assertEqual(c["continuous_improvement"]["method"],"evaluate_improvement"); self.assertIn("live-canary",c["continuous_improvement"]["cycle"])

    def test_all_ordinals_work_without_audit_receipts(self):
        for ordinal in (0, 1, 4, 5, 6, 9, 10, 15, 20, 25, 99, 100):
            with self.subTest(ordinal=ordinal):
                v=ch.engineering_preflight("PCE12", ordinal)
                self.assertTrue(v["ok"])
                self.assertFalse(v["audit_required"])
                self.assertFalse(v["review_due"])
                self.assertEqual(v["blockers"], [])

    def test_legacy_audit_receipt_cannot_block(self):
        for receipt in (None, {}, {"source":"wrong"}, {"path":"invalid"}):
            with self.subTest(receipt=receipt):
                v=ch.engineering_preflight("PCE12", 5, github_audit_receipt=receipt)
                self.assertTrue(v["ok"])
                self.assertFalse(v["github_audit_receipt_valid"])

    def test_invalid_arguments_still_raise(self):
        for series, op in (("PCE12", 101), ("PCE12", -1), ("Termux", 5), ("PCE12", True)):
            with self.subTest(series=series, op=op):
                with self.assertRaises(ch.ControlHarnessError): ch.engineering_preflight(series, op)
        with self.assertRaises(ch.ControlHarnessError):
            ch.engineering_preflight("PCE12", 5, max_ordinal=101)

    def test_blocked_operations_still_consume_ordinals(self):
        issued = [
            "PCE12.000-bootstrap", "PCE12.001-direct-new-chat-click",
            "PCE12.002-canonical-controls-read",
            "PCE12.003-bounded-canonical-index-and-preflight-discovery",
            "PCE12.004-source-index-and-preflight-contract",
            "PCE12.005-local-windows-authority-check",
            "PCE12.005-verified-cursor-new-chat",
        ]
        next_op = ch.assess_next_engineering_operation("PCE12", issued, 6)
        self.assertTrue(next_op["ok"])
        self.assertEqual(next_op["next_ordinal"], 6)
        self.assertEqual(next_op["historical_repeated_ordinals"], [5])
        self.assertFalse(ch.assess_next_engineering_operation("PCE12", issued, 5)["ok"])
        self.assertFalse(ch.assess_next_engineering_operation("PCE12", issued, 7)["ok"])

    def test_attempt_history_is_advisory(self):
        issued=["PCE12.005-REJECTED"]
        current=ch.engineering_preflight("PCE12", 6, attempted_action_ids=issued)
        repeated=ch.engineering_preflight("PCE12", 5, attempted_action_ids=issued)
        self.assertTrue(current["ok"])
        self.assertTrue(repeated["ok"])
        self.assertIn("attempted_ordinal_must_not_be_reused_or_skipped", repeated["sequence_advisory"]["blockers"])

    def test_attempt_history_rejects_cross_series_and_series_overflow(self):
        with self.assertRaises(ch.ControlHarnessError):
            ch.assess_next_engineering_operation("PCE12", ["PCE11.005-old"], 6)
        with self.assertRaises(ch.ControlHarnessError):
            ch.assess_next_engineering_operation("PCE12", ["PCE12.100-finished"], 101)

if __name__=='__main__': unittest.main()
