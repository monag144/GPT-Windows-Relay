(()=>{
const OPEN='[GPT_WINDOWS_ACTION]';
const CLOSE='[/GPT_WINDOWS_ACTION]';
const RECOVERY_ADVICE_OPEN='[GPT_RELAY_RECOVERY_ADVICE]';
const RECOVERY_ADVICE_CLOSE='[/GPT_RELAY_RECOVERY_ADVICE]';
const RECOVERY_ADVICE_ALLOWED=new Set(['rebuild_browser_integration','audited_update','restart_relay']);
/* GPT_WINDOWS_RECOVERY_ADVICE_SECONDARY_OBSERVER_V1 */
const ASSISTANT_SELECTOR=[
  /* GPT_CHATGPT_DATA_MESSAGE_ROLE_COMPAT_V1 */
  '[data-message-role="assistant"]',
  '[data-message-author-role="assistant"]',
  'article[data-turn="assistant"]',
  '[data-content-search-unit-key$=":assistant"]',
  '[data-chatgpt-search-unit-key$=":assistant"]',
  'article[data-testid^="conversation-turn-"]',
  'section[data-testid^="conversation-turn-"]'
].join(',');
const USER_SELECTOR=[
  '[data-message-role="user"]',
  '[data-message-author-role="user"]',
  '[data-turn="user"]',
  '[data-conversation-role="user"]',
  '[data-markdown-text-style="user-message"]'
].join(',');
const DELIVERY_ATTEMPTS=3;
const DELIVERY_CONFIRM_MS=8000;
const DELIVERY_CLEAR_STABLE_MS=1500;
const SEND_READY_TIMEOUT_MS=90000;
const SEND_READY_POLL_MS=250;
const CHAT_IDLE_TIMEOUT_MS=120000;
const CHAT_IDLE_POLL_MS=250;
const RELAY_RECOVERY_INTERVAL_MS=15000;
const RELAY_STALL_PATIENCE_MS=300000;
const DISCOVERY_SETTLE_MS=500;
const DISCOVERY_SETTLE_LEASE_MS=5000;
const RELAY_REFRESH_GRACE_MS=2500;
const RECOVERY_WATCH_MAX_AGE_MS=RELAY_STALL_PATIENCE_MS*3;
const RECOVERY_WATCH_SESSION_KEY='gptWindowsRelayRecoveryWatchV1';
/* GPT_WINDOWS_DURABLE_RECOVERY_OBLIGATION_V1 */
/* GPT_WINDOWS_STALE_OWNER_LEASE_V1 */
/* GPT_WINDOWS_SEND_READINESS_GATE_V1 */
/* GPT_WINDOWS_PREINJECTION_IDLE_GATE_V1 */
/* GPT_WINDOWS_RELAY_DRAFT_RECOVERY_V1 */
const ATTEMPTED_SESSION_KEY='gptWindowsRelayAttemptedIdsV2';
const RESULT_SUBMITTED_SESSION_KEY='gptWindowsRelaySubmittedIdsV1';
const RESULT_SUBMIT_WATCH_MS=120000;
const RESULT_SCAN_LIMIT=128;
/* GPT_WINDOWS_RESULT_DELIVERY_RECOVERY_V1 */
/* GPT_WINDOWS_RESULT_SUBMIT_ONCE_V1 */
/* GPT_WINDOWS_RESULT_ANTISPAM_V2 */
const MAX_ATTEMPTED=256;
const MAX_DEFERRED_ACTIONS=16;
/* GPT_WINDOWS_GENERATION_START_ACK_V1 */
/* GPT_WINDOWS_DEFERRED_ACTION_QUEUE_V1 */
const attempted=new Set(), attemptedOrder=[], inflight=new Set(), pending=new Map();
const submittedResults=new Map(), submittedWatchTimers=new Map();
const resultMatcherDiagnosticsReported=new Set();
const deferredActions=new Map();
let deferredDrainTimer=null;
let relayDisarmedUntil=0;
let watchedUnit=null;
let watchedObserver=null;
let watchedInspectTimer=null;
let scrollRoot=null;
let scrollTimer=null;
let relayHandoffScrollUntil=0;
const HANDOFF_SESSION_KEY='gptWindowsRelayHandoffUntil';
const ENGINEERING_ROTATION_SESSION_KEY='gptEngineeringRotationV1';
let followBottom=true;
let conversationRoot=null;
let conversationObserver=null;
let recoveryTimer=null;
let approvalPromptObserver=null;
let approvalInspectTimer=null;
let lastApprovalSignature='';
let lastApprovalAt=0;
let lastAutoApprovalSignature='';
let lastAutoApprovalAt=0;
let uiErrorObserver=null;
let uiErrorInspectTimer=null;
let activeUiErrorSignature='';
let lastUiErrorAt=0;
let lastRecoveryAdviceSignature='';
let recoveryScrollDone=false;
let backgroundPort=null;
let backgroundPortReconnectTimer=null;
let backgroundRequestSeq=0;
let backgroundPortUnavailableSince=0;
let backgroundRuntimeReloadRequested=false;
let recoveryPacketId=null;
let recoveryPacketFirstSeenAt=0;
let recoveryPacketLastRefreshAt=0;
let recoveryRefreshScheduled=false;
let scannerSnapshotSent=false;
let attemptedConversationHydrated=false;
let activeRelayOperationId=null;
let activeRelayOperationClaimedAt=0;
let draftRecoveryInFlight=false;
let draftRecoveryTimer=null;
let consumerMissionInFlight=null;
let consumerMissionPollTimer=null;
const CONSUMER_MISSION_ACK_KEY='gptOneClickMissionAwaitingAckV1';
const CONSUMER_RECOVERY_KEY='gptOneClickMissionRecoveryV1';
const CONSUMER_RECOVERY_MAX=2;
const CONSUMER_CLASSIFY_DELAY_MS=1800;
let consumerClassificationTimer=null;
let consumerRecoveryInFlight=false;
/* GPT_WINDOWS_WHOLE_PRODUCT_STOP_V1 */
let outboundOwner='browser';
let operatorPaused=true;
let operatorControlPollTimer=null;
let uiErrorInspectInterval=null;
let approvalInspectInterval=null;
let recoveryRefreshTimer=null;
let lastOperatorQuiescedGeneration=0;
/* GPT_ONE_CLICK_RELAY_OUTPUT_CLASSIFIER_V1 */
/* GPT_ONE_CLICK_COLLAPSE_AUTO_RECOVERY_V1 */
/* GPT_ONE_CLICK_MISSION_VISIBLE_ACK_V1 */
/* GPT_ONE_CLICK_CLIENT_SYNC_DIVERGENCE_V1 */
const backgroundPending=new Map();

function claimActiveRelayOperation(id){
  if(activeRelayOperationId!==id || !activeRelayOperationClaimedAt){
    activeRelayOperationClaimedAt=Date.now();
  }
  activeRelayOperationId=id;
}

function persistAttemptedHistory(){
  try{
    sessionStorage.setItem(
      ATTEMPTED_SESSION_KEY,
      JSON.stringify(attemptedOrder.slice(-MAX_ATTEMPTED))
    );
  }catch{}
}

function hydrateAttemptedHistory(){
  try{
    const raw=JSON.parse(sessionStorage.getItem(ATTEMPTED_SESSION_KEY)||'[]');
    if(!Array.isArray(raw))return;
    for(const id of raw.slice(-MAX_ATTEMPTED)){
      if(typeof id!=='string' || !id || attempted.has(id))continue;
      attempted.add(id);
      attemptedOrder.push(id);
    }
  }catch{}
}

/* GPT_WINDOWS_RESULT_ACK_STRICT_V1
   A displayed packet id is not a delivery receipt.  Only a complete relay
   result envelope occupying a positively identified user turn can acknowledge
   delivery.  In particular, assistant prose, code examples, quoted results,
   and broad conversation wrappers are not receipts. */
const RESULT_TURN_SELECTOR=USER_SELECTOR;
function resultPacketIdFromUserUnit(unit){
  if(!unit?.matches?.(USER_SELECTOR))return null;
  const text=(unit.textContent||'').trim();
  const composer=findComposer();
  if(composer && (unit===composer || unit.contains?.(composer) || composer.contains?.(unit)))return null;
  const match=text.match(/^\[GPT_WINDOWS_RESULT\]\s*\n([\s\S]+?)\n\[\/GPT_WINDOWS_RESULT\]$/);
  if(!match)return null;
  try{
    const result=JSON.parse(match[1]);
    return typeof result?.id==='string' && result.id ? result.id : null;
  }catch{return null;}
}

function hydrateAttemptedFromConversation(){
  if(attemptedConversationHydrated)return;
  const nodes=document.querySelectorAll(RESULT_TURN_SELECTOR);
  if(!nodes.length)return;
  attemptedConversationHydrated=true;
  let added=0;
  const start=Math.max(0,nodes.length-RESULT_SCAN_LIMIT);
  for(let i=start;i<nodes.length;i++){
    const id=resultPacketIdFromUserUnit(nodes[i]);
    if(!id || attempted.has(id))continue;
    attempted.add(id);
    attemptedOrder.push(id);
    added++;
  }
  while(attemptedOrder.length>MAX_ATTEMPTED){
    attempted.delete(attemptedOrder.shift());
  }
  persistAttemptedHistory();
  emitRelayEvent('attempted_history_hydrated',{
    source:'conversation_results',
    added,
    total:attempted.size
  });
}

function rememberAttempted(id){
  if(attempted.has(id))return;
  attempted.add(id);
  attemptedOrder.push(id);
  while(attemptedOrder.length>MAX_ATTEMPTED){
    attempted.delete(attemptedOrder.shift());
  }
  persistAttemptedHistory();
}

function persistSubmittedResults(){
  try{
    sessionStorage.setItem(
      RESULT_SUBMITTED_SESSION_KEY,
      JSON.stringify([...submittedResults.entries()].slice(-MAX_ATTEMPTED))
    );
  }catch{}
}

function hydrateSubmittedResults(){
  try{
    const raw=JSON.parse(sessionStorage.getItem(RESULT_SUBMITTED_SESSION_KEY)||'[]');
    if(!Array.isArray(raw))return;
    for(const row of raw.slice(-MAX_ATTEMPTED)){
      if(!Array.isArray(row) || typeof row[0]!=='string' || !row[0])continue;
      const at=Number(row[1])||Date.now();
      submittedResults.set(row[0],at);
      rememberAttempted(row[0]);
    }
  }catch{}
}

function markResultSubmitted(packetId){
  if(!submittedResults.has(packetId))submittedResults.set(packetId,Date.now());
  rememberAttempted(packetId);
  persistSubmittedResults();
}

function clearResultSubmitted(packetId){
  submittedResults.delete(packetId);
  const timer=submittedWatchTimers.get(packetId);
  if(timer!==undefined)clearTimeout(timer);
  submittedWatchTimers.delete(packetId);
  persistSubmittedResults();
}

function confirmSubmittedResult(packetId,source='post_submit_watch'){
  if(!submittedResults.has(packetId))return false;
  clearResultSubmitted(packetId);
  emitRelayEvent('relay_result_send_confirmed',{
    packet_id:packetId,
    attempt:0,
    method:source
  });
  emitRelayEvent('relay_result_delivery_complete',{
    packet_id:packetId,
    submitted_once:true
  });
  try{backgroundPort?.postMessage({type:'relay_operation_delivered',id:packetId});}catch{}
  return true;
}

function trackSubmittedResult(packetId){
  if(!submittedResults.has(packetId) || submittedWatchTimers.has(packetId))return;
  const submittedAt=Number(submittedResults.get(packetId))||Date.now();
  const deadline=submittedAt+RESULT_SUBMIT_WATCH_MS;
  const tick=()=>{
    submittedWatchTimers.delete(packetId);
    if(!submittedResults.has(packetId))return;
    if(userTurnContainsPacketId(packetId)){
      confirmSubmittedResult(packetId,'post_submit_user_result_turn');
      return;
    }
    if(Date.now()>=deadline){
      emitResultTurnMatchDiagnostic(packetId,document.querySelectorAll(RESULT_TURN_SELECTOR),true);
      emitRelayEvent('relay_result_turn_end_watchdog_expired',{
        packet_id:packetId,
        submitted_at:submittedAt,
        waited_ms:Math.max(0,Date.now()-submittedAt),
        resend:false,
        reexecution:false
      });
      return;
    }
    submittedWatchTimers.set(packetId,setTimeout(tick,500));
  };
  submittedWatchTimers.set(packetId,setTimeout(tick,250));
}

function reconcileSubmittedResults(){
  for(const packetId of submittedResults.keys()){
    if(userTurnContainsPacketId(packetId)){
      confirmSubmittedResult(packetId,'recovery_scan_user_result_turn');
    }
  }
}

function hash(s){
  let h=2166136261;
  for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}
  return(h>>>0).toString(16);
}

function validPacketBody(body){
  let p;
  try{p=JSON.parse(body.trim())}catch{return null}
  if(
    p.version!==1 ||
    p.platform!=='windows' ||
    String(p.action||'').toUpperCase()!=='EXEC' ||
    typeof p.id!=='string' ||
    !p.id
  ) return null;
  return {id:p.id,packet:(OPEN+'\n'+body.trim()+'\n'+CLOSE)};
}

function extract(text){
  // Fallback parser for combined assistant text. Delimiters must occupy their
  // own lines so marker strings embedded inside JSON command data cannot win.
  const blockRe=/(?:^|\n)[ \t]*\[GPT_WINDOWS_ACTION\][ \t]*\r?\n([\s\S]*?)\r?\n[ \t]*\[\/GPT_WINDOWS_ACTION\][ \t]*(?=\r?\n|$)/g;
  let match, found=null;
  while((match=blockRe.exec(text))!==null){
    const parsed=validPacketBody(match[1]);
    if(parsed)found=parsed;
  }
  return found;
}

function extractUnit(unit){
  if(!unit)return null;

  // Primary path: parse rendered code blocks directly. This avoids depending
  // on how ChatGPT concatenates prose/code textContent in a particular DOM build.
  const codes=unit.querySelectorAll?.('pre code, code') || [];
  for(let i=codes.length-1;i>=0;i--){
    const text=codes[i].textContent||'';
    const a=text.indexOf(OPEN);
    const b=text.lastIndexOf(CLOSE);
    if(a<0 || b<=a)continue;
    const body=text.slice(a+OPEN.length,b).trim();
    const parsed=validPacketBody(body);
    if(parsed)return parsed;
  }

  return extract(unit.textContent||'');
}

function classifyRecoveryAdvice(text){
  if(!text.includes(RECOVERY_ADVICE_OPEN) && !text.includes(RECOVERY_ADVICE_CLOSE))return null;
  const a=text.lastIndexOf(RECOVERY_ADVICE_OPEN);
  const b=a>=0?text.indexOf(RECOVERY_ADVICE_CLOSE,a+RECOVERY_ADVICE_OPEN.length):-1;
  const incidentMatch=text.match(/"incident_id"\s*:\s*"([^"]+)"/);
  const incidentId=incidentMatch?.[1]||null;
  if(a<0 || b<a)return {kind:'INVALID_RECOVERY_ADVICE',incident_id:incidentId,reason:'incomplete_envelope'};
  let value;
  try{value=JSON.parse(text.slice(a+RECOVERY_ADVICE_OPEN.length,b).trim());}
  catch{return {kind:'INVALID_RECOVERY_ADVICE',incident_id:incidentId,reason:'invalid_json'};}
  const repairs=value?.recommended_repairs;
  const valid=value?.version===1 && typeof value?.incident_id==='string' && !!value.incident_id &&
    Array.isArray(repairs) && repairs.length>0 &&
    repairs.every(x=>typeof x==='string' && RECOVERY_ADVICE_ALLOWED.has(x));
  return valid
    ? {kind:'RECOVERY_ADVICE',incident_id:value.incident_id,repairs}
    : {kind:'INVALID_RECOVERY_ADVICE',incident_id:value?.incident_id||incidentId,reason:'schema_or_whitelist'};
}

