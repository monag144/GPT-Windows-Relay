import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RetiredRotationHandlerTests(unittest.TestCase):
    def test_no_browser_controlled_handoff(self):
        c=(ROOT/'extension'/'content.js').read_text(encoding='utf-8')
        for retired in (
            'GPT_ENGINEERING_CHAT_ROTATION_HANDLER_V1',
            'ENGINEERING_ROTATION_SESSION_KEY',
            "m?.type==='relay_chat_rotation_start'",
            'resumeEngineeringRotation()',
            'beginEngineeringRotation(',
            'renameEngineeringChat(',
            'chat_rotation_verified',
        ):
            self.assertNotIn(retired,c,retired)
        self.assertIn("m?.type==='operator_control_state'",c)
        self.assertIn("m?.type==='relay_handoff_scroll'",c)
        self.assertEqual((ROOT/'content.js').read_bytes(),(ROOT/'extension'/'content.js').read_bytes())
        self.assertEqual((ROOT/'content.js').read_bytes(),(ROOT/'extension-persistent'/'content.js').read_bytes())

if __name__=='__main__':unittest.main()
