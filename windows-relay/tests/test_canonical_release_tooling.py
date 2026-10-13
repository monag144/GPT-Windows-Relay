"""No-side-effect contracts for the dated canonical Windows Relay release tooling."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
RELAY = ROOT / "windows-relay"
TAG_COMMIT = "f00307494a83338d29b4c35dd6264e71fa142dbd"


class CanonicalReleaseToolingTests(unittest.TestCase):
    def test_manifest_is_the_approved_persistent_extension(self):
        doc = json.loads((RELAY / "extension-persistent" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["name"], "GPT Windows Relay")
        self.assertEqual(doc["version"], "0.3.18")
        self.assertEqual(doc["browser_specific_settings"]["gecko"]["id"], "gpt-windows-relay@local")

    def test_xpi_builder_derives_version_from_manifest(self):
        script = (RELAY / "build-extension-xpi.ps1").read_text(encoding="utf-8")
        self.assertIn("extension-persistent", script)
        self.assertIn("$version=[string]$manifest.version", script)
        self.assertIn("dist\\gpt-windows-relay.xpi", script)
        self.assertNotIn("gpt-windows-relay-0.3.17.xpi", script)

    def test_relay_installer_does_not_publish_bearer_token_to_consumer_extension(self):
        script = (RELAY / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("relay.config(relay.cfg_dir()/'bridge.json')", script)
        self.assertIn("extension-persistent\\manifest.json", script)
        self.assertNotIn("export const RELAY_TOKEN", script)
        self.assertNotIn("extension\\config.js", script)
        self.assertNotIn("The relay starts ARMED", script)
        self.assertNotIn("relay-control.ps1 start", script)
        self.assertNotIn("backups", script.lower())

    def test_codex_rejects_bad_remote_before_launch(self):
        launcher = (ROOT / "tools" / "Launch-Codex-CLI.bat").read_text(encoding="utf-8")
        self.assertIn('set "START_DIR="', launcher)
        self.assertIn('set "WORKSPACE=%USERPROFILE%\\Downloads\\Dev\\GPT-Windows-Relay-Main-Build"', launcher)
        denial = launcher.index("echo ERROR: checkout remote does not match")
        verification = launcher.index("if not defined START_DIR")
        self.assertIn("exit /b 1", launcher[denial:verification])
        self.assertIn("call :CheckOrigin", launcher)
        self.assertIn("exit /b 1", launcher[verification:])

    def test_tag_checkpoint_is_dated_and_does_not_claim_full_project_acceptance(self):
        path = ROOT / "docs" / "releases" / "WINDOWS_RELAY_LIVE_EXECUTION_CHECKPOINT_2026-10-12.md"
        document = path.read_text(encoding="utf-8")
        self.assertIn(TAG_COMMIT, document)
        self.assertIn("13 / 13 passed", document)
        self.assertIn("not a blanket certification", document)


if __name__ == "__main__":
    unittest.main()