function classifyAssistantRelayOutput(unit){
  const text=unit?.textContent||'';
  const parsed=extractUnit(unit);
  if(parsed)return {kind:'VALID_SANDWICH',packet_id:parsed.id};
  const recovery=classifyRecoveryAdvice(text);
  if(recovery)return recovery;
  const hasOpen=text.includes(OPEN),hasClose=text.includes(CLOSE);
  if(hasOpen||hasClose)return {kind:'INCOMPLETE_SANDWICH'};
  if(/\bWorked for\b\s+\S+/i.test(text))return {kind:'COLLAPSED_STATUS_ARTIFACT'};
  return {kind:'NO_ACTION_PACKET'};
}

function isAssistantUnit(node){
  if(!(node instanceof Element) || !node.matches(ASSISTANT_SELECTOR))return false;

  // GPT_CHATGPT_DATA_MESSAGE_ROLE_VALIDATOR_V1
  // Fail closed on any explicit user role, including ChatGPT's current DOM.
  if(
    node.matches('[data-message-role="user"]') ||
    node.matches('[data-message-author-role="user"]') ||
    node.matches('article[data-turn="user"]') ||
    node.querySelector('[data-message-role="user"],[data-message-author-role="user"],article[data-turn="user"]')
  ) return false;

  return (
    node.matches('[data-message-role="assistant"]') ||
    node.matches('[data-message-author-role="assistant"]') ||
    node.matches('article[data-turn="assistant"]') ||
    node.matches('[data-content-search-unit-key$=":assistant"]') ||
    node.matches('[data-chatgpt-search-unit-key$=":assistant"]') ||
    node.matches('[data-conversation-role="assistant"]') ||
    node.matches('[data-markdown-text-style="assistant-message"]') ||
    !!node.querySelector(
      '[data-message-role="assistant"],[data-message-author-role="assistant"],article[data-turn="assistant"],'+
      '[data-conversation-role="assistant"],[data-markdown-text-style="assistant-message"]'
    )
  );
}

function assistantUnits(){
  return [...document.querySelectorAll(ASSISTANT_SELECTOR)].filter(isAssistantUnit);
}

function recentAssistantUnits(limit=4){
  const nodes=document.querySelectorAll(ASSISTANT_SELECTOR);
  const out=[];
  for(let i=nodes.length-1;i>=0 && out.length<limit;i--){
    if(isAssistantUnit(nodes[i]))out.push(nodes[i]);
  }
  return out;
}

// GPT_CHATGPT_COMPOSER_MULTI_SHAPE_V1
function findComposer(){
  const selectors=[
    'textarea#mobile-composer-prompt',
    'textarea[name="prompt"][aria-label="Chat with ChatGPT"]',
    'textarea[name="prompt"][placeholder="Ask ChatGPT"]',
    'textarea[name="prompt"]',
    '[data-composer-markdown][contenteditable="true"][role="textbox"]',
    '[contenteditable="true"][role="textbox"][aria-label="Ask ChatGPT"]',
    '#prompt-textarea'
  ];
  for(const selector of selectors){
    for(const e of document.querySelectorAll(selector)){
      if(!e?.isConnected || e.disabled || e.getAttribute('aria-disabled')==='true')continue;
      return e;
    }
  }
  return null;
}

function setText(text){
  const e=findComposer();
  if(!e)throw new Error('ChatGPT composer not found');

  e.focus();

  if(e instanceof HTMLTextAreaElement || e instanceof HTMLInputElement){
    const proto=e instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
    const setter=Object.getOwnPropertyDescriptor(proto,'value')?.set;
    if(!setter)throw new Error('composer value setter unavailable');
    setter.call(e,text);
    e.dispatchEvent(new Event('input',{bubbles:true}));
    return;
  }

  const sel=getSelection();
  const r=document.createRange();
  r.selectNodeContents(e);
  sel.removeAllRanges();
  sel.addRange(r);

  let ok=false;
  try{ok=document.execCommand('insertText',false,text);}catch{}
  if(!ok){
    e.textContent='';
    const p=document.createElement('p');
    p.textContent=text;
    e.appendChild(p);
    e.dispatchEvent(new InputEvent('input',{
      bubbles:true,
      inputType:'insertText',
      data:text
    }));
  }
}

function composerRoot(){
  const e=findComposer();
  if(!e)return document;
  return e.closest('form') || e.closest('[data-composer-body]') || e.parentElement?.parentElement || document;
}

// GPT_CHATGPT_SEND_BUTTON_MULTI_SHAPE_V1
function findReadySendButton(){
  const root=composerRoot();
  const selectors=[
    '[data-testid="send-button"]',
    'button[aria-label="Send message"]',
    'button[aria-label="Send prompt"]',
    'button[aria-label="Send"]'
  ];
  for(const scope of [root,document]){
    for(const selector of selectors){
      const b=scope.querySelector?.(selector);
      if(b && !b.disabled && b.getAttribute('aria-disabled')!=='true')return b;
    }
  }
  return null;
}

async function send(packetId=null,attempt=null){
  assertOperatorActive();
  const started=Date.now();
  if(packetId){
    emitRelayEvent('relay_result_send_waiting',{
      packet_id:packetId,
      attempt,
      timeout_ms:SEND_READY_TIMEOUT_MS
    });
  }

  const until=started+SEND_READY_TIMEOUT_MS;
  while(Date.now()<until){
    assertOperatorActive();
    const b=findReadySendButton();
    if(b){
      if(packetId){
        emitRelayEvent('relay_result_send_ready',{
          packet_id:packetId,
          attempt,
          waited_ms:Date.now()-started
        });
      }
      assertOperatorActive();
      b.click();
      return;
    }
    await new Promise(r=>setTimeout(r,SEND_READY_POLL_MS));
  }

  throw new Error('Send button not ready within '+SEND_READY_TIMEOUT_MS+'ms');
}

function scrollDistanceFromBottom(root){
  if(!root)return null;
  return Math.max(0,root.scrollHeight-root.scrollTop-root.clientHeight);
}

function scrollRootDescriptor(root){
  if(!root)return 'none';
  if(root===document.scrollingElement)return 'document.scrollingElement';
  if(root===document.documentElement)return 'document.documentElement';
  const tag=(root.tagName||'element').toLowerCase();
  const id=root.id?('#'+root.id):'';
  const cls=typeof root.className==='string' && root.className
    ? '.'+root.className.trim().split(/\s+/).slice(0,3).join('.')
    : '';
  return tag+id+cls;
}

function emitRelayEvent(event,detail){
  try{
    backgroundPort?.postMessage({
      type:'relay_event',
      event,
      detail
    });
  }catch{}
}

function assertOperatorActive(){
  if(operatorPaused)throw new Error('operator_paused');
}

function quiesceBrowserRelay(source='operator'){
  const changed=!operatorPaused;
  operatorPaused=true;
  for(const id of [deferredDrainTimer,watchedInspectTimer,scrollTimer,approvalInspectTimer,uiErrorInspectTimer,draftRecoveryTimer,consumerClassificationTimer,recoveryRefreshTimer]){
    if(id!==null && id!==undefined)clearTimeout(id);
  }
  deferredDrainTimer=null;
  watchedInspectTimer=null;
  scrollTimer=null;
  approvalInspectTimer=null;
  uiErrorInspectTimer=null;
  draftRecoveryTimer=null;
  consumerClassificationTimer=null;
  recoveryRefreshTimer=null;
  if(recoveryTimer!==null){clearInterval(recoveryTimer);recoveryTimer=null;}
  if(consumerMissionPollTimer!==null){clearInterval(consumerMissionPollTimer);consumerMissionPollTimer=null;}
  if(approvalInspectInterval!==null){clearInterval(approvalInspectInterval);approvalInspectInterval=null;}
  if(uiErrorInspectInterval!==null){clearInterval(uiErrorInspectInterval);uiErrorInspectInterval=null;}
  for(const timer of submittedWatchTimers.values())clearTimeout(timer);
  submittedWatchTimers.clear();
  for(const [requestId,pendingRequest] of backgroundPending){
    backgroundPending.delete(requestId);
    clearTimeout(pendingRequest.timer);
    try{pendingRequest.reject(new Error('operator_paused'));}catch{}
  }
  watchedObserver?.disconnect();watchedObserver=null;watchedUnit=null;
  conversationObserver?.disconnect();conversationObserver=null;conversationRoot=null;
  approvalPromptObserver?.disconnect();approvalPromptObserver=null;
  uiErrorObserver?.disconnect();uiErrorObserver=null;
  recoveryRefreshScheduled=false;
  if(changed)emitRelayEvent('browser_operator_quiesced',{source});
}

function resumeBrowserRelay(source='operator'){
  const changed=operatorPaused;
  operatorPaused=false;
  resumePersistedHandoff();
  bindToolApprovalPromptDetector();
  bindChatGPTUiErrorDetector();
  if(consumerMissionPollTimer===null)consumerMissionPollTimer=setInterval(pollConsumerMission,1500);
  if(recoveryTimer===null)recoveryTimer=setInterval(recoverLatestAssistant,15000);
  if(changed)emitRelayEvent('browser_operator_resumed',{source});
  setTimeout(()=>{if(!operatorPaused)recoverExistingRelayDraft().catch(()=>{});},150);
  setTimeout(()=>{if(!operatorPaused)for(const id of submittedResults.keys())trackSubmittedResult(id);},500);
  setTimeout(()=>{if(!operatorPaused)recoverLatestAssistant();},250);
}

function acknowledgeOperatorQuiescedGeneration(generation){
  const g=Number(generation)||0;
  if(g<=0 || g===lastOperatorQuiescedGeneration)return;
  const port=connectBackgroundPort();
  if(!port)return;
  try{
    port.postMessage({type:'operator_quiesced_ack',stop_generation:g});
    lastOperatorQuiescedGeneration=g;
  }catch{}
}

function applyOperatorControlState(m){
  if(m?.online!==true)return;
  const owner=m?.outbound_owner;
  if(owner==='browser'||owner==='windows')outboundOwner=owner;
  if(m.armed===false){
    quiesceBrowserRelay('backend_disarmed');
    acknowledgeOperatorQuiescedGeneration(m.stop_generation);
    return;
  }
  if(m.armed===true && operatorPaused)resumeBrowserRelay('backend_armed');
}

function pollOperatorControlState(){
  const port=connectBackgroundPort();
  try{port?.postMessage({type:'operator_control_poll'});}catch{}
}


function newestConversationEdge(){
  const main=document.querySelector('main') || document;
  const turns=main.querySelectorAll(
    'article[data-turn], article[data-testid^="conversation-turn-"], section[data-testid^="conversation-turn-"]'
  );
  if(turns.length)return turns[turns.length-1];
  return findComposer() || main;
}

function forceConversationBottom(){
  const anchor=newestConversationEdge();
  let root=anchor ? findScrollRoot(anchor) : null;
  if(!root)root=scrollRoot || document.scrollingElement || document.documentElement;
  if(root && root!==scrollRoot){
    scrollRoot?.removeEventListener?.('scroll',onScroll);
    scrollRoot=root;
    scrollRoot?.addEventListener?.('scroll',onScroll,{passive:true});
  }

  try{
    anchor?.scrollIntoView?.({block:'end',inline:'nearest',behavior:'auto'});
  }catch{}

  try{
    root?.scrollTo?.({top:root.scrollHeight,left:root.scrollLeft||0,behavior:'auto'});
  }catch{}

  try{
    if(root)root.scrollTop=root.scrollHeight;
  }catch{}

  return {root,anchor};
}

function persistHandoffUntil(until){
  try{sessionStorage.setItem(HANDOFF_SESSION_KEY,String(until));}catch{}
}

function clearPersistedHandoff(){
  try{sessionStorage.removeItem(HANDOFF_SESSION_KEY);}catch{}
}

function resumePersistedHandoff(){
  let until=0;
  try{until=Number(sessionStorage.getItem(HANDOFF_SESSION_KEY)||0);}catch{}
  if(!Number.isFinite(until) || until<=Date.now()){
    clearPersistedHandoff();
    return;
  }
  relayHandoffScrollUntil=until;
  followBottom=true;
  emitRelayEvent('handoff_scroll_resumed',{
    remaining_ms:Math.max(0,until-Date.now())
  });
  runHandoffScrollLoop(false);
}

function runHandoffScrollLoop(emitStart=true){
  const root=scrollRoot || document.scrollingElement || document.documentElement;
  const before=scrollDistanceFromBottom(root);
  const forced=forceConversationBottom();
  const activeRoot=forced?.root || root;

  if(emitStart){
    emitRelayEvent('handoff_scroll_start',{
      root:scrollRootDescriptor(activeRoot),
      anchor:scrollRootDescriptor(forced?.anchor),
      before_distance:before,
      after_distance:scrollDistanceFromBottom(activeRoot)
    });
  }

  const tick=()=>{
    if(Date.now()>=relayHandoffScrollUntil){
      const endRoot=scrollRoot || document.scrollingElement || document.documentElement;
      emitRelayEvent('handoff_scroll_end',{
        root:scrollRootDescriptor(endRoot),
        end_distance:scrollDistanceFromBottom(endRoot),
        near_bottom:nearBottom(endRoot)
      });
      clearPersistedHandoff();
      return;
    }
    const forcedTick=forceConversationBottom();
    emitRelayEvent('handoff_scroll_tick',{
      root:scrollRootDescriptor(forcedTick?.root),
      anchor:scrollRootDescriptor(forcedTick?.anchor),
      distance:scrollDistanceFromBottom(forcedTick?.root)
    });
    setTimeout(tick,500);
  };
  setTimeout(tick,250);
}

