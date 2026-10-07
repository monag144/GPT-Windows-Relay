import json
import tempfile
import unittest
from pathlib import Path

import windows_outbound_worker as wow
from windows_relay import State

URL="https://chatgpt.com/c/abc"

class FakeState:
    def __init__(self,phase="READY",claimable=True,finish_raises=False):
        self.phase=phase;self.claimable=claimable;self.finish_raises=finish_raises;self.calls=[]
    def list_claimable_outbound_ids(self):
        self.calls.append("list")
        return ["pkt"] if self.claimable and self.phase in {"READY","PRE_SUBMIT_FAILED"} else []
    def outbound_lookup(self,aid):
        self.calls.append("lookup")
        return {"id":aid,"phase":self.phase,"has_attachments":False}
    def claim_outbound_delivery(self,aid):
        self.calls.append("claim")
        if self.phase not in {"READY","PRE_SUBMIT_FAILED"}: raise RuntimeError("not claimable")
        self.phase="SUBMITTING";return {"id":aid,"phase":self.phase}
    def finish_outbound_delivery(self,aid,phase):
        self.calls.append("finish:"+phase)
        if self.finish_raises: raise RuntimeError("finish failed")
        if self.phase!="SUBMITTING": raise RuntimeError("not submitting")
        self.phase=phase;return {"id":aid,"phase":phase}

def target(url,profile_path=None):
    return {"conversation_url":url,"tab_name":"Engineering","firefox_pid":18160,"match_count":1}

class DormantWorkerTests(unittest.TestCase):
    def make_worker(self,state,tmp,**kw):
        wire=Path(tmp)/"wire.txt";wire.write_text("exact-wire",encoding="utf-8")
        return wow.WindowsOutboundWorker(state,URL,pause_path=Path(tmp)/"pause",resolver=kw.get("resolver",target),sender=kw.get("sender",lambda *a,**k:{"state":"SUBMITTED"}),result_file_getter=kw.get("getter",lambda s,a:str(wire)))

    def test_state_claimable_enumerator_is_read_only_deterministic_and_filtered(self):
        with tempfile.TemporaryDirectory() as d:
            st=State(Path(d)/"state.json")
            st.data["outbound_deliveries"]={
                "b":{"phase":"READY","has_attachments":False,"created_at":"2026-01-02"},
                "a":{"phase":"PRE_SUBMIT_FAILED","has_attachments":False,"created_at":"2026-01-01"},
                "c":{"phase":"SUBMITTED","has_attachments":False,"created_at":"2026-01-00"},
                "d":{"phase":"READY","has_attachments":True,"created_at":"2025-01-01"}}
            before=json.dumps(st.data,sort_keys=True)
            self.assertEqual(st.list_claimable_outbound_ids(),[])
            st.data["outbound_owner"]="windows"
            self.assertEqual(st.list_claimable_outbound_ids(),["a","b"])
            self.assertEqual(json.loads(before)["outbound_deliveries"],st.data["outbound_deliveries"])
            st.set_armed(False);self.assertEqual(st.list_claimable_outbound_ids(),[])

    def test_browser_owner_disarmed_and_pause_are_inert(self):
        with tempfile.TemporaryDirectory() as d:
            st=State(Path(d)/"state.json");st.data["outbound_deliveries"]={"pkt":{"phase":"READY","has_attachments":False,"created_at":"x"}}
            hits=[]
            w=wow.WindowsOutboundWorker(st,URL,pause_path=Path(d)/"pause",resolver=lambda *a,**k:hits.append("resolver"),sender=lambda *a,**k:hits.append("sender"),result_file_getter=lambda *a:hits.append("wire"))
            self.assertEqual(w.run_once()["status"],"IDLE")
            st.data["outbound_owner"]="windows";st.set_armed(False)
            self.assertEqual(w.run_once()["status"],"IDLE")
            st.data["armed"]=True;(Path(d)/"pause").write_text("",encoding="utf-8")
            self.assertEqual(w.run_once()["status"],"PAUSED")
            self.assertEqual(hits,[])

    def test_wire_failure_is_preclaim_and_never_resolves_or_claims(self):
        with tempfile.TemporaryDirectory() as d:
            st=FakeState();hits=[]
            def bad(*a): hits.append("wire");raise OSError("bad")
            w=self.make_worker(st,d,getter=bad,resolver=lambda *a,**k:hits.append("resolver"))
            r=w.run_once();self.assertEqual(r["status"],"PRECLAIM_FAILED")
            self.assertEqual(hits,["wire"]);self.assertNotIn("claim",st.calls)

    def test_target_resolution_failure_is_preclaim(self):
        with tempfile.TemporaryDirectory() as d:
            st=FakeState()
            def bad(*a,**k): raise RuntimeError("no target")
            r=self.make_worker(st,d,resolver=bad).run_once()
            self.assertEqual(r["status"],"PRECLAIM_FAILED");self.assertNotIn("claim",st.calls)

    def test_submitted_flow_claims_once_sends_once_and_finishes_once(self):
        with tempfile.TemporaryDirectory() as d:
            st=FakeState();sent=[]
            def sender(*a,**k): sent.append((a,k));return {"state":"SUBMITTED","send_invoked":True,"confirmed":True}
            r=self.make_worker(st,d,sender=sender).run_once()
            self.assertEqual(r["status"],"SUBMITTED");self.assertEqual(len(sent),1)
            self.assertEqual(sent[0][0][1:4],("pkt","Engineering",URL))
            self.assertEqual(st.calls.count("claim"),1);self.assertEqual(st.calls.count("finish:SUBMITTED"),1)

    def test_pre_submit_failed_sender_state_is_persisted(self):
        with tempfile.TemporaryDirectory() as d:
            st=FakeState();r=self.make_worker(st,d,sender=lambda *a,**k:{"state":"PRE_SUBMIT_FAILED"}).run_once()
            self.assertEqual(r["status"],"PRE_SUBMIT_FAILED");self.assertEqual(st.phase,"PRE_SUBMIT_FAILED")

    def test_sender_exception_after_claim_becomes_uncertain_and_never_retries(self):
        with tempfile.TemporaryDirectory() as d:
            st=FakeState();hits=[]
            def boom(*a,**k): hits.append("send");raise RuntimeError("unknown")
            w=self.make_worker(st,d,sender=boom)
            self.assertEqual(w.run_once()["status"],"SUBMIT_UNCERTAIN")
            self.assertEqual(st.phase,"SUBMIT_UNCERTAIN");self.assertEqual(hits,["send"])
            self.assertEqual(w.run_once()["status"],"IDLE");self.assertEqual(hits,["send"])

    def test_finish_failure_leaves_submitting_unresolved(self):
        with tempfile.TemporaryDirectory() as d:
            st=FakeState(finish_raises=True)
            r=self.make_worker(st,d).run_once()
            self.assertEqual(r["status"],"SUBMITTING_UNRESOLVED");self.assertEqual(st.phase,"SUBMITTING")

    def test_worker_is_not_wired_into_production_startup(self):
        relay=(Path(__file__).parents[1]/"windows_relay.py").read_text(encoding="utf-8-sig")
        worker=(Path(__file__).parents[1]/"windows_outbound_worker.py").read_text(encoding="utf-8-sig")
        self.assertNotIn("windows_outbound_worker",relay)
        self.assertNotIn("def main(",worker)
        self.assertNotIn("threading.Thread(",worker)
        self.assertNotIn("set_outbound_owner",worker)

if __name__=="__main__":
    unittest.main()
