from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]


def sync_files():
    text = (ROOT / "sync-live.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "FILES" for t in node.targets):
                return list(ast.literal_eval(node.value))
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "FILES":
            return list(ast.literal_eval(node.value))
    raise AssertionError("sync-live.py FILES assignment not found")


class ControlLauncherSplitPCE9Tests(unittest.TestCase):
    def test_dedicated_8766_control_launcher_exists_and_uses_legacy_runtime(self):
        path = ROOT / "run-control.ps1"
        self.assertTrue(path.is_file(), "8766 control launcher run-control.ps1 is missing")
        text = path.read_text(encoding="utf-8-sig")
        self.assertIn("Local\\GPTWindowsRelaySupervisor", text)
        self.assertIn("& $py $server server", text)
        self.assertNotIn("GPTWindowsRelayConsumer", text)
        self.assertNotIn("--config $config --state-dir $stateDir server", text)

    def test_control_and_watchdog_launch_dedicated_control_launcher(self):
        control = (ROOT / "relay-control.ps1").read_text(encoding="utf-8-sig")
        watchdog = (ROOT / "relay-watchdog-loop.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("run-control.ps1", control)
        self.assertIn("run-control.ps1", watchdog)
        self.assertNotIn("Join-Path $root 'run.ps1'", control)
        self.assertNotIn("Join-Path $root 'run.ps1'", watchdog)

    def test_live_sync_carries_control_launcher_but_not_consumer_launcher(self):
        files = sync_files()
        self.assertIn("run-control.ps1", files)
        self.assertNotIn("run.ps1", files)


if __name__ == "__main__":
    unittest.main()