function beginRelayHandoffScroll(){
  // Relay-owned send: begin before clicking Send and persist the deadline so a
  // ChatGPT navigation/content-script reconnect can resume the handoff.
  relayHandoffScrollUntil=Date.now()+8000;
  persistHandoffUntil(relayHandoffScrollUntil);
  followBottom=true;
  runHandoffScrollLoop(true);
}

function elementText(e){
  if(!e)return '';
  if(e instanceof HTMLTextAreaElement || e instanceof HTMLInputElement)return e.value||'';
  return e.textContent||'';
}

function relayDraftFromComposer(){
  const text=elementText(findComposer()).trim();
  if(!text.includes('[GPT_WINDOWS_RESULT]') || !text.includes('[/GPT_WINDOWS_RESULT]'))return null;
  const a=text.indexOf('[GPT_WINDOWS_RESULT]');
  const b=text.indexOf('[/GPT_WINDOWS_RESULT]',a);
  if(a<0 || b<a)return null;
  const block=text.slice(a,b+'[/GPT_WINDOWS_RESULT]'.length);
  const m=block.match(/"id"\s*:\s*"([^"]+)"/);
  if(!m?.[1])return null;
  return {id:m[1],text:block};
}

function clearOwnedRelayDraft(packetId){
  const draft=relayDraftFromComposer();
  if(!draft || draft.id!==packetId)return false;
  const e=findComposer();
  if(!e)return false;
  e.focus();

  if(e instanceof HTMLTextAreaElement || e instanceof HTMLInputElement){
    const proto=e instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
    const setter=Object.getOwnPropertyDescriptor(proto,'value')?.set;
    if(!setter)return false;
    setter.call(e,'');
    e.dispatchEvent(new Event('input',{bubbles:true}));
    return true;
  }

  try{
    const sel=getSelection();
    const r=document.createRange();
    r.selectNodeContents(e);
    sel.removeAllRanges();
    sel.addRange(r);
    if(document.execCommand('delete',false,null)){
      e.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'deleteContent'}));
      return true;
    }
  }catch{}

  e.textContent='';
  e.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'deleteContent'}));
  return true;
}

function scheduleDraftRecovery(delay=1000){
  if(operatorPaused)return;
  if(draftRecoveryTimer!==null)return;
  draftRecoveryTimer=setTimeout(()=>{
    draftRecoveryTimer=null;
    recoverExistingRelayDraft().catch(()=>{});
  },delay);
}

function textContainsResultPacketEnvelope(text,packetId){
  const value=String(text||'');
  let idIndex=value.indexOf(packetId);
  while(idIndex>=0){
    const resultOpen=value.lastIndexOf('[GPT_WINDOWS_RESULT]',idIndex);
    const actionOpen=value.lastIndexOf('[GPT_WINDOWS_ACTION]',idIndex);
    if(resultOpen>=0 && resultOpen>actionOpen)return true;
    idIndex=value.indexOf(packetId,idIndex+Math.max(1,packetId.length));
  }
  return false;
}

function safeResultDiagnosticNode(node){
  const attr=(name)=>node?.getAttribute?.(name)||null;
  const className=typeof node?.className==='string'?node.className.slice(0,240):null;
  return {
    tag:node?.tagName||null,
    class_name:className,
    role:attr('role'),
    testid:attr('data-testid'),
    message_role:attr('data-message-role'),
    author_role:attr('data-message-author-role'),
    turn:attr('data-turn'),
    conversation_role:attr('data-conversation-role'),
    markdown_style:attr('data-markdown-text-style'),
    scroll_anchor:attr('data-scroll-anchor')
  };
}

function resultDiagnosticAncestorChain(node,maxDepth=8){
  const chain=[];
  let current=node;
  for(let depth=0;current && depth<maxDepth;depth++,current=current.parentElement){
    chain.push({depth,...safeResultDiagnosticNode(current)});
  }
  return chain;
}

function emitResultTurnMatchDiagnostic(packetId,nodes,force=false){
  if(resultMatcherDiagnosticsReported.has(packetId))return;
  const bodyText=document.body?.textContent||'';
  const bodyPacketVisible=bodyText.includes(packetId);
  const bodyResultMarkerVisible=bodyText.includes('[GPT_WINDOWS_RESULT]');
  const exactResultPacketVisible=textContainsResultPacketEnvelope(bodyText,packetId);
  const candidates=Array.from(nodes||[]);
  let candidatePacketHits=0, candidateResultHits=0, candidateEnvelopeHits=0;
  for(const node of candidates){
    const text=node?.textContent||'';
    if(text.includes(packetId))candidatePacketHits++;
    if(text.includes(packetId) && text.includes('[GPT_WINDOWS_RESULT]'))candidateResultHits++;
    if(textContainsResultPacketEnvelope(text,packetId))candidateEnvelopeHits++;
  }
  if(!force && !exactResultPacketVisible)return;
  let carrier=null, carrierTextLength=Number.MAX_SAFE_INTEGER;
  if(exactResultPacketVisible){
    const all=document.querySelectorAll('*');
    for(const node of all){
      const text=node?.textContent||'';
      if(!textContainsResultPacketEnvelope(text,packetId))continue;
      if(text.length<carrierTextLength){carrier=node;carrierTextLength=text.length;}
    }
  }
  const attr=(node,name)=>node?.getAttribute?.(name)||null;
  const parent=carrier?.parentElement||null;
  resultMatcherDiagnosticsReported.add(packetId);
  emitRelayEvent('relay_result_turn_match_diagnostic',{
    packet_id:packetId,
    trigger:exactResultPacketVisible?'visible_result_envelope':'watchdog_deadline',
    body_packet_visible:bodyPacketVisible,
    body_result_marker_visible:bodyResultMarkerVisible,
    exact_result_packet_visible:exactResultPacketVisible,
    result_candidate_count:candidates.length,
    result_candidate_packet_hits:candidatePacketHits,
    result_candidate_result_hits:candidateResultHits,
    candidate_envelope_hits:candidateEnvelopeHits,
    carrier_tag:carrier?.tagName||null,
    carrier_testid:attr(carrier,'data-testid'),
    carrier_message_role:attr(carrier,'data-message-role'),
    carrier_author_role:attr(carrier,'data-message-author-role'),
    carrier_turn:attr(carrier,'data-turn'),
    carrier_conversation_role:attr(carrier,'data-conversation-role'),
    carrier_markdown_style:attr(carrier,'data-markdown-text-style'),
    parent_tag:parent?.tagName||null,
    parent_testid:attr(parent,'data-testid'),
    parent_message_role:attr(parent,'data-message-role'),
    parent_author_role:attr(parent,'data-message-author-role'),
    carrier_ancestors:resultDiagnosticAncestorChain(carrier,8)
  });
}

function userTurnContainsPacketId(packetId){
  const nodes=document.querySelectorAll(RESULT_TURN_SELECTOR);
  for(let i=nodes.length-1;i>=0 && i>=nodes.length-32;i--){
    if(resultPacketIdFromUserUnit(nodes[i])===packetId || elementText(nodes[i]).includes(packetId))return true;
  }
  emitResultTurnMatchDiagnostic(packetId,nodes,false);
  return false;
}

function composerContainsPacketId(packetId){
  return elementText(findComposer()).includes(packetId);
}

function visibleSendFailure(){
  const nodes=document.querySelectorAll(
    '[role="alert"],[data-testid*="error"],.text-token-text-error,[class*="text-red"]'
  );
  for(const node of nodes){
    const text=(node.textContent||'').trim();
    if(/could not send this chatgpt message|failed to send|unable to send|something went wrong/i.test(text)){
      return text.slice(0,240);
    }
  }
  return null;
}

function visibleElement(node){
  if(!node)return false;
  const rect=node.getBoundingClientRect?.();
  if(rect && rect.width===0 && rect.height===0)return false;
  const style=getComputedStyle?.(node);
  if(style && (style.display==='none' || style.visibility==='hidden'))return false;
  return true;
}

function activeGenerationStopControl(){
  const root=composerRoot();
  const selectors=[
    '[data-testid="stop-button"]',
    'button[aria-label="Stop generating"]',
    'button[aria-label="Stop response"]',
    'button[aria-label="Stop"]'
  ];
  for(const selector of selectors){
    const local=root.querySelector?.(selector);
    if(local && visibleElement(local))return local;
    const global=document.querySelector(selector);
    if(global && visibleElement(global))return global;
  }
  return null;
}

function visibleInterruptedWaitState(){
  const nodes=document.querySelectorAll(
    '[role="alert"],[role="status"],[aria-live="polite"],[aria-live="assertive"]'
  );
  for(const node of nodes){
    if(!visibleElement(node))continue;
    const text=(node.textContent||'').trim();
    if(/connection interrupted|waiting for the complete answer/i.test(text))return text.slice(0,240);
  }
  return null;
}

function chatBusyReason(){
  if(activeGenerationStopControl())return 'generation_stop_control';
  const interrupted=visibleInterruptedWaitState();
  if(interrupted)return interrupted;
  return null;
}

async function waitForChatIdle(packetId,attempt){
  assertOperatorActive();
  const started=Date.now();
  let lastReason=chatBusyReason();
  if(!lastReason)return true;

  emitRelayEvent('relay_result_idle_waiting',{
    packet_id:packetId,
    attempt,
    reason:lastReason,
    timeout_ms:CHAT_IDLE_TIMEOUT_MS
  });

  const until=started+CHAT_IDLE_TIMEOUT_MS;
  while(Date.now()<until){
    assertOperatorActive();
    const reason=chatBusyReason();
    if(!reason){
      emitRelayEvent('relay_result_idle_ready',{
        packet_id:packetId,
        attempt,
        waited_ms:Date.now()-started
      });
      return true;
    }
    lastReason=reason;
    await new Promise(r=>setTimeout(r,CHAT_IDLE_POLL_MS));
  }

  emitRelayEvent('relay_result_idle_timeout',{
    packet_id:packetId,
    attempt,
    reason:String(lastReason||'chat_busy').slice(0,240),
    waited_ms:Date.now()-started
  });
  return false;
}

/* GPT_WINDOWS_EXACT_RESULT_CONFIRMATION_V1 */
async function waitForDeliveryConfirmation(packetId,attempt){
  assertOperatorActive();
  const until=Date.now()+DELIVERY_CONFIRM_MS;
  let clearedSince=0;
  let generationObserved=false;
  let clearObserved=false;
  while(Date.now()<until){
    assertOperatorActive();
    if(userTurnContainsPacketId(packetId)){
      emitRelayEvent('relay_result_send_confirmed',{
        packet_id:packetId,
        attempt,
        method:'user_result_turn'
      });
      return 'confirmed';
    }

    const failure=visibleSendFailure();
    if(failure){
      emitRelayEvent('relay_result_send_rejected',{
        packet_id:packetId,
        attempt,
        error:failure
      });
      return 'rejected';
    }

    const composerHasPacket=composerContainsPacketId(packetId);
    if(!composerHasPacket && activeGenerationStopControl() && !generationObserved){
      generationObserved=true;
      emitRelayEvent('relay_result_send_progress',{
        packet_id:packetId,
        attempt,
        method:'generation_started'
      });
      emitRelayEvent('relay_result_send_accepted',{
        packet_id:packetId,
        attempt,
        method:'generation_started'
      });
      return 'accepted';
    }

    if(!composerHasPacket){
      if(!clearedSince)clearedSince=Date.now();
      if(Date.now()-clearedSince>=DELIVERY_CLEAR_STABLE_MS && !clearObserved){
        clearObserved=true;
        emitRelayEvent('relay_result_send_progress',{
          packet_id:packetId,
          attempt,
          method:'composer_cleared'
        });
        emitRelayEvent('relay_result_send_accepted',{
          packet_id:packetId,
          attempt,
          method:'composer_cleared_stable'
        });
        return 'accepted';
      }
    }else{
      clearedSince=0;
      clearObserved=false;
    }

    await new Promise(r=>setTimeout(r,250));
  }

  emitRelayEvent('relay_result_send_unconfirmed',{
    packet_id:packetId,
    attempt,
    generation_observed:generationObserved,
    composer_cleared:clearObserved
  });
  return 'timeout';
}

