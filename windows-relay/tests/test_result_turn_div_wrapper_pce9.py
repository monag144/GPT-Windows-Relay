import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRRORS = [
    ROOT / "content.js",
    ROOT / "extension" / "content.js",
    ROOT / "extension-persistent" / "content.js",
]

class ResultTurnDivWrapperPce9Tests(unittest.TestCase):
    def test_result_confirmation_accepts_div_conversation_turn_wrapper_in_all_mirrors(self):
        needle = 'div[data-testid^="conversation-turn-"]'
        for path in MIRRORS:
            text = path.read_text(encoding="utf-8")
            selector = next(line for line in text.splitlines() if line.startswith("const RESULT_TURN_SELECTOR="))
            self.assertIn("USER_SELECTOR+", selector, path.name)
            self.assertIn('article[data-testid^="conversation-turn-"]', selector, path.name)
            self.assertIn('section[data-testid^="conversation-turn-"]', selector, path.name)
            self.assertIn(needle, selector, path.name)

if __name__ == "__main__":
    unittest.main()