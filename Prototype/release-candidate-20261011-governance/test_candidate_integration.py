import hashlib, json, pathlib, tempfile, importlib, re, unittest, threading, urllib.request

M=importlib.import_module('windows_relay')
PACKET='[GPT_WINDOWS_ACTION]{"version":1,"platform":"windows","action":"EXEC","id":"PCE16.041","session":"pce16.041","command":"echo isolated"}[/GPT_WINDOWS_ACTION]'
OWNER={'conversation_key':'https://chatgpt.com/c/test','session':'pce16.041','tab_id':7}
class CandidateIntegration(unittest.TestCase):
 def test_manifest_hashes_match_bytes(self):
  root=pathlib.Path(__file__).parent; manifest=json.loads((root/'CANDIDATE_MANIFEST.json').read_text())
  for rel,expected in manifest['hashes'].items():
   p=root/rel; self.assertTrue(p.is_file(),rel); self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest().upper(),expected,rel)
 def setUp(self):
  self.d=pathlib.Path(tempfile.mkdtemp()); self.s=M.State(self.d/'state.json'); self.s.set_armed(True); self.s.bind_conversation_owner(OWNER); self.calls=[]
  self.issuance={'id':'PCE16.041','session':'pce16.041','packet_hash':hashlib.sha256(PACKET.encode()).hexdigest(),'provenance':'persistent-content-port'}
  self.old=M.execute; M.execute=lambda a:self.calls.append(a.id) or {'version':1,'platform':'windows','id':a.id,'session':a.session,'action':'EXEC','shell':a.shell,'status':'OK','exit_code':0,'cwd':'.','started_at':M.now(),'finished_at':M.now(),'duration_ms':0,'stdout':'mock','stderr':''}
 def tearDown(self): M.execute=self.old
 def test_authenticated_issuance_owner_and_exact_once(self):
  self.assertTrue(M.validate_transport_identity(PACKET,self.issuance,OWNER,self.s)); transport={'issuance':self.issuance,'owner':OWNER}; M.process(PACKET,self.s,transport); M.process(PACKET,self.s,transport)
  self.assertEqual(self.calls,['PCE16.041']); self.assertEqual(len((self.d/'issuance-journal.jsonl').read_text().splitlines()),1)
 def test_forged_owner_and_changed_payload_rejected(self):
  with self.assertRaises(M.RelayError): M.validate_transport_identity(PACKET,self.issuance,{**OWNER,'conversation_key':'https://chatgpt.com/c/other'},self.s)
  with self.assertRaises(M.RelayError): M.validate_transport_identity(PACKET,self.issuance,{**OWNER,'session':'other'},self.s)
 def test_stop_before_claim(self):
  self.s.set_armed(False); out=M.process(PACKET,self.s,{'issuance':self.issuance,'owner':OWNER}); self.assertIn('STOPPED',out); self.assertEqual(self.calls,[])
 def test_conflicting_issuance_rejected(self):
  M.validate_transport_identity(PACKET,self.issuance,OWNER,self.s)
  with self.assertRaises(M.RelayError): M.validate_transport_identity(PACKET,{**self.issuance,'packet_hash':'0'*64},OWNER,self.s)
 def test_http_handler_requires_auth_and_executes_once(self):
  token='t'*40; srv=M.Server(('127.0.0.1',0),token,self.s); thread=threading.Thread(target=srv.serve_forever,daemon=True); thread.start()
  try:
   body=json.dumps({'packet':PACKET,'issuance':self.issuance,'owner':OWNER}).encode(); req=urllib.request.Request('http://127.0.0.1:%d/action'%srv.server_address[1],data=body,method='POST',headers={'Content-Type':'application/json','X-GPT-Windows-Relay-Token':token})
   with urllib.request.urlopen(req) as r: self.assertEqual(r.status,200)
   self.assertEqual(self.calls,['PCE16.041'])
  finally: srv.shutdown(); srv.server_close()
 def test_owner_bind_requires_separate_operator_secret(self):
  token='t'*40; operator='o'*40; srv=M.Server(('127.0.0.1',0),token,self.s,operator); thread=threading.Thread(target=srv.serve_forever,daemon=True); thread.start()
  try:
   body=json.dumps({'operator_authorized':True,'owner':OWNER}).encode(); url='http://127.0.0.1:%d/owner-bind'%srv.server_address[1]
   ordinary=urllib.request.Request(url,data=body,method='POST',headers={'Content-Type':'application/json','X-GPT-Windows-Relay-Token':token})
   with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(ordinary)
   approved=urllib.request.Request(url,data=body,method='POST',headers={'Content-Type':'application/json','X-GPT-Windows-Relay-Token':token,'X-GPT-Windows-Relay-Operator-Token':operator})
   with urllib.request.urlopen(approved) as r: self.assertEqual(r.status,200)
   self.assertEqual(self.s.data['conversation_owner']['conversation_key'],OWNER['conversation_key'])
  finally: srv.shutdown(); srv.server_close()
 def test_owner_bind_rolls_back_on_persistence_failure(self):
  old=dict(self.s.data); original=self.s.save; self.s.save=lambda: (_ for _ in ()).throw(OSError('disk'))
  with self.assertRaises(OSError): self.s.bind_conversation_owner({'conversation_key':'https://chatgpt.com/c/new','session':'pce16.041','tab_id':8})
  self.assertEqual(self.s.data,old); self.s.save=original
if __name__=='__main__': unittest.main()
