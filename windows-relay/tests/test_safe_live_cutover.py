import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('safe_live_cutover',HERE/'safe_live_cutover.py')
CUT=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(CUT)

class SafeLiveCutoverTests(unittest.TestCase):
    def test_send_accepted_is_required_firefox_gate(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'browser-events.jsonl'
            rows=[
                {'event':'relay_result_received','detail':{'packet_id':'OPX'}},
                {'event':'relay_result_delivery_complete','detail':{'packet_id':'OPX'}},
            ]
            p.write_text('\n'.join(json.dumps(x) for x in rows)+'\n',encoding='utf-8')
            self.assertFalse(CUT.event_matches_send_accepted(p,'OPX'))
            with p.open('a',encoding='utf-8') as f:
                f.write(json.dumps({'event':'relay_result_send_accepted','detail':{'packet_id':'OTHER'}})+'\n')
                f.write(json.dumps({'event':'relay_result_send_accepted','detail':{'packet_id':'OPX'}})+'\n')
            self.assertTrue(CUT.event_matches_send_accepted(p,'OPX'))

    def test_missing_event_file_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(CUT.event_matches_send_accepted(Path(td)/'missing.jsonl','OPX'))

    def test_firefox_discovery_uses_unscoped_list_tabs(self):
        fake=mock.Mock(returncode=0,stdout=json.dumps({'firefox_pid':18160})+'\n',stderr='')
        with tempfile.TemporaryDirectory() as td, mock.patch.object(CUT,'run',return_value=fake) as r:
            live=Path(td);py=live/'python.exe'
            self.assertEqual(CUT.discover_firefox_pid(py,live),18160)
            args=r.call_args.args[0]
            self.assertEqual(args,[py,live/'firefox_adapter.py','list-tabs'])
            self.assertNotIn('--firefox-pid',args)

    def test_restore_snapshot_restores_and_removes(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);live=base/'live';backup=base/'backup';(backup/'files').mkdir(parents=True);live.mkdir()
            (live/'keep.txt').write_text('new',encoding='utf-8')
            (live/'added.txt').write_text('added',encoding='utf-8')
            old=b'old';(backup/'files'/'keep.txt').write_bytes(old)
            import hashlib
            manifest=[
                {'rel':'keep.txt','existed':True,'before_sha':hashlib.sha256(old).hexdigest()},
                {'rel':'added.txt','existed':False,'before_sha':None},
            ]
            (backup/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            CUT.restore_snapshot(live,backup)
            self.assertEqual((live/'keep.txt').read_text(encoding='utf-8'),'old')
            self.assertFalse((live/'added.txt').exists())
            self.assertTrue(CUT.snapshot_matches(live,backup))

    def test_reload_targets_existing_pre_reload_name(self):
        fake=mock.Mock(returncode=0,stdout='{}',stderr='')
        with tempfile.TemporaryDirectory() as td, mock.patch.object(CUT,'run',return_value=fake) as r:
            live=Path(td);py=live/'python.exe'
            CUT.reload_existing_addon(py,live,18160,CUT.OLD_ADDON_NAME)
            args=r.call_args.args[0]
            self.assertIn('reload-addon',args)
            self.assertIn('GPT Windows Relay',args)
            self.assertIn('--firefox-pid',args)
            self.assertIn('18160',args)

    def test_run_deadline_caps_subprocess_timeout(self):
        fake=mock.Mock(return_value=mock.Mock(returncode=0,stdout='',stderr=''))
        with mock.patch.object(CUT.time,'monotonic',return_value=100.0), mock.patch.object(CUT.subprocess,'run',fake):
            CUT._RUN_DEADLINE=110.0
            CUT.run(['echo','x'],timeout=60)
            self.assertEqual(fake.call_args.kwargs['timeout'],10.0)
        CUT.set_run_deadline(None)

    def test_wait_v17_requires_event_after_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'browser-events.jsonl'
            old={'event':'content_script_started','detail':{'runtime':'v11-scroll-v5-delivery-v17-whole-stop-v1-owner-v1'}}
            p.write_text(json.dumps(old)+'\n',encoding='utf-8')
            baseline=CUT.event_line_count(p)
            with self.assertRaises(RuntimeError): CUT.wait_v17(p,0,baseline)
            with p.open('a',encoding='utf-8') as f:f.write(json.dumps(old)+'\n')
            self.assertIn('owner-v1',CUT.wait_v17(p,1,baseline))

    def test_write_report_is_atomic_and_complete(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'report.json';CUT.write_report(p,{'ok':False,'steps':[{'step':'x'}]})
            self.assertEqual(json.loads(p.read_text(encoding='utf-8'))['steps'][0]['step'],'x')
            self.assertFalse(p.with_suffix('.json.tmp').exists())

if __name__=='__main__': unittest.main()
