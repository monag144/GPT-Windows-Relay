"""PCE11.016 mocked private health canary acceptance: never starts a real process."""
from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock,Mock,patch

MODULE=Path(__file__).resolve().parents[1]/"tools"/"pce11_016_v16_health_canary.py"
sys.path.insert(0,str(MODULE.parent))
spec=importlib.util.spec_from_file_location("pce11_016_v16_health_canary",MODULE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class FakeContained:
    last=None
    def __init__(self):
        self.pid=123456
        self.job=101
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

class FakeHost:
    def __init__(self,pid=123456,parent=123456,fail_exit=False):
        self.pid=pid
        self.parent_pid=parent
        self.job_member=True
        self.verified=True
        self.closed=False
        self.fail_exit=fail_exit
    def wait_for_exit(self):
        if self.fail_exit:raise RuntimeError("private host exit timeout")
        return True
    def close(self):self.closed=True

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
        context=MagicMock()
        context.__enter__.return_value=response
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
                 patch.object(m,"port_pids",side_effect=[[123456],[],[]]),\
                 patch.object(m,"attest_private_host",return_value=FakeHost()),\
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
            self.assertEqual(record["observed_status_pid"],123456)
            self.assertEqual(record["observed_pending_missions"],0)
            self.assertIs(record["status_pid_matches_child"],True)
            self.assertIs(record["status_missions_zero"],True)
            self.assertTrue(record["listener_pid_matches_status"])
            self.assertTrue(record["host_identity_verified"])
            self.assertTrue(record["host_exited_after_job_close"])
            self.assertTrue(record["host_handle_closed"])

    def test_foreign_listener_response_blocks_and_releases_job(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t)
            private=self.private(live)
            baseline={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":0}
            legacy=Mock()
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",return_value=baseline),\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",side_effect=[[998877],[],[]]),\
                 patch.object(m,"attest_private_host",side_effect=RuntimeError("foreign child ancestry")),\
                 patch.object(m,"get_status",return_value={
                    "ok":True,"pid":998877,"pending_missions":0,"armed":True}):
                with self.assertRaisesRegex(RuntimeError,"forensic evidence"):
                    m.run_health_canary(live,{"source":str(live/"s.py")},
                                        legacy,Mock(ContainedProcess=FakeContained))
            self.assertTrue(FakeContained.last.disposed)
            self.assertFalse(private[2].exists())
            evidence=json.loads((private[0]/"health-report.json").read_text())
            self.assertFalse(evidence["status_ok"])
            self.assertEqual(evidence["observed_status_pid"],998877)
            self.assertEqual(evidence["expected_child_pid"],123456)
            self.assertEqual(evidence["observed_pending_missions"],0)
            self.assertIs(evidence["status_pid_matches_child"],False)
            self.assertIs(evidence["status_missions_zero"],True)
            self.assertIn("foreign child ancestry",evidence["failure"])

    def test_nonzero_private_missions_are_reported_independently_and_cleanup(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t);private=self.private(live)
            baseline={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":2}
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",return_value=baseline),\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",side_effect=[[123456],[],[]]),\
                 patch.object(m,"attest_private_host",return_value=FakeHost()),\
                 patch.object(m,"get_status",return_value={
                    "ok":True,"pid":123456,"pending_missions":5,"armed":True}):
                with self.assertRaisesRegex(RuntimeError,"forensic evidence"):
                    m.run_health_canary(live,{"source":str(live/"s.py")},
                                        Mock(),Mock(ContainedProcess=FakeContained))
            result=json.loads((private[0]/"health-report.json").read_text())
            self.assertTrue(result["job_contained"])
            self.assertTrue(result["cleanup_verified"])
            self.assertEqual(result["observed_status_pid"],123456)
            self.assertEqual(result["observed_pending_missions"],5)
            self.assertIs(result["status_pid_matches_child"],True)
            self.assertIs(result["status_missions_zero"],False)
            self.assertIn("nonzero or malformed mission count",result["failure"])
            self.assertNotIn(private[3],str(result))
            self.assertFalse(private[2].exists())

    def test_missing_or_string_pid_is_rejected_and_recorded(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t);private=self.private(live)
            baseline={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":2}
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",return_value=baseline),\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",return_value=[]),\
                 patch.object(m,"get_status",return_value={
                    "ok":True,"pid":"123456","pending_missions":0,"armed":True}):
                with self.assertRaisesRegex(RuntimeError,"forensic evidence"):
                    m.run_health_canary(live,{"source":str(live/"s.py")},
                                        Mock(),Mock(ContainedProcess=FakeContained))
            result=json.loads((private[0]/"health-report.json").read_text())
            self.assertEqual(result["observed_status_pid"],"123456")
            self.assertIs(result["status_pid_matches_child"],False)
            self.assertIs(result["status_missions_zero"],True)
            self.assertIn("status PID mismatch",result["failure"])
            self.assertTrue(result["cleanup_verified"])

    def test_verified_direct_child_venv_host_is_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t); private=self.private(live)
            baseline={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":2}
            server={"ok":True,"pid":778899,"armed":True,"pending_missions":0}
            host=FakeHost(pid=778899,parent=123456)
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",return_value=baseline),\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",side_effect=[[778899],[],[]]),\
                 patch.object(m,"attest_private_host",return_value=host) as verifier,\
                 patch.object(m,"get_status",return_value=server):
                receipt=m.run_health_canary(live,{"source":str(live/"s.py")},Mock(),Mock(ContainedProcess=FakeContained))
            verifier.assert_called_once_with(778899,123456,101)
            self.assertIs(receipt["status_pid_matches_child"],False)
            self.assertTrue(receipt["host_identity_verified"])
            self.assertEqual(receipt["host_parent_pid"],123456)
            self.assertTrue(receipt["host_exited_after_job_close"])
            self.assertTrue(receipt["cleanup_verified"])
            self.assertTrue(host.closed)

    def test_foreign_listener_port_pid_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t);private=self.private(live)
            baseline={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":2}
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",return_value=baseline),\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",side_effect=[[444444],[],[]]),\
                 patch.object(m,"attest_private_host") as verifier,\
                 patch.object(m,"get_status",return_value={
                    "ok":True,"pid":123456,"armed":True,"pending_missions":0}):
                with self.assertRaisesRegex(RuntimeError,"forensic evidence"):
                    m.run_health_canary(live,{"source":str(live/"s.py")},Mock(),Mock(ContainedProcess=FakeContained))
            verifier.assert_not_called()
            receipt=json.loads((private[0]/"health-report.json").read_text())
            self.assertFalse(receipt["listener_pid_matches_status"])
            self.assertTrue(receipt["cleanup_verified"])

    def test_host_nonexit_blocks_health_acceptance(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t);private=self.private(live)
            baseline={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":2}
            host=FakeHost(fail_exit=True)
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",return_value=baseline),\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",side_effect=[[123456],[],[]]),\
                 patch.object(m,"attest_private_host",return_value=host),\
                 patch.object(m,"get_status",return_value={
                    "ok":True,"pid":123456,"armed":True,"pending_missions":0}):
                with self.assertRaisesRegex(RuntimeError,"forensic evidence"):
                    m.run_health_canary(live,{"source":str(live/"s.py")},Mock(),Mock(ContainedProcess=FakeContained))
            receipt=json.loads((private[0]/"health-report.json").read_text())
            self.assertFalse(receipt["cleanup_verified"])
            self.assertFalse(receipt["host_exited_after_job_close"])
            self.assertTrue(host.closed)

    def test_production_identity_drift_fails(self):
        with tempfile.TemporaryDirectory() as t:
            live=Path(t)
            private=self.private(live)
            baseline={"pid":555,"armed":True,"outbound_owner":"browser","pending_missions":0}
            changed=dict(baseline,pid=999)
            with patch.object(m,"verify_no_sidecar"),\
                 patch.object(m,"main_baseline",side_effect=[baseline,changed]),\
                 patch.object(m,"create_private",return_value=private),\
                 patch.object(m,"port_pids",side_effect=[[123456],[],[]]),\
                 patch.object(m,"attest_private_host",return_value=FakeHost()),\
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
