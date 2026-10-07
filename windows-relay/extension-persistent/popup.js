const s=document.getElementById('s'),b=document.getElementById('b'),pair=document.getElementById('pair'),unpair=document.getElementById('unpair'),token=document.getElementById('token');
let armed=false;
async function refresh(){
  const r=await chrome.runtime.sendMessage({type:'status'});
  if(!r?.ok){
    armed=false;b.disabled=true;
    s.textContent=r?.error==='relay_unpaired'?'NOT PAIRED':('Relay unavailable: '+(r?.error||'unknown'));
    return;
  }
  armed=!!r.data.armed;s.textContent=armed?'ARMED - commands may execute':'DISARMED';
  b.textContent=armed?'Disarm relay':'Arm relay';b.disabled=false;
}
b.onclick=async()=>{b.disabled=true;await chrome.runtime.sendMessage({type:'arm',armed:!armed});await refresh();};
pair.onclick=async()=>{pair.disabled=true;const r=await chrome.runtime.sendMessage({type:'pair',token:token.value});token.value='';pair.disabled=false;if(!r?.ok)s.textContent='Pairing failed: '+(r?.error||'unknown');else await refresh();};
unpair.onclick=async()=>{await chrome.runtime.sendMessage({type:'unpair'});await refresh();};
refresh();