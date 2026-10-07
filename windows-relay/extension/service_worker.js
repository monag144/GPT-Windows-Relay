import { RELAY_PORT, RELAY_TOKEN, RELAY_BROWSER_ID } from './config.js';
const BASE=`http://127.0.0.1:${RELAY_PORT}`;
const HEAD={"Content-Type":"application/json","X-GPT-Windows-Relay-Token":RELAY_TOKEN};
async function call(path,init={},timeoutMs=15000){const r=await fetch(BASE+path,{...init,signal:AbortSignal.timeout(timeoutMs),headers:{...HEAD,...(init.headers||{})}});let d={};try{d=await r.json()}catch{};if(!r.ok||!d.ok){const e=new Error(d.detail||d.error||`HTTP ${r.status}`);e.code=d.error||`http_${r.status}`;throw e;}return d;}
const ACTION_RETRY_WINDOW_MS=45000;
const ACTION_RETRY_DELAY_MS=1000;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const consumerMissionPorts=new Map();
const relayContentPorts=new Set();
let operatorStopAckGeneration=0;
let operatorStopAckExpected=new Set();
let operatorStopAckReceived=new Set();
let operatorStopAckEmittedGeneration=0;
let preferredConsumerMissionTabId=null;
let lastBrowserHeartbeatAt=0;

const CHAT_ROTATION_KEY='gptRelayChatRotationV1';
const CHAT_ROTATION_EVERY=100;
const ENGINEERING_ROTATION_KEY='gptEngineeringRotationV1';
const ENGINEERING_ROTATION_FORCE_FROM_PCE8_OP=92;
/* GPT_ENGINEERING_ROTATION_TRIGGER_V1 */
function engineeringGeneration(id){const m=String(id||'').match(/PCE(\d+)/i);return m?Number(m[1]):null;}
function engineeringOperation(id){const m=String(id||'').match(/PCE\d+BOOT-OP(\d+)/i);return m?Number(m[1]):null;}
function pce9Target(){return {title:'💻PC Engineering 9🔧',session:'pce9.1'};}
function pce9Handoff(id){return `[GPT_ENGINEERING_ROTATION_HANDOFF_V1]\nTarget title: 💻PC Engineering 9🔧\nTarget relay session: pce9.1\nSource packet: ${id}\nRead docs/HANDOFF_2026-10-07_PCE8_TO_PCE9.md, roadmap, established facts, recent incidents, and engineering log. Continue autonomously; do not restart the audit. First relay operation: PCE9BOOT-OP001 with owner_claim true.\n[/GPT_ENGINEERING_ROTATION_HANDOFF_V1]`;}

function extensionStorageGet(key){
  return new Promise(resolve=>{
    try{chrome.storage.local.get(key,v=>resolve(v||{}));}
    catch{resolve({});}
  });
}

function extensionStorageSet(value){
  return new Promise(resolve=>{
    try{chrome.storage.local.set(value,()=>resolve());}
    catch{resolve();}
  });
}

