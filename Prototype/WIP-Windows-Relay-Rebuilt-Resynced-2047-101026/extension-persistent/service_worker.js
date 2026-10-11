const RELAY_PORT=8766;
const BASE=`http://127.0.0.1:${RELAY_PORT}`;

async function getToken(){
  const d=await chrome.storage.local.get(['relayToken']);
  const token=String(d.relayToken||'').trim();
  if(!token){const e=new Error('Relay is not paired');e.code='relay_unpaired';throw e;}
  return token;
}

async function call(path,init={},timeoutMs=15000){
  const token=await getToken();
  const headers={"Content-Type":"application/json","X-GPT-Windows-Relay-Token":token,...(init.headers||{})};
  const r=await fetch(BASE+path,{...init,headers,signal:AbortSignal.timeout(timeoutMs)});
  let d={};
  try{d=await r.json()}catch{}
  if(!r.ok||!d.ok){const e=new Error(d.detail||d.error||`HTTP ${r.status}`);e.code=d.error||`http_${r.status}`;throw e;}
  return d;
}

const ACTION_RETRY_WINDOW_MS=45000;
const ACTION_RETRY_DELAY_MS=1000;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function transientActionError(e){
  const code=String(e?.code||e?.name||'');
  const msg=String(e?.message||e||'');
  return code==='TypeError' || code==='AbortError' || code==='NetworkError' ||
    /^http_5\d\d$/.test(code) || /fetch|network|connection|aborted|reset|refused/i.test(msg);
}
async function callAction(packet){
  const deadline=Date.now()+ACTION_RETRY_WINDOW_MS;
  while(true){
    try{
      const d=await call('/action',{method:'POST',body:JSON.stringify({packet})},315000);
      const body=String(d.result||'');
      if(/\"status\"\s*:\s*\"DUPLICATE_INFLIGHT\"/.test(body) && Date.now()<deadline){
        await sleep(ACTION_RETRY_DELAY_MS);
        continue;
      }
      return d;
    }catch(e){
      if(!transientActionError(e) || Date.now()>=deadline)throw e;
      await sleep(ACTION_RETRY_DELAY_MS);
    }
  }
}

// GPT_WINDOWS_SCREENSHOT_ATTACHMENT_TRANSPORT_V1
function resultAttachments(text){
  try{const a=text.indexOf('\n'),b=text.lastIndexOf('\n[/GPT_WINDOWS_RESULT]');if(a<0||b<=a)return[];const p=JSON.parse(text.slice(a+1,b));return Array.isArray(p.attachments)?p.attachments:[];}catch{return[];}
}
function bytesToBase64(bytes){let out='';const step=0x8000;for(let i=0;i<bytes.length;i+=step)out+=String.fromCharCode(...bytes.subarray(i,i+step));return btoa(out);}
async function fetchManagedAttachment(a){
  if(a?.kind!=='image'||a?.mime!=='image/png'||!/^[A-Za-z0-9._-]+\.png$/.test(String(a.name||'')))throw new Error('invalid_attachment_descriptor');
  const r=await fetch(BASE+'/managed-screenshot/'+encodeURIComponent(a.name),{signal:AbortSignal.timeout(15000),headers:{'X-GPT-Windows-Relay-Token':RELAY_TOKEN}});
  if(!r.ok)throw new Error('attachment_fetch_http_'+r.status);const ab=await r.arrayBuffer();if(!ab.byteLength||ab.byteLength>12*1024*1024)throw new Error('attachment_size_invalid');
  return {kind:'image',name:a.name,mime:'image/png',base64:bytesToBase64(new Uint8Array(ab)),bytes:ab.byteLength};
}
async function hydratedAttachments(result){const out=[];for(const a of resultAttachments(String(result||'')))out.push(await fetchManagedAttachment(a));return out;}
async function cleanupManagedAttachments(names){for(const name of names||[]){try{await call('/managed-screenshot-delete',{method:'POST',body:JSON.stringify({name})},5000);}catch{}}}

async function browserEvent(event,detail=null){
  try{
    await call('/browser-event',{method:'POST',body:JSON.stringify({event,detail})},5000);
  }catch{}
}

const relayContentPorts=new Set();
let operatorStopAckGeneration=0;
let operatorStopAckExpected=new Set();
let operatorStopAckReceived=new Set();
let operatorStopAckEmittedGeneration=0;

function clearOperatorStopGeneration(){
  operatorStopAckGeneration=0;
  operatorStopAckExpected=new Set();
  operatorStopAckReceived=new Set();
  operatorStopAckEmittedGeneration=0;
}

