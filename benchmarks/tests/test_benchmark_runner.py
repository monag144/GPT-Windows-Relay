"""Regression contract for PCE011 benchmark scorer and independent observer."""
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import benchmark_runner as bm
import overnight_observer as ob

class BenchmarkContract(unittest.TestCase):
    def test_all_26_cases_and_scope(self):
        cases=bm.catalog()["cases"]
        self.assertEqual([x["id"] for x in cases],list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        data={c["id"]:c for c in cases}
        self.assertFalse(bm.applicable(data["X"],{"product":"relay","browser":"firefox"}))
        self.assertFalse(bm.applicable(data["F"],{"product":"consumer","browser":"chrome"}))
        self.assertTrue(bm.applicable(data["U"],{"product":"consumer","browser":"edge"}))
    def test_unexecuted_and_unverified_never_pass(self):
        self.assertEqual(bm.proof("A",None)[0],"NOT_RUN")
        self.assertEqual(bm.proof("A",{"result":"PASS","reviewer":"x","evidence":{}})[0],"BLOCKED")
    def test_safety_metrics_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"e.json"
            p.write_text('{"passed":true}',encoding="utf-8")
            rec={"result":"PASS","reviewer":"independent",
                 "evidence":{"local_path":str(p),"sha256":bm.digest(p)}}
            self.assertEqual(bm.proof("O",rec)[0],"FAIL")
    def test_mutated_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"e.json"
            p.write_text('{"passed":true}',encoding="utf-8")
            rec={"result":"PASS","reviewer":"reviewer",
                 "evidence":{"local_path":str(p),"sha256":bm.digest(p)}}
            p.write_text('{"passed":false}',encoding="utf-8")
            self.assertEqual(bm.proof("A",rec)[0],"BLOCKED")
    def test_short_overnight_never_qualifies(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"p.jsonl"
            p.write_text("\n".join(json.dumps(x) for x in [
                {"kind":"start","utc":"2026-10-08T00:00:00+00:00","interval_seconds":15},
                {"kind":"probe","utc":"2026-10-08T00:00:00+00:00","ok":True},
                {"kind":"complete","utc":"2026-10-08T00:00:02+00:00","success":True}])+"\n")
            self.assertFalse(ob.summarize(p,43200)["qualified_for_tcp_gate"])
    def test_12h_needs_12_distinct_hourly_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"e.json"
            payload={"passed":True,"manual_rescues":0,"duplicate_effects":0,"unsafe_executions":0,
                "observer_summary":{"complete":True,"duration_seconds":43200,
                                     "uptime_percent":100,"max_gap_seconds":15},
                "hourly_receipts":[{"hour":i,"executions":1,"visible_result":True,"duplicate_effects":0}
                                    for i in range(11)],"unrecovered_stalls":0}
            p.write_text(json.dumps(payload))
            rec={"result":"PASS","reviewer":"reviewer",
                 "evidence":{"local_path":str(p),"sha256":bm.digest(p)}}
            self.assertEqual(bm.proof("U",rec)[0],"FAIL")
            payload["hourly_receipts"].append({"hour":11,"executions":1,
                                                "visible_result":True,"duplicate_effects":0})
            p.write_text(json.dumps(payload))
            rec["evidence"]["sha256"]=bm.digest(p)
            self.assertEqual(bm.proof("U",rec)[0],"BLOCKED")  # hourly claims alone cannot replace raw independent observation

if __name__=="__main__":
    unittest.main()
