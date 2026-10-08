"""PCE011 document hygiene: canonical dated docs, permanent compatibility paths and size boundaries."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{4}Z")
COMPAT = {
    "README.md", "consumer/README.txt", "windows-relay/README.md",
    "windows-relay/TASKS.md", "docs/RELAY_OPERATIONAL_RULES.md",
    "docs/relay-sandwich-procedure.md", "docs/windows-relay-established-facts.md",
    "docs/windows-relay-mission-and-roadmap.md",
    "docs/job-application-engine-v2.md", "docs/job-application-automation-defaults.md",
    "docs/job-applications/README.md",
    "docs/windows-relay-engineering-log-2026-10-01.md",
    "docs/windows-relay-engineering-log-2026-10-07.md",
}

class PCE11DocumentHygiene(unittest.TestCase):
    def test_maintained_docs_are_timed_or_compatibility_pointers(self):
        files = sorted((ROOT / "docs").rglob("*.md"))
        files += [ROOT / "README.md", ROOT / "consumer" / "README.txt",
                  ROOT / "windows-relay" / "README.md", ROOT / "windows-relay" / "TASKS.md"]
        for p in files:
            rel = p.relative_to(ROOT).as_posix()
            data = p.read_text(encoding="utf-8-sig")
            self.assertLessEqual(len(p.read_bytes()), 10240, rel)
            if not STAMP.search(p.name) and rel not in COMPAT:
                self.assertIn("PCE11_TIMESTAMP_COMPAT_POINTER", data, rel)
                m = re.search(r"\[Open timestamped document\]\(\./([^\)]+)\)", data)
                self.assertIsNotNone(m, rel)
                self.assertTrue((p.parent / m.group(1)).is_file(), rel)

    def test_compatibility_control_entrypoints_remain_present(self):
        for name in COMPAT:
            self.assertTrue((ROOT / name).is_file(), name)
            self.assertTrue((ROOT / name).read_text(encoding="utf-8-sig").strip(), name)

if __name__ == "__main__":
    unittest.main()
