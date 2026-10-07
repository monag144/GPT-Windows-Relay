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


chrome.runtime.onConnect.addListener(port=>{
  if(port?.name!=='gpt-windows-relay-content')return;
  browserEvent('content_port_connected').catch(()=>{});
  port.onMessage.addListener(m=>{
    if(m?.type==='relay_event' && typeof m.event==='string'){
      browserEvent(m.event,m.detail??null).catch(()=>{});
      return;
    }
    if(m?.type==='relay_attachment_cleanup'){cleanupManagedAttachments(Array.isArray(m.names)?m.names:[]).catch(()=>{});return;}
    if(m?.type!=='relay_action' || typeof m.request_id!=='string')return;
    browserEvent('action_received',{request_id:m.request_id}).catch(()=>{});
    (async()=>{
      let reply;
      try{
        const d=await callAction(m.packet);
        if(/\"status\"\s*:\s*\"DUPLICATE_IGNORED\"/.test(String(d.result||''))){
          reply={ok:false,error:'duplicate_suppressed'};
        }else{
          const attachments=await hydratedAttachments(d.result);
          reply={ok:true,result:d.result,attachments};
        }
      }catch(e){
        reply={ok:false,error:e.code||e.message||String(e)};
      }
      browserEvent('action_result',{request_id:m.request_id,ok:!!reply?.ok}).catch(()=>{});
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
