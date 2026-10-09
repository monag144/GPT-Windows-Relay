#!/usr/bin/env python3
"""PCE14 disposable local browser fixture with independent receiver-side receipts.

Loopback-only HTTP server. No ChatGPT endpoints, Firefox injection, credentials,
storage of raw messages, browser launches, or production relay writes. The page
is intentionally branded TEST ONLY and disabled until geometry is calibrated.
Never infer real ChatGPT delivery from a local fixture receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from dataclasses import dataclass, field

MAX_MESSAGE_BYTES = 16384
MAX_POST_BYTES = 20480
MAX_OPERATIONS = 250

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>PCE14 LOCAL TEST FIXTURE - NOT CHATGPT</title>
<style>
* { box-sizing: border-box; }
body { margin: 0; background: #151c28; color: #e9f4ff; font: 16px Arial, sans-serif; }
.banner { position: fixed; top: 0; left: 0; right: 0; z-index: 3; background: #a11920;
 color: white; text-align: center; padding: 9px; pointer-events: none; }
#new-chat { position: absolute; width: 132px; height: 44px; transform: translate(-50%,-50%);
 border: 2px solid #ffcb66; border-radius: 8px; background: #23364c; color: white; cursor: pointer; }
#message { position: absolute; width: 480px; height: 112px; transform: translate(-50%,-50%);
 border: 3px solid #ffcb66; background: #fbfbfc; color: #111; border-radius: 8px; padding: 12px;
 resize: none; }
#state { position: fixed; bottom: 14px; left: 18px; right: 18px; background: #27344a;
 border: 1px solid #6f889d; padding: 13px; }
#new-chat:disabled, #message:disabled { opacity: 0.32; cursor: not-allowed; }
</style></head><body>
<div class="banner">PCE14 LOCAL TEST FIXTURE — NOT CHATGPT — NO REAL CHAT MESSAGES</div>
<button id="new-chat" disabled>+ New chat</button>
<textarea id="message" placeholder="Paste synthetic test message" disabled></textarea>
<div id="state" role="status">Geometry uncalibrated; controls disabled.</div>
<script>
'use strict';
const nonce = __NONCE_JSON__;
const state = document.getElementById('state');
const newChat = document.getElementById('new-chat');
const message = document.getElementById('message');
let conversation = null;
let submitting = false;
let sent = 0;
function geometry() {
 const q = new URLSearchParams(location.search);
 const manual = ['outer_w','outer_h','content_left','content_top'].every(k => q.has(k));
 if (manual && !['outer_w','outer_h','content_left','content_top'].every(k =>
     /^[0-9]{1,4}$/.test(q.get(k)))) return null;
 const w=manual?Number(q.get('outer_w')):window.outerWidth;
 const h=manual?Number(q.get('outer_h')):window.outerHeight;
 const left=manual?Number(q.get('content_left')):window.mozInnerScreenX-window.screenX;
 const top=manual?Number(q.get('content_top')):window.mozInnerScreenY-window.screenY;
 if (![w,h,left,top].every(Number.isFinite)) return null;
 if (w<700 || w>5000 || h<450 || h>3000 || left>240 || top>250) return null;
 const nx=120-left,ny=163-top,cx=Math.round(w*.585)-left,cy=Math.round(h*.56)-top;
 if (nx<0 || ny<0 || cx<260 || cy<60 || cx>innerWidth || cy>innerHeight) return null;
 return {nx,ny,cx,cy};
}
const launchId = new URLSearchParams(location.search).get('launch_id');
const validLaunchId = typeof launchId==='string' && /^[a-f0-9]{24}$/.test(launchId);
if (validLaunchId) document.title += ' ['+launchId+']';
const g=validLaunchId ? geometry() : null;
async function post(path, body) {
 const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json',
 'X-PCE14-Fixture':nonce},body:JSON.stringify(body)});
 return {status:r.status, data:await r.json()};
}
// Read-only fixture initialization telemetry. No URLs, clipboard, user text or browser titles.
const diagNumber = v => Number.isFinite(v) ? Math.round(v) : null;
post('/api/diagnostic',{
 launch_id:validLaunchId?launchId:null,
 geometry_status:g?'VALID':'NULL',
 outer_w:diagNumber(window.outerWidth),outer_h:diagNumber(window.outerHeight),
 inner_w:diagNumber(window.innerWidth),inner_h:diagNumber(window.innerHeight),
 left:diagNumber(window.mozInnerScreenX-window.screenX),
 top:diagNumber(window.mozInnerScreenY-window.screenY)
}).catch(()=>{state.textContent='Local diagnostic channel failed; input remains disabled.';});
if (g) {
 newChat.style.left=g.nx+'px'; newChat.style.top=g.ny+'px';
 message.style.left=g.cx+'px'; message.style.top=g.cy+'px';
 state.textContent='Validating local fixture geometry; do not send.';
 post('/api/ready',{launch_id:launchId,outer_w:Math.round(window.outerWidth),
  outer_h:Math.round(window.outerHeight),
  content_left:Math.round(window.mozInnerScreenX-window.screenX),
  content_top:Math.round(window.mozInnerScreenY-window.screenY),
  client_w:Math.round(window.innerWidth),client_h:Math.round(window.innerHeight),
  new_chat_x:g.nx,new_chat_y:g.ny,composer_x:g.cx,composer_y:g.cy
 }).then(r=>{
  if(r.status!==200 || r.data.ready!==true) throw Error('READY_REJECTED');
  newChat.disabled=false;
  state.textContent='Fixture ready ['+launchId+']. Press New chat, click composer, Ctrl+V, Enter. Test only.';
 }).catch(()=>{state.textContent='LOCAL READY HANDSHAKE FAILED; DO NOT SEND.';newChat.disabled=true;});
}
newChat.addEventListener('click',async function(){
 if (!g || submitting) return;
 try {
  const r=await post('/api/new-chat',{});
  if (r.status!==201) throw Error('new-chat receiver rejected request');
  conversation=r.data.conversation_id; message.value=''; message.disabled=false;
  state.textContent='New local test conversation created.';
 }catch(_) {state.textContent='LOCAL NEW CHAT FAILED (no ChatGPT activity).';}
});
message.addEventListener('keydown',async function(e){
 if(e.key!=='Enter'||e.shiftKey||e.isComposing) return;
 e.preventDefault();
 if (!conversation || submitting || !message.value) return;
 submitting=true;
 const op='PCE14-FIXTURE-'+crypto.randomUUID();
 const text=message.value;
 try {
  const r=await post('/api/send',{conversation_id:conversation,operation_id:op,text});
  if(r.status!==201) throw Error('submission receiver rejected');
  sent++;
  message.value='';
  state.textContent='LOCAL receiver accepted '+sent+' message(s). This is NOT a ChatGPT receipt.';
 }catch(_) {state.textContent='LOCAL SUBMISSION FAILED; verify receiver before retry.';}
 finally {submitting=false;}
});
</script></body></html>"""


