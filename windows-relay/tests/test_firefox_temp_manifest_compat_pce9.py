import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "extension" / "manifest.json"

class FirefoxTempManifestCompatPce9Tests(unittest.TestCase):
    def test_temp_manifest_keeps_firefox_and_chromium_mv3_background_contracts(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(m.get("manifest_version"), 3)
        bg = m.get("background", {})
        self.assertEqual(bg.get("service_worker"), "service_worker.js")
        self.assertEqual(bg.get("scripts"), ["service_worker.js"])
        self.assertEqual(bg.get("type"), "module")

if __name__ == "__main__":
    unittest.main()