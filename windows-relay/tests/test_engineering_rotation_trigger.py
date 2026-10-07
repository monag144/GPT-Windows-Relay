import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EngineeringRotationTriggerTests(unittest.TestCase):
    def test_rotation_is_generic_and_budget_is_fail_closed(self):
        worker = (ROOT / "extension" / "service_worker.js").read_text(encoding="utf-8")
        persistent = (ROOT / "extension-persistent" / "service_worker.js").read_text(encoding="utf-8")

        self.assertIn("GPT_ENGINEERING_ROTATION_TRIGGER_V2", worker)
        self.assertIn("GPT_ENGINEERING_SERIES_BUDGET_V1", worker)
        self.assertIn("function engineeringSeriesInfo(id)", worker)
        self.assertIn("function engineeringSuccessorTarget(generation)", worker)
        self.assertIn("title:\`💻PC Engineering \${next}🔧\`", worker)
        self.assertIn("session:\`pce\${next}.1\`", worker)
        self.assertIn("PCE\${next}.000", worker)
        self.assertIn("PCE\${next}.100", worker)
        self.assertIn("PCE\${next}.101", worker)
        self.assertIn("engineeringSeriesBudgetExceeded", worker)
        self.assertIn("info.ordinal>CHAT_ROTATION_EVERY", worker)
        self.assertGreaterEqual(worker.count("engineering_series_budget_exceeded"), 2)
        self.assertIn("type:'relay_chat_rotation_start'", worker)
        self.assertNotIn("function pce9Target", worker)
        self.assertNotIn("ENGINEERING_ROTATION_FORCE_FROM_PCE8_OP", worker)
        self.assertNotIn("chrome.tabs.update(tabId,{url:'https://chatgpt.com/'})", worker)

        self.assertIn("chrome.storage.local.get(['relayToken'])", persistent)
        self.assertNotIn("CHAT_ROTATION_KEY", persistent)

    def test_dot_ordinal_and_legacy_op_forms_are_supported(self):
        worker = (ROOT / "extension" / "service_worker.js").read_text(encoding="utf-8")
        self.assertIn("match(/^PCE\\d+\\.(\\d+)", worker)
        self.assertIn("match(/(?:BOOT-)?OP(\\d+)", worker)
        self.assertIn("const engineering=engineeringSeriesInfo(id)", worker)


if __name__ == "__main__":
    unittest.main()
