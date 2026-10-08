import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "migration" / "MIGRATION_2026-10-08T0110Z_TERMUX_WINDOWS_EVIDENCE_MANIFEST.json"


def committed_blob(path: str) -> str:
    p = subprocess.run(
        ["git", "rev-parse", f"HEAD:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if p.returncode:
        raise AssertionError(f"git rev-parse failed for {path}: {p.stderr}")
    return p.stdout.strip()


class MigrationEvidenceManifestTests(unittest.TestCase):
    def test_manifest_is_exact_and_complete_for_declared_entries(self):
        obj = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(obj["version"], 1)
        self.assertEqual(obj["source_repository"], "monag144/GPT-Termux-Relay")
        self.assertEqual(obj["source_commit"], "249e3bb46c6ea57968d9ecf5157d73867a7f918d")
        self.assertEqual(obj["entry_count"], len(obj["entries"]))
        self.assertEqual(obj["entry_count"], 42)
        seen = set()
        for entry in obj["entries"]:
            path = entry["destination_path"]
            self.assertNotIn(path, seen)
            seen.add(path)
            self.assertTrue((ROOT / path).is_file(), path)
            self.assertEqual(committed_blob(path), entry["git_blob_sha1"], path)
            self.assertTrue(entry["source_paths"], path)


if __name__ == "__main__":
    unittest.main()
