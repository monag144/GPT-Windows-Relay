import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ResultTurnRecognitionTests(unittest.TestCase):
    def test_generic_current_turn_wrappers_are_supported(self):
        c = (ROOT / "extension" / "content.js").read_text(encoding="utf-8")

        # Generic current-role compatibility must remain available.
        self.assertIn("'[data-turn=\"user\"]'", c)
        self.assertIn("'article[data-turn=\"assistant\"]'", c)
        self.assertIn('[data-turn="user"]', c)
        self.assertIn('[data-turn="assistant"]', c)

        # Generic wrappers remain valid for discovery, but not result receipts.
        selector = next(line for line in c.splitlines()
                        if line.startswith("const RESULT_TURN_SELECTOR="))
        self.assertEqual(selector,"const RESULT_TURN_SELECTOR=USER_SELECTOR;")
        self.assertIn("if(!unit?.matches?.(USER_SELECTOR))return null;",c)
        self.assertNotIn("USER_SELECTOR+",selector)

        self.assertEqual(
            (ROOT / "content.js").read_bytes(),
            (ROOT / "extension" / "content.js").read_bytes(),
        )
        self.assertEqual(
            (ROOT / "content.js").read_bytes(),
            (ROOT / "extension-persistent" / "content.js").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
