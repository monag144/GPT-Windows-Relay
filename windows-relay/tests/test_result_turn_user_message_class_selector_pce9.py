import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRRORS = [ROOT / 'content.js', ROOT / 'extension' / 'content.js', ROOT / 'extension-persistent' / 'content.js']
TOKEN = 'div[class~=bg-user-message]'

class ResultTurnUserMessageClassSelectorPce9Tests(unittest.TestCase):
    def test_result_confirmation_selector_includes_semantic_user_message_bubble_only(self):
        for path in MIRRORS:
            text = path.read_text(encoding='utf-8')
            selector = next(line for line in text.splitlines() if line.startswith('const RESULT_TURN_SELECTOR='))
            self.assertIn(TOKEN, selector)
            self.assertIn('USER_SELECTOR+', selector)
            self.assertEqual(text.count(TOKEN), 1)
            self.assertIn('if(explicitAssistant && !explicitUser)return null;', text)
            self.assertIn('if(resultPacketIdFromUserUnit(nodes[i])===packetId || elementText(nodes[i]).includes(packetId))return true;', text)

if __name__ == '__main__':
    unittest.main()