function beginOperatorStopGeneration(generation){
  const g=Number(generation)||0;
  if(g<=0 || g===operatorStopAckGeneration)return;
  operatorStopAckGeneration=g;
  operatorStopAckExpected=new Set(relayContentPorts);
  operatorStopAckReceived=new Set();
  operatorStopAckEmittedGeneration=0;
}

function maybeEmitOperatorStopQuiesced(generation){
  const g=Number(generation)||0;
  if(g<=0 || g!==operatorStopAckGeneration || operatorStopAckEmittedGeneration===g)return;
  for(const p of operatorStopAckExpected){if(!operatorStopAckReceived.has(p))return;}
  operatorStopAckEmittedGeneration=g;
  browserEvent('browser_operator_quiesced_all',{
    stop_generation:g,
    expected_ports:operatorStopAckExpected.size,
    acked_ports:operatorStopAckReceived.size
  }).catch(()=>{});
}

async function badge(){
  try{
    const s=await call('/status');
    await chrome.action.setBadgeText({text:s.armed?'ON':'OFF'});
    await chrome.action.setBadgeBackgroundColor({color:s.armed?'#16803a':'#666'});
  }catch(e){
    await chrome.action.setBadgeText({text:e.code==='relay_unpaired'?'PAIR':'ERR'});
    await chrome.action.setBadgeBackgroundColor({color:e.code==='relay_unpaired'?'#8a5a00':'#b42318'});
  }
}

chrome.runtime.onInstalled.addListener(badge);
chrome.runtime.onStartup.addListener(badge);


function extensionStorageGet(key){
  return new Promise(resolve=>{try{chrome.storage.local.get(key,v=>resolve(v||{}));}catch{resolve({});}});
}
function extensionStorageSet(value){
  return new Promise(resolve=>{try{chrome.storage.local.set(value,()=>resolve());}catch{resolve();}});
}

/* GPT_RELAY_LATE_PACKET_CURSOR_V2 */
const OPERATION_CURSOR_KEY='gptRelayOperationCursorV2';
const RELAY_OWNER_KEY='gptRelayConversationOwnerV1';
let operationCursorChain=Promise.resolve();
let relayOwnerChain=Promise.resolve();

