"""Regression: GitHub engineering audit policy cannot block runtime dispatch.

The legacy nested runtime incorrectly called engineering_preflight(series, ordinal)
without a github_audit_receipt and blocked every fifth PCE operation.  GitHub
audits are assistant-side requirements; backend-side auth/owner/STOP still apply.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1] / "windows_relay.py"


class RuntimeAuditIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = BACKEND.read_text(encoding="utf-8-sig")
        cls.tree = ast.parse(cls.source, filename=str(BACKEND))

    def test_no_engineering_audit_receipt_or_preflight_in_backend(self):
        # Does not prohibit separate assistant-side consumer/control_harness.py.
        self.assertNotIn("engineering_preflight", self.source)
        self.assertNotIn("github_audit_receipt", self.source)
        self.assertNotIn("GOVERNANCE_CHECKPOINT_BLOCKED", self.source)
        self.assertNotIn("github_checkpoint_audit_missing", self.source)

    def test_dispatcher_keeps_operator_security_gates(self):
        process = next(
            n for n in self.tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == "process"
        )
        body = ast.get_source_segment(self.source, process)
        self.assertIsNotNone(body)
        self.assertIn("validate_transport_identity(", body)
        self.assertIn("if not state.armed", body)
        self.assertIn("state.reserve(a)", body)
        self.assertIn("replay_saved_result(a,prior)", body)

        handler = next(
            n for n in self.tree.body
            if isinstance(n, ast.ClassDef) and n.name == "Handler"
        )
        post = next(n for n in handler.body if isinstance(n, ast.FunctionDef) and n.name == "do_POST")
        post_source = ast.get_source_segment(self.source, post)
        self.assertIsNotNone(post_source)
        self.assertIn("if not self.auth()", post_source)
        self.assertIn("operator_authorization_required", post_source)


if __name__ == "__main__":
    unittest.main()
