import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RetiredEngineeringRotationTriggerTests(unittest.TestCase):
    def test_no_automatic_agent_switch_or_counter(self):
        a=(ROOT/'extension'/'service_worker.js').read_text(encoding='utf-8')
        p=(ROOT/'extension-persistent'/'service_worker.js').read_text(encoding='utf-8')
        for retired in (
            'GPT_ENGINEERING_ROTATION_TRIGGER_V1',
            'CHAT_ROTATION_EVERY',
            'ENGINEERING_ROTATION_FORCE_FROM_PCE8_OP',
            "type:'relay_chat_rotation_start'",
            'pce9Handoff(',
            'noteDeliveredOperation(',
        ):
            self.assertNotIn(retired,a,retired)
        self.assertIn('checkAndClaimRelayOwner',a)
        self.assertIn('callAction(m.packet)',a)
        self.assertIn('GPT_AGENT_SWITCHING_RETIRED_2026_10_09',a)
        self.assertIn("chrome.storage.local.get(['relayToken'])",p)

if __name__=='__main__':unittest.main()