/* GPT_WINDOWS_STALE_OWNER_RELEASE_V1 */
async function recoverExistingRelayDraft(){
  if(draftRecoveryInFlight)return false;
  const draft=relayDraftFromComposer();
  if(!draft){
    const owner=activeRelayOperationId;
    if(owner && !inflight.has(owner) && userTurnContainsPacketId(owner)){
      rememberAttempted(owner);
      activeRelayOperationId=null;
      emitRelayEvent('relay_operation_owner_released',{
        packet_id:owner,
        reason:'exact_user_result_visible_no_draft'
      });
    }
    scheduleDeferredDrain(0);
    return true;
  }

  if(attempted.has(draft.id)){
    const cleared=clearOwnedRelayDraft(draft.id);
    if(activeRelayOperationId===draft.id)activeRelayOperationId=null;
    emitRelayEvent('relay_result_draft_cleared',{
      packet_id:draft.id,
      reason:'already_exactly_delivered',
      cleared
    });
    scheduleDeferredDrain(100);
    setTimeout(scheduleWatchedInspect,100);
    return true;
  }

  // GPT_WINDOWS_RELAY_DRAFT_SINGLE_OWNER_V2
  // Normal delivery already owns this exact packet. Recovery must not become
  // a second sender merely because the freshly injected result is visible.
  if(inflight.has(draft.id)){
    emitRelayEvent('relay_result_draft_recovery_deferred',{
      packet_id:draft.id,
      reason:'normal_delivery_inflight'
    });
    scheduleDraftRecovery(1000);
    return false;
  }

  if(activeRelayOperationId && activeRelayOperationId!==draft.id){
    emitRelayEvent('relay_result_draft_deferred',{
      packet_id:draft.id,
      active_packet_id:activeRelayOperationId
    });
    return false;
  }

  draftRecoveryInFlight=true;
  claimActiveRelayOperation(draft.id);
  emitRelayEvent('relay_result_draft_detected',{
    packet_id:draft.id,
    chars:draft.text.length
  });

  try{
    if(userTurnContainsPacketId(draft.id)){
      const cleared=clearOwnedRelayDraft(draft.id);
      rememberAttempted(draft.id);
      emitRelayEvent('relay_result_draft_cleared',{
        packet_id:draft.id,
        reason:'already_visible_as_user_result',
        cleared
      });
      activeRelayOperationId=null;
      scheduleDeferredDrain(100);
      setTimeout(scheduleWatchedInspect,100);
      return true;
    }

    if(!await waitForChatIdle(draft.id,0)){
      emitRelayEvent('relay_result_draft_recovery_deferred',{
        packet_id:draft.id,
        reason:'chat_not_idle'
      });
      scheduleDraftRecovery(5000);
      return false;
    }

    emitRelayEvent('relay_result_send_attempt',{
      packet_id:draft.id,
      attempt:0,
      recovery:true
    });
    await send(draft.id,0);
    emitRelayEvent('relay_result_send_clicked',{
      packet_id:draft.id,
      attempt:0,
      recovery:true
    });

    const deliveryState=await waitForDeliveryConfirmation(draft.id,0);
    if(deliveryState==='confirmed'){
      rememberAttempted(draft.id);
      emitRelayEvent('relay_result_draft_recovered',{
        packet_id:draft.id
      });
      emitRelayEvent('relay_result_delivery_complete',{
        packet_id:draft.id,
        recovery:true
      });
      try{backgroundPort?.postMessage({type:'relay_operation_delivered',id:draft.id});}catch{}
      activeRelayOperationId=null;
      scheduleDeferredDrain(100);
      setTimeout(scheduleWatchedInspect,100);
      return true;
    }
    if(deliveryState==='accepted'){
      markResultSubmitted(draft.id);
      emitRelayEvent('relay_result_waiting_for_gpt_turn_end',{
        packet_id:draft.id,
        recovery:true,
        resend:false,
        reexecution:false
      });
      trackSubmittedResult(draft.id);
      activeRelayOperationId=null;
      scheduleDeferredDrain(100);
      setTimeout(scheduleWatchedInspect,100);
      return true;
    }

    emitRelayEvent('relay_result_draft_recovery_deferred',{
      packet_id:draft.id,
      reason:visibleSendFailure()||'delivery_not_confirmed'
    });
    scheduleDraftRecovery(5000);
    return false;
  }catch(e){
    emitRelayEvent('relay_result_draft_recovery_deferred',{
      packet_id:draft.id,
      reason:String(e?.message||e||'draft_recovery_error').slice(0,240)
    });
    scheduleDraftRecovery(5000);
    return false;
  }finally{
    draftRecoveryInFlight=false;
    if(activeRelayOperationId===draft.id){
      activeRelayOperationId=null;
      emitRelayEvent('relay_operation_owner_released',{
        packet_id:draft.id,
        reason:'draft_recovery_attempt_finished'
      });
      scheduleDeferredDrain(100);
      setTimeout(scheduleWatchedInspect,100);
    }
  }
}

// GPT_WINDOWS_CHATGPT_IMAGE_ATTACHMENT_V1
const relayAttachmentPackets=new Set();
function relayUploadInput(){const root=composerRoot();const local=[...(root.querySelectorAll?.('input[type="file"]')||[])];const all=local.length?local:[...document.querySelectorAll('input[type="file"]')];return all.find(e=>!e.disabled)||null;}
function decodeBase64(s){const raw=atob(s),out=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);return out;}
async function ensureRelayAttachments(list,packetId){
  assertOperatorActive();
  if(!Array.isArray(list)||!list.length||relayAttachmentPackets.has(packetId))return;
  if(list.length!==1)throw new Error('relay_attachment_count_unsupported');const a=list[0];if(a?.kind!=='image'||a?.mime!=='image/png'||typeof a.base64!=='string')throw new Error('relay_attachment_invalid');
  const input=relayUploadInput();if(!input)throw new Error('chatgpt_file_input_not_found');const file=new File([decodeBase64(a.base64)],a.name,{type:'image/png'});const dt=new DataTransfer();dt.items.add(file);input.files=dt.files;input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));
  await new Promise(r=>setTimeout(r,900));relayAttachmentPackets.add(packetId);emitRelayEvent('relay_attachment_attached',{packet_id:packetId,name:a.name,bytes:a.bytes||null});
}
function cleanupRelayAttachments(list){const names=(Array.isArray(list)?list:[]).map(a=>a?.name).filter(Boolean);if(!names.length)return;try{backgroundPort?.postMessage({type:'relay_attachment_cleanup',names});}catch{}}

async function injectConfirmed(text,packetId,attachments=[]){
  assertOperatorActive();
  let lastError='delivery_not_confirmed';

  for(let attempt=1;attempt<=DELIVERY_ATTEMPTS;attempt++){
    assertOperatorActive();
    if(userTurnContainsPacketId(packetId)){
      emitRelayEvent('relay_result_send_confirmed',{
        packet_id:packetId,
        attempt,
        already_present:true
      });
      return 'confirmed';
    }

    try{
      if(!composerContainsPacketId(packetId)){
        if(!await waitForChatIdle(packetId,attempt)){
          throw new Error('chat_not_idle_before_injection');
        }
        await ensureRelayAttachments(attachments,packetId);
        assertOperatorActive();
        setText(text);
        emitRelayEvent('relay_result_text_set',{
          packet_id:packetId,
          attempt,
          chars:text.length
        });
        await new Promise(r=>setTimeout(r,350));
      }else{
        emitRelayEvent('relay_result_text_preserved',{
          packet_id:packetId,
          attempt,
          chars:text.length
        });
      }

      assertOperatorActive();
      emitRelayEvent('relay_result_send_attempt',{packet_id:packetId,attempt});
      await send(packetId,attempt);
      emitRelayEvent('relay_result_send_clicked',{packet_id:packetId,attempt});

      const deliveryState=await waitForDeliveryConfirmation(packetId,attempt);
      if(deliveryState==='confirmed')return 'confirmed';
      if(deliveryState==='accepted'){
        markResultSubmitted(packetId);
        return 'accepted';
      }
      lastError=visibleSendFailure()||('delivery_'+deliveryState);
    }catch(e){
      if(operatorPaused)throw e;
      lastError=String(e?.message||e||'delivery_error');
      emitRelayEvent('relay_result_send_exception',{
        packet_id:packetId,
        attempt,
        error:lastError.slice(0,240)
      });
    }

    emitRelayEvent('relay_result_send_retry',{
      packet_id:packetId,
      attempt,
      error:lastError.slice(0,240),
      composer_has_packet:composerContainsPacketId(packetId)
    });

    if(attempt<DELIVERY_ATTEMPTS){
      const delay=Math.min(15000,1000*Math.pow(2,attempt-1));
      await new Promise(r=>setTimeout(r,delay));
    }
  }

  emitRelayEvent('relay_result_delivery_failed',{
    packet_id:packetId,
    attempts:DELIVERY_ATTEMPTS,
    error:lastError.slice(0,240),
    composer_has_packet:composerContainsPacketId(packetId)
  });
  throw new Error('relay_result_delivery_failed: '+lastError);
}

function consumerMissionAwaitingAck(){
  try{const v=JSON.parse(sessionStorage.getItem(CONSUMER_MISSION_ACK_KEY)||'null');return v&&typeof v.id==='string'?v:null;}catch{return null;}
}
function rememberConsumerMissionAwaitingAck(missionId){
  try{sessionStorage.setItem(CONSUMER_MISSION_ACK_KEY,JSON.stringify({id:missionId,sent_at:Date.now(),href:location.href}));}catch{}
}
function clearConsumerMissionAwaitingAck(missionId){
  try{const v=consumerMissionAwaitingAck();if(!v||!missionId||v.id===missionId)sessionStorage.removeItem(CONSUMER_MISSION_ACK_KEY);}catch{}
}

function consumerRecoveryContext(){
  try{const v=JSON.parse(sessionStorage.getItem(CONSUMER_RECOVERY_KEY)||'null');return v&&typeof v.mission_id==='string'?v:null;}catch{return null;}
}
function saveConsumerRecoveryContext(v){
  try{sessionStorage.setItem(CONSUMER_RECOVERY_KEY,JSON.stringify(v));}catch{}
}
function missionUserTurn(missionId){
  const nodes=document.querySelectorAll(USER_SELECTOR);
  for(let i=nodes.length-1;i>=0 && i>=nodes.length-24;i--){
    const text=nodes[i].textContent||'';
    if(text.includes('[GPT_CONSUMER_MISSION') && text.includes(missionId))return nodes[i];
  }
  return null;
}
function assistantFollowsTrackedMission(unit,ctx){
  if(!unit||!ctx?.mission_id)return false;
  const user=missionUserTurn(ctx.mission_id);
  if(!user)return false;
  return !!(user.compareDocumentPosition(unit)&Node.DOCUMENT_POSITION_FOLLOWING);
}
function beginConsumerRecoveryTracking(mission){
  const ctx={mission_id:mission.id,state:'awaiting_first_action',action_seen:false,recovery_attempts:0,probe_id:null,started_at:Date.now(),href:location.href};
  saveConsumerRecoveryContext(ctx);
  emitRelayEvent('consumer_relay_recovery_tracking_started',{mission_id:mission.id});
}
function recentUserTurnContainsToken(token){
  const nodes=document.querySelectorAll(USER_SELECTOR);
  for(let i=nodes.length-1;i>=0 && i>=nodes.length-16;i--)if((nodes[i].textContent||'').includes(token))return true;
  return false;
}
async function waitForUserToken(token,timeoutMs=15000){
  const until=Date.now()+timeoutMs;
  while(Date.now()<until){if(recentUserTurnContainsToken(token))return true;await new Promise(r=>setTimeout(r,250));}
  return false;
}
function noteTrackedRelayAction(unit,p){
  const ctx=consumerRecoveryContext();
  if(!ctx||!assistantFollowsTrackedMission(unit,ctx))return;
  ctx.action_seen=true;ctx.last_action_id=p.id;ctx.last_action_at=Date.now();
  ctx.state=ctx.probe_id===p.id?'probe_action_seen':'active';
  saveConsumerRecoveryContext(ctx);
  emitRelayEvent('consumer_relay_output_classified',{mission_id:ctx.mission_id,classification:'VALID_SANDWICH',packet_id:p.id});
}
function recoveryProbePrompt(ctx,classification,probeId){
  const packet=JSON.stringify({version:1,platform:'windows',action:'EXEC',id:probeId,session:'default',shell:'cmd',command:'echo RELAY_RENDER_PROBE_OK',timeout:30,result_mode:'compact'});
  const fence='```';
  return `[GPT_CONSUMER_RECOVERY mission_id="${ctx.mission_id}" probe_id="${probeId}"]\nThe previous assistant response was classified ${classification}. Do not repeat or assume any original side effect. First prove relay rendering with one read-only probe. Emit ONE FINAL assistant response using this exact five-part structure: ordinary visible HEADER, the literal opening fence shown below, the action tags and JSON only, the literal closing fence shown below, then ordinary visible FOOTER.\nHEADER\n${fence}\n${OPEN}\n${packet}\n${CLOSE}\n${fence}\nFOOTER\nThe second ${fence} line CLOSES the Markdown fence. FOOTER must be outside it. Do not use a language-tagged or metadata fence and do not use commentary. After the GPT_WINDOWS_RESULT for ${probeId} arrives, resume the original mission ${ctx.mission_id}. Before reissuing any side-effecting operation, inspect the conversation/result evidence or PC state so an operation that may already have executed is never duplicated.\n[/GPT_CONSUMER_RECOVERY]`;
}
async function triggerConsumerRelayRecovery(classification,unit,externalStatus=false){
  if(consumerRecoveryInFlight)return;
  let ctx=consumerRecoveryContext();
  if(!ctx)return;
  if(externalStatus){if(ctx.action_seen||!missionUserTurn(ctx.mission_id))return;}
  else if(!assistantFollowsTrackedMission(unit,ctx))return;
  if(Number(ctx.recovery_attempts||0)>=CONSUMER_RECOVERY_MAX){
    emitRelayEvent('consumer_relay_recovery_terminal',{mission_id:ctx.mission_id,classification,attempts:ctx.recovery_attempts});
    return;
  }
  consumerRecoveryInFlight=true;
  try{
    const attempt=Number(ctx.recovery_attempts||0)+1;
    const probeId=(ctx.mission_id+'-probe-'+attempt).slice(0,128);
    ctx={...ctx,recovery_attempts:attempt,probe_id:probeId,state:'recovery_prompt_sending',last_classification:classification,recovery_started_at:Date.now()};
    saveConsumerRecoveryContext(ctx);
    emitRelayEvent('consumer_relay_recovery_started',{mission_id:ctx.mission_id,classification,attempt,probe_id:probeId});
    if(!await waitForChatIdle(probeId,0))throw new Error('chat_not_idle_for_recovery');
    const composer=findComposer();
    if(!composer)throw new Error('recovery_composer_not_found');
    if(elementText(composer).trim())throw new Error('recovery_composer_not_empty');
    setText(recoveryProbePrompt(ctx,classification,probeId));
    await new Promise(r=>setTimeout(r,350));
    await send();
    if(!await waitForUserToken(probeId,15000))throw new Error('recovery_prompt_user_turn_not_confirmed');
    ctx=consumerRecoveryContext()||ctx;ctx.state='awaiting_probe_action';ctx.recovery_prompt_confirmed_at=Date.now();saveConsumerRecoveryContext(ctx);
    emitRelayEvent('consumer_relay_recovery_prompt_confirmed',{mission_id:ctx.mission_id,probe_id:probeId,attempt});
  }catch(e){
    ctx=consumerRecoveryContext()||ctx;if(ctx){ctx.state='recovery_required';ctx.last_recovery_error=String(e?.message||e).slice(0,240);saveConsumerRecoveryContext(ctx);}
    emitRelayEvent('consumer_relay_recovery_deferred',{mission_id:ctx?.mission_id||null,classification,error:String(e?.message||e).slice(0,240)});
  }finally{consumerRecoveryInFlight=false;}
}

