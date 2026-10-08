"""PCE11 independent v16 supervisor static contracts. Tests never start a server."""
from __future__ import annotations
import importlib.util
import hashlib
import tempfile
import unittest
from pathlib import Path

MODULE=Path(__file__).resolve().parents[1]/"tools"/"pce11_013_isolated_supervisor.py"
spec=importlib.util.spec_from_file_location("pce11_supervisor",MODULE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PCE11SidecarContractTests(unittest.TestCase):
    def test_self_contract(self):
        self.assertTrue(mod.self_test())

    def test_isolation_arguments_enforced(self):
        config=Path("X:/isolated/private/bridge.json")
        state=Path("X:/isolated/private/state")
        args=[mod.sys.executable,"-B","X:/staged/windows_relay.py","--config",
              str(config),"--state-dir",str(state),"server"]
        self.assertTrue(mod.validate_launch(args,state,config))
        with self.assertRaisesRegex(RuntimeError,"launch argument"):
            mod.validate_launch(args[:3]+["--config","X:/wrong.json"]+args[5:],state,config)

    def test_sidecar_port_separate(self):
        self.assertNotEqual(mod.PORT,8766)
        self.assertEqual(mod.PORT,8768)
        self.assertEqual(mod.V16_SHA,"694d47ab89596d5c3801f749caa352b951a2be52")

    def test_blob_integrity_is_exact_content(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"file.py"
            src.write_bytes(b"abc\n")
            self.assertEqual(mod.git_blob(src.read_bytes()),
              hashlib.sha1(b"blob 4\0abc\n").hexdigest())

    def test_job_guards_are_fail_closed(self):
        if not mod.win_job_available():
            with self.assertRaisesRegex(RuntimeError,"unavailable"):
                mod.OwnedJob()

    def test_run_does_not_touch_live_by_default(self):
        from inspect import getsource
        body=getsource(mod.main)
        self.assertIn('if a.mode=="preflight":',body)
        self.assertIn('else:',body)
        self.assertNotIn("relay-control.ps1",body)
        self.assertNotIn("taskkill",body)

if __name__=="__main__":
    unittest.main()
