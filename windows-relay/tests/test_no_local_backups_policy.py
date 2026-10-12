"""Offline regression checks for the 2026-10-12 no-on-device-backups rule."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
WIN = ROOT / "windows-relay"


class NoLocalBackupsPolicyTests(unittest.TestCase):
    def test_operator_policy_is_documented_and_local_backup_is_prohibited(self):
        policy = ROOT / "docs" / "policy" / "WINDOWS_RELAY_NO_ON_DEVICE_BACKUPS_2026-10-12.md"
        content = policy.read_text(encoding="utf-8")
        self.assertIn("NO ON-DEVICE BACKUPS", content)
        self.assertIn("no new local backup", content.lower())
        self.assertIn("GitHub", content)
        self.assertIn("irreplaceable", content.lower())

    def test_legacy_mutating_entrypoints_refuse_to_run(self):
        for filename in ("sync-live.py", "safe_live_cutover.py", "tools/pce7_446_live_cutover.py", "tools/pce7_447_source_repair.py"):
            with self.subTest(filename=filename):
                script = WIN / filename
                completed = subprocess.run(
                    [sys.executable, "-B", str(script), "--help"],
                    cwd=str(WIN), text=True, capture_output=True,
                    timeout=15, check=False,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(
                    "RETIRED_NO_LOCAL_BACKUPS",
                    completed.stdout + completed.stderr,
                    completed.stdout + completed.stderr,
                )

    def test_browser_fix_installer_is_retired(self):
        source = (WIN / "install-browser-fix.ps1").read_text(encoding="utf-8")
        stop = source.index("throw 'RETIRED_NO_LOCAL_BACKUPS")
        creation = source.index("New-Item -ItemType Directory -Force -Path $backupRoot")
        self.assertLess(stop, creation)

    def test_signed_extension_policy_installer_creates_no_backup_copy(self):
        source = (WIN / "install-signed-extension-policy.ps1").read_text(encoding="utf-8")
        self.assertIn("LOCAL_POLICY_BACKUP_CREATED=False", source)
        self.assertNotIn("POLICY_BACKUP=", source)
        self.assertNotIn("$backup=", source)
        self.assertNotIn(".bak-", source)
        self.assertIn("Get-Content -LiteralPath $pol -Raw", source)

    def test_archive_not_tracked_on_current_working_branch(self):
        completed = subprocess.run(
            ["git", "ls-files", "--", "STUPID BACKUPS DO NOT USE"],
            cwd=str(ROOT), text=True, capture_output=True,
            timeout=15, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(completed.stdout.strip(), completed.stdout)


if __name__ == "__main__":
    unittest.main()