/* GPT_ONE_CLICK_EXTERNAL_COLLAPSE_STATUS_V1 */
let externalCollapseTimer=null;
function visibleExternalCollapseArtifact(){
  const root=document.querySelector('main')||document;
  const nodes=root.querySelectorAll('[role="status"],[aria-live="polite"],[aria-live="assertive"],button');
  for(const node of nodes){
    if(!visibleElement(node))continue;
    const text=(node.textContent||'').trim().replace(/\s+/g,' ');
    if(/^Worked for\s+\d+(?:\.\d+)?(?:ms|s|m|h)$/i.test(text))return {node,text};
  }
  return null;
}
function scheduleExternalCollapseCheck(){
  const ctx=consumerRecoveryContext();
  if(!ctx||ctx.action_seen||externalCollapseTimer!==null)return;
  externalCollapseTimer=setTimeout(()=>{
    externalCollapseTimer=null;
    const current=consumerRecoveryContext();
    if(!current||current.action_seen||!missionUserTurn(current.mission_id)||chatBusyReason())return;
    const artifact=visibleExternalCollapseArtifact();
    if(!artifact)return;
    emitRelayEvent('consumer_relay_external_collapse_detected',{mission_id:current.mission_id,classification:'COLLAPSED_STATUS_ARTIFACT',text:artifact.text.slice(0,80)});
    triggerConsumerRelayRecovery('COLLAPSED_STATUS_ARTIFACT',null,true).catch(()=>{});
  },CONSUMER_CLASSIFY_DELAY_MS);
}

/* GPT_WINDOWS_ENGINEERING_COLLAPSE_OBSERVER_V1
   Consumer mission tracking does not cover PCE engineering conversations.
   Detect a rendered status collapse independently, but NEVER replay an
   invisible/unverified command or inject a recovery prompt. */
let engineeringCollapseTimer=null;
let lastEngineeringCollapseSignature='';
function latestEngineeringResultContext(){
  const nodes=document.querySelectorAll(USER_SELECTOR);
  if(!nodes.length)return null;
  const last=nodes[nodes.length-1];
  const text=last?.textContent||'';
  if(!text.includes('[GPT_WINDOWS_RESULT]'))return null;
  const m=text.match(/"id"\s*:\s*"(PCE\d+\.\d{3})"/i);
  return m?{previous_result_id:m[1],user_turn:last}:null;
}
function scheduleEngineeringCollapseCheck(){
  if(operatorPaused||engineeringCollapseTimer!==null)return;
  if(!latestEngineeringResultContext())return;
  engineeringCollapseTimer=setTimeout(()=>{
    engineeringCollapseTimer=null;
    if(operatorPaused||activeGenerationStopControl())return;
    const ctx=latestEngineeringResultContext();
    if(!ctx)return;
    const newest=recentAssistantUnits(1)[0];
    const rendered=(newest?.textContent||'').trim().replace(/\s+/g,' ');
    const artifact=visibleExternalCollapseArtifact() ||
      (/^Worked for\s+\d+(?:\.\d+)?(?:ms|s|m|h)$/i.test(rendered)?{text:rendered}:null);
    if(!artifact)return;
    if(newest && (ctx.user_turn?.compareDocumentPosition(newest)&Node.DOCUMENT_POSITION_FOLLOWING) && extractUnit(newest))return;
    const signature=ctx.previous_result_id+'|'+artifact.text;
    if(signature===lastEngineeringCollapseSignature)return;
    lastEngineeringCollapseSignature=signature;
    emitRelayEvent('relay_engineering_action_render_collapsed',{
      previous_result_id:ctx.previous_result_id,
      classification:'COLLAPSED_STATUS_ARTIFACT',
      text:artifact.text.slice(0,80),
      original_packet_visible:false,
      safe_replay:false
    });
  },CONSUMER_CLASSIFY_DELAY_MS);
}

function scheduleConsumerAssistantClassification(unit){
  const ctx=consumerRecoveryContext();
  if(!ctx||!assistantFollowsTrackedMission(unit,ctx))return;
  if(consumerClassificationTimer!==null)clearTimeout(consumerClassificationTimer);
  consumerClassificationTimer=setTimeout(()=>{
    consumerClassificationTimer=null;
    const current=consumerRecoveryContext();
    if(!current||!unit?.isConnected||!assistantFollowsTrackedMission(unit,current))return;
    if(chatBusyReason()){scheduleConsumerAssistantClassification(unit);return;}
    const c=classifyAssistantRelayOutput(unit);
    emitRelayEvent('consumer_relay_output_classified',{mission_id:current.mission_id,classification:c.kind,packet_id:c.packet_id||null});
    if(c.kind==='VALID_SANDWICH')return;
    const firstActionMissing=!current.action_seen;
    if(firstActionMissing && c.kind==='NO_ACTION_PACKET'){
      try{sessionStorage.removeItem(CONSUMER_RECOVERY_KEY);}catch{}
      emitRelayEvent('consumer_mission_completed_without_relay',{mission_id:current.mission_id,classification:c.kind});
      return;
    }
    if(c.kind==='COLLAPSED_STATUS_ARTIFACT' || (firstActionMissing && c.kind==='INCOMPLETE_SANDWICH')){
      triggerConsumerRelayRecovery(c.kind,unit).catch(()=>{});
    }
  },CONSUMER_CLASSIFY_DELAY_MS);
}

function userTurnContainsMissionId(missionId){
  const nodes=document.querySelectorAll(USER_SELECTOR);
  for(let i=nodes.length-1;i>=0 && i>=nodes.length-16;i--){
    const text=nodes[i].textContent||'';
    if(text.includes('[GPT_CONSUMER_MISSION') && text.includes(missionId))return true;
  }
  return false;
}

async function waitForConsumerMissionConfirmation(missionId){
  const until=Date.now()+20000;
  while(Date.now()<until){
    if(userTurnContainsMissionId(missionId)){
      emitRelayEvent('consumer_mission_user_turn_confirmed',{mission_id:missionId,href:location.href});
      return true;
    }
    const failure=visibleSendFailure();
    if(failure)throw new Error(failure);
    await new Promise(r=>setTimeout(r,250));
  }
  emitRelayEvent('consumer_mission_client_sync_divergence',{
    mission_id:missionId,
    href:location.href,
    composer_has_mission:elementText(findComposer()).includes(missionId)
  });
  return false;
}

async function deliverConsumerMission(mission){
  if(!mission || typeof mission.id!=='string' || typeof mission.text!=='string')return;
  if(consumerMissionInFlight)return;
  if(userTurnContainsMissionId(mission.id)){
    clearConsumerMissionAwaitingAck(mission.id);
    backgroundPort?.postMessage({type:'consumer_mission_ack',id:mission.id});
    return;
  }
  const awaiting=consumerMissionAwaitingAck();
  if(awaiting?.id===mission.id){
    emitRelayEvent('consumer_mission_client_sync_divergence',{mission_id:mission.id,reason:'sent_without_visible_user_turn',age_ms:Math.max(0,Date.now()-Number(awaiting.sent_at||0)),href:location.href});
    return;
  }
  if(awaiting && awaiting.id!==mission.id)clearConsumerMissionAwaitingAck(awaiting.id);
  const composer=findComposer();
  if(!composer){
    emitRelayEvent('consumer_mission_composer_not_found',{
      mission_id:mission.id,
      href:location.href
    });
    return;
  }
  const draft=elementText(composer).trim();
  if(draft){
    emitRelayEvent('consumer_mission_deferred',{mission_id:mission.id,reason:'composer_not_empty'});
    return;
  }
  if(!await waitForChatIdle(mission.id,0)){
    emitRelayEvent('consumer_mission_deferred',{mission_id:mission.id,reason:'chat_not_idle'});
    return;
  }

  consumerMissionInFlight=mission.id;
  try{
    setText(mission.text);
    emitRelayEvent('consumer_mission_text_set',{mission_id:mission.id,chars:mission.text.length});
    await new Promise(r=>setTimeout(r,350));
    await send(mission.id,0);
    rememberConsumerMissionAwaitingAck(mission.id);
    emitRelayEvent('consumer_mission_send_clicked',{mission_id:mission.id});
    if(!await waitForConsumerMissionConfirmation(mission.id)){
      throw new Error('consumer_mission_user_turn_not_confirmed');
    }
    clearConsumerMissionAwaitingAck(mission.id);
    beginConsumerRecoveryTracking(mission);
    backgroundPort?.postMessage({type:'consumer_mission_ack',id:mission.id});
    emitRelayEvent('consumer_mission_delivered',{mission_id:mission.id});
  }catch(e){
    emitRelayEvent('consumer_mission_delivery_failed',{
      mission_id:mission.id,
      error:String(e?.message||e||'delivery_error').slice(0,240)
    });
  }finally{
    consumerMissionInFlight=null;
  }
}

function pollConsumerMission(){
  if(operatorPaused)return;
  try{backgroundPort?.postMessage({type:'consumer_mission_poll'});}catch{}
}

async function inject(text){
  assertOperatorActive();
  setText(text);
  await new Promise(r=>setTimeout(r,350));
  await send();
}

function scheduleBackgroundReconnect(){
  if(!backgroundPortUnavailableSince)backgroundPortUnavailableSince=Date.now();
  if(
    Date.now()-backgroundPortUnavailableSince>=RELAY_STALL_PATIENCE_MS &&
    !operatorPaused &&
    !backgroundRuntimeReloadRequested
  ){
    backgroundRuntimeReloadRequested=true;
    try{
      if(typeof chrome.runtime.reload==='function'){chrome.runtime.reload();return;}
    }catch{}
  }
  if(backgroundPortReconnectTimer!==null)return;
  backgroundPortReconnectTimer=setTimeout(()=>{
    backgroundPortReconnectTimer=null;
    connectBackgroundPort();
bindToolApprovalPromptDetector();
  },500);
}

/* GPT_ENGINEERING_CHAT_ROTATION_HANDLER_V1 */
function rotationLoad(){try{return JSON.parse(sessionStorage.getItem(ENGINEERING_ROTATION_SESSION_KEY)||'null');}catch{return null;}}
function rotationSave(v){try{sessionStorage.setItem(ENGINEERING_ROTATION_SESSION_KEY,JSON.stringify(v));}catch{}}
function rotationPath(){return /^\/c\/[^/?#]+/.test(location.pathname)?location.pathname:null;}
function rotationExactAnchor(title,path){return [...document.querySelectorAll('a[href]')].find(a=>{try{return new URL(a.href,location.origin).pathname===path && String(a.textContent||'').trim()===title;}catch{return false;}})||null;}
async function renameEngineeringChat(title,path){
 const until=Date.now()+45000;
 while(Date.now()<until){
  const exact=rotationExactAnchor(title,path);if(exact)return true;
  const anchor=[...document.querySelectorAll('a[href]')].find(a=>{try{return new URL(a.href,location.origin).pathname===path;}catch{return false;}});
  if(anchor){
   const row=anchor.closest('li')||anchor.parentElement?.parentElement||anchor.parentElement;
   try{row?.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));}catch{}
   await new Promise(r=>setTimeout(r,200));
   const buttons=[...(row?.querySelectorAll?.('button')||[])].filter(visibleElement);
   const menu=buttons.find(b=>/more|options|conversation/i.test(String(b.getAttribute('aria-label')||b.getAttribute('title')||'')))||buttons.at(-1);
   if(menu){
    menu.click();await new Promise(r=>setTimeout(r,250));
    const rename=[...document.querySelectorAll('[role="menuitem"],button')].find(e=>visibleElement(e)&&/^rename$/i.test(String(e.textContent||'').trim()));
    if(rename){
     rename.click();await new Promise(r=>setTimeout(r,250));
     const inputs=[...document.querySelectorAll('input')].filter(visibleElement);const input=inputs.at(-1);
     if(input){
      const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')?.set;setter?.call(input,title);input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));
      const save=[...document.querySelectorAll('button')].find(e=>visibleElement(e)&&/^(save|rename)$/i.test(String(e.textContent||'').trim()));
      if(save)save.click();else input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',bubbles:true}));
     }
    }
   }
  }
  await new Promise(r=>setTimeout(r,500));
 }
 throw new Error('engineering_chat_rename_timeout');
}
function engineeringRotationTargetValid(title,session){
 const tm=String(title||'').match(/^💻PC Engineering (\\d+)🔧$/);const sm=String(session||'').match(/^pce(\\d+)\\.1$/i);return !!tm&&!!sm&&Number(tm[1])===Number(sm[1]);
}
async function resumeEngineeringRotation(){
 const st=rotationLoad();if(!st||!engineeringRotationTargetValid(st.target_title,st.target_session)||!String(st.handoff||'').includes('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]'))return;
 if(Date.now()-Number(st.started_at||0)>180000)throw new Error('engineering_rotation_expired');
 if(st.phase==='navigate'){if(location.pathname!=='/'){location.assign('https://chatgpt.com/');return;}st.phase='handoff';rotationSave(st);}
 if(st.phase==='handoff'||st.phase==='handoff_submitting'){
  if(recentUserTurnContainsToken('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]')){st.phase='await_conversation';rotationSave(st);}
  else{
   const until=Date.now()+30000;while((operatorPaused||!findComposer())&&Date.now()<until)await new Promise(r=>setTimeout(r,250));
   const composer=findComposer();if(operatorPaused||!composer)throw new Error('engineering_rotation_composer_unavailable');
   const existing=elementText(composer).trim();if(existing && !existing.includes('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]'))throw new Error('engineering_rotation_composer_not_empty');
   if(!existing)setText(st.handoff);st.phase='handoff_submitting';rotationSave(st);await new Promise(r=>setTimeout(r,250));await send();
   if(!await waitForUserToken('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]',15000))throw new Error('engineering_rotation_handoff_unconfirmed');
   st.phase='await_conversation';rotationSave(st);
  }
 }
 if(st.phase==='await_conversation'){const until=Date.now()+30000;while(!rotationPath()&&Date.now()<until)await new Promise(r=>setTimeout(r,250));const path=rotationPath();if(!path)throw new Error('engineering_rotation_conversation_identity_timeout');st.conversation_path=path;st.phase='rename';rotationSave(st);}
 if(st.phase==='rename'){const path=st.conversation_path||rotationPath();if(!path)throw new Error('engineering_rotation_identity_missing');await renameEngineeringChat(st.target_title,path);if(!rotationExactAnchor(st.target_title,path))throw new Error('engineering_rotation_title_verify_failed');st.phase='verified';st.verified_at=Date.now();rotationSave(st);emitRelayEvent('chat_rotation_verified',{source_packet_id:st.source_packet_id,title:st.target_title,session:st.target_session,conversation_key:location.origin+path});}
}
function beginEngineeringRotation(m){
 if(!engineeringRotationTargetValid(m?.target_title,m?.target_session)||!String(m?.handoff||'').includes('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]'))return;
 const st={phase:'navigate',source_packet_id:m.source_packet_id||null,target_title:m.target_title,target_session:m.target_session,handoff:m.handoff,started_at:Date.now()};rotationSave(st);emitRelayEvent('chat_rotation_started',{source_packet_id:st.source_packet_id,title:st.target_title,session:st.target_session});location.assign('https://chatgpt.com/');
}

