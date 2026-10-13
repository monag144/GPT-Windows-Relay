"""Run the real persistent-worker transport smoke under Node when available."""
from pathlib import Path
import shutil
import subprocess
import unittest

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "relay_action_transport_smoke.cjs"


class BrowserTransportNodeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_persistent_worker_auth_transport_and_operator_prompt(self):
        command = [shutil.which("node"), str(RUNNER)]
        result = subprocess.run(
            command, cwd=str(HERE), text=True, capture_output=True,
            timeout=35, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("BROWSER_TRANSPORT_MOCK_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
