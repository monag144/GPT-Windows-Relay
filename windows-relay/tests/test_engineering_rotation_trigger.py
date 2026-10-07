import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class EngineeringRotationTriggerTests(unittest.TestCase):
 def test_temp_worker_owns_rotation_and_persistent_keeps_pairing(self):
  a=(ROOT/'extension'/'service_worker.js').read_text(encoding='utf-8')
  p=(ROOT/'extension-persistent'/'service_worker.js').read_text(encoding='utf-8')
  self.assertIn('GPT_ENGINEERING_ROTATION_TRIGGER_V1',a)
  self.assertIn('ENGINEERING_ROTATION_FORCE_FROM_PCE8_OP=95',a)
  self.assertIn("type:'relay_chat_rotation_start'",a)
  self.assertIn("title:'💻PC Engineering 9🔧'",a)
  self.assertIn("session:'pce9.1'",a)
  self.assertIn('PCE9BOOT-OP001',a)
  self.assertIn('if(ordinal && !rotationDue)',a)
  self.assertIn('!ordinal && !rotationDue',a)
  self.assertNotIn("chrome.tabs.update(tabId,{url:'https://chatgpt.com/'})",a)
  self.assertIn("chrome.storage.local.get(['relayToken'])",p)
  self.assertNotIn('CHAT_ROTATION_KEY',p)
if __name__=='__main__':unittest.main()
