"""Regression for the proven PowerShell 5.1 DETACHED_PROCESS startup failure.

Only executes the rotation worker with a NONEXISTENT handoff file. If the
script runs at all, it must fail before any browser access or UI mutation.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"semantic_agent_rotation.ps1"

class RotationLaunchModeTests(unittest.TestCase):
    @unittest.skipUnless(os.name=="nt","Windows-only process flags")
    def test_create_no_window_executes_worker_and_fails_before_click(self):
        powershell=shutil.which("powershell.exe")
        if powershell is None:
            self.skipTest("Windows PowerShell unavailable")
        with tempfile.TemporaryDirectory(prefix="agent011-safe-negative-") as folder:
            tmp=Path(folder)
            missing=tmp/"intentionally-missing-handoff.md"
            receipt=tmp/"negative-receipt.json"
            self.assertFalse(missing.exists())
            proc=subprocess.Popen(
                [powershell,"-STA","-NoLogo","-NoProfile",
                 "-ExecutionPolicy","Bypass","-File",str(SCRIPT),
                 "-SourcePacketId","PCE11.029-TEST-NEGATIVE",
                 "-HandoffFile",str(missing),"-ReceiptFile",str(receipt)],
                cwd=str(SCRIPT.parent),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                close_fds=True,
            )
            try:
                code=proc.wait(timeout=16)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=4)
                self.fail("negative rotation worker did not terminate")
            self.assertEqual(code,2)
            self.assertTrue(receipt.is_file())
            data=json.loads(receipt.read_text(encoding="utf-8-sig"))
            self.assertEqual(data.get("phase"),"HALT_BEFORE_CLICK")
            self.assertEqual(data.get("error"),"HANDOFF_FILE_MISSING")
            self.assertIs(data.get("click_invoked"),False)
            self.assertIs(data.get("send_invoked"),False)

if __name__=="__main__":
    unittest.main()
