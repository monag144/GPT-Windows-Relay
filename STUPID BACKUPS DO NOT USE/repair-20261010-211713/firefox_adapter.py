#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,binascii,json,subprocess,sys
from urllib.parse import urlsplit
from pathlib import Path

GPT_WINDOWS_FIREFOX_TAB_ADAPTER_V1=True
GPT_WINDOWS_FIREFOX_RECOVERY_ADAPTER_V2=True
GPT_WINDOWS_FIREFOX_RELAY_RESULT_SENDER_V1=True
GPT_WINDOWS_FIREFOX_RELAY_RESULT_URL_BOUND_V2=True
GPT_WINDOWS_FIREFOX_CONVERSATION_RESOLVER_V1=True

def _call(action: str, *, tab_name: str | None = None, contains: str | None = None, addon_name: str | None = None, manifest_path: str | None = None, firefox_pid: int | None = None, profile_path: str | None = None, prompt_text: str | None = None, result_file: str | None = None, packet_id: str | None = None, exact_tab_name: str | None = None, conversation_url: str | None = None) -> dict:
    if action not in {"list-tabs","select-tab","reload-addon","refresh-tab","ensure-addon","close-profile","send-chatgpt-prompt","read-chatgpt-text","send-relay-result","resolve-conversation-tab"}: raise ValueError("unsupported Firefox adapter action")
    if action in {"select-tab","refresh-tab"} and bool(tab_name) == bool(contains): raise ValueError(f"{action} requires exactly one of tab_name or contains")
    if action in {"reload-addon","ensure-addon"} and not addon_name: raise ValueError(f"{action} requires addon_name")
    if action=="ensure-addon" and not manifest_path: raise ValueError("ensure-addon requires manifest_path")
    if action=="close-profile" and not profile_path: raise ValueError("close-profile requires profile_path")
    if action=="send-chatgpt-prompt" and not prompt_text: raise ValueError("send-chatgpt-prompt requires prompt_text")
    if action=="send-relay-result" and (not result_file or not packet_id or not exact_tab_name or not conversation_url): raise ValueError("send-relay-result requires result_file, packet_id, exact_tab_name, conversation_url")
    if action=="resolve-conversation-tab" and not conversation_url: raise ValueError("resolve-conversation-tab requires conversation_url")
    script=Path(__file__).with_name("firefox_tab_adapter.ps1")
    if not script.is_file(): raise FileNotFoundError(script)
    args=["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(script),"-Action",action]
    if tab_name: args += ["-TabName",tab_name]
    if contains: args += ["-Contains",contains]
    if addon_name: args += ["-AddonName",addon_name]
    if manifest_path: args += ["-ManifestPath",manifest_path]
    if firefox_pid: args += ["-FirefoxPid",str(int(firefox_pid))]
    if profile_path: args += ["-ProfilePath",str(Path(profile_path).resolve())]
    if prompt_text: args += ["-PromptText",prompt_text]
    if result_file: args += ["-ResultFile",str(Path(result_file).resolve())]
    if packet_id: args += ["-PacketId",packet_id]
    if exact_tab_name: args += ["-ExactTabName",exact_tab_name]
    if conversation_url: args += ["-ConversationUrl",conversation_url]
    cp=subprocess.run(args,text=True,capture_output=True,encoding="utf-8",errors="replace")
    if cp.returncode: raise RuntimeError((cp.stderr or cp.stdout or "Firefox adapter failed").strip())
    lines=[x for x in cp.stdout.splitlines() if x.strip()]
    if not lines: raise RuntimeError("Firefox adapter returned no result")
    result=json.loads(lines[-1])
    if result.get("ok") is not True: raise RuntimeError("Firefox adapter verification failed")
    return result

def normalize_conversation_url(value: str) -> str:
    parts=urlsplit(str(value or ''))
    pieces=[piece for piece in parts.path.split('/') if piece]
    if parts.scheme!='https' or parts.hostname!='chatgpt.com' or len(pieces)!=2 or pieces[0]!='c' or not pieces[1]:
        raise ValueError('invalid ChatGPT conversation URL')
    return 'https://chatgpt.com/c/'+pieces[1]

def resolve_conversation_tab(conversation_url: str, *, firefox_pid: int | None = None, profile_path: str | None = None) -> dict:
    expected=normalize_conversation_url(conversation_url)
    resolved=_call('resolve-conversation-tab',conversation_url=expected,firefox_pid=firefox_pid,profile_path=profile_path)
    if resolved.get('conversation_url')!=expected:
        raise RuntimeError('conversation resolver URL mismatch')
    if resolved.get('match_count')!=1:
        raise RuntimeError('conversation resolver match count invalid')
    if not isinstance(resolved.get('firefox_pid'),int) or resolved['firefox_pid']<=0:
        raise RuntimeError('conversation resolver Firefox PID invalid')
    if not isinstance(resolved.get('tab_name'),str) or not resolved['tab_name']:
        raise RuntimeError('conversation resolver tab name invalid')
    return resolved

def list_tabs(*, firefox_pid: int | None = None, profile_path: str | None = None) -> dict:
    return _call("list-tabs",firefox_pid=firefox_pid,profile_path=profile_path)

def select_tab(*, tab_name: str | None = None, contains: str | None = None) -> dict:
    return _call("select-tab",tab_name=tab_name,contains=contains)

def reload_addon(addon_name: str="GPT Windows Relay", *, firefox_pid: int | None = None, profile_path: str | None = None) -> dict:
    return _call("reload-addon",addon_name=addon_name,firefox_pid=firefox_pid,profile_path=profile_path)

def ensure_addon(manifest_path: str, addon_name: str="GPT Windows Relay", *, firefox_pid: int | None = None, profile_path: str | None = None) -> dict:
    manifest=Path(manifest_path).resolve()
    if not manifest.is_file(): raise FileNotFoundError(manifest)
    return _call("ensure-addon",addon_name=addon_name,manifest_path=str(manifest),firefox_pid=firefox_pid,profile_path=profile_path)

def refresh_tab(*, tab_name: str | None = None, contains: str | None = None, firefox_pid: int | None = None, profile_path: str | None = None) -> dict:
    return _call("refresh-tab",tab_name=tab_name,contains=contains,firefox_pid=firefox_pid,profile_path=profile_path)

def close_profile(profile_path: str) -> dict:
    return _call("close-profile",profile_path=profile_path)

# GPT_WINDOWS_FIREFOX_OUT_OF_BAND_PROMPT_V1
def send_chatgpt_prompt(prompt_text: str, *, firefox_pid: int | None = None, profile_path: str | None = None) -> dict:
    if not prompt_text or not prompt_text.strip(): raise ValueError("prompt_text is required")
    return _call("send-chatgpt-prompt",prompt_text=prompt_text,firefox_pid=firefox_pid,profile_path=profile_path)


# GPT_WINDOWS_FIREFOX_RELAY_RESULT_FILE_TRANSPORT_V1
def send_relay_result(result_file: str, packet_id: str, exact_tab_name: str, conversation_url: str, *, firefox_pid: int | None = None, profile_path: str | None = None) -> dict:
    path=Path(result_file).resolve()
    if not path.is_file(): raise FileNotFoundError(path)
    if not packet_id: raise ValueError("packet_id is required")
    if not exact_tab_name: raise ValueError("exact_tab_name is required")
    expected_url=normalize_conversation_url(conversation_url)
    result=_call("send-relay-result",result_file=str(path),packet_id=packet_id,exact_tab_name=exact_tab_name,conversation_url=expected_url,firefox_pid=firefox_pid,profile_path=profile_path)
    state=result.get("state")
    if state not in {"PRE_SUBMIT_FAILED","SUBMITTED","SUBMIT_UNCERTAIN"}: raise RuntimeError("invalid relay result sender state")
    invoked=bool(result.get("send_invoked"))
    confirmed=bool(result.get("confirmed"))
    if state=="PRE_SUBMIT_FAILED" and invoked: raise RuntimeError("invalid pre-submit state")
    if state=="SUBMITTED" and (not invoked or not confirmed): raise RuntimeError("invalid submitted state")
    if state=="SUBMIT_UNCERTAIN" and not invoked: raise RuntimeError("invalid uncertain state")
    return result

def read_chatgpt_text(*, firefox_pid: int | None = None, profile_path: str | None = None) -> dict:
    return _call("read-chatgpt-text",firefox_pid=firefox_pid,profile_path=profile_path)

# GPT_WINDOWS_FIREFOX_PROMPT_B64_TRANSPORT_V1
def decode_prompt_input(prompt_text: str | None, prompt_b64: str | None) -> str:
    if bool(prompt_text) == bool(prompt_b64):
        raise ValueError("exactly one prompt input is required")
    if prompt_b64:
        try:
            return base64.b64decode(prompt_b64, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise ValueError("prompt-b64 must be valid base64 UTF-8") from exc
    return str(prompt_text)

def main(argv=None) -> int:
    # CLI JSON is deliberately ASCII-safe: Windows relay hosts may expose a
    # legacy code page while Firefox tab titles contain arbitrary Unicode.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, OSError):
        pass
    ap=argparse.ArgumentParser(description="Fail-closed Firefox browser recovery adapter")
    sub=ap.add_subparsers(dest="command",required=True)
    lt=sub.add_parser("list-tabs");lt.add_argument("--firefox-pid",type=int);lt.add_argument("--profile-path")
    rv=sub.add_parser("resolve-conversation-tab");rv.add_argument("--conversation-url",required=True);rv.add_argument("--firefox-pid",type=int);rv.add_argument("--profile-path")
    for name in ("select-tab","refresh-tab"):
        s=sub.add_parser(name);g=s.add_mutually_exclusive_group(required=True);g.add_argument("--tab-name");g.add_argument("--contains");s.add_argument("--firefox-pid",type=int);s.add_argument("--profile-path")
    a=sub.add_parser("reload-addon");a.add_argument("--addon-name",default="GPT Windows Relay");a.add_argument("--firefox-pid",type=int);a.add_argument("--profile-path")
    e=sub.add_parser("ensure-addon");e.add_argument("--manifest-path",required=True);e.add_argument("--addon-name",default="GPT Windows Relay");e.add_argument("--firefox-pid",type=int);e.add_argument("--profile-path")
    x=sub.add_parser("close-profile");x.add_argument("--profile-path",required=True)
    p=sub.add_parser("send-chatgpt-prompt");pg=p.add_mutually_exclusive_group(required=True);pg.add_argument("--prompt-text");pg.add_argument("--prompt-b64");p.add_argument("--firefox-pid",type=int);p.add_argument("--profile-path")
    q=sub.add_parser("read-chatgpt-text");q.add_argument("--firefox-pid",type=int);q.add_argument("--profile-path")
    rr=sub.add_parser("send-relay-result");rr.add_argument("--result-file",required=True);rr.add_argument("--packet-id",required=True);rr.add_argument("--exact-tab-name",required=True);rr.add_argument("--conversation-url",required=True);rr.add_argument("--firefox-pid",type=int);rr.add_argument("--profile-path")
    ns=ap.parse_args(argv)
    if ns.command=="list-tabs":
        result=list_tabs(firefox_pid=ns.firefox_pid,profile_path=ns.profile_path)
    elif ns.command=="resolve-conversation-tab":
        result=resolve_conversation_tab(ns.conversation_url,firefox_pid=ns.firefox_pid,profile_path=ns.profile_path)
    elif ns.command=="select-tab":
        result=select_tab(tab_name=ns.tab_name,contains=ns.contains)
    elif ns.command=="refresh-tab":
        result=refresh_tab(tab_name=ns.tab_name,contains=ns.contains,firefox_pid=ns.firefox_pid,profile_path=ns.profile_path)
    elif ns.command=="ensure-addon":
        result=ensure_addon(ns.manifest_path,ns.addon_name,firefox_pid=ns.firefox_pid,profile_path=ns.profile_path)
    elif ns.command=="close-profile":
        result=close_profile(ns.profile_path)
    elif ns.command=="send-chatgpt-prompt":
        result=send_chatgpt_prompt(decode_prompt_input(ns.prompt_text,ns.prompt_b64),firefox_pid=ns.firefox_pid,profile_path=ns.profile_path)
    elif ns.command=="read-chatgpt-text":
        result=read_chatgpt_text(firefox_pid=ns.firefox_pid,profile_path=ns.profile_path)
    elif ns.command=="send-relay-result":
        result=send_relay_result(ns.result_file,ns.packet_id,ns.exact_tab_name,ns.conversation_url,firefox_pid=ns.firefox_pid,profile_path=ns.profile_path)
    else:
        result=reload_addon(ns.addon_name,firefox_pid=ns.firefox_pid,profile_path=ns.profile_path)
    print(json.dumps(result,ensure_ascii=True));return 0

if __name__=="__main__": raise SystemExit(main())