class FixtureError(ValueError):
    def __init__(self, code: str, status: int = 422):
        super().__init__(code)
        self.code = code
        self.status = status


@dataclass
class Receiver:
    token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    lock: threading.Lock = field(default_factory=threading.Lock)
    serial: int = 0
    current_conversation: str | None = None
    receipts: dict = field(default_factory=dict)
    stopped: bool = False
    ready_report: dict | None = None
    diagnostic_report: dict | None = None

    def diagnostic(self, token: str, data: dict) -> dict:
        self.authenticate(token)
        required = {"launch_id","geometry_status","outer_w","outer_h","inner_w","inner_h","left","top"}
        if not isinstance(data, dict) or set(data) != required:
            raise FixtureError("INVALID_DIAGNOSTIC")
        if data["launch_id"] is not None and (
            not isinstance(data["launch_id"], str) or len(data["launch_id"]) != 24
            or any(c not in "0123456789abcdef" for c in data["launch_id"])):
            raise FixtureError("INVALID_LAUNCH_ID")
        if data["geometry_status"] not in ("VALID","NULL"):
            raise FixtureError("INVALID_GEOMETRY_STATUS")
        for key in required - {"launch_id","geometry_status"}:
            value = data[key]
            if value is not None and (type(value) is not int or not -6000 <= value <= 6000):
                raise FixtureError("INVALID_GEOMETRY_DIAGNOSTIC")
        with self.lock:
            if self.stopped:
                raise FixtureError("STOPPED",423)
            self.diagnostic_report = dict(data)
            return {"accepted":True}

    def ready(self, token: str, data: dict) -> dict:
        self.authenticate(token)
        required = {"launch_id","outer_w","outer_h","content_left","content_top",
                    "client_w","client_h","new_chat_x","new_chat_y","composer_x","composer_y"}
        if not isinstance(data, dict) or set(data) != required:
            raise FixtureError("INVALID_READY")
        if not isinstance(data["launch_id"], str) or len(data["launch_id"]) != 24 or any(c not in "0123456789abcdef" for c in data["launch_id"]):
            raise FixtureError("INVALID_LAUNCH_ID")
        for key in required - {"launch_id"}:
            if type(data[key]) is not int or not -200 <= data[key] <= 6000:
                raise FixtureError("INVALID_GEOMETRY")
        w, h = data["outer_w"], data["outer_h"]
        left, top = data["content_left"], data["content_top"]
        if not (700 <= w <= 5000 and 450 <= h <= 3000 and 0 <= left <= 240 and 0 <= top <= 250):
            raise FixtureError("GEOMETRY_OUT_OF_RANGE")
        if (data["new_chat_x"],data["new_chat_y"]) != (120-left,163-top) or (data["composer_x"],data["composer_y"]) != (int(w*.585+.5)-left,int(h*.56+.5)-top):
            raise FixtureError("GEOMETRY_INCONSISTENT")
        if not (0 <= data["new_chat_x"] < data["client_w"] and 0 <= data["new_chat_y"] < data["client_h"] and 0 <= data["composer_x"] < data["client_w"] and 0 <= data["composer_y"] < data["client_h"]):
            raise FixtureError("CONTROLS_OUTSIDE_CLIENT")
        with self.lock:
            if self.stopped:
                raise FixtureError("STOPPED",423)
            self.ready_report = dict(data)
            return {"ready": True}

    def authenticate(self, token: str) -> None:
        if not secrets.compare_digest(token, self.token):
            raise FixtureError("DENIED", 403)

    def new_chat(self, token: str) -> dict:
        self.authenticate(token)
        with self.lock:
            if self.stopped:
                raise FixtureError("STOPPED", 423)
            if len(self.receipts) >= MAX_OPERATIONS:
                raise FixtureError("LIMIT_REACHED", 429)
            self.serial += 1
            self.current_conversation = "local-fixture-" + str(self.serial)
            return {"conversation_id": self.current_conversation}

    def send(self, token: str, data: dict) -> dict:
        self.authenticate(token)
        if not isinstance(data, dict) or set(data) != {"conversation_id","operation_id","text"}:
            raise FixtureError("INVALID_BODY")
        conversation, operation, text = (data[k] for k in ("conversation_id","operation_id","text"))
        if not isinstance(operation, str) or len(operation) > 80 or not operation.startswith("PCE14-FIXTURE-"):
            raise FixtureError("INVALID_OPERATION_ID")
        if not isinstance(text, str):
            raise FixtureError("INVALID_TEXT")
        raw = text.encode("utf-8")
        if not 0 < len(raw) <= MAX_MESSAGE_BYTES:
            raise FixtureError("INVALID_MESSAGE_LENGTH")
        with self.lock:
            if self.stopped:
                raise FixtureError("STOPPED", 423)
            if operation in self.receipts:
                raise FixtureError("DUPLICATE_OPERATION", 409)
            if len(self.receipts) >= MAX_OPERATIONS:
                raise FixtureError("LIMIT_REACHED", 429)
            if conversation != self.current_conversation or not isinstance(conversation,str):
                raise FixtureError("WRONG_CONVERSATION", 409)
            receipt = {"conversation_id": conversation, "operation_id": operation,
                       "payload_sha256": hashlib.sha256(raw).hexdigest(),
                       "payload_bytes": len(raw), "role": "user", "effect_count": 1}
            self.receipts[operation] = receipt
            return dict(receipt)

    def snapshot(self, token: str) -> dict:
        self.authenticate(token)
        with self.lock:
            return {"total_effects": len(self.receipts), "stopped": self.stopped,
                    "ready": dict(self.ready_report) if self.ready_report else None,
                    "diagnostic": dict(self.diagnostic_report) if self.diagnostic_report else None,
                    "receipts": [dict(v) for v in self.receipts.values()]}

    def stop(self, token: str) -> dict:
        self.authenticate(token)
        with self.lock:
            self.stopped = True
            return {"stopped": True}


