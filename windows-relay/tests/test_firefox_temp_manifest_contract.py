import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class FirefoxTemporaryManifestContractTests(unittest.TestCase):
    def test_temporary_firefox_manifest_declares_background_scripts_and_worker(self):
        manifest=json.loads((ROOT/'extension'/'manifest.json').read_text(encoding='utf-8'))
        background=manifest.get('background') or {}
        self.assertEqual(background.get('scripts'),['service_worker.js'])
        self.assertEqual(background.get('service_worker'),'service_worker.js')
        self.assertEqual(background.get('type'),'module')

    def test_persistent_firefox_manifest_keeps_same_firefox_background_entrypoint(self):
        manifest=json.loads((ROOT/'extension-persistent'/'manifest.json').read_text(encoding='utf-8'))
        background=manifest.get('background') or {}
        self.assertEqual(background.get('scripts'),['service_worker.js'])
        self.assertEqual(background.get('service_worker'),'service_worker.js')

    def test_temporary_worker_uses_local_runtime_config(self):
        worker=(ROOT/'extension'/'service_worker.js').read_text(encoding='utf-8')
        self.assertIn("from './config.js'",worker)
        self.assertIn('RELAY_PORT',worker)
        self.assertIn('RELAY_TOKEN',worker)

if __name__=='__main__': unittest.main()