function operationOrdinal(id){
  const matches=[...String(id||'').matchAll(/(?:^|[-.])(\d{2,})(?=[-.]|$)/g)];
  if(!matches.length)return null;
  const n=Number(matches[matches.length-1][1]);
  return Number.isSafeInteger(n) && n>0?n:null;
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

async function noteDeliveredOperation(port,id){
  const raw=await extensionStorageGet(CHAT_ROTATION_KEY);
  const saved=raw?.[CHAT_ROTATION_KEY];
  const state=saved && typeof saved==='object'?saved:{};
  const counted=Array.isArray(state.counted_ids)?state.counted_ids.filter(x=>typeof x==='string'):[];
  if(counted.includes(id))return;
  counted.push(id);
  while(counted.length>512)counted.shift();

  const ordinal=operationOrdinal(id);
  const count=Math.max(0,Number(state.delivered_count)||0)+1;
  let fallbackSinceRotation=Math.max(0,Number(state.fallback_since_rotation)||0)+1;
  let lastRotationOrdinal=Number(state.last_rotation_ordinal)||0;
  const eg=engineeringGeneration(id),eop=engineeringOperation(id);
  const engineeringDue=eg===8 && Number.isFinite(eop) && eop>=ENGINEERING_ROTATION_FORCE_FROM_PCE8_OP;
  let rotationDue=engineeringDue;
  if(ordinal && !rotationDue){
    rotationDue=ordinal%CHAT_ROTATION_EVERY===0 && ordinal!==lastRotationOrdinal;
    if(rotationDue)lastRotationOrdinal=ordinal;
  }else if(!ordinal && !rotationDue && fallbackSinceRotation>=CHAT_ROTATION_EVERY){
    rotationDue=true;
    fallbackSinceRotation=0;
  }

  await extensionStorageSet({[CHAT_ROTATION_KEY]:{
    delivered_count:count,
    fallback_since_rotation:fallbackSinceRotation,
    last_rotation_ordinal:lastRotationOrdinal,
    counted_ids:counted,
    updated_at:new Date().toISOString()
  }});

  browserEvent('relay_operation_counted',{packet_id:id,ordinal,delivered_count:count,rotation_due:rotationDue,engineering_due:engineeringDue}).catch(()=>{});
  const tabId=port?.sender?.tab?.id;
  if(!rotationDue || RELAY_BROWSER_ID!=='firefox' || !Number.isInteger(tabId))return;
  const target=pce9Target();
  const rotation={source_packet_id:id,target_title:target.title,target_session:target.session,handoff:pce9Handoff(id),phase:'requested',requested_at:new Date().toISOString()};
  await extensionStorageSet({[ENGINEERING_ROTATION_KEY]:rotation});
  browserEvent('chat_rotation_due',{packet_id:id,ordinal,tab_id:tabId,target}).catch(()=>{});
  try{port.postMessage({type:'relay_chat_rotation_start',...rotation});}catch{}
}

function rememberConsumerPort(port){
  const tabId=port?.sender?.tab?.id;
  if(!Number.isInteger(tabId))return null;
  consumerMissionPorts.set(tabId,port);
  if(port?.sender?.tab?.active)preferredConsumerMissionTabId=tabId;
  return tabId;
}

async function currentConsumerMissionTarget(){
  if(!consumerMissionPorts.size)return null;
  try{
    const tabs=await chrome.tabs.query({active:true,lastFocusedWindow:true});
    const active=tabs.find(tab=>Number.isInteger(tab?.id) && consumerMissionPorts.has(tab.id));
    if(active){
      preferredConsumerMissionTabId=active.id;
      return active.id;
    }
  }catch{}
  if(
    Number.isInteger(preferredConsumerMissionTabId) &&
    consumerMissionPorts.has(preferredConsumerMissionTabId)
  ) return preferredConsumerMissionTabId;
  if(consumerMissionPorts.size===1)return consumerMissionPorts.keys().next().value;
  return null;
}

async function portOwnsConsumerMission(port){
  const tabId=port?.sender?.tab?.id;
  if(!Number.isInteger(tabId))return false;
  return (await currentConsumerMissionTarget())===tabId;
}
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
    const enriched=(detail && typeof detail==='object' && !Array.isArray(detail))
      ? {...detail,browser_id:RELAY_BROWSER_ID}
      : {browser_id:RELAY_BROWSER_ID,value:detail};
    await call('/browser-event',{method:'POST',body:JSON.stringify({event,detail:enriched})},5000);
  }catch{}
}


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

function browserHeartbeat(force=false){
  const now=Date.now();
  if(!force && now-lastBrowserHeartbeatAt<5000)return;
  lastBrowserHeartbeatAt=now;
  const integrationConnected=consumerMissionPorts.size>0;
  call('/browser-heartbeat?browser_id='+encodeURIComponent(RELAY_BROWSER_ID)+
    '&integration_connected='+(integrationConnected?'1':'0'),{},3000).catch(()=>{});
}

const GPT_BROWSER_HEARTBEAT_ALARM_V1='gpt-oneclick-browser-heartbeat';
let browserHeartbeatAlarmBound=false;
function installBrowserHeartbeatLifecycle(){
  browserHeartbeat();
  try{
    const alarms=chrome?.alarms;
    if(!alarms)return;
    if(typeof alarms.create==='function'){
      const created=alarms.create(GPT_BROWSER_HEARTBEAT_ALARM_V1,{periodInMinutes:0.5});
      created?.catch?.(()=>{});
    }
    if(!browserHeartbeatAlarmBound && alarms.onAlarm && typeof alarms.onAlarm.addListener==='function'){
      alarms.onAlarm.addListener(alarm=>{
        if(alarm?.name===GPT_BROWSER_HEARTBEAT_ALARM_V1)browserHeartbeat();
      });
      browserHeartbeatAlarmBound=true;
    }
  }catch{}
}

async function badge(){try{const s=await call('/status');await chrome.action.setBadgeText({text:s.armed?'ON':'OFF'});await chrome.action.setBadgeBackgroundColor({color:s.armed?'#16803a':'#666'});}catch{await chrome.action.setBadgeText({text:'ERR'});await chrome.action.setBadgeBackgroundColor({color:'#b42318'});}}
chrome.runtime.onInstalled.addListener(()=>{badge();installBrowserHeartbeatLifecycle();}); chrome.runtime.onStartup.addListener(()=>{badge();installBrowserHeartbeatLifecycle();});

