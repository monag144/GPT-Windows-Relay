#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import windows_tools as wt
import firefox_adapter as ff

GPT_WINDOWS_WORKFLOW_V1 = True
MAX_STEPS = 32
_STEP_ID = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")

_OP_ARGS = {
    "clipboard.read": set(),
    "clipboard.write": {"text"},
    "clipboard.clear": set(),
    "uia.field_set_text": {"window_title","text","field_name","automation_id","process_id"},
    "uia.inspect": {"window_title","control_type","control_name","automation_id","process_id","max_results"},
    "uia.invoke": {"window_title","control_type","control_name","automation_id","process_id"},
    "uia.select": {"window_title","control_type","control_name","automation_id","process_id"},
    "uia.set_toggle": {"window_title","checked","control_type","control_name","automation_id","process_id"},
    "firefox.list_tabs": set(),
    "firefox.select_tab": {"tab_name","contains"},
    "screenshot.capture": {"target","window_title","process_id","x","y","width","height","max_files","max_age_hours"},
}
_REQUIRED = {
    "clipboard.write": {"text"},
    "uia.field_set_text": {"window_title","text"},
    "uia.inspect": {"window_title"},
    "uia.invoke": {"window_title","control_type"},
    "uia.select": {"window_title","control_type"},
    "uia.set_toggle": {"window_title","checked"},
    "screenshot.capture": {"target"},
}
_FALLBACK_ARGS = {"target","window_title","process_id","x","y","width","height","max_files","max_age_hours"}

def _validate_capture(args: dict, *, fallback: bool) -> None:
    unknown=set(args)-_FALLBACK_ARGS
    if unknown: raise ValueError("unsupported screenshot args: "+",".join(sorted(unknown)))
    target=args.get("target")
    allowed={"window","region"} if fallback else {"screen","window","region"}
    if target not in allowed: raise ValueError("invalid screenshot target")
    if target=="window" and not args.get("window_title"): raise ValueError("window screenshot requires window_title")
    if target=="region":
        if not isinstance(args.get("width"),int) or not isinstance(args.get("height"),int) or args["width"]<=0 or args["height"]<=0:
            raise ValueError("region screenshot requires positive integer width/height")

def validate_plan(plan: dict) -> dict:
    if not isinstance(plan,dict): raise TypeError("workflow plan must be an object")
    if set(plan)-{"version","name","steps"}: raise ValueError("unsupported workflow top-level key")
    if plan.get("version") != 1: raise ValueError("workflow version must be 1")
    name=plan.get("name")
    if name is not None and (not isinstance(name,str) or not name or len(name)>128): raise ValueError("invalid workflow name")
    steps=plan.get("steps")
    if not isinstance(steps,list) or not steps or len(steps)>MAX_STEPS: raise ValueError("workflow steps must contain 1..32 items")
    ids=set(); direct_captures=0
    for step in steps:
        if not isinstance(step,dict): raise TypeError("workflow step must be an object")
        if set(step)-{"id","op","args","fallback_screenshot"}: raise ValueError("unsupported workflow step key")
        sid=step.get("id");op=step.get("op");args=step.get("args",{})
        if not isinstance(sid,str) or not _STEP_ID.fullmatch(sid): raise ValueError("invalid step id")
        if sid in ids: raise ValueError("duplicate step id: "+sid)
        ids.add(sid)
        if op not in _OP_ARGS: raise ValueError("unsupported workflow op: "+str(op))
        if not isinstance(args,dict): raise TypeError("step args must be an object")
        unknown=set(args)-_OP_ARGS[op]
        if unknown: raise ValueError("unsupported args for %s: %s"%(op,",".join(sorted(unknown))))
        missing=_REQUIRED.get(op,set())-set(args)
        if missing: raise ValueError("missing args for %s: %s"%(op,",".join(sorted(missing))))
        if op=="clipboard.write" and not isinstance(args.get("text"),str): raise TypeError("clipboard.write text must be str")
        if op=="uia.field_set_text" and not isinstance(args.get("text"),str): raise TypeError("field text must be str")
        if op=="uia.set_toggle" and not isinstance(args.get("checked"),bool): raise TypeError("checked must be bool")
        if op=="firefox.select_tab" and bool(args.get("tab_name")) == bool(args.get("contains")): raise ValueError("firefox.select_tab requires exactly one selector")
        if op in {"uia.invoke","uia.select","uia.set_toggle"} and not args.get("control_name") and not args.get("automation_id"): raise ValueError(op+" requires control_name or automation_id")
        if op=="screenshot.capture":
            direct_captures+=1;_validate_capture(args,fallback=False)
        fb=step.get("fallback_screenshot")
        if fb is not None:
            if not isinstance(fb,dict): raise TypeError("fallback_screenshot must be an object")
            _validate_capture(fb,fallback=True)
    if direct_captures>1: raise ValueError("workflow v1 permits at most one direct screenshot step")
    return plan

