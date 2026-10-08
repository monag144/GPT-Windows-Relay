import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIRRORS=(ROOT/'content.js',ROOT/'extension'/'content.js',ROOT/'extension-persistent'/'content.js')

class StrictResultTurnPce9Tests(unittest.TestCase):
    def test_result_confirmation_requires_exact_user_result_without_broad_wrapper(self):
        for path in MIRRORS:
            source=path.read_text(encoding="utf-8")
            selector=next(line for line in source.splitlines() if line.startswith("const RESULT_TURN_SELECTOR="))
            self.assertEqual(selector,"const RESULT_TURN_SELECTOR=USER_SELECTOR;")
            self.assertIn("if(!unit?.matches?.(USER_SELECTOR))return null;",source)
            self.assertNotIn("USER_SELECTOR+",selector)

if __name__=="__main__":unittest.main()