// GPT_WINDOWS_CORE_PORT_BEFORE_OPTIONAL_HEARTBEAT_V1
chrome.runtime.onConnect.addListener(port=>{
  if(port?.name!=='gpt-windows-relay-content')return;
  relayContentPorts.add(port);
  const firstConsumerPort=consumerMissionPorts.size===0;
  const consumerTabId=rememberConsumerPort(port);
  browserHeartbeat(true);
  browserEvent('content_port_connected',{tab_id:consumerTabId}).catch(()=>{});
  if(firstConsumerPort && Number.isInteger(consumerTabId)){
    browserEvent('browser_integration_connected',{tab_id:consumerTabId}).catch(()=>{});
  }
  port.onDisconnect.addListener(()=>{
    relayContentPorts.delete(port);
    if(Number.isInteger(consumerTabId) && consumerMissionPorts.get(consumerTabId)===port){
      consumerMissionPorts.delete(consumerTabId);
      browserHeartbeat(true);
      if(preferredConsumerMissionTabId===consumerTabId)preferredConsumerMissionTabId=null;
      browserEvent('consumer_mission_owner_disconnected',{tab_id:consumerTabId}).catch(()=>{});
      if(consumerMissionPorts.size===0){
        browserEvent('browser_integration_disconnected',{tab_id:consumerTabId}).catch(()=>{});
      }
    }
  });
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
    if(m?.type==='consumer_mission_poll'){
      browserHeartbeat();
      (async()=>{
        try{
          if(!await portOwnsConsumerMission(port))return;
          const d=await call('/mission-next?browser_id='+encodeURIComponent(RELAY_BROWSER_ID),{},5000);
          if(d?.mission?.id && typeof d.mission.text==='string'){
            const tabId=port?.sender?.tab?.id;
            browserEvent('consumer_mission_target_selected',{tab_id:tabId,mission_id:d.mission.id,browser_id:RELAY_BROWSER_ID}).catch(()=>{});
            port.postMessage({type:'consumer_mission',mission:d.mission});
          }
        }catch{}
      })();
      return;
    }
    if(m?.type==='consumer_mission_ack' && typeof m.id==='string'){
      call('/mission-ack',{method:'POST',body:JSON.stringify({id:m.id})},5000).catch(()=>{});
      return;
    }
    if(m?.type==='relay_operation_delivered' && typeof m.id==='string'){
      noteDeliveredOperation(port,m.id).catch(()=>{});
      return;
    }
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
          if(ownerDecision.claimed||ownerDecision.transferred||ownerDecision.upgraded){
            browserEvent(ownerDecision.transferred?'relay_conversation_owner_transferred':'relay_conversation_owner_claimed',{packet_id:packetId,session:meta.session,owner:ownerDecision.owner,previous:ownerDecision.previous||null}).catch(()=>{});
          }
          const cursorDecision=await checkAndAdvanceOperationCursor(packetId,ownerDecision.owner);
        if(cursorDecision.late){
          browserEvent('relay_late_packet_suppressed',{
            packet_id:packetId,
            position:cursorDecision.position,
            cursor:cursorDecision.cursor
          }).catch(()=>{});
          reply={ok:false,error:'late_packet_suppressed'};
        }else{
          browserEvent('action_received',{request_id:m.request_id,packet_id:packetId}).catch(()=>{});
          const d=await callAction(m.packet);
          if(/\"status\"\s*:\s*\"DUPLICATE_IGNORED\"/.test(String(d.result||''))){
            reply={ok:false,error:'duplicate_suppressed'};
            }else{
              const attachments=await hydratedAttachments(d.result);
              reply={ok:true,result:d.result,attachments};
            }
          }
        }
      }catch(e){
        reply={ok:false,error:e.code||e.message||String(e)};
      }
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

// Optional heartbeat setup is deliberately after the core onConnect registration.
// A missing or incompatible alarms API must never prevent relay-port startup.
installBrowserHeartbeatLifecycle();

chrome.runtime.onMessage.addListener((m,_s,reply)=>{(async()=>{try{
 if(m.type==='status') return reply({ok:true,data:await call('/status')});
 if(m.type==='arm'){const d=await call('/arm',{method:'POST',body:JSON.stringify({armed:!!m.armed})});await badge();return reply({ok:true,data:d});}
 if(m.type==='action'){const d=await callAction(m.packet);if(/\"status\"\s*:\s*\"DUPLICATE_IGNORED\"/.test(String(d.result||'')))return reply({ok:false,error:'duplicate_suppressed'});return reply({ok:true,result:d.result});}
 reply({ok:false,error:'unsupported_message'});
}catch(e){reply({ok:false,error:e.code||e.message||String(e)});}})();return true;});

/* GPT_ONE_CLICK_ACTIVE_TAB_TARGET_V1 */

/* GPT_ONE_CLICK_BROWSER_QUEUE_TARGET_V1 */

/* GPT_ONE_CLICK_BROWSER_HEARTBEAT_V1 */
/* GPT_RELAY_CHAT_ROTATION_100_V1 */
/* GPT_RELAY_DELIVERED_OPERATION_DEDUPE_V1 */