function connectBackgroundPort(){
  if(backgroundPort)return backgroundPort;
  try{
    const port=chrome.runtime.connect({name:'gpt-windows-relay-content'});
    backgroundPort=port;
    backgroundPortUnavailableSince=0;
    backgroundRuntimeReloadRequested=false;

    port.onMessage.addListener(m=>{
      if(m?.type==='operator_control_state'){applyOperatorControlState(m);return;}
      if(m?.type==='relay_scanner_recover'){
        recoverScannerForPacket(m);
        return;
      }
      if(m?.type==='relay_chat_rotation_start'){beginEngineeringRotation(m);return;}
      if(m?.type==='consumer_mission'){
        if(operatorPaused)return;
        deliverConsumerMission(m.mission).catch(()=>{});
        return;
      }
      if(m?.type==='relay_handoff_scroll'){
        beginRelayHandoffScroll();
        return;
      }
      if(m?.type!=='relay_action_result' && m?.type!=='relay_packet_status_result')return;
      if(typeof m.request_id!=='string')return;
      const pending=backgroundPending.get(m.request_id);
      if(!pending)return;
      backgroundPending.delete(m.request_id);
      clearTimeout(pending.timer);
      pending.resolve(m.reply);
    });

    port.onDisconnect.addListener(()=>{
      if(backgroundPort===port)backgroundPort=null;
      if(!backgroundPortUnavailableSince)backgroundPortUnavailableSince=Date.now();
      for(const [requestId,pending] of backgroundPending){
        backgroundPending.delete(requestId);
        clearTimeout(pending.timer);
        pending.reject(new Error('background_port_disconnected'));
      }
      scheduleBackgroundReconnect();
    });

    return port;
  }catch{
    backgroundPort=null;
    if(!backgroundPortUnavailableSince)backgroundPortUnavailableSince=Date.now();
    scheduleBackgroundReconnect();
    return null;
  }
}

function relayConversationKey(){
  try{
    const u=new URL(location.href);
    return u.origin+u.pathname.replace(/\/+$/,'');
  }catch{
    return String(location.origin||'')+String(location.pathname||'');
  }
}

/* GPT_RELAY_CONVERSATION_OWNER_V1 */
function backgroundAction(packet){
  if(operatorPaused)return Promise.reject(new Error('operator_paused'));
  return new Promise((resolve,reject)=>{
    const port=connectBackgroundPort();
    if(!port){
      reject(new Error('background_port_unavailable'));
      return;
    }

    const requestId='action-'+Date.now().toString(36)+'-'+(++backgroundRequestSeq).toString(36);
    const timer=setTimeout(()=>{
      backgroundPending.delete(requestId);
      reject(new Error('background_action_timeout'));
    },330000);

    backgroundPending.set(requestId,{resolve,reject,timer});
    try{
      port.postMessage({
        type:'relay_action',
        request_id:requestId,
        packet,
        conversation_key:relayConversationKey(),
        conversation_href:location.href
      });
    }catch(e){
      backgroundPending.delete(requestId);
      clearTimeout(timer);
      if(backgroundPort===port)backgroundPort=null;
      scheduleBackgroundReconnect();
      reject(e);
    }
  });
}

function backgroundPacketStatus(packetId){
  return new Promise((resolve,reject)=>{
    const port=connectBackgroundPort();
    if(!port){reject(new Error('background_port_unavailable'));return;}
    const requestId='packet-status-'+Date.now().toString(36)+'-'+(++backgroundRequestSeq).toString(36);
    const timer=setTimeout(()=>{
      backgroundPending.delete(requestId);
      reject(new Error('background_packet_status_timeout'));
    },5000);
    backgroundPending.set(requestId,{resolve,reject,timer});
    try{port.postMessage({type:'relay_packet_status',request_id:requestId,packet_id:packetId});}
    catch(e){backgroundPending.delete(requestId);clearTimeout(timer);reject(e);}
  }).then(reply=>{
    if(!reply?.ok)throw new Error(reply?.error||'background_packet_status_failed');
    return reply.data;
  });
}

function queueDeferredAction(p,reason,ownerId=null){
  if(!p?.id || attempted.has(p.id) || inflight.has(p.id))return;
  if(userTurnContainsPacketId(p.id)){
    rememberAttempted(p.id);
    return;
  }
  if(!deferredActions.has(p.id) && deferredActions.size>=MAX_DEFERRED_ACTIONS){
    const oldest=deferredActions.keys().next().value;
    if(oldest){
      deferredActions.delete(oldest);
      emitRelayEvent('relay_action_deferred_dropped',{
        packet_id:oldest,
        reason:'queue_capacity',
        queue_size:deferredActions.size
      });
    }
  }
  for(const oldId of [...deferredActions.keys()]){
    if(oldId===p.id)continue;
    deferredActions.delete(oldId);
    emitRelayEvent('relay_deferred_superseded_by_newer',{packet_id:oldId,newer_packet_id:p.id});
  }
  deferredActions.set(p.id,p);
  emitRelayEvent('relay_action_queued',{
    packet_id:p.id,
    reason,
    owner_packet_id:ownerId||null,
    queue_size:deferredActions.size
  });
}

function scheduleDeferredDrain(delay=100){
  if(operatorPaused)return;
  if(deferredDrainTimer!==null)return;
  deferredDrainTimer=setTimeout(()=>{
    deferredDrainTimer=null;
    drainDeferredActions();
  },delay);
}

function drainDeferredActions(){
  if(operatorPaused)return;
  if(activeRelayOperationId || draftRecoveryInFlight)return;
  if(relayDraftFromComposer()){
    scheduleDraftRecovery(0);
    return;
  }
  for(const [id,p] of deferredActions){
    deferredActions.delete(id);
    if(attempted.has(id) || inflight.has(id) || userTurnContainsPacketId(id)){
      if(userTurnContainsPacketId(id))rememberAttempted(id);
      continue;
    }
    emitRelayEvent('relay_action_dequeued',{
      packet_id:id,
      queue_size:deferredActions.size
    });
    run(p).catch(()=>{});
    return;
  }
}

function forgetAttempted(id){
  if(!attempted.delete(id))return false;
  for(let i=attemptedOrder.length-1;i>=0;i--){
    if(attemptedOrder[i]===id)attemptedOrder.splice(i,1);
  }
  persistAttemptedHistory();
  return true;
}

async function run(p){
  if(operatorPaused)return;
  if(inflight.has(p.id))return;
  if(attempted.has(p.id)){
    // Attempt history is advisory only: a prior false UI match must not turn
    // into a durable non-execution. The backend is the source of truth.
    let durable=null;
    try{durable=await backgroundPacketStatus(p.id);}catch{}
    if(durable?.state==='EXECUTION_CONFIRMED' || durable?.state==='EXECUTING')return;
    if(forgetAttempted(p.id)){
      emitRelayEvent('relay_attempt_history_rearmed',{
        packet_id:p.id,
        durable_state:durable?.state||'UNKNOWN'
      });
    }
  }
  if(userTurnContainsPacketId(p.id)){
    // Visible text is only a candidate receipt.  Before suppressing an
    // action, obtain packet-specific durable identity from the backend.
    // An absent durable record means this is quoted/stale UI text, not proof
    // that the command ran, and execution remains eligible.
    let durable=null;
    try{durable=await backgroundPacketStatus(p.id);}catch{}
    if(durable?.state==='EXECUTION_CONFIRMED' || durable?.state==='EXECUTING'){
      rememberAttempted(p.id);
      emitRelayEvent('relay_result_replay_suppressed',{
        packet_id:p.id,
        reason:'durable_execution_and_exact_user_result',
        durable_state:durable.state,
        durable_identity:durable.identity||null
      });
      return;
    }
    emitRelayEvent('relay_result_visibility_untrusted',{
      packet_id:p.id,
      durable_state:durable?.state||'UNKNOWN',
      action:'execute_exact_packet'
    });
  }

  // GPT_WINDOWS_NEWER_INSTRUCTION_SUPERSEDES_STALE_V1
  if(activeRelayOperationId && activeRelayOperationId!==p.id && !inflight.has(activeRelayOperationId) && !draftRecoveryInFlight && !relayDraftFromComposer()){
    const stale=activeRelayOperationId; activeRelayOperationId=null; activeRelayOperationClaimedAt=0; deferredActions.delete(stale);
    emitRelayEvent('relay_stale_owner_superseded_by_newer',{packet_id:stale,newer_packet_id:p.id});
  }
  const draft=relayDraftFromComposer();
  if(draft && draft.id!==p.id){
    queueDeferredAction(p,'existing_draft',draft.id);
    emitRelayEvent('relay_action_deferred_for_existing_draft',{
      packet_id:p.id,
      draft_packet_id:draft.id
    });
    scheduleDraftRecovery(0);
    return;
  }

  if(activeRelayOperationId && activeRelayOperationId!==p.id){
    queueDeferredAction(p,'active_operation',activeRelayOperationId);
    emitRelayEvent('relay_action_deferred_for_active_operation',{
      packet_id:p.id,
      active_packet_id:activeRelayOperationId
    });
    return;
  }

  if(Date.now()<relayDisarmedUntil)return;
  activeRelayOperationId=p.id;
  activeRelayOperationClaimedAt=Date.now();
  inflight.add(p.id);
  emitRelayEvent('relay_action_execution_requested',{
    packet_id:p.id,
    source:'content_scanner'
  });

  let r;
  try{
    r=await backgroundAction(p.packet);
  }catch{
    inflight.delete(p.id);
    if(activeRelayOperationId===p.id)activeRelayOperationId=null;
    relayDisarmedUntil=Date.now()+1000;
    scheduleBackgroundReconnect();
    setTimeout(scheduleWatchedInspect,1200);
    return;
  }

  if(!r?.ok){
    inflight.delete(p.id);
    if(activeRelayOperationId===p.id)activeRelayOperationId=null;
    if(r?.error==='relay_disarmed'){
      relayDisarmedUntil=Date.now()+15000;
      return;
    }
    if(r?.error==='duplicate_suppressed'){
      rememberAttempted(p.id);
      return;
    }
    if(r?.error==='late_packet_suppressed'){
      rememberAttempted(p.id);
      emitRelayEvent('relay_late_packet_suppressed',{
        packet_id:p.id,
        reason:'newer_operation_cursor'
      });
      scheduleDeferredDrain(100);
      return;
    }
    rememberAttempted(p.id);
    return inject(
`[GPT_WINDOWS_FEEDBACK]
${JSON.stringify({
  version:1,
  type:'RELAY_DIAGNOSTIC',
  source:'windows_browser_bridge',
  state:'ACTION_FAILED',
  packet_id:p.id,
  detail:r?.error||'unknown_error',
  recommended_action:'Before retry: read roadmap/facts/incidents/log; prove net-new progress; log this failure; update development log; preserve rollback; check PCE8/PCE9 budget; then diagnose and reissue with a new unique id.'
})}
[/GPT_WINDOWS_FEEDBACK]`);
  }

  relayDisarmedUntil=0;
  emitRelayEvent('relay_result_received',{
    packet_id:p.id,
    chars:String(r.result||'').length
  });

  rememberAttempted(p.id);
  if(outboundOwner==='windows'){
    inflight.delete(p.id);
    if(activeRelayOperationId===p.id)activeRelayOperationId=null;
    emitRelayEvent('relay_result_delivery_delegated_windows',{packet_id:p.id});
    scheduleDeferredDrain(100);
    return;
  }
  try{
    const deliveryState=await injectConfirmed(r.result,p.id,r.attachments||[]);
    inflight.delete(p.id);
    if(activeRelayOperationId===p.id)activeRelayOperationId=null;
    if(deliveryState==='accepted'){
      emitRelayEvent('relay_result_waiting_for_gpt_turn_end',{
        packet_id:p.id,
        resend:false,
        reexecution:false
      });
      trackSubmittedResult(p.id);
    }else{
      emitRelayEvent('relay_result_delivery_complete',{packet_id:p.id});
      try{backgroundPort?.postMessage({type:'relay_operation_delivered',id:p.id});}catch{}
      let recoveryCtx=consumerRecoveryContext();
      if(recoveryCtx?.probe_id===p.id){
        recoveryCtx.state='probe_proven_resume_expected';recoveryCtx.probe_proven_at=Date.now();saveConsumerRecoveryContext(recoveryCtx);
        emitRelayEvent('consumer_relay_recovery_probe_proven',{mission_id:recoveryCtx.mission_id,probe_id:p.id});
      }else if(recoveryCtx?.action_seen){
        recoveryCtx.state='active';recoveryCtx.last_result_packet_id=p.id;recoveryCtx.last_result_at=Date.now();saveConsumerRecoveryContext(recoveryCtx);
      }
    }
    cleanupRelayAttachments(r.attachments||[]);
    relayAttachmentPackets.delete(p.id);
    scheduleDeferredDrain(100);
  }catch(e){
    inflight.delete(p.id);
    const ownedDraft=relayDraftFromComposer();
    emitRelayEvent('relay_result_delivery_retry_deferred',{
      packet_id:p.id,
      error:String(e?.message||e||'delivery_error').slice(0,240),
      draft_present:ownedDraft?.id===p.id
    });
    if(ownedDraft?.id===p.id){
      claimActiveRelayOperation(p.id);
      scheduleDraftRecovery(5000);
    }else{
      if(activeRelayOperationId===p.id)activeRelayOperationId=null;
      scheduleDeferredDrain(100);
      setTimeout(scheduleWatchedInspect,30000);
    }
  }
}

/* GPT_WINDOWS_DISCOVERY_SETTLE_REACQUIRE_V2 */
function recoverDiscoveredPacket(p,reason){
  if(!p?.id || attempted.has(p.id) || inflight.has(p.id))return;
  emitRelayEvent('relay_packet_settle_reacquire',{packet_id:p.id,reason});
  setTimeout(()=>recoverLatestAssistant(),0);
}

