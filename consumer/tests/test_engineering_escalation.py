"""PCE12 ordinal, Codex escalation, and nonblocking review cadence."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import control_harness as ch


class EngineeringEscalationTests(unittest.TestCase):
    def test_six_repeated_failures_trigger_terra_medium(self):
        same = ["URL_NOT_FRESH"] * 6
        p = ch.assess_engineering_rescue(same, 18)
        self.assertTrue(p["codex_escalation_due"])
        self.assertEqual((p["codex_model"], p["codex_reasoning_effort"]),
                         ("gpt-5.6-terra", "medium"))

    def test_five_failures_not_yet_due(self):
        p = ch.assess_engineering_rescue(["URL_NOT_FRESH"] * 5, 18)
        self.assertFalse(p["codex_escalation_due"])

    def test_success_unknown_or_changed_class_breaks_streak(self):
        for history in (
            ["URL_NOT_FRESH"] * 5 + ["OK"],
            ["URL_NOT_FRESH"] * 5 + ["UNKNOWN"],
            ["URL_NOT_FRESH"] * 5 + ["UIA_NOT_FOUND"],
        ):
            self.assertFalse(ch.assess_engineering_rescue(history, 18)["codex_escalation_due"])

    def test_fifth_and_twentieth_slots_require_no_governance(self):
        for ordinal in (5, 10, 20, 100):
            v=ch.engineering_preflight("PCE12", ordinal)
            self.assertTrue(v["ok"])
            self.assertFalse(v["audit_required"])
            self.assertFalse(v["review_due"])
            self.assertEqual(v["blockers"], [])
        c=ch.build_control_harness_contract("PCE12")
        self.assertNotIn("github_audit_checkpoint", c)
        self.assertNotIn("twenty_operation_review", c)
        self.assertEqual(c["codex_escalation"]["model"], "gpt-5.6-terra")


if __name__ == "__main__":
    unittest.main()
