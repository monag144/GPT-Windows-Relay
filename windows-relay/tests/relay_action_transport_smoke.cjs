/* Offline behavioral test of the *published* persistent worker. No real browser/HTTP. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const {TextEncoder}=require('node:util');

const workerSource=fs.readFileSync(path.join(__dirname,'..','extension-persistent','service_worker.js'),'utf8');
const packet='[GPT_WINDOWS_ACTION]\n'+JSON.stringify({
  version:1,platform:'windows',action:'EXEC',id:'TRANSPORT-MOCK-001',
  session:'default',shell:'powershell',command:'Write-Output MOCK'
})+'\n[/GPT_WINDOWS_ACTION]';
const owner={conversation_key:'https://chatgpt.com/c/transport-mock',session:'default',tab_id:37};
let requests=[],ownerAnswer='approve',storeFails=false;
let directMessageListener=null;
const storage={
  relayToken:'ISOLATED_TEST_TOKEN'
};
const chrome={
  runtime:{
    lastError:null,
    onInstalled:{addListener(){}},onStartup:{addListener(){}},
    onConnect:{addListener(){}},
    onMessage:{addListener(fn){directMessageListener=fn;}}
  },
  tabs:{query:async()=>[{id:37}]},
  action:{setBadgeText:async()=>{},setBadgeBackgroundColor:async()=>{}},
  storage:{local:{
    get(key,done){
      const response=Array.isArray(key)?{relayToken:storage.relayToken}:{};
      if(done){chrome.runtime.lastError=storeFails?{message:'simulated failure'}:null;done(response);return;}
      return Promise.resolve(response);
    },
    set(value,done){
      if(done){chrome.runtime.lastError=storeFails?{message:'simulated failure'}:null;done();return;}
      Object.assign(storage,value);return Promise.resolve();
    },
  }},
};
async function fakeFetch(url,opts){
  const endpoint=url.split(':8766')[1]||'';
  const body=JSON.parse(opts.body);
  requests.push({endpoint,body});
  let payload;
  if(endpoint==='/action'&&requests.filter(x=>x.endpoint==='/action').length===1)
    payload={ok:false,error:'RelayError',detail:'conversation_owner_mismatch'};
  else if(endpoint==='/owner-bind-request'&&ownerAnswer==='decline')
    payload={ok:false,error:'RelayError',detail:'operator_confirmation_declined'};
  else if(endpoint==='/owner-bind-request')
    payload={ok:true,owner_bound:true};
  else payload={ok:true,result:'MOCK_ACTION_RESULT'};
  return {ok:payload.ok,status:payload.ok?200:400,json:async()=>payload};
}
const sandbox={chrome,crypto:webcrypto,TextEncoder,URL,AbortSignal,fetch:fakeFetch,
               setTimeout,clearTimeout,btoa:global.btoa};
vm.createContext(sandbox);
vm.runInContext(workerSource+'\n;globalThis.__test__={actionTransport,callAction,extensionStorageGet,extensionStorageSet,unlockedFocusedConversation};',sandbox);
const actor=sandbox.__test__;
(async()=>{
  const meta=await actor.actionTransport(packet,owner);
  const digest=await webcrypto.subtle.digest('SHA-256',new TextEncoder().encode(packet));
  const expected=Buffer.from(digest).toString('hex');
  assert.equal(meta.issuance.packet_hash,expected,'exact packet hash');
  assert.equal(meta.issuance.id,'TRANSPORT-MOCK-001');
  assert.equal(meta.owner.tab_id,37);
  const success=await actor.callAction(packet,owner);
  assert.equal(success.result,'MOCK_ACTION_RESULT');
  assert.deepEqual(requests.map(x=>x.endpoint),
                   ['/action','/owner-bind-request','/action']);
  assert.equal(JSON.stringify(requests[0].body.issuance),JSON.stringify(meta.issuance));
  assert.equal(JSON.stringify(requests[0].body.owner),JSON.stringify(meta.owner));

  requests=[];ownerAnswer='decline';
  await assert.rejects(actor.callAction(packet,owner),
    e=>e.code==='operator_confirmation_declined');
  assert.deepEqual(requests.map(x=>x.endpoint),
                   ['/action','/owner-bind-request'],
                   'decline must not submit executable action again');

  requests=[];ownerAnswer='approve';
  await assert.rejects(actor.callAction(packet,{...owner,tab_id:0}),
    /transport_owner_unavailable/);
  assert.equal(requests.length,0,'invalid owner must never reach backend');

  storeFails=true;
  await assert.rejects(actor.extensionStorageGet('owner'),/relay_storage_read_failed/);
  await assert.rejects(actor.extensionStorageSet({x:1}),/relay_storage_write_failed/);

  // Lock OFF does not rely on stale storage; only the focused sender tab can act.
  const focused={sender:{tab:{id:37,url:owner.conversation_key}}};
  const accepted=await actor.unlockedFocusedConversation(focused,{conversation_key:owner.conversation_key},{session:'pce18.1'});
  assert.equal(accepted.ok,true);
  assert.equal(accepted.owner.session,'pce18.1');
  const backgroundTab=await actor.unlockedFocusedConversation(
    {sender:{tab:{id:38,url:owner.conversation_key}}},
    {conversation_key:owner.conversation_key},{session:'pce18.1'});
  assert.equal(backgroundTab.ok,false);
  assert.equal(backgroundTab.error,'relay_active_tab_required');
  const forged=await actor.unlockedFocusedConversation(
    focused,{conversation_key:'https://chatgpt.com/c/other'},{session:'pce18.1'});
  assert.equal(forged.ok,false);
  assert.ok(directMessageListener);
  console.log('BROWSER_TRANSPORT_MOCK_OK');
})().catch(e=>{console.error(e);process.exitCode=1;});
