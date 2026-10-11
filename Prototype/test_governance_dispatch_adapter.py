import importlib.util, unittest
from governance_dispatch_adapter import DispatchAdapter

ROOT='..'
AUDIT={'repository':'monag144/GPT-Windows-Relay','branch':'main','path':'docs/audits/AUDIT_2026-10-11T0555Z_PCE16_035_039_CHECKPOINT.md','start':35,'end':39,'commit_sha':'fd0c1ba93fb219a6d399435da19896fdda1052a2','file_sha':'1235f2af0c1fcac6efc6a6a3d2c04f3486f2afb4','url':'https://github.com/monag144/GPT-Windows-Relay/blob/fd0c1ba93fb219a6d399435da19896fdda1052a2/docs/audits/AUDIT_2026-10-11T0555Z_PCE16_035_039_CHECKPOINT.md','readback_verified':True}
REVIEW={'repository':AUDIT['repository'],'branch':'main','path':'docs/reviews/REVIEW_2026-10-11T0555Z_PCE16_020_039_CHECKPOINT.md','commit_sha':AUDIT['commit_sha'],'file_sha':'0f6143d09dfd16364a6233050a746eb1dfe3634e'}
class Harness:
    def engineering_preflight(self, series, ordinal, **kw):
        return {'ok':True,'blockers':[],'audit_required':True,'review_due':True}
class Tests(unittest.TestCase):
    def setUp(self):
        self.records=[{'id':f'PCE16.{i:03d}','source':'audit-or-runtime','status':'UNKNOWN' if i in (35,36,37) else 'GOVERNANCE_BLOCKED' if i in (38,39,40) else 'documented'} for i in range(41)]
        self.calls=[]
    def fetch(self,url,headers):
        if '/git/ref/' in url: return {'object':{'sha':AUDIT['commit_sha']}}
        return {'sha':AUDIT['file_sha'] if 'audits/' in url else REVIEW['file_sha']}
    def adapter(self,records=None): return DispatchAdapter(Harness(),self.fetch,AUDIT,REVIEW,records or self.records)
    def test_pce041_real_path_fixture_accepts_complete_history(self):
        v=self.adapter().preflight(41); self.assertTrue(v.allowed); self.assertEqual(len(v.attempted_ids),41)
    def test_gap_or_bad_blob_fails_before_reservation(self):
        v=self.adapter(self.records[:-1]).preflight(41); self.assertFalse(v.allowed); self.assertIn('missing_ordinals',v.reason)
        bad=dict(AUDIT,file_sha='0'*40); self.assertFalse(DispatchAdapter(Harness(),self.fetch,bad,REVIEW,self.records).preflight().allowed)
    def test_stop_owner_and_governance_precede_reservation(self):
        reserved=[]; executed=[]; a=self.adapter()
        self.assertEqual(a.dispatch('PCE16.041',stopped=True,owner_ok=True,reserve=lambda x:reserved.append(x) or True,execute=lambda x:executed.append(x)).reason,'stop_active')
        self.assertEqual(a.dispatch('PCE16.041',stopped=False,owner_ok=False,reserve=lambda x:reserved.append(x) or True,execute=lambda x:executed.append(x)).reason,'conversation_owner_mismatch')
        self.assertEqual(reserved,[]); self.assertEqual(executed,[])
    def test_duplicate_claim_is_refused(self):
        a=self.adapter(); n=[]
        v=a.dispatch('PCE16.041',stopped=False,owner_ok=True,reserve=lambda x:False,execute=lambda x:n.append(x))
        self.assertFalse(v.allowed); self.assertEqual(v.reason,'action_already_claimed'); self.assertEqual(n,[])
if __name__=='__main__': unittest.main()
