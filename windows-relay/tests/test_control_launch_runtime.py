import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(os.name == "nt", "Windows-only control launch acceptance")
class SourceRunnerIsolationTests(unittest.TestCase):
    def test_main_and_consumer_launchers_are_separate(self):
        root=Path(__file__).resolve().parents[1]
        main=(root/'run.ps1').read_text(encoding='utf-8-sig')
        consumer=(root/'run-consumer.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('Local\\GPTWindowsRelaySupervisor',main)
        self.assertNotIn('GPTWindowsRelayConsumer',main)
        self.assertIn('& $py $server server',main)
        self.assertIn('Local\\GPTWindowsRelayConsumerSupervisor',consumer)
        self.assertIn('GPTWindowsRelayConsumer',consumer)
        self.assertIn('--config $config --state-dir $stateDir server',consumer)

class ControlLaunchRuntimeTests(unittest.TestCase):
    def test_candidate_powershell_launch_pattern_handles_space_paths(self):
        with tempfile.TemporaryDirectory(prefix="relay launch ") as d:
            root = Path(d)
            script = root / "probe child.ps1"
            output = root / "probe result.txt"
            script.write_text(
                "param([string]$OutPath)\n"
                "Set-Content -LiteralPath $OutPath -Value 'GREEN' -Encoding ASCII\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PCE_SCRIPT"] = str(script)
            env["PCE_OUT"] = str(output)
            command = (
                "$s=$env:PCE_SCRIPT; $o=$env:PCE_OUT; "
                "$a='-NoProfile -ExecutionPolicy Bypass -File \"' + $s + '\" -OutPath \"' + $o + '\"'; "
                "$p=Start-Process powershell.exe -PassThru -Wait -ArgumentList $a; "
                "exit $p.ExitCode"
            )
            cp = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            self.assertTrue(output.is_file(), cp.stdout + cp.stderr)
            self.assertEqual(output.read_text(encoding="ascii").strip(), "GREEN")

    def test_candidate_python_launch_pattern_handles_space_paths(self):
        with tempfile.TemporaryDirectory(prefix="relay hud ") as d:
            root = Path(d)
            script = root / "probe child.py"
            output = root / "probe result.txt"
            script.write_text(
                "import pathlib,sys\npathlib.Path(sys.argv[1]).write_text('GREEN', encoding='ascii')\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PCE_PY"] = sys.executable
            env["PCE_SCRIPT"] = str(script)
            env["PCE_OUT"] = str(output)
            command = (
                "$py=$env:PCE_PY; $s=$env:PCE_SCRIPT; $o=$env:PCE_OUT; "
                "$a='\"' + $s + '\" \"' + $o + '\"'; "
                "$p=Start-Process -FilePath $py -PassThru -Wait -ArgumentList $a; "
                "exit $p.ExitCode"
            )
            cp = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            self.assertTrue(output.is_file(), cp.stdout + cp.stderr)
            self.assertEqual(output.read_text(encoding="ascii").strip(), "GREEN")


if __name__ == "__main__":
    unittest.main()
