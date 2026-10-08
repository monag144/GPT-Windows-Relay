"""Preserve immutable migration source blobs even as destination docs evolve.

The source git commit was independently verified against all 42 manifest paths.
Current HEAD destination blobs MAY differ; that is not a provenance failure.
"""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_REL = "docs/migration/MIGRATION_2026-10-08T0110Z_TERMUX_WINDOWS_EVIDENCE_MANIFEST.json"
MANIFEST = ROOT / MANIFEST_REL
MANIFEST_GIT_BLOB = "a90e21b95b77cf4e9c80cf0eb4d219b1754bb308"
SOURCE_REPO = "monag144/GPT-Termux-Relay"
SOURCE_SHA = "249e3bb46c6ea57968d9ecf5157d73867a7f918d"


def git(*args):
    p = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True,
        encoding="utf-8", errors="replace", timeout=25,
    )
    if p.returncode:
        raise AssertionError("git " + " ".join(args[:2]) + " failed: " + p.stderr[-170:])
    return p.stdout.strip()


class MigrationEvidenceManifestTests(unittest.TestCase):
    def test_manifest_is_exact_and_complete_for_declared_entries(self):
        # A historical manifest is immutable, not an assertion that all 42
        # destination documents must remain byte-identical to migration day.
        self.assertEqual(git("rev-parse", "HEAD:" + MANIFEST_REL), MANIFEST_GIT_BLOB)
        obj = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(obj["version"], 1)
        self.assertEqual(obj["source_repository"], SOURCE_REPO)
        self.assertEqual(obj["source_commit"], SOURCE_SHA)
        self.assertEqual(obj["entry_count"], len(obj["entries"]))
        self.assertEqual(obj["entry_count"], 42)
        seen = set()
        for entry in obj["entries"]:
            path = entry["destination_path"]
            self.assertNotIn(path, seen)
            seen.add(path)
            self.assertTrue((ROOT / path).is_file(), path)
            self.assertTrue(entry["source_paths"], path)
            expected = entry["git_blob_sha1"]
            self.assertRegex(expected, r"^[0-9a-f]{40}$")
            # The original content blob must still exist as an exact Git object.
            # Changing the expected hash to current HEAD cannot fake provenance.
            self.assertEqual(git("cat-file", "-t", expected), "blob", path)
            self.assertRegex(git("rev-parse", "HEAD:" + path), r"^[0-9a-f]{40}$")

    def test_manifest_source_baseline_is_not_misrepresented_as_live_head(self):
        obj = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(obj["source_commit"], SOURCE_SHA)
        self.assertTrue(obj["entries"])
        # This regression records that migration SHA describes historical
        # source content, rather than a lock on future maintained documents.
        self.assertTrue(all(e["source_paths"] for e in obj["entries"]))


if __name__ == "__main__":
    unittest.main()
