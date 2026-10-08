import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RepositoryHygieneTests(unittest.TestCase):
    def test_root_gitignore_covers_python_test_artifacts(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for token in ("__pycache__/", "*.py[cod]", ".pytest_cache/"):
            self.assertIn(token, text)

    def test_control_harness_contract_declares_source_tree_hygiene(self):
        import sys
        consumer = ROOT / "consumer"
        sys.path.insert(0, str(consumer))
        try:
            import control_harness as ch
            contract = ch.build_control_harness_contract("repo-hygiene-test")
        finally:
            sys.path.pop(0)
        hygiene = contract["source_tree_hygiene"]
        self.assertIn("Classify every dirty path", hygiene["dirty_preflight_rule"])
        self.assertIn("bytecode generation disabled", hygiene["test_rule"])


if __name__ == "__main__":
    unittest.main()
