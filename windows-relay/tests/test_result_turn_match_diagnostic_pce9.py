import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRRORS = [
    ROOT / "content.js",
    ROOT / "extension" / "content.js",
    ROOT / "extension-persistent" / "content.js",
]


class ResultTurnMatchDiagnosticPce9Tests(unittest.TestCase):
    def test_matcher_diagnostic_waits_for_exact_result_envelope_and_stays_safe(self):
        for path in MIRRORS:
            text = path.read_text(encoding="utf-8")
            self.assertIn("const resultMatcherDiagnosticsReported=new Set();", text)
            self.assertIn("function textContainsResultPacketEnvelope(text,packetId)", text)
            self.assertIn("resultOpen>actionOpen", text)
            self.assertIn("const exactResultPacketVisible=textContainsResultPacketEnvelope(bodyText,packetId);", text)
            self.assertIn("if(!force && !exactResultPacketVisible)return;", text)
            self.assertIn("candidate_envelope_hits", text)
            self.assertIn("exact_result_packet_visible", text)
            self.assertIn("document.querySelectorAll('*')", text)
            self.assertIn("relay_result_turn_match_diagnostic", text)
            self.assertIn("carrier_testid", text)
            self.assertIn("carrier_author_role", text)
            self.assertIn("function safeResultDiagnosticNode(node)", text)
            self.assertIn("function resultDiagnosticAncestorChain(node,maxDepth=8)", text)
            self.assertIn("carrier_ancestors:resultDiagnosticAncestorChain(carrier,8)", text)
            self.assertIn("class_name", text)
            self.assertIn("scroll_anchor", text)
            self.assertNotIn("if(!force && !(bodyPacketVisible && bodyResultMarkerVisible))return;", text)
            self.assertNotIn("carrier_text:", text)
            self.assertNotIn("text_content", text)


if __name__ == "__main__":
    unittest.main()