function operationSeriesPosition(id){
  const m=String(id||'').match(/(?:^|[-.])OP(\d+)([a-z]*)(?=[-.]|$)/i);
  if(!m)return null;
  const ordinal=Number(m[1]);
  if(!Number.isSafeInteger(ordinal)||ordinal<0)return null;
  let suffix_rank=0;
  for(const ch of String(m[2]||'').toLowerCase()){
    suffix_rank=suffix_rank*26+(ch.charCodeAt(0)-96);
    if(!Number.isSafeInteger(suffix_rank))return null;
  }
  return {ordinal,suffix_rank,id:String(id)};
}
function compareOperationPosition(a,b){
  for(const key of ['ordinal','suffix_rank']){
    const d=Number(a?.[key]||0)-Number(b?.[key]||0);
    if(d)return d<0?-1:1;
  }
  return 0;
}
function relayPacketMeta(packet){
  const text=String(packet||'');
  const a=text.indexOf('[GPT_WINDOWS_ACTION]');
  const b=text.lastIndexOf('[/GPT_WINDOWS_ACTION]');
  if(a<0||b<=a)return {id:null,session:'default',owner_claim:false};
  try{
    const body=text.slice(a+'[GPT_WINDOWS_ACTION]'.length,b).trim();
    const parsed=JSON.parse(body);
    return {
      id:typeof parsed?.id==='string'?parsed.id:null,
      session:typeof parsed?.session==='string'&&parsed.session.trim()?parsed.session.trim():'default',
      owner_claim:parsed?.owner_claim===true
    };
  }catch{return {id:null,session:'default',owner_claim:false};}
}
function relayPacketId(packet){return relayPacketMeta(packet).id;}
function normalizeConversationKey(value){
  try{
    const u=new URL(String(value||''));
    if(u.origin!=='https://chatgpt.com')return null;
    return u.origin+u.pathname.replace(/\/+$/,'');
  }catch{return null;}
}
function relaySessionVersion(session){
  const m=String(session||'').trim().match(/^(?:pce|pceng)(\d+)(?:\.(\d+))?$/i);
  if(!m)return null;
  return {major:Number(m[1]),minor:Number(m[2]||0)};
}
function compareSessionVersion(a,b){
  if(!a||!b)return 0;
  if(a.major!==b.major)return a.major<b.major?-1:1;
  if(a.minor!==b.minor)return a.minor<b.minor?-1:1;
  return 0;
}
async function activeFocusedTabId(){
  try{
    const tabs=await chrome.tabs.query({active:true,lastFocusedWindow:true});
    const tab=tabs.find(x=>Number.isInteger(x?.id));
    return tab?.id??null;
  }catch{return null;}
}
function checkAndClaimRelayOwner(port,message,meta){
  const task=relayOwnerChain.then(async()=>{
    const tabId=port?.sender?.tab?.id;
    const conversationKey=normalizeConversationKey(message?.conversation_key||message?.conversation_href||port?.sender?.tab?.url);
    if(!Number.isInteger(tabId)||!conversationKey)return {ok:false,error:'conversation_identity_missing',owner:null};
    const activeTabId=await activeFocusedTabId();
    const isActive=activeTabId===tabId;
    const raw=await extensionStorageGet(RELAY_OWNER_KEY);
    const saved=raw?.[RELAY_OWNER_KEY];
    const owner=saved&&typeof saved==='object'?saved:null;
    const session=String(meta?.session||'default');
    if(!owner){
      if(!isActive)return {ok:false,error:'relay_owner_unclaimed_inactive_tab',owner:null};
      const next={conversation_key:conversationKey,session,tab_id:tabId,updated_at:new Date().toISOString()};
      await extensionStorageSet({[RELAY_OWNER_KEY]:next});
      return {ok:true,claimed:true,transferred:false,owner:next};
    }
    if(owner.conversation_key===conversationKey){
      if(owner.session==='default'&&session!=='default'){
        const next={...owner,session,tab_id:tabId,updated_at:new Date().toISOString()};
        await extensionStorageSet({[RELAY_OWNER_KEY]:next});
        return {ok:true,claimed:false,transferred:false,upgraded:true,owner:next};
      }
      return {ok:true,claimed:false,transferred:false,owner};
    }
    if(!isActive)return {ok:false,error:'relay_owner_mismatch_inactive_tab',owner};
    if(session==='default')return {ok:false,error:'legacy_default_session_blocked',owner};
    const incomingVersion=relaySessionVersion(session);
    const ownerVersion=relaySessionVersion(owner.session);
    const newer=!!incomingVersion&&!!ownerVersion&&compareSessionVersion(incomingVersion,ownerVersion)>0;
    if(session===owner.session&&!meta?.owner_claim)return {ok:false,error:'relay_owner_same_session_different_conversation',owner};
    if(!meta?.owner_claim&&!newer&&owner.session!=='default')return {ok:false,error:'relay_owner_transfer_requires_claim',owner};
    const next={conversation_key:conversationKey,session,tab_id:tabId,updated_at:new Date().toISOString(),previous_conversation_key:owner.conversation_key,previous_session:owner.session};
    await extensionStorageSet({[RELAY_OWNER_KEY]:next});
    return {ok:true,claimed:false,transferred:true,owner:next,previous:owner};
  });
  relayOwnerChain=task.catch(()=>{});
  return task;
}
function checkAndAdvanceOperationCursor(id,owner){
  const task=operationCursorChain.then(async()=>{
    const pos=operationSeriesPosition(id);
    if(!pos)return {late:false,position:null,cursor:null};
    const ownerKey=String(owner?.session||'default')+'|'+String(owner?.conversation_key||'');
    const raw=await extensionStorageGet(OPERATION_CURSOR_KEY);
    const cursor=raw?.[OPERATION_CURSOR_KEY];
    if(cursor&&typeof cursor==='object'&&cursor.owner_key===ownerKey&&compareOperationPosition(pos,cursor)<0)return {late:true,position:pos,cursor};
    const next={...pos,owner_key:ownerKey,session:owner?.session||'default',conversation_key:owner?.conversation_key||null,updated_at:new Date().toISOString()};
    await extensionStorageSet({[OPERATION_CURSOR_KEY]:next});
    return {late:false,position:pos,cursor:next};
  });
  operationCursorChain=task.catch(()=>{});
  return task;
}
/* GPT_RELAY_CONVERSATION_OWNER_V1 */
/* GPT_RELAY_OP_TOKEN_CURSOR_V1 */