def _dispatch(op: str, args: dict):
    if op=="clipboard.read": return {"text":wt.clipboard_read_text()}
    if op=="clipboard.write": wt.clipboard_write_text(args["text"]); return {"chars":len(args["text"])}
    if op=="clipboard.clear": wt.clipboard_clear(); return {"cleared":True}
    if op=="uia.field_set_text": return wt.field_set_text(**args)
    if op=="uia.inspect": return wt.control_inspect(**args)
    if op=="uia.invoke": return wt.control_invoke(**args)
    if op=="uia.select": return wt.control_select(**args)
    if op=="uia.set_toggle":
        a=dict(args);checked=a.pop("checked");return wt.control_set_toggle(checked=checked,**a)
    if op=="firefox.list_tabs": return ff.list_tabs()
    if op=="firefox.select_tab": return ff.select_tab(**args)
    if op=="screenshot.capture": return wt.screenshot_capture(**args)
    raise ValueError("unsupported workflow op")

def execute_workflow(plan: dict) -> dict:
    validate_plan(plan)
    out={"ok":True,"status":"completed","version":1,"name":plan.get("name"),"steps":[]}
    root_attachment=None
    for step in plan["steps"]:
        try:
            result=_dispatch(step["op"],dict(step.get("args",{})))
            item={"id":step["id"],"op":step["op"],"ok":True,"result":result}
            out["steps"].append(item)
            if isinstance(result,dict) and result.get("chatgpt_attachment"):
                root_attachment=result["chatgpt_attachment"]
        except Exception as exc:
            item={"id":step["id"],"op":step["op"],"ok":False,"error":{"type":type(exc).__name__,"message":str(exc)}}
            out["steps"].append(item);out["ok"]=False;out["failed_step"]=step["id"]
            fb=step.get("fallback_screenshot")
            if fb is not None:
                try:
                    cap=wt.screenshot_capture(**fb)
                    out["fallback_screenshot"]=cap
                    out["status"]="needs_visual_reasoning"
                    if cap.get("chatgpt_attachment"): root_attachment=cap["chatgpt_attachment"]
                except Exception as cap_exc:
                    out["status"]="failed"
                    out["fallback_error"]={"type":type(cap_exc).__name__,"message":str(cap_exc)}
            else:
                out["status"]="failed"
            if root_attachment: out["chatgpt_attachment"]=root_attachment
            return out
    if root_attachment: out["chatgpt_attachment"]=root_attachment
    return out

def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description="Fixed-allowlist fail-closed Windows workflow runner")
    g=ap.add_mutually_exclusive_group(required=True);g.add_argument("--plan",type=Path);g.add_argument("--stdin",action="store_true")
    ns=ap.parse_args(argv)
    raw=sys.stdin.read() if ns.stdin else ns.plan.read_text(encoding="utf-8")
    result=execute_workflow(json.loads(raw));print(json.dumps(result,ensure_ascii=False));return 0 if result.get("ok") else 2

if __name__=="__main__": raise SystemExit(main())
