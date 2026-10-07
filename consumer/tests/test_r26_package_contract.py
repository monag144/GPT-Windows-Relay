from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class R26PackageContractTests(unittest.TestCase):
    def test_control_harness_is_in_package_builder_manifest(self):
        src=(ROOT/"consumer"/"build-package.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("control_harness.py",src)
    def test_control_harness_is_in_updater_manifest(self):
        src=(ROOT/"consumer"/"updater.py").read_text(encoding="utf-8")
        self.assertIn('"control_harness.py"',src)

if __name__=="__main__": unittest.main()
