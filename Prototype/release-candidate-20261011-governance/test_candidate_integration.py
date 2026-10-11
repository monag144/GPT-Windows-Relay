import hashlib, json, pathlib, tempfile, importlib, re, unittest

M=importlib.import_module('windows_relay')
PACKET='[GPT_WINDOWS_ACTION]{"version":1,"platform":"windows","action":"EXEC","id":"PCE16.041","session":"pce16.041","command":"echo isolated"}[/GPT_WINDOWS_ACTION]'
OWNER={'conversation_key':'https://chatgpt.com/c/test','session':'pce16.041','tab_id':7}
class CandidateIntegration(unittest.TestCase):
 def setUp(self):
  self.d=pathlib.Path(tempfile.mkdtemp()); self.s=M.State(self.d/'state.json'); self.s.set_armed(True); self.s.data['conversation_owner']=OWNER; self.s.save(); self.calls=[]
  self.issuance={'id':'PCE16.041','session':'pce16.041','packet_hash':hashlib.sha256(PACKET.encode()).hexdigest(),'provenance':'persistent-content-port'}
  self.old=M.execute; M.execute=lambda a:self.calls.append(a.id) or {'version':1,'platform':'windows','id':a.id,'session':a.session,'action':'EXEC','shell':a.shell,'status':'OK','exit_code':0,'cwd':'.','started_at':M.now(),'finished_at':M.now(),'duration_ms':0,'stdout':'mock','stderr':''}
  M._candidate_governance.preflight=lambda n:{'ok':True,'next_ordinal':n}
 def tearDown(self): M.execute=self.old
 def test_authenticated_issuance_owner_and_exact_once(self):
  self.assertTrue(M.validate_transport_identity(PACKET,self.issuance,OWNER,self.s)); M.process(PACKET,self.s); M.process(PACKET,self.s)
  self.assertEqual(self.calls,['PCE16.041']); self.assertEqual(len((self.d/'issuance-journal.jsonl').read_text().splitlines()),1)
 def test_forged_owner_and_changed_payload_rejected(self):
  with self.assertRaises(M.RelayError): M.validate_transport_identity(PACKET,self.issuance,{**OWNER,'conversation_key':'https://chatgpt.com/c/other'},self.s)
  with self.assertRaises(M.RelayError): M.validate_transport_identity(PACKET,self.issuance,{**OWNER,'session':'other'},self.s)
 def test_stop_before_claim(self):
  self.s.set_armed(False); out=M.process(PACKET,self.s); self.assertIn('STOPPED',out); self.assertEqual(self.calls,[])
 def test_conflicting_issuance_rejected(self):
  M.validate_transport_identity(PACKET,self.issuance,OWNER,self.s)
  with self.assertRaises(M.RelayError): M.validate_transport_identity(PACKET,{**self.issuance,'packet_hash':'0'*64},OWNER,self.s)
if __name__=='__main__': unittest.main()
