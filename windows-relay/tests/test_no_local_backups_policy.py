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
        for filename in ("sync-live.py", "safe_live_cutover.py"):
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
