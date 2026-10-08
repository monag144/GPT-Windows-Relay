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

        # Result confirmation also needs the live-proven conversation-turn
        # wrapper fallbacks retained by the PCE9 regressions.
        selector = next(
            line for line in c.splitlines()
            if line.startswith("const RESULT_TURN_SELECTOR=")
        )
        self.assertIn("USER_SELECTOR+", selector)
        self.assertIn('article[data-testid^="conversation-turn-"]', selector)
        self.assertIn('section[data-testid^="conversation-turn-"]', selector)
        self.assertIn('div[data-testid^="conversation-turn-"]', selector)
        self.assertIn('div[class~=bg-user-message]', selector)

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
