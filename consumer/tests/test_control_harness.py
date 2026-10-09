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

    def test_operation_budget_makes_rotation_p0(self):
        x=ch.assess_engineering_operation_budget(77)
        self.assertEqual(x["remaining_after_current"],23)
        self.assertEqual(x["rotation_priority"],"P0")
        self.assertTrue(x["rotation_build_due"])
        self.assertEqual(x["next_chat_title"],"💻PC Engineering 9🔧")

    def test_pce9_rotation_budget_is_p0(self):
        x=ch.assess_engineering_operation_budget(78)
        self.assertEqual(x["rotation_priority"],"P0"); self.assertEqual(x["remaining_after_current"],22); self.assertEqual(x["next_chat_title"],"💻PC Engineering 9🔧")

    def test_contract_contains_required_methods(self):
        c=ch.build_control_harness_contract("consumer-20261004T000000Z-deadbeef")
        self.assertEqual(c["incident_logging"]["method"],"write_incident"); self.assertEqual(c["runtime_gates"]["source_contract_method"],"validate_windows_runtime_contract"); self.assertEqual(c["reflection"]["method"],"append_reflection"); self.assertEqual(c["data_policy"]["method"],"record_once"); self.assertEqual(c["continuous_improvement"]["method"],"evaluate_improvement"); self.assertIn("live-canary",c["continuous_improvement"]["cycle"])

    @staticmethod
    def github_receipt(ordinal=5, series="PCE12"):
        first, last = ordinal - 5, ordinal - 1
        path = f"docs/audits/AUDIT_2026-10-09T0710Z_{series}_{first:03d}_{last:03d}_CHECKPOINT.md"
        sha = "a" * 40
        return {
            "repository": "monag144/GPT-Windows-Relay",
            "branch": "main",
            "source": "github_connector",
            "path": path,
            "start": first,
            "end": last,
            "commit_sha": sha,
            "file_sha": "b" * 40,
            "readback_verified": True,
            "url": f"https://github.com/monag144/GPT-Windows-Relay/blob/{sha}/{path}",
        }

    def test_github_audit_is_required_at_fifth_operation(self):
        result = ch.engineering_preflight("PCE12", 5)
        self.assertFalse(result["ok"])
        self.assertIn("github_checkpoint_audit_missing", result["blockers"])
        self.assertEqual(result["audit_expected"]["start"], 0)
        self.assertEqual(result["audit_expected"]["end"], 4)

    def test_github_readback_receipt_allows_five_turn_checkpoint(self):
        result = ch.engineering_preflight("PCE12", 5, github_audit_receipt=self.github_receipt())
        self.assertTrue(result["ok"], result["blockers"])
        self.assertTrue(result["github_audit_receipt_valid"])

    def test_github_audit_rejects_wrong_repository_branch_and_transport(self):
        for key, invalid in (
            ("repository", "monag144/GPT-Termux-Relay"),
            ("branch", "development"),
            ("source", "windows_relay"),
            ("readback_verified", False),
        ):
            with self.subTest(key=key):
                receipt = self.github_receipt()
                receipt[key] = invalid
                self.assertFalse(ch.engineering_preflight("PCE12", 5, github_audit_receipt=receipt)["ok"])

    def test_github_audit_rejects_wrong_range_path_and_uncommitted_receipt(self):
        for key, invalid in (
            ("start", 1),
            ("end", 5),
            ("path", "docs/audits/local-note.md"),
            ("commit_sha", ""),
            ("file_sha", "unverified"),
            ("url", "https://github.com/monag144/GPT-Termux-Relay"),
        ):
            with self.subTest(key=key):
                receipt = self.github_receipt()
                receipt[key] = invalid
                self.assertFalse(ch.engineering_preflight("PCE12", 5, github_audit_receipt=receipt)["ok"])

    def test_five_operation_cadence_is_exact(self):
        for ordinal in (0, 1, 4, 6, 9, 11):
            with self.subTest(ordinal=ordinal):
                verdict = ch.engineering_preflight("PCE12", ordinal)
                self.assertTrue(verdict["ok"])
                self.assertFalse(verdict["audit_required"])
        for ordinal in (10, 20, 100):
            with self.subTest(ordinal=ordinal):
                expected = ch.engineering_preflight("PCE12", ordinal)
                self.assertFalse(expected["ok"])
                self.assertEqual(expected["audit_expected"]["start"], ordinal - 5)
                self.assertEqual(expected["audit_expected"]["end"], ordinal - 1)
                verdict = ch.engineering_preflight("PCE12", ordinal, github_audit_receipt=self.github_receipt(ordinal))
                self.assertTrue(verdict["ok"], verdict["blockers"])

    def test_operation_budget_and_bad_series_fail_closed(self):
        for series, op in (("PCE12", 101), ("PCE12", -1), ("Termux", 5), ("PCE12", True)):
            with self.subTest(series=series, op=op):
                with self.assertRaises(ch.ControlHarnessError):
                    ch.engineering_preflight(series, op)
        with self.assertRaises(ch.ControlHarnessError):
            ch.engineering_preflight("PCE12", 5, max_ordinal=101)

    def test_contract_explicitly_mandates_github_first_audits(self):
        c = ch.build_control_harness_contract("PCE12")
        self.assertEqual(c["github_audit_checkpoint"]["method"], "engineering_preflight")
        self.assertEqual(c["github_audit_checkpoint"]["repository"], "monag144/GPT-Windows-Relay")
        self.assertIn("GitHub connector", c["github_audit_checkpoint"]["publication"])
        self.assertIn("no Windows Relay git push", c["github_audit_checkpoint"]["publication"])


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

    def test_attempt_ordinal_gate_applies_to_preflight(self):
        issued = ["PCE12.005-GOVERNANCE_BLOCKED"]
        allowed = ch.engineering_preflight("PCE12", 6, attempted_action_ids=issued)
        rejected = ch.engineering_preflight("PCE12", 5, attempted_action_ids=issued)
        self.assertTrue(allowed["ok"], allowed["blockers"])
        self.assertIn("attempted_ordinal_must_not_be_reused_or_skipped", rejected["blockers"])

    def test_attempt_history_rejects_cross_series_and_series_overflow(self):
        with self.assertRaises(ch.ControlHarnessError):
            ch.assess_next_engineering_operation("PCE12", ["PCE11.005-old"], 6)
        with self.assertRaises(ch.ControlHarnessError):
            ch.assess_next_engineering_operation("PCE12", ["PCE12.100-finished"], 101)

if __name__=='__main__': unittest.main()
