import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ResultTurnRecognitionTests(unittest.TestCase):
 def test_generic_current_turn_wrappers_are_supported(self):
  c=(ROOT/'extension'/'content.js').read_text(encoding='utf-8')
  self.assertIn("'[data-turn=\"user\"]'",c)
  self.assertIn("RESULT_TURN_SELECTOR=USER_SELECTOR+',[data-testid^=\"conversation-turn-\"]'",c)
  self.assertIn('[data-turn=\"user\"]',c)
  self.assertIn('[data-turn=\"assistant\"]',c)
  self.assertNotIn('article[data-testid^=\"conversation-turn-\"],section[data-testid^=\"conversation-turn-\"]',c)
  self.assertEqual((ROOT/'content.js').read_bytes(),(ROOT/'extension'/'content.js').read_bytes())
  self.assertEqual((ROOT/'content.js').read_bytes(),(ROOT/'extension-persistent'/'content.js').read_bytes())
if __name__=='__main__':unittest.main()
