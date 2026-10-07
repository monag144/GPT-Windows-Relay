import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RotationHandlerTests(unittest.TestCase):
 def test_durable_create_rename_verify_contract(self):
  c=(ROOT/'extension'/'content.js').read_text(encoding='utf-8')
  self.assertIn('GPT_ENGINEERING_CHAT_ROTATION_HANDLER_V1',c)
  self.assertIn("ENGINEERING_ROTATION_SESSION_KEY='gptEngineeringRotationV1'",c)
  self.assertIn("m?.type==='relay_chat_rotation_start'",c)
  self.assertIn("location.assign('https://chatgpt.com/')",c)
  self.assertIn("[GPT_ENGINEERING_ROTATION_HANDOFF_V1]",c)
  self.assertIn('engineering_rotation_handoff_unconfirmed',c)
  self.assertIn('engineering_rotation_conversation_identity_timeout',c)
  self.assertIn('renameEngineeringChat(st.target_title,path)',c)
  self.assertIn('rotationExactAnchor(st.target_title,path)',c)
  self.assertIn("emitRelayEvent('chat_rotation_verified'",c)
  self.assertIn('resumeEngineeringRotation()',c)
  self.assertEqual((ROOT/'content.js').read_bytes(),(ROOT/'extension'/'content.js').read_bytes())
  self.assertEqual((ROOT/'content.js').read_bytes(),(ROOT/'extension-persistent'/'content.js').read_bytes())
if __name__=='__main__':unittest.main()
