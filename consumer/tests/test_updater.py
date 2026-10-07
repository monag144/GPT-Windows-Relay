#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest
import zipfile

import updater


class UpdaterTests(unittest.TestCase):
    def test_release_metadata_declares_self_contained_python_runtime_contract(self):
        release = updater.load_release()
        self.assertEqual(release["version"], "1.1.0")
        self.assertIsInstance(release["revision"], int)
        self.assertGreaterEqual(release["revision"], 1)
        self.assertEqual(release["external_python_packages"], [])
        self.assertEqual(release["browser_policy"], "user_supplied")

    def test_package_allowlists_include_control_center_components(self):
        for name in ("browser_manager.py", "updater.py", "release.json", "requirements.txt"):
            self.assertIn(name, updater.CONSUMER_FILES)
        for name in ("windows_relay.py", "content.js", "chromium_extension_setup.ps1"):
            self.assertIn(name, updater.RUNTIME_FILES)

    def test_private_repository_update_falls_back_to_authenticated_git(self):
        root=Path(__file__).resolve().parents[2]
        src=(root/"consumer"/"updater.py").read_text(encoding="utf-8-sig")
        self.assertIn("_clone_private_update_source",src)
        self.assertIn("private_git_package",src)
        self.assertIn("git_authenticated_fallback",src)
        self.assertIn("exc.code in (401, 403, 404)",src)
        self.assertIn("--single-branch",src)
        self.assertIn("existing GitHub credentials",src)

    def test_version_comparison_is_numeric(self):
        self.assertGreater(updater.version_tuple("1.10.0"), updater.version_tuple("1.2.9"))
        self.assertEqual(updater.version_tuple("1.1.0"), (1, 1, 0))
        self.assertGreater(
            updater.release_key({"version": "1.1.0", "revision": 2}),
            updater.release_key({"version": "1.1.0", "revision": 1}),
        )

    def test_release_label_always_includes_revision_when_present(self):
        self.assertEqual(updater.release_label({"version": "1.1.0", "revision": 15}), "1.1.0 r15")
        self.assertEqual(updater.release_label({"version": "1.1.0", "revision": 0}), "1.1.0")

    def test_git_update_contract_polls_remote_and_attempts_pull(self):
        src = Path(updater.__file__).read_text(encoding="utf-8")
        self.assertIn('"ls-remote", "--heads", "origin"', src)
        self.assertIn('"pull", "--ff-only", "origin", branch', src)
        self.assertIn('"remote_polled": True', src)
        self.assertIn('"pull_attempted": True', src)
        self.assertIn('"display_version": release_label', src)

    def test_new_updater_can_run_second_phase_source_sync(self):
        old_here = updater.HERE
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                target = root / "installed"
                target.mkdir()
                source = root / "source"
                source.mkdir()
                updater.HERE = target
                stub = target / "updater.py"
                stub.write_text(
                    "import json, pathlib, sys\n"
                    "pathlib.Path(sys.argv[2], 'second-phase-called').write_text('yes')\n"
                    "print(json.dumps({'ok': True, 'mode': 'second_phase_source_sync'}))\n",
                    encoding="utf-8",
                )
                result = updater._second_phase_source_sync(source, True)
                self.assertTrue(result["ok"])
                self.assertTrue((source / "second-phase-called").is_file())
        finally:
            updater.HERE = old_here

    def test_updater_exposes_second_phase_sync_command(self):
        src = Path(updater.__file__).read_text(encoding="utf-8")
        self.assertIn('"sync-source"', src)
        self.assertIn("_second_phase_source_sync", src)
        self.assertIn('"second_phase_sync": bool(second_phase)', src)

    def test_safe_extract_rejects_archive_escape(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("../escape.txt", "no")
            out = root / "out"
            out.mkdir()
            with zipfile.ZipFile(archive) as zf:
                with self.assertRaises(updater.UpdateError):
                    updater._safe_extract(zf, out)


if __name__ == "__main__":
    unittest.main()
