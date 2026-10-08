from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import control_harness as ch


class EngineeringGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in ch.MANDATORY_ENGINEERING_READS:
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("Control: " + rel + "\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def checkpoint(self, kind, low, high):
        folder = "audits" if kind == "AUDIT" else "reviews"
        p = self.root / "docs" / folder / (
            f"{kind}_2026-10-08T0430Z_PCE10_OPERATIONS_{low:03d}_{high:03d}.md"
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# CHECKPOINT COMPLETE\n" +
            "Independent attempted-operation evidence:\n" +
            "\n".join(f"- PCE10.{n:03d}: reviewed" for n in range(low, high + 1)) +
            "\nPromotion BLOCKED without live canary.\n" +
            "Source and rollback evidence reconciled.\n" * 10,
            encoding="utf-8"
        )
        return p

    def test_every_operation_reads_five_sources_including_procedure(self):
        result = ch.engineering_preflight(self.root, 21)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["reads"]), 5)
        self.assertIn("docs/relay-sandwich-procedure.md", result["reads"])
        self.assertFalse(result["mutation_authorized"])
        self.assertEqual(result["schedule"]["next_audit"], 25)
        self.assertEqual(result["schedule"]["next_review"], 40)

    def test_missing_procedure_blocks_every_operation(self):
        (self.root / "docs" / "relay-sandwich-procedure.md").unlink()
        with self.assertRaisesRegex(ch.ControlHarnessError, "mandatory control missing"):
            ch.engineering_preflight(self.root, 21)

    def test_audit_due_before_025_and_not_after(self):
        self.assertEqual(ch.due_engineering_checkpoints(25)["audit_window"], [20, 24])
        with self.assertRaisesRegex(ch.ControlHarnessError, "audit checkpoint missing"):
            ch.engineering_preflight(self.root, 25)
        self.checkpoint("AUDIT", 20, 24)
        result = ch.engineering_preflight(self.root, 25)
        self.assertEqual(result["checkpoints"]["audit"]["window"], [20, 24])
        self.assertFalse(result["schedule"]["review_due"])

    def test_review_due_before_020_and_040(self):
        self.assertEqual(ch.due_engineering_checkpoints(20)["review_window"], [0, 19])
        self.checkpoint("AUDIT", 15, 19)
        with self.assertRaisesRegex(ch.ControlHarnessError, "review checkpoint missing"):
            ch.engineering_preflight(self.root, 20)
        self.checkpoint("REVIEW", 0, 19)
        result = ch.engineering_preflight(self.root, 20)
        self.assertEqual(set(result["checkpoints"]), {"audit", "review"})
        self.assertEqual(ch.due_engineering_checkpoints(40)["review_window"], [20, 39])
        with self.assertRaisesRegex(ch.ControlHarnessError, "audit checkpoint missing"):
            ch.engineering_preflight(self.root, 40)
        self.checkpoint("AUDIT", 35, 39)
        with self.assertRaisesRegex(ch.ControlHarnessError, "review checkpoint missing"):
            ch.engineering_preflight(self.root, 40)
        self.checkpoint("REVIEW", 20, 39)
        self.assertTrue(ch.engineering_preflight(self.root, 40)["ok"])

    def test_unsubstantiated_checkpoint_is_rejected(self):
        p = self.checkpoint("AUDIT", 20, 24)
        p.write_text("# report\n", encoding="utf-8")
        with self.assertRaisesRegex(ch.ControlHarnessError, "unsubstantiated"):
            ch.engineering_preflight(self.root, 25)

    def test_missing_operation_slot_is_rejected(self):
        p = self.checkpoint("AUDIT", 20, 24)
        p.write_text(
            "# CHECKPOINT COMPLETE\n" + "M" * 500 +
            "\nPCE10.020 PCE10.021 PCE10.022 PCE10.024\n",
            encoding="utf-8"
        )
        with self.assertRaisesRegex(ch.ControlHarnessError, "missing slot .023"):
            ch.engineering_preflight(self.root, 25)

    def test_100_is_valid_but_101_is_forbidden(self):
        self.assertEqual(ch.due_engineering_checkpoints(100)["review_window"], [80, 99])
        with self.assertRaises(ch.ControlHarnessError):
            ch.due_engineering_checkpoints(101)


if __name__ == "__main__":
    unittest.main()