function recoverScannerForPacket(request){
  const packetId=typeof request?.packet_id==='string'?request.packet_id:'';
  const expectedConversation=typeof request?.conversation_key==='string'?request.conversation_key:'';
  if(!packetId || operatorPaused || expectedConversation!==relayConversationKey())return;
  let target=null;
  for(const unit of assistantUnits().reverse()){
    const parsed=extractUnit(unit);
    if(parsed?.id===packetId){target={unit,parsed};break;}
  }
  if(!target || attempted.has(packetId) || inflight.has(packetId)){
    emitRelayEvent('relay_scanner_recovery_noop',{
      packet_id:packetId,
      reason:target?'already_terminal_or_inflight':'packet_not_bound_to_current_conversation'
    });
    return;
  }
  const prior=pending.get(packetId);
  if(prior?.timer)clearTimeout(prior.timer);
  pending.delete(packetId);
  bindConversationRoot();
  bindAssistantUnit(target.unit);
  emitRelayEvent('relay_scanner_recovery_reinspect',{
    packet_id:packetId,
    source:String(request?.reason||'extension_supervisor'),
    conversation_key:expectedConversation
  });
  inspectUnit(target.unit);
}

function inspectUnit(unit){
  if(!unit?.isConnected || !isAssistantUnit(unit))return;

  // Recovery advice is not executable relay code. Observe it independently so
  // a missing supervisor claimant cannot disappear as generic NO_ACTION_PACKET.
  const recoveryAdvice=classifyRecoveryAdvice(unit.textContent||'');
  if(recoveryAdvice){
    const adviceSignature=hash(JSON.stringify(recoveryAdvice));
    if(adviceSignature!==lastRecoveryAdviceSignature){
      lastRecoveryAdviceSignature=adviceSignature;
      emitRelayEvent(
        recoveryAdvice.kind==='RECOVERY_ADVICE'?'gpt_recovery_advice_observed':'gpt_recovery_advice_invalid',
        {incident_id:recoveryAdvice.incident_id||null,valid:recoveryAdvice.kind==='RECOVERY_ADVICE',
         reason:recoveryAdvice.reason||null,repairs:recoveryAdvice.repairs||[]}
      );
    }
  }

  // textContent avoids forced layout/reflow while ChatGPT streams.
  const p=extractUnit(unit);
  scheduleConsumerAssistantClassification(unit);
  if(!p)return;
  noteTrackedRelayAction(unit,p);
  if(attempted.has(p.id) || inflight.has(p.id))return;

  const sig=hash(p.packet);
  const prior=pending.get(p.id);
  const now=Date.now();
  if(prior?.sig===sig && prior?.unit===unit){
    const age=Math.max(0,now-Number(prior.started_at||0));
    if(age<DISCOVERY_SETTLE_LEASE_MS)return;
    if(prior?.timer)clearTimeout(prior.timer);
    pending.delete(p.id);
    emitRelayEvent('relay_packet_settle_stale_rearmed',{
      packet_id:p.id,
      age_ms:age,
      lease_ms:DISCOVERY_SETTLE_LEASE_MS
    });
  }else if(prior?.timer){
    clearTimeout(prior.timer);
  }

  emitRelayEvent('relay_packet_discovered',{
    packet_id:p.id,
    source:unit===watchedUnit?'watched_turn':'recovery_scan'
  });

  const timer=setTimeout(()=>{
    const current=pending.get(p.id);
    if(!current || current.timer!==timer)return;
    pending.delete(p.id);

    if(!unit.isConnected){
      recoverDiscoveredPacket(p,'unit_disconnected');
      return;
    }
    const settled=extractUnit(unit);
    if(!settled || settled.id!==p.id || hash(settled.packet)!==sig){
      recoverDiscoveredPacket(p,'packet_changed_during_settle');
      return;
    }
    run(settled).catch(()=>{});
  },DISCOVERY_SETTLE_MS);

  pending.set(p.id,{sig,unit,timer,started_at:now});
}

function latestAssistantPair(){
  // One startup/recovery query. Steady state does not rescan the conversation.
  const root=document.querySelector('main') || document;
  const nodes=root.querySelectorAll(ASSISTANT_SELECTOR);
  let latest=null, previous=null;
  for(let i=nodes.length-1;i>=0;i--){
    if(!isAssistantUnit(nodes[i]))continue;
    if(!latest)latest=nodes[i];
    else{previous=nodes[i];break;}
  }
  return {latest,previous};
}

function newestRelayCommandUnit(){
  // Recovery-only scan: find the newest assistant turn that contains a complete,
  // valid Windows relay packet. This is never called from mutation callbacks.
  const root=document.querySelector('main') || document;
  const nodes=root.querySelectorAll(ASSISTANT_SELECTOR);
  for(let i=nodes.length-1;i>=0;i--){
    const unit=nodes[i];
    if(!isAssistantUnit(unit))continue;
    if(extractUnit(unit))return unit;
  }
  return null;
}

