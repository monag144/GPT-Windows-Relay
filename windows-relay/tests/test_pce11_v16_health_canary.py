"""PCE11.016 mocked private health canary acceptance: never starts a real process."""
from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

MODULE=Path(__file__).resolve().parents[1]/"tools"/"pce11_016_v16_health_canary.py"
spec=importlib.util.spec_from_file_location("pce11_016_v16_health_canary",MODULE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class FakeContained:
    last=None
    def __init__(self):
        self.pid=123456
        self.resumed=False
        self.contained=False
        self.disposed=False
        self.events=[]
        self.started_args=None
        self.started_cwd=None
        FakeContained.last=self
    def start(self,args,cwd):
        self.started_args=list(args);self.started_cwd=cwd
        self.events=["job_created","job_kill_on_close","child_created_suspended",
                     "child_contained","child_resumed"]
        self.resumed=True;self.contained=True
        return self
    def poll(self):return None
    def close(self):
        self.disposed=True
        self.events.extend(["private_job_terminated","child_handles_closed"])

class V16HealthCanaryTests(unittest.TestCase):
    def test_main_and_canary_ports_are_distinct(self):
        self.assertEqual(m.PROD_PORT,8766)
        self.assertEqual(m.SIDECAR_PORT,8768)
        self.assertNotEqual(m.PROD_PORT,m.SIDECAR_PORT)

    def test_empty_canary_port_required(self):
        with patch.object(m,"port_pids",return_value=[123]):
            with self.assertRaisesRegex(RuntimeError,"isolated port is occupied"):
                m.verify_no_sidecar()

    def test_auth_request_uses_readonly_get(self):
        data={"ok":True,"pid":123456,"armed":True,"pending_missions":0}
        response=Mock()
        response.read.return_value=json.dumps(data).encode()
        context=Mock()
        context.__enter__=Mock(return_value=response)
        context.__exit__=Mock(return_value=False)
        with patch.object(m.urllib.request,"urlopen",return_value=context) as opener:
            actual=m.get_status(8768,"test-private-token")
        self.assertEqual(actual["pid"],123456)
        req=opener.call_args.args[0]
        self.assertEqual(req.get_method(),"GET")
        self.assertEqual(req.full_url,"http://127.0.0.1:8768/status")
        self.assertEqual(req.headers["X-gpt-windows-relay-token"],"test-private-token")

    def private(self,root):
        box=root/"private-canary"
        box.mkdir()
        state=box/"state";state.mkdir()
        config=box/"bridge.json"
        config.write_text('{"private":true}',encoding="utf-8")
        return box,state,config,"secret-not-for-output"

    def test_success_contained_readonly_canary_and_config_scrub(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t)
            private=self.private(live)
            base={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":2}
            stage={"source":str(live/"windows_relay.py")}
            legacy=Mock()
            containment=Mock(ContainedProcess=FakeContained)
            status={"ok":True,"pid":123456,"pending_missions":0,"armed":True}
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",return_value=base) as livecheck,\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",return_value=[]),\
                 patch.object(m,"get_status",return_value=status):
                result=m.run_health_canary(live,stage,legacy,containment)
            self.assertEqual(result["private_missions_count"],0)
            self.assertTrue(result["status_ok"])
            self.assertTrue(result["job_contained"])
            self.assertTrue(result["cleanup_verified"])
            self.assertTrue(result["production_main_identity_preserved"])
            self.assertTrue(result["sidecar_released"])
            self.assertTrue(FakeContained.last.disposed)
            self.assertTrue(legacy.validate_launch.called)
            self.assertEqual(livecheck.call_count,2)
            self.assertFalse(private[2].exists())
            record=json.loads((private[0]/"health-report.json").read_text())
            self.assertNotIn(private[3],str(record))
            self.assertFalse(record["browser_control_used"])
            self.assertFalse(record["operator_stop_triggered"])

    def test_foreign_listener_response_blocks_and_releases_job(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t)
            private=self.private(live)
            baseline={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":0}
            legacy=Mock()
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",return_value=baseline),\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",return_value=[]),\
                 patch.object(m,"get_status",return_value={
                    "ok":True,"pid":998877,"pending_missions":0,"armed":True}):
                with self.assertRaisesRegex(RuntimeError,"forensic evidence"):
                    m.run_health_canary(live,{"source":str(live/"s.py")},
                                        legacy,Mock(ContainedProcess=FakeContained))
            self.assertTrue(FakeContained.last.disposed)
            self.assertFalse(private[2].exists())
            evidence=json.loads((private[0]/"health-report.json").read_text())
            self.assertFalse(evidence["status_ok"])
            self.assertIn("foreign sidecar PID",evidence["failure"])

    def test_production_identity_drift_fails(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t)
            private=self.private(live)
            baseline={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":0}
            changed=dict(baseline,pid=999)
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",side_effect=[baseline,changed]),\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",return_value=[]),\
                 patch.object(m,"get_status",return_value={
                    "ok":True,"pid":123456,"pending_missions":0,"armed":True}):
                with self.assertRaisesRegex(RuntimeError,"forensic evidence"):
                    m.run_health_canary(live,{"source":str(live/"s.py")},
                                        Mock(),Mock(ContainedProcess=FakeContained))
            self.assertTrue(FakeContained.last.disposed)

    def test_canary_exposes_neither_token_nor_external_payload(self):
        src=MODULE.read_text(encoding="utf-8")
        for needle in ("POST /action","/mission-ack","/arm","taskkill","firefox_adapter.py"):
            self.assertNotIn(needle,src)
        self.assertIn("ContainedProcess()",src)
        self.assertIn("private_missions_count",src)

if __name__=="__main__":unittest.main()
