import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIRRORS=(ROOT/'content.js',ROOT/'extension'/'content.js',ROOT/'extension-persistent'/'content.js')

class StrictResultUserRolePce9Tests(unittest.TestCase):
    def test_generic_css_user_message_class_is_not_a_result_receipt(self):
        for path in MIRRORS:
            source=path.read_text(encoding="utf-8")
            selector=next(line for line in source.splitlines() if line.startswith("const RESULT_TURN_SELECTOR="))
            self.assertEqual(selector,"const RESULT_TURN_SELECTOR=USER_SELECTOR;")
            self.assertIn("if(!unit?.matches?.(USER_SELECTOR))return null;",source)
            self.assertNotIn("div[class~=bg-user-message]",selector)

if __name__=="__main__":unittest.main()
