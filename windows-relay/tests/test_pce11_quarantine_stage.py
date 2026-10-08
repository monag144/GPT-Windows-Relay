"""PCE011 reversible Relay/bin quarantine and immutable candidate-staging contract."""
from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("pce11_quarantine_stage",ROOT/"tools"/"pce11_quarantine_stage.py")
stage=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage)

class PCE11SafeQuarantineTests(unittest.TestCase):
    def fixture(self,where):
        root=Path(where)
        (root/"extension").mkdir()
        (root/"extension"/"content.js").write_text("PCE11_TEST",encoding="utf-8")
        (root/"windows_relay.py").write_text("original legacy",encoding="utf-8")
        (root/"secrets.local").write_text("local secret-not-for-output",encoding="utf-8")
        (root/"bin").mkdir()
        (root/"bin"/"old.archive").write_text("old")
        (root/"builds").mkdir()
        (root/"builds"/"previous.marker").write_text("old build")
        return root
    def test_snapshots_working_live_bytes_without_moving_or_deleting_them(self):
        with tempfile.TemporaryDirectory() as d:
            live=self.fixture(d)
            before=(live/"windows_relay.py").read_bytes()
            result=stage.archive_live(live,"2026-10-08T0910Z")
            self.assertTrue(Path(result["archive"]).is_file())
            self.assertTrue(Path(result["manifest"]).is_file())
            manifest=json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["zip_sha256"],stage.hashes(Path(result["archive"])))
            with zipfile.ZipFile(result["archive"]) as archive:
                self.assertIn("windows_relay.py",archive.namelist())
                self.assertIn("secrets.local",archive.namelist())
                self.assertNotIn("bin/old.archive",archive.namelist())
                self.assertNotIn("builds/previous.marker",archive.namelist())
                self.assertEqual(archive.read("windows_relay.py"),before)
            self.assertEqual((live/"windows_relay.py").read_bytes(),before)
            with self.assertRaises(FileExistsError):
                stage.archive_live(live,"2026-10-08T0910Z")
    def test_fail_closed_on_unrecognized_live_tree(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                stage.archive_live(Path(d),"2026-10-08T0912Z")
            self.assertFalse((Path(d)/"bin").exists())
    def test_legacy_git_shas_are_exact_40_hex_reference(self):
        self.assertEqual(len(stage.CANDIDATES),2)
        for label,ref,sha in stage.CANDIDATES:
            self.assertEqual(len(sha),40)
            self.assertRegex(sha,r"^[0-9a-f]{40}$")
            self.assertTrue(ref.startswith("consumer/"))
            self.assertIn(label,("RELAY_PCE8_V16","ONE_CLICK_GO_R28"))
    def test_stage_existing_tree_never_overwrites_nonmatching_sha(self):
        with tempfile.TemporaryDirectory() as d:
            live=Path(d); (live/"builds"/"RELAY_PCE8_V16_694d47ab8959").mkdir(parents=True)
            with mock.patch.object(stage,"command",return_value="0"*40):
                with self.assertRaises(RuntimeError):
                    stage.stage_one(live,"git",*stage.CANDIDATES[0])

if __name__=="__main__":unittest.main()
