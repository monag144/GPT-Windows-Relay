import unittest
from governance_evidence import authenticated_github_fetch
from governance_evidence import EvidenceError, verify_github_audit, reconstruct_issued_ids, validate_pce16_ledger, verify_audit_and_review

class GovernanceEvidenceTests(unittest.TestCase):
    def test_authenticated_fetch_requires_token_and_sets_bearer(self):
        with self.assertRaises(EvidenceError): authenticated_github_fetch("")
        seen = {}
        class Resp:
            def __enter__(self): return self
            def __exit__(self,*a): pass
            def read(self): return b'{"ok":true}'
        def opener(req, timeout=0):
            seen.update(dict(req.header_items())); return Resp()
        self.assertEqual(authenticated_github_fetch("tok", opener)("https://x", {}), {"ok":True})
        self.assertEqual(seen["Authorization"], "Bearer tok")
    def setUp(self):
        self.c='a'*40; self.b='b'*40
        self.r={'repository':'monag144/GPT-Windows-Relay','branch':'main','path':'docs/audits/AUDIT_2026-10-10T2353Z_PCE16_030_034_CHECKPOINT.md','start':30,'end':34,'commit_sha':self.c,'file_sha':self.b,'url':f'https://github.com/monag144/GPT-Windows-Relay/blob/{self.c}/docs/audits/AUDIT_2026-10-10T2353Z_PCE16_030_034_CHECKPOINT.md','readback_verified':True}
    def fetch(self,url,headers):
        if '/git/ref/' in url:return {'object':{'sha':self.c}}
        return {'sha':self.b}
    def test_verified(self): self.assertTrue(verify_github_audit(self.r,self.fetch)['readback_verified'])
    def test_local_flag_cannot_fix_commit(self):
        r={**self.r,'commit_sha':'c'*40}
        with self.assertRaises(EvidenceError): verify_github_audit(r,self.fetch)
    def test_blob_mismatch(self):
        with self.assertRaises(EvidenceError): verify_github_audit({**self.r,'file_sha':'c'*40},self.fetch)
    def test_duplicate_ids_rejected(self):
        with self.assertRaises(EvidenceError): reconstruct_issued_ids([{'id':'PCE16.035-x'},{'id':'PCE16.035-x'}])
    def test_missing_ids_are_not_invented(self):
        self.assertEqual(reconstruct_issued_ids([{'id':'PCE16.035-x'},{'status':'UNKNOWN'}]),['PCE16.035-x'])
    def test_complete_ledger_requires_all_slots(self):
        rows=[{'id':f'PCE16.{n:03d}-x'} for n in range(40)]
        self.assertEqual(len(validate_pce16_ledger(rows)),40)
    def test_ledger_gap_rejected(self):
        with self.assertRaises(EvidenceError): validate_pce16_ledger([{'id':f'PCE16.{n:03d}-x'} for n in range(39)])
    def test_review_commit_and_blob_verified(self):
        review={'repository':'monag144/GPT-Windows-Relay','branch':'main','path':'docs/reviews/x.md','commit_sha':self.c,'file_sha':self.b}
        out=verify_audit_and_review(self.r,review,self.fetch)
        self.assertEqual(out['review']['verified_blob'],self.b)

if __name__=='__main__': unittest.main()
