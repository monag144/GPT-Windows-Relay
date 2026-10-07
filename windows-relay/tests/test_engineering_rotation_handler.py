import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RotationHandlerTests(unittest.TestCase):
    def test_durable_create_rename_verify_contract_is_successor_generic(self):
        content = (ROOT / "extension" / "content.js").read_text(encoding="utf-8")
        self.assertIn("GPT_ENGINEERING_CHAT_ROTATION_HANDLER_V1", content)
        self.assertIn("ENGINEERING_ROTATION_SESSION_KEY='gptEngineeringRotationV1'", content)
        self.assertIn("m?.type==='relay_chat_rotation_start'", content)
        self.assertIn("location.assign('https://chatgpt.com/')", content)
        self.assertIn("[GPT_ENGINEERING_ROTATION_HANDOFF_V1]", content)
        self.assertIn("engineeringRotationTargetValid", content)
        self.assertIn("engineering_rotation_handoff_unconfirmed", content)
        self.assertIn("engineering_rotation_conversation_identity_timeout", content)
        self.assertIn("renameEngineeringChat(st.target_title,path)", content)
        self.assertIn("rotationExactAnchor(st.target_title,path)", content)
        self.assertIn("emitRelayEvent('chat_rotation_verified'", content)
        self.assertIn("resumeEngineeringRotation()", content)
        self.assertNotIn("st.target_title!=='💻PC Engineering 9🔧'", content)
        self.assertNotIn("m?.target_session!=='pce9.1'", content)

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
