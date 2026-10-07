import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SYNC=ROOT/'sync-live.py'
REQUIRED={
 'hud.py',
 'relay-control.ps1',
 'relay-watchdog-loop.ps1',
 'STOP-RELAY.bat',
 'job_application_engine_v2.py',
 'job_application_manifest_v2.py',
 'job_application_runner_v2.py',
 'job_application_session_v2.py',
 'reasoning_broker_v2.py',
 'sync-live.py',
 'windows_outbound_worker.py',
 'workday_provider_v2.py',
}

def sync_files():
 tree=ast.parse(SYNC.read_text(encoding='utf-8'))
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FILES' for t in node.targets):
   return set(ast.literal_eval(node.value))
 raise AssertionError('FILES assignment not found')

class SyncLiveManifestPce9Tests(unittest.TestCase):
 def test_proven_live_runtime_assets_are_synced(self):
  self.assertEqual(REQUIRED-sync_files(),set())
  for rel in REQUIRED:
   self.assertTrue((ROOT/rel).is_file(),rel)

if __name__=='__main__': unittest.main()