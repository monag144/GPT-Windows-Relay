"""PCE11 independent v16 supervisor static contracts. Tests never start a server."""
from __future__ import annotations
import importlib.util
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_normalized_git_blob_accepts_crlf_checkout_only_when_index_matches(self):
        with tempfile.TemporaryDirectory() as d:
            live=Path(d)
            folder=live/"builds"/("RELAY_PCE8_V16_"+mod.V16_SHA[:12])
            path=folder/"windows-relay"/"windows_relay.py"
            path.parent.mkdir(parents=True)
            raw="print('--config','--state-dir','server','127.0.0.1')\\r\\nState(a.state_dir)\\r\\nconfig(a.config)\\r\\n"
            # Simulate Git checkout with Windows CRLF worktree but pinned normalized Git object.
            path.write_bytes(raw.replace("\\\\r", "\\r").replace("\\\\n", "\\n").encode("utf-8"))
            self.assertNotEqual(mod.git_blob(path.read_bytes()),mod.V16_BLOB)
            def fake_git(directory,*parts,**kwargs):
                commands={
                    ("rev-parse","HEAD"):mod.V16_SHA,
                    ("status","--porcelain"):"",
                    ("rev-parse","HEAD:windows-relay/windows_relay.py"):mod.V16_BLOB,
                    ("hash-object","--path=windows-relay/windows_relay.py","windows-relay/windows_relay.py"):mod.V16_BLOB,
                }
                return commands[tuple(parts)]
            with patch.object(mod,"git",side_effect=fake_git):
                record=mod.candidate(None,live)
            self.assertFalse(record["raw_worktree_matches_blob"])
            self.assertEqual(record["tracked_git_blob"],mod.V16_BLOB)
            self.assertEqual(record["normalized_worktree_blob"],mod.V16_BLOB)

    def test_normalized_worktree_mismatch_blocks_untrusted_file(self):
        with tempfile.TemporaryDirectory() as d:
            live=Path(d)
            folder=live/"builds"/("RELAY_PCE8_V16_"+mod.V16_SHA[:12])
            path=folder/"windows-relay"/"windows_relay.py"
            path.parent.mkdir(parents=True)
            path.write_text("print('--config', '--state-dir', 'server', '127.0.0.1')\\nState(a.state_dir)\\nconfig(a.config)\\n",encoding="utf-8")
            def wrong_git(directory,*parts,**kwargs):
                if parts==("rev-parse","HEAD"):return mod.V16_SHA
                if parts==("status","--porcelain"):return ""
                if parts==("rev-parse","HEAD:windows-relay/windows_relay.py"):return mod.V16_BLOB
                if parts[0]=="hash-object":return "0"*40
                raise RuntimeError("unexpected git call")
            with patch.object(mod,"git",side_effect=wrong_git):
                with self.assertRaisesRegex(RuntimeError,"normalized working source mismatched"):
                    mod.candidate(None,live)

    def test_canary_mode_cannot_run_until_containment_is_repaired(self):
        args=["x","--repo","R:/dummy","--live","R:/dummy-live",
              "--expected-head","unused","--mode","canary"]
        with patch.object(mod.sys,"argv",args):
            with self.assertRaisesRegex(RuntimeError,"canary disabled"):
                mod.main()

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