def server_for(receiver: Receiver) -> ThreadingHTTPServer:
    """Create loopback listener on OS-assigned ephemeral port. Caller controls lifetime."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log URLs, headers, bodies or nonce.
        def _reply(self, status: int, value: dict | str, mime="application/json"):
            raw = (json.dumps(value, separators=(",", ":")).encode("utf-8")
                   if mime == "application/json" else value.encode("utf-8"))
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(raw)
        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                html = PAGE.replace("__NONCE_JSON__",json.dumps(receiver.token))
                self._reply(200, html, "text/html; charset=utf-8")
                return
            if path == "/api/receipts":
                try:
                    self._reply(200, receiver.snapshot(self.headers.get("X-PCE14-Fixture", "")))
                except FixtureError as exc:
                    self._reply(exc.status, {"error": exc.code})
                return
            self._reply(404, {"error": "NOT_FOUND"})
        def do_POST(self):
            path = urlparse(self.path).path
            if path not in ("/api/new-chat", "/api/send", "/api/stop", "/api/ready", "/api/diagnostic"):
                self._reply(404, {"error": "NOT_FOUND"});return
            try:
                receiver.authenticate(self.headers.get("X-PCE14-Fixture", ""))
                if self.headers.get("Content-Type", "").split(";")[0].lower() != "application/json":
                    raise FixtureError("CONTENT_TYPE_REQUIRED", 415)
                length = self.headers.get("Content-Length", "")
                if not length.isdigit() or not 0 <= int(length) <= MAX_POST_BYTES:
                    raise FixtureError("BODY_TOO_LARGE", 413)
                payload = json.loads(self.rfile.read(int(length)).decode("utf-8"))
                if path == "/api/new-chat":
                    if payload != {}: raise FixtureError("INVALID_BODY")
                    self._reply(201, receiver.new_chat(self.headers["X-PCE14-Fixture"]))
                elif path == "/api/ready":
                    self._reply(200, receiver.ready(self.headers["X-PCE14-Fixture"],payload))
                elif path == "/api/diagnostic":
                    self._reply(200, receiver.diagnostic(self.headers["X-PCE14-Fixture"],payload))
                elif path == "/api/stop":
                    if payload != {}: raise FixtureError("INVALID_BODY")
                    self._reply(200, receiver.stop(self.headers["X-PCE14-Fixture"]))
                else:
                    self._reply(201, receiver.send(self.headers["X-PCE14-Fixture"],payload))
            except FixtureError as exc:
                self._reply(exc.status, {"error": exc.code})
            except (ValueError, UnicodeDecodeError):
                self._reply(400, {"error": "INVALID_JSON"})
    return ThreadingHTTPServer(("127.0.0.1", 0), Handler)


def main() -> int:
    parser = argparse.ArgumentParser(description="Explicit opt-in PCE14 loopback fixture")
    parser.add_argument("--serve", action="store_true", help="Start disposable local receiver (does not launch browser)")
    args = parser.parse_args()
    if not args.serve:
        parser.print_help()
        return 0
    listener = server_for(Receiver())
    print("PCE14_FIXTURE_LOCAL_SERVER_PORT=" + str(listener.server_port), flush=True)
    print("PCE14_FIXTURE_NO_BROWSER_LAUNCH_NO_CHATGPT_SEND=true", flush=True)
    try:
        listener.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        listener.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