function recoveryConversationKey(){
  const m=String(location.pathname||"").match(/^\/c\/[^/?#]+/);
  return m?(location.origin+m[0]):null;
}

function persistRecoveryPacketWatch(){
  try{
    if(!recoveryPacketId){
      sessionStorage.removeItem(RECOVERY_WATCH_SESSION_KEY);
      return;
    }
    sessionStorage.setItem(RECOVERY_WATCH_SESSION_KEY,JSON.stringify({
      id:recoveryPacketId,
      conversation_key:recoveryConversationKey(),
      first_seen_at:recoveryPacketFirstSeenAt,
      last_refresh_at:recoveryPacketLastRefreshAt
    }));
  }catch{}
}

function hydrateRecoveryPacketWatch(){
  try{
    const raw=JSON.parse(sessionStorage.getItem(RECOVERY_WATCH_SESSION_KEY)||"null");
    if(!raw||typeof raw.id!=="string"||!raw.id)return;
    const first=Number(raw.first_seen_at||0);
    const currentKey=recoveryConversationKey();
    const storedKey=typeof raw.conversation_key==="string"?raw.conversation_key:"";
    const age=first>0?Math.max(0,Date.now()-first):Number.POSITIVE_INFINITY;
    if(!currentKey||!storedKey||storedKey!==currentKey||age>RECOVERY_WATCH_MAX_AGE_MS){
      sessionStorage.removeItem(RECOVERY_WATCH_SESSION_KEY);
      emitRelayEvent("relay_recovery_obligation_discarded",{packet_id:raw.id,age_ms:Number.isFinite(age)?age:null});
      return;
    }
    recoveryPacketId=raw.id;
    recoveryPacketFirstSeenAt=first;
    recoveryPacketLastRefreshAt=Number(raw.last_refresh_at||0)||0;
    emitRelayEvent("relay_recovery_obligation_restored",{packet_id:recoveryPacketId,conversation_key:currentKey});
  }catch{}
}

function armRecoveryPacketWatch(packetId,now=Date.now()){
  if(!recoveryConversationKey()){resetRecoveryPacketWatch();return;}
  if(recoveryPacketId===packetId && recoveryPacketFirstSeenAt)return;
  recoveryPacketId=packetId;
  recoveryPacketFirstSeenAt=now;
  recoveryPacketLastRefreshAt=0;
  recoveryRefreshScheduled=false;
  persistRecoveryPacketWatch();
  emitRelayEvent('relay_recovery_packet_seen',{
    packet_id:packetId,
    source:'recovery_scan'
  });
}

function resetRecoveryPacketWatch(packetId=null){
  if(packetId && recoveryPacketId!==packetId)return;
  recoveryPacketId=null;
  recoveryPacketFirstSeenAt=0;
  recoveryPacketLastRefreshAt=0;
  recoveryRefreshScheduled=false;
  persistRecoveryPacketWatch();
}

function expireStaleRelayOperationOwner(now=Date.now()){
  const owner=activeRelayOperationId;
  if(!owner || inflight.has(owner) || draftRecoveryInFlight)return false;
  if(!activeRelayOperationClaimedAt)activeRelayOperationClaimedAt=now;
  if(now-activeRelayOperationClaimedAt<RELAY_STALL_PATIENCE_MS)return false;

  const exactVisible=userTurnContainsPacketId(owner);
  if(exactVisible)rememberAttempted(owner);
  const draft=relayDraftFromComposer();
  const clearedDraft=draft?.id===owner ? clearOwnedRelayDraft(owner) : false;
  activeRelayOperationId=null;
  activeRelayOperationClaimedAt=0;
  emitRelayEvent('relay_operation_owner_released',{
    packet_id:owner,
    reason:exactVisible?'stale_owner_lease_expired_exact_result_visible':'stale_owner_lease_expired_for_exact_replay',
    cleared_draft:clearedDraft
  });
  scheduleDeferredDrain(0);
  return true;
}

function maybeScheduleRecoveryRefresh(packetId,now=Date.now()){
  if(operatorPaused)return;
  if(!packetId || !recoveryPacketFirstSeenAt)return;
  const currentKey=recoveryConversationKey();
  if(!currentKey){resetRecoveryPacketWatch(packetId);return;}
  const stalledFor=Math.max(0,now-recoveryPacketFirstSeenAt);
  if(stalledFor>RECOVERY_WATCH_MAX_AGE_MS){emitRelayEvent("relay_recovery_obligation_expired",{packet_id:packetId,age_ms:stalledFor,conversation_key:currentKey});resetRecoveryPacketWatch(packetId);return;}
  if(stalledFor<RELAY_STALL_PATIENCE_MS || recoveryRefreshScheduled)return;
  if(
    recoveryPacketLastRefreshAt &&
    now-recoveryPacketLastRefreshAt<RELAY_STALL_PATIENCE_MS
  ) return;
  if(inflight.size>0 || activeRelayOperationId || draftRecoveryInFlight)return;

  recoveryRefreshScheduled=true;
  recoveryPacketLastRefreshAt=now;
  persistRecoveryPacketWatch();
  emitRelayEvent('relay_scanner_stalled',{
    packet_id:packetId,
    stalled_ms:stalledFor,
    recovery:'page_refresh_after_durable_obligation'
  });
  recoveryRefreshTimer=setTimeout(()=>{
    recoveryRefreshTimer=null;
    if(operatorPaused)return;
    recoveryRefreshScheduled=false;
    if(
      recoveryPacketId!==packetId ||
      attempted.has(packetId) || userTurnContainsPacketId(packetId) ||
      inflight.size>0 || activeRelayOperationId || draftRecoveryInFlight
    ){
      if(attempted.has(packetId) || userTurnContainsPacketId(packetId)){
        resetRecoveryPacketWatch(packetId);
      }
      return;
    }
    emitRelayEvent('relay_page_refresh_requested',{
      packet_id:packetId,
      stalled_ms:Date.now()-recoveryPacketFirstSeenAt,
      source:'durable_recovery_obligation'
    });
    location.reload();
  },RELAY_REFRESH_GRACE_MS);
}

function forceRecoveryPacketInspect(){
  if(operatorPaused)return;
  const now=Date.now();
  expireStaleRelayOperationOwner(now);
  const unit=newestRelayCommandUnit();
  if(!unit){
    // Absence from the currently materialized DOM is not completion. Keep a
    // previously observed obligation alive across virtualization/remount.
    if(recoveryPacketId){
      if(attempted.has(recoveryPacketId) || userTurnContainsPacketId(recoveryPacketId)){
        resetRecoveryPacketWatch(recoveryPacketId);
      }else{
        maybeScheduleRecoveryRefresh(recoveryPacketId,now);
      }
    }
    return;
  }

  const p=extractUnit(unit);
  if(!p)return;
  if(attempted.has(p.id) || userTurnContainsPacketId(p.id)){
    resetRecoveryPacketWatch(p.id);
    return;
  }

  armRecoveryPacketWatch(p.id,now);

  // A recovery pass must actually reinspect the valid command. Merely binding
  // or scrolling to a turn is not proof that the packet was consumed.
  if(!inflight.has(p.id))inspectUnit(unit);
  maybeScheduleRecoveryRefresh(p.id,now);
}

function scrollToNewestRelayCommandOnce(){
  if(recoveryScrollDone)return;
  const unit=newestRelayCommandUnit();
  if(!unit)return;
  recoveryScrollDone=true;
  try{
    unit.scrollIntoView({block:'center',inline:'nearest',behavior:'auto'});
  }catch{
    const root=findScrollRoot(unit);
    if(root)root.scrollTop=Math.max(0,unit.offsetTop-root.clientHeight/2);
  }
}


function assistantUnitFromNode(node){
  const el=node instanceof Element ? node : node?.parentElement;
  if(!el)return null;
  if(el.matches?.(ASSISTANT_SELECTOR) && isAssistantUnit(el))return el;
  const owner=el.closest?.(ASSISTANT_SELECTOR);
  if(owner && isAssistantUnit(owner))return owner;
  const nested=el.querySelector?.(ASSISTANT_SELECTOR);
  return nested && isAssistantUnit(nested) ? nested : null;
}

function bindFromMutations(mutations){
  scheduleExternalCollapseCheck();
  scheduleEngineeringCollapseCheck();
  let candidate=null;
  for(const m of mutations){
    if(watchedUnit && (m.target===watchedUnit || watchedUnit.contains(m.target)))continue;
    for(const node of m.addedNodes||[]){
      const unit=assistantUnitFromNode(node);
      if(unit)candidate=unit;
    }
    if(!candidate){
      const unit=assistantUnitFromNode(m.target);
      if(unit && unit!==watchedUnit)candidate=unit;
    }
  }
  if(candidate)bindAssistantUnit(candidate);
}

function bindConversationRoot(){
  // Observe the stable ChatGPT main region rather than a computed conversation
  // subtree that may be replaced or too narrow as the UI virtualizes turns.
  const next=document.querySelector('main');
  if(!next || next===conversationRoot)return;
  conversationObserver?.disconnect();
  conversationRoot=next;
  conversationObserver=new MutationObserver(bindFromMutations);
  conversationObserver.observe(conversationRoot,{childList:true,subtree:true});
}

function scheduleWatchedInspect(){
  if(operatorPaused)return;
  if(watchedInspectTimer!==null)return;
  watchedInspectTimer=setTimeout(()=>{
    watchedInspectTimer=null;
    if(watchedUnit?.isConnected)inspectUnit(watchedUnit);
  },350);
}

function findScrollRoot(node){
  for(let p=node?.parentElement;p;p=p.parentElement){
    const style=getComputedStyle(p);
    if(/^(auto|scroll|overlay)$/.test(style.overflowY) && p.scrollHeight>p.clientHeight+8){
      return p;
    }
  }
  return document.scrollingElement || document.documentElement;
}

function nearBottom(root){
  if(!root)return true;
  return (root.scrollHeight-root.scrollTop-root.clientHeight)<=320;
}

function onScroll(){
  if(Date.now()<relayHandoffScrollUntil){
    followBottom=true;
    return;
  }
  followBottom=nearBottom(scrollRoot);
}

function bindScrollRoot(unit){
  const next=findScrollRoot(unit);
  if(next===scrollRoot)return;
  scrollRoot?.removeEventListener?.('scroll',onScroll);
  scrollRoot=next;
  scrollRoot?.addEventListener?.('scroll',onScroll,{passive:true});
  followBottom=nearBottom(scrollRoot);
}

function scheduleAutoScroll(){
  if(operatorPaused)return;
  if(!scrollRoot || (!followBottom && Date.now()>=relayHandoffScrollUntil) || scrollTimer!==null)return;
  scrollTimer=setTimeout(()=>{
    scrollTimer=null;
    if(!scrollRoot || !followBottom)return;
    scrollRoot.scrollTop=scrollRoot.scrollHeight;
  },1200);
}

function bindAssistantUnit(latest){
  if(operatorPaused)return;
  if(!latest)return;
  if(latest===watchedUnit){
    scheduleWatchedInspect();
    return;
  }
  watchedObserver?.disconnect();
  watchedUnit=latest;
  bindScrollRoot(watchedUnit);
  watchedObserver=new MutationObserver(()=>{
    scheduleWatchedInspect();
    scheduleAutoScroll();
  });
  watchedObserver.observe(watchedUnit,{
    subtree:true,
    childList:true,
    characterData:true
  });
  scheduleWatchedInspect();
  scheduleAutoScroll();
}

function recoverLatestAssistant(){
  if(operatorPaused)return;
  bindConversationRoot();
  scheduleEngineeringCollapseCheck();
  hydrateAttemptedFromConversation();
  reconcileSubmittedResults();
  if(relayDraftFromComposer()){
    scheduleDraftRecovery(0);
  }

  if(!scannerSnapshotSent){
    scannerSnapshotSent=true;
    try{
      const candidates=[...document.querySelectorAll(ASSISTANT_SELECTOR)];
      const valid=candidates.filter(isAssistantUnit);
      backgroundPort?.postMessage({
        type:'relay_event',
        event:'scanner_snapshot',
        detail:{
          main_present:!!document.querySelector('main'),
          candidate_count:candidates.length,
          assistant_count:valid.length
        }
      });
    }catch{}
  }

  const {latest}=latestAssistantPair();
  if(latest)bindAssistantUnit(latest);
  forceRecoveryPacketInspect();
  scrollToNewestRelayCommandOnce();
}

chrome.runtime.onMessage.addListener((m,_s,reply)=>{
  if(m?.type==='content_diagnostics'){
    const units=assistantUnits();
    let newestPacketId=null;
    for(let i=units.length-1;i>=0;i--){
      const p=extractUnit(units[i]);
      if(p){newestPacketId=p.id;break;}
    }
    reply({
      ok:true,
      content_script_loaded:true,
      url:location.href,
      assistant_units:units.length,
      composer_found:!!findComposer(),
      newest_packet_id:newestPacketId,
      scanner:'event-driven-v11',
      watched_unit:!!watchedUnit?.isConnected,
      conversation_root:!!conversationRoot?.isConnected,
      approval_detector_bound:!!approvalPromptObserver,
      ui_error_detector_bound:!!uiErrorObserver,
      pending_packets:pending.size,
      inflight_packets:inflight.size
    });
  }
});

/* GPT_CHATGPT_VISIBLE_ERROR_DETECTOR_V1 */
function chatGPTUiErrorFromText(raw){
  const text=String(raw||'').trim().replace(/\s+/g,' ');
  if(!text)return null;
  if(/error in input stream/i.test(text))return {kind:'input_stream_error',text};
  if(/something went wrong/i.test(text))return {kind:'something_went_wrong',text};
  if(/network error|connection (?:was )?(?:interrupted|lost)|failed to (?:load|generate)/i.test(text))return {kind:'network_or_generation_error',text};
  return null;
}

function visibleUiElement(node){
  try{
    if(!node?.isConnected)return false;
    const style=getComputedStyle(node);
    if(style.display==='none' || style.visibility==='hidden')return false;
    return node.getClientRects().length>0;
  }catch{return false;}
}

function inspectChatGPTUiError(){
  let found=null;
  for(const alert of document.querySelectorAll('[role="alert"],[role="status"],[data-testid*="error"]')){
    if(!visibleUiElement(alert))continue;
    const parsed=chatGPTUiErrorFromText(alert.textContent);
    if(parsed){found={...parsed,retry_available:false};break;}
  }
  if(!found){
    for(const button of document.querySelectorAll('button,[role="button"]')){
      if(!visibleUiElement(button))continue;
      const label=String(button.getAttribute?.('aria-label')||button.textContent||'').trim().replace(/\s+/g,' ');
      if(!/^(retry|try again|reload)$/i.test(label))continue;
      let node=button;
      for(let depth=0;depth<8 && node;depth++,node=node.parentElement){
        const parsed=chatGPTUiErrorFromText(node.textContent);
        if(parsed && parsed.text.length<=1600){
          found={...parsed,retry_available:true,retry_label:label};
          break;
        }
      }
      if(found)break;
    }
  }

  const now=Date.now();
  if(found){
    const signature=found.kind+'|'+found.text.slice(0,220);
    if(signature!==activeUiErrorSignature || now-lastUiErrorAt>=10000){
      activeUiErrorSignature=signature;
      lastUiErrorAt=now;
      emitRelayEvent('chatgpt_ui_error_detected',found);
    }
    return;
  }
  if(activeUiErrorSignature){
    const previous=activeUiErrorSignature;
    activeUiErrorSignature='';
    lastUiErrorAt=now;
    emitRelayEvent('chatgpt_ui_error_cleared',{previous_signature:previous});
  }
}

function scheduleChatGPTUiErrorInspect(){
  if(operatorPaused)return;
  if(uiErrorInspectTimer!==null)return;
  uiErrorInspectTimer=setTimeout(()=>{
    uiErrorInspectTimer=null;
    inspectChatGPTUiError();
  },200);
}

function bindChatGPTUiErrorDetector(){
  if(operatorPaused)return;
  if(!document.body){setTimeout(bindChatGPTUiErrorDetector,250);return;}
  uiErrorObserver?.disconnect();
  uiErrorObserver=null;
  scheduleChatGPTUiErrorInspect();
  if(uiErrorInspectInterval===null)uiErrorInspectInterval=setInterval(scheduleChatGPTUiErrorInspect,2000);
}

/* GPT_CHATGPT_TOOL_APPROVAL_PROMPT_DETECTOR_V1 */
function scheduleToolApprovalPromptInspect(){
  if(operatorPaused)return;
  if(approvalInspectTimer!==null)return;
  approvalInspectTimer=setTimeout(()=>{
    approvalInspectTimer=null;
    const candidates=[];
    for(const button of document.querySelectorAll('button,[role="button"]')){
      const label=String(button.getAttribute?.('aria-label')||button.textContent||'').trim().replace(/\s+/g,' ');
      if(/^(allow|allow once|always allow|approve|approve once)$/i.test(label))candidates.push({button,label});
    }
    for(const {button,label} of candidates){
      let surface=button.closest?.('[role="dialog"],[role="alertdialog"],[data-testid*="approval"],[data-testid*="tool"],article,section') || null;
      if(!surface){
        let node=button;
        for(let depth=0;depth<8 && node;depth++,node=node.parentElement){
          const candidateText=String(node.textContent||'').trim().replace(/\s+/g,' ');
          if(candidateText.length<=2000 && /(allow chatgpt to use|github|google drive|tool|permission|approval|connector)/i.test(candidateText)){
            surface=node;break;
          }
        }
      }
      const text=String(surface?.textContent||'').trim().replace(/\s+/g,' ');
      if(!/(github|google drive|tool|action|permission|approval|connector|app)/i.test(text))continue;
      const provider=/github/i.test(text)?'GitHub':(/google\s*drive/i.test(text)?'Google Drive':'unknown app');
      const labels=[...new Set(candidates.map(x=>x.label))].sort();
      const signature=provider+'|'+labels.join('|')+'|'+text.slice(0,180);
      const now=Date.now();
      if(signature===lastApprovalSignature && now-lastApprovalAt<5000)return;
      lastApprovalSignature=signature;lastApprovalAt=now;
      emitRelayEvent('chatgpt_tool_approval_prompt_detected',{
        provider,
        buttons:labels,
        persistent_option:labels.some(x=>/^always allow$/i.test(x))
      });

      /* GPT_CHATGPT_GITHUB_APPROVAL_AUTOCLICK_V1
         Director-preauthorized narrow policy: only the exact GitHub approval card,
         only with all three expected controls, only while its conversation scroll
         root is at bottom, and only the persistent "Always allow" choice. */
      const surfaceButtons=[...(surface?.querySelectorAll?.('button,[role="button"]')||[])].map(b=>({
        button:b,
        label:String(b.getAttribute?.('aria-label')||b.textContent||'').trim().replace(/\s+/g,' ')
      }));
      const surfaceLabels=[...new Set(surfaceButtons.map(x=>x.label))];
      const alwaysAllow=surfaceButtons.find(x=>/^always allow$/i.test(x.label))?.button || null;
      const exactGitHubCard=provider==='GitHub' &&
        /allow chatgpt to use github\?/i.test(text) &&
        surfaceLabels.some(x=>/^always allow$/i.test(x)) &&
        surfaceLabels.some(x=>/^deny$/i.test(x)) &&
        surfaceLabels.some(x=>/^allow once$/i.test(x));
      const approvalScrollRoot=surface ? findScrollRoot(surface) : null;
      const approvalAtBottom=!!approvalScrollRoot && nearBottom(approvalScrollRoot);
      const rect=alwaysAllow?.getBoundingClientRect?.();
      const style=alwaysAllow ? getComputedStyle(alwaysAllow) : null;
      const visibleEnabled=!!alwaysAllow && !!rect && rect.width>0 && rect.height>0 &&
        style?.display!=='none' && style?.visibility!=='hidden' &&
        !alwaysAllow.disabled && alwaysAllow.getAttribute?.('aria-disabled')!=='true';
      if(exactGitHubCard && approvalAtBottom && visibleEnabled){
        const autoSignature='GitHub|Always allow|'+text.slice(0,180);
        const autoNow=Date.now();
        if(autoSignature!==lastAutoApprovalSignature || autoNow-lastAutoApprovalAt>=5000){
          lastAutoApprovalSignature=autoSignature;lastAutoApprovalAt=autoNow;
          emitRelayEvent('chatgpt_tool_approval_autoapproved',{
            provider:'GitHub',
            choice:'Always allow',
            bottom:true,
            exact_surface:true
          });
          if(operatorPaused)return;
          alwaysAllow.click();
        }
      }
      return;
    }
  },250);
}

function bindToolApprovalPromptDetector(){
  if(operatorPaused)return;
  if(!document.body){setTimeout(bindToolApprovalPromptDetector,250);return;}
  approvalPromptObserver?.disconnect();
  approvalPromptObserver=null;
  scheduleToolApprovalPromptInspect();
  if(approvalInspectInterval===null)approvalInspectInterval=setInterval(scheduleToolApprovalPromptInspect,2000);
}

// Persistent background channel:
// - content script holds a runtime.connect() Port while the ChatGPT tab is open
// - Firefox keeps its MV3 event page alive while the message port remains open
// - action replies use the same port instead of a one-shot sendMessage callback
// - disconnects reject pending requests and trigger reconnect + packet reinspection
hydrateAttemptedHistory();
hydrateSubmittedResults();
hydrateRecoveryPacketWatch();
connectBackgroundPort();
// The worker coalesces concurrent callers and pushes the resulting state to
// every connected tab.  This fallback keeps STOP latency bounded without
// issuing four independent /status requests per second from every scanner.
operatorControlPollTimer=setInterval(pollOperatorControlState,2000);
setTimeout(pollOperatorControlState,25);
setTimeout(()=>resumeEngineeringRotation().catch(e=>emitRelayEvent('chat_rotation_failed',{error:String(e?.message||e).slice(0,240),phase:rotationLoad()?.phase||null})),800);
emitRelayEvent('content_script_started',{
  href:location.href,
  runtime:'v11-scroll-v5-delivery-v17-whole-stop-v1-submit-once-scoped-recovery-draft-owner-release-approval-v3-uierror-v1-owner-v1',
  stop_contract:'whole-stop-v1',
  operator_paused:operatorPaused
});

// Relay UX scroll handoff:
// - after the relay injects/sends a result, follow the newest conversation edge
//   for 8 seconds so the user lands on the next assistant response
// - outside that brief relay-owned window, manual scrolling remains authoritative
// - recovery/load still uses the separate one-shot jump to the newest relay command

// Performance mode V11:
// - mutation-local assistant discovery; no querySelectorAll from observer callbacks
// - one observer scoped to the active assistant turn for packet settling
// - one conversation-branch childList observer for new-turn structure
// - a 15-second recovery scan is the only steady-state whole-branch fallback
// - one recovery-only scan may locate the newest valid relay command and scroll it
//   into view exactly once; manual scrolling remains authoritative afterward
// - attempted packet history is bounded
// - smart bottom-follow is throttled to 1200 ms and yields to manual scrolling
void operatorControlPollTimer;
void recoveryTimer;
void consumerMissionPollTimer;
})();

/* GPT_WINDOWS_EVENT_DRIVEN_SCANNER_V11 */
/* GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V5 */
/* GPT_WINDOWS_WORKER_DRIVEN_SCROLL_CONTROL_V1 */
/* GPT_WINDOWS_SCROLL_TELEMETRY_V5 */
/* GPT_WINDOWS_TRUE_CONTENT_START_TELEMETRY_V1 */
/* GPT_WINDOWS_CURRENT_CHATGPT_ROLE_SELECTORS_V1 */
/* GPT_WINDOWS_STABLE_MAIN_OBSERVER_V1 */
/* GPT_WINDOWS_CODEBLOCK_PACKET_EXTRACTION_V1 */
/* GPT_WINDOWS_PERSISTENT_BACKGROUND_PORT_V1 */
/* GPT_WINDOWS_LINE_ANCHORED_PACKET_PARSER_V1 */
/* GPT_WINDOWS_RECOVERY_SCROLL_V1 */
/* GPT_WINDOWS_SMART_AUTOSCROLL_V2 */
/* GPT_WINDOWS_FORCED_RECOVERY_REINSPECTION_V1 */
/* GPT_WINDOWS_FIVE_MINUTE_STALL_WATCHDOG_V1 */
/* GPT_WINDOWS_DURABLE_RECOVERY_OBLIGATION_V1 */
/* GPT_WINDOWS_STALE_OWNER_LEASE_V1 */