chrome.runtime.onConnect.addListener(port=>{
  if(port?.name!=='gpt-windows-relay-content')return;
  relayContentPorts.add(port);
  browserEvent('content_port_connected').catch(()=>{});
  port.onDisconnect.addListener(()=>{relayContentPorts.delete(port);});
  port.onMessage.addListener(m=>{
    if(m?.type==='operator_control_poll'){
      (async()=>{
        try{
          const st=await call('/status',{},1000);
          const generation=Number(st?.stop_generation)||0;
          if(st?.armed===false)beginOperatorStopGeneration(generation);
          else if(st?.armed===true && operatorStopAckGeneration)clearOperatorStopGeneration();
          port.postMessage({type:'operator_control_state',online:true,armed:!!st?.armed,stop_generation:generation,outbound_owner:st?.outbound_owner==='windows'?'windows':'browser'});
        }catch{
          try{port.postMessage({type:'operator_control_state',online:false});}catch{}
        }
      })();
      return;
    }
    if(m?.type==='operator_quiesced_ack'){
      const generation=Number(m.stop_generation)||0;
      if(generation===operatorStopAckGeneration && operatorStopAckExpected.has(port)){
        operatorStopAckReceived.add(port);
        maybeEmitOperatorStopQuiesced(generation);
      }
      return;
    }
    if(m?.type==='relay_event' && typeof m.event==='string'){
      browserEvent(m.event,m.detail??null).catch(()=>{});
      return;
    }
    if(m?.type==='relay_attachment_cleanup'){cleanupManagedAttachments(Array.isArray(m.names)?m.names:[]).catch(()=>{});return;}
    if(m?.type!=='relay_action' || typeof m.request_id!=='string')return;
    (async()=>{
      let reply;
      const meta=relayPacketMeta(m.packet);
      const packetId=meta.id;
      try{
        const ownerDecision=await checkAndClaimRelayOwner(port,m,meta);
        if(!ownerDecision.ok){
          browserEvent('relay_cross_conversation_suppressed',{request_id:m.request_id,packet_id:packetId,session:meta.session,conversation_key:normalizeConversationKey(m.conversation_key||m.conversation_href||port?.sender?.tab?.url),error:ownerDecision.error,owner:ownerDecision.owner}).catch(()=>{});
          reply={ok:false,error:ownerDecision.error};
        }else{
          if(ownerDecision.claimed||ownerDecision.transferred||ownerDecision.upgraded){browserEvent(ownerDecision.transferred?'relay_conversation_owner_transferred':'relay_conversation_owner_claimed',{packet_id:packetId,session:meta.session,owner:ownerDecision.owner,previous:ownerDecision.previous||null}).catch(()=>{});}
          const cursorDecision=await checkAndAdvanceOperationCursor(packetId,ownerDecision.owner);
          if(cursorDecision.late){
            browserEvent('relay_late_packet_suppressed',{packet_id:packetId,position:cursorDecision.position,cursor:cursorDecision.cursor}).catch(()=>{});
            reply={ok:false,error:'late_packet_suppressed'};
          }else{
            browserEvent('action_received',{request_id:m.request_id,packet_id:packetId,session:meta.session,conversation_key:ownerDecision.owner?.conversation_key||null}).catch(()=>{});
            const d=await callAction(m.packet);
            if(/\"status\"\s*:\s*\"DUPLICATE_IGNORED\"/.test(String(d.result||''))){reply={ok:false,error:'duplicate_suppressed'};}
            else{const attachments=await hydratedAttachments(d.result);reply={ok:true,result:d.result,attachments};}
          }
        }
      }catch(e){reply={ok:false,error:e.code||e.message||String(e)};}
      browserEvent('action_result',{request_id:m.request_id,packet_id:packetId,ok:!!reply?.ok,error:reply?.error||null}).catch(()=>{});
      try{
        port.postMessage({
          type:'relay_handoff_scroll',
          request_id:m.request_id
        });
        port.postMessage({
          type:'relay_action_result',
          request_id:m.request_id,
          reply
        });
      }catch{}
    })();
  });
});

chrome.runtime.onMessage.addListener((m,_s,reply)=>{
  (async()=>{
    try{
      if(m.type==='pair'){
        const token=String(m.token||'').trim();
        if(!token) return reply({ok:false,error:'empty_token'});
        const old=(await chrome.storage.local.get(['relayToken'])).relayToken;
        await chrome.storage.local.set({relayToken:token});
        try{const d=await call('/status');await badge();return reply({ok:true,data:d});}
        catch(e){
          if(old) await chrome.storage.local.set({relayToken:old}); else await chrome.storage.local.remove('relayToken');
          await badge();
          return reply({ok:false,error:e.code||e.message||String(e)});
        }
      }
      if(m.type==='unpair'){await chrome.storage.local.remove('relayToken');await badge();return reply({ok:true});}
      if(m.type==='status') return reply({ok:true,data:await call('/status')});
      if(m.type==='arm'){const d=await call('/arm',{method:'POST',body:JSON.stringify({armed:!!m.armed})});await badge();return reply({ok:true,data:d});}
      if(m.type==='action'){const d=await callAction(m.packet);if(/\"status\"\s*:\s*\"DUPLICATE_IGNORED\"/.test(String(d.result||'')))return reply({ok:false,error:'duplicate_suppressed'});return reply({ok:true,result:d.result});}
      reply({ok:false,error:'unsupported_message'});
    }catch(e){reply({ok:false,error:e.code||e.message||String(e)});}
  })();
  return true;
});
