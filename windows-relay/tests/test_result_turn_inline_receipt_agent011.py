"""PCE11 Agent011: execute the real JavaScript result-turn parser against
positive user-turn and negative assistant/composer examples; no browser reload.
"""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIRRORS = (
    ROOT / "content.js",
    ROOT / "extension" / "content.js",
    ROOT / "extension-persistent" / "content.js",
)
PACKET = "PCE11.015-synthetic-result-receipt"

class ResultTurnInlineReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        content = MIRRORS[0].read_text(encoding="utf-8")
        start = content.index("function resultPacketIdFromExactEnvelope(text){")
        stop = content.index("\nfunction hydrateAttemptedFromConversation(){", start)
        matcher = content[start:stop]
        payload = {"version": 1, "platform": "windows", "action": "EXEC",
                   "id": PACKET, "status": "OK"}
        inline = "[GPT_WINDOWS_RESULT] " + json.dumps(payload) + " [/GPT_WINDOWS_RESULT]"
        multiline = ("[GPT_WINDOWS_RESULT]\n" +
                     json.dumps(payload, indent=2) +
                     "\n[/GPT_WINDOWS_RESULT]")
        invalid = dict(payload, platform="linux")
        invalid_action = dict(payload, action="READ")
        no_version = {k:v for k,v in payload.items() if k!="version"}
        cases = {
            "inline_user": [inline, True, False],
            "multiline_user": [multiline, True, False],
            "inline_user_whitespace": ["\t" + inline + "\n", True, False],
            "inline_failed_status": [
                "[GPT_WINDOWS_RESULT] " +
                json.dumps(dict(payload, status="COMMAND_FAILED")) +
                " [/GPT_WINDOWS_RESULT]", True, False
            ],
            "assistant_inline": [inline, False, False],
            "assistant_multiline": [multiline, False, False],
            "composer_owned": [inline, True, True],
            "quoted_with_prefix": ["The command said: " + inline, True, False],
            "quoted_with_suffix": [inline + " followed by explanation", True, False],
            "bare_packet_id": [PACKET, True, False],
            "no_markers": [json.dumps(payload), True, False],
            "missing_action": [
                "[GPT_WINDOWS_RESULT] " +
                json.dumps({k:v for k,v in payload.items() if k!="action"}) +
                " [/GPT_WINDOWS_RESULT]", True, False
            ],
            "missing_version": [
                "[GPT_WINDOWS_RESULT] " + json.dumps(no_version) +
                " [/GPT_WINDOWS_RESULT]", True, False
            ],
            "wrong_platform": [
                "[GPT_WINDOWS_RESULT] " + json.dumps(invalid) +
                " [/GPT_WINDOWS_RESULT]", True, False
            ],
            "wrong_action": [
                "[GPT_WINDOWS_RESULT] " + json.dumps(invalid_action) +
                " [/GPT_WINDOWS_RESULT]", True, False
            ],
            "malformed_json": [
                '[GPT_WINDOWS_RESULT] {"version":1,"platform":"windows", ' +
                ' [/GPT_WINDOWS_RESULT]', True, False
            ],
        }
        harness = (
            'const USER_SELECTOR="[data-message-role=user]";\n'
            'let composer=null;function findComposer(){return composer;}\n'
            + matcher + "\n"
            + "const cases=" + json.dumps(cases) + ";\n"
            + "const output={};\n"
            + "for(const [label,[text,isUser,owned]] of Object.entries(cases)){\n"
            + "  composer=owned?{}:null;\n"
            + "  const unit={textContent:text,matches:()=>isUser,contains:()=>owned};\n"
            + "  output[label]=resultPacketIdFromUserUnit(unit);\n"
            + "}\n"
            + "console.log(JSON.stringify(output));\n"
        )
        done = subprocess.run(["node", "-e", harness], capture_output=True,
                              text=True, timeout=15, check=False)
        if done.returncode:
            raise AssertionError("Node parser harness failed: "+done.stderr[-1000:])
        cls.results = json.loads(done.stdout.strip())
        cls.source = content

    def test_inline_user_envelope_confirms(self):
        self.assertEqual(self.results["inline_user"], PACKET)

    def test_multiline_user_envelope_confirms(self):
        self.assertEqual(self.results["multiline_user"], PACKET)

    def test_whitespace_and_failed_result_are_valid_receipts(self):
        self.assertEqual(self.results["inline_user_whitespace"], PACKET)
        self.assertEqual(self.results["inline_failed_status"], PACKET)

    def test_assistant_prose_is_not_a_receipt(self):
        self.assertIsNone(self.results["assistant_inline"])
        self.assertIsNone(self.results["assistant_multiline"])

    def test_composer_draft_is_not_a_receipt(self):
        self.assertIsNone(self.results["composer_owned"])

    def test_quoted_or_embedded_envelope_is_not_a_receipt(self):
        self.assertIsNone(self.results["quoted_with_prefix"])
        self.assertIsNone(self.results["quoted_with_suffix"])

    def test_bare_packet_id_and_markerless_json_not_receipts(self):
        self.assertIsNone(self.results["bare_packet_id"])
        self.assertIsNone(self.results["no_markers"])

    def test_missing_or_wrong_identity_fields_rejected(self):
        for name in ("missing_action", "missing_version", "wrong_platform", "wrong_action"):
            with self.subTest(name=name):
                self.assertIsNone(self.results[name])

    def test_malformed_result_json_rejected(self):
        self.assertIsNone(self.results["malformed_json"])

    def test_confirm_requires_positive_user_role(self):
        self.assertIn("if(!unit?.matches?.(USER_SELECTOR))return null;",self.source)
        self.assertIn("function userTurnContainsPacketId(packetId)",self.source)
        self.assertIn("if(resultPacketIdFromUserUnit(nodes[i])===packetId)return true;",self.source)
        self.assertIn("GPT_WINDOWS_RESULT_SINGLE_LINE_OR_MULTILINE_RECEIPT_V1",self.source)

    def test_all_three_content_scripts_are_byte_identical(self):
        self.assertEqual(MIRRORS[0].read_bytes(),MIRRORS[1].read_bytes())
        self.assertEqual(MIRRORS[0].read_bytes(),MIRRORS[2].read_bytes())

if __name__=="__main__":
    unittest.main()
