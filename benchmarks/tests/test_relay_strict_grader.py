"""Strict 90% grading contract; no Firefox, relay or network dependencies."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relay_strict_grader import assess, assess_case, grade

EVIDENCE = Path(__file__).resolve().parents[1] / "RELAY_STRICT_GRADES_2026-10-09T2258Z.json"


def sample(mode="observed", passed=9, attempted=10, planned=None, critical=True):
    c = {"id":"CASE", "name":"Synthetic strict grade check",
         "purpose":"Verify grade system, not a relay capability", "mode":mode,
         "passed":passed, "attempted":attempted,
         "critical":critical, "evidence":"synthetic unit test",
         "improvement":"No implementation changes in scoring tests"}
    if planned is not None:
        c["planned"] = planned
    return c


class StrictGradeTests(unittest.TestCase):
    def test_grade_89_99_fails(self):
        self.assertEqual(grade(89.99),"F")

    def test_grade_exact_90_passes(self):
        self.assertEqual(grade(90),"C")

    def test_grade_94_99_is_c(self):
        self.assertEqual(grade(94.99),"C")

    def test_grade_95_is_b(self):
        self.assertEqual(grade(95),"B")

    def test_grade_97_99_is_b(self):
        self.assertEqual(grade(97.99),"B")

    def test_grade_98_is_a(self):
        self.assertEqual(grade(98),"A")

    def test_grade_100_is_a(self):
        self.assertEqual(grade(100),"A")

    def test_grade_rejects_out_of_range(self):
        for n in (-1,101):
            with self.subTest(value=n),self.assertRaises(ValueError):grade(n)

    def test_80_percent_measured_is_fail(self):
        result=assess_case(sample(passed=4,attempted=5))
        self.assertEqual(result["grade"],"F")
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(result["observed_pass_percent"],80)

    def test_90_percent_measured_is_pass(self):
        result=assess_case(sample())
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["observed_pass_percent"],90)

    def test_not_run_has_no_fabricated_performance(self):
        result=assess_case(sample(mode="not_run",passed=None,attempted=None))
        self.assertIsNone(result["observed_pass_percent"])
        self.assertEqual(result["status"],"UNPROVEN")

    def test_coverage_zero_is_not_performance_zero(self):
        result=assess_case(sample(mode="coverage",passed=0,attempted=0,planned=60))
        self.assertEqual(result["coverage_percent"],0)
        self.assertIsNone(result["observed_pass_percent"])
        self.assertEqual(result["status"],"FAIL_COVERAGE")

    def test_coverage_high_but_bad_success_rate_fails(self):
        result=assess_case(sample(mode="coverage",passed=70,attempted=100,planned=100))
        self.assertEqual(result["coverage_percent"],100)
        self.assertEqual(result["observed_pass_percent"],70)
        self.assertEqual(result["status"],"FAIL")

    def test_coverage_89_percent_fails(self):
        result=assess_case(sample(mode="coverage",passed=89,attempted=89,planned=100))
        self.assertEqual(result["grade"],"F")
        self.assertEqual(result["status"],"FAIL_COVERAGE")

    def test_coverage_90_percent_passes(self):
        result=assess_case(sample(mode="coverage",passed=90,attempted=90,planned=100))
        self.assertEqual(result["status"],"PASS_COVERAGE")

    def test_negative_or_impossible_evidence_rejected(self):
        for case in (sample(passed=11,attempted=10),
                     sample(passed=-1,attempted=10),
                     sample(mode="coverage",passed=3,attempted=2,planned=5),
                     sample(mode="observed",passed=0,attempted=0),
                     sample(mode="not_run",passed=0,attempted=0)):
            with self.subTest(case=case),self.assertRaises(ValueError):assess_case(case)

    def test_real_evidence_has_28_unique_gates(self):
        report=assess(json.loads(EVIDENCE.read_text(encoding="utf-8")))
        self.assertEqual(report["gate_count"],28)
        self.assertEqual(len({x["id"] for x in report["cases"]}),28)

    def test_evidence_grade_never_treats_unproven_as_pass(self):
        report=assess(json.loads(EVIDENCE.read_text(encoding="utf-8")))
        self.assertEqual(report["passed_gates"],11)
        self.assertEqual(report["failed_gates"],7)
        self.assertEqual(report["unproven_gates"],10)
        self.assertEqual(report["proven_gate_coverage_percent"],39.29)
        self.assertEqual(report["overall_evidence_grade"],"F")
        self.assertEqual(report["overall_release_status"],"BLOCKED")

    def test_pending_029_is_not_classified_as_a_win_or_loss(self):
        report=assess(json.loads(EVIDENCE.read_text(encoding="utf-8")))
        self.assertEqual(report["pending_action"],
                         "PCE14.029-headless-zero-outer-geometry-fix-acceptance")
        self.assertEqual(next(x for x in report["cases"] if x["id"]=="G15")["observed_pass_percent"],0)

    def test_ci_red_remains_measured_fail(self):
        report=assess(json.loads(EVIDENCE.read_text(encoding="utf-8")))
        case=next(x for x in report["cases"] if x["id"]=="G05")
        self.assertEqual(case["status"],"FAIL")
        self.assertEqual(case["observed_pass_percent"],0)

    def test_critical_fail_blocks_otherwise_green_report(self):
        report=assess({"schema_version":1,"minimum_pass_percent":90,
                       "cases":[sample(passed=10,attempted=10),
                                dict(sample(mode="not_run",passed=None,attempted=None),id="MISSING")]})
        self.assertEqual(report["overall_release_status"],"BLOCKED")

    def test_duplicate_evidence_ids_rejected(self):
        with self.assertRaises(ValueError):
            assess({"schema_version":1,"minimum_pass_percent":90,
                    "cases":[sample(),sample()]})

    def test_invalid_schema_rejected(self):
        with self.assertRaises(ValueError):
            assess({"schema_version":2,"minimum_pass_percent":90,"cases":[sample()]})


if __name__=="__main__":
    unittest.main()
