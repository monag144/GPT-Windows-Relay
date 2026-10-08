#!/usr/bin/env python3
"""Standalone read-only TCP liveness sampler for overnight Relay comparisons.
It intentionally never reads pairing credentials or makes an EXEC/POST request.
A listening port is not proof of browser/agent health; case U/Z also require
hourly independently confirmed packet/result receipts.
"""
import argparse
import json
import os
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def instant(line):
    return datetime.fromisoformat(line.replace("Z", "+00:00"))

def append(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record,separators=(",",":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())

def check(port, timeout=3):
    before=time.monotonic()
    try:
        with socket.create_connection(("127.0.0.1",port),timeout=timeout):
            ok=True
    except (OSError,TimeoutError):
        ok=False
    return {"ok":ok,"latency_ms":round((time.monotonic()-before)*1000,2)}

def summarize(path, minimum_seconds):
    entries=[json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    first=next((r for r in entries if r.get("kind")=="start"),None)
    last=next((r for r in reversed(entries) if r.get("kind")=="complete"),None)
    samples=[r for r in entries if r.get("kind")=="probe"]
    if not first or not last:
        return {"complete":False,"duration_seconds":0,"uptime_percent":0,"max_gap_seconds":0,"sample_count":len(samples)}
    dates=[instant(first["utc"])] + [instant(r["utc"]) for r in samples] + [instant(last["utc"])]
    gaps=[(b-a).total_seconds() for a,b in zip(dates,dates[1:])]
    duration=(dates[-1]-dates[0]).total_seconds()
    total=len(samples)
    good=sum(1 for r in samples if r.get("ok") is True)
    uptime=100*good/total if total else 0
    max_gap=max(gaps,default=0)
    interval=first.get("interval_seconds",15)
    enough=total>=int(minimum_seconds/max(interval,1)*0.95)
    complete=(last.get("success") is True and duration>=minimum_seconds
              and min(gaps,default=0)>=0 and enough)
    return {"complete":complete,"duration_seconds":round(duration,2),
            "uptime_percent":round(uptime,3),"max_gap_seconds":round(max_gap,2),
            "sample_count":total,"successful_probes":good,
            "qualified_for_tcp_gate":bool(complete and uptime>=99.5 and max_gap<=120),
            "notice":"TCP listener only: use independent mission/result evidence for overnight certification"}

def observe(args):
    if args.output.exists():
        raise FileExistsError("observer cannot overwrite historical samples")
    duration=args.hours*3600
    began=time.monotonic()
    append(args.output,{"kind":"start","utc":now(),"interval_seconds":args.interval,
                        "planned_seconds":duration,"endpoint":"127.0.0.1:"+str(args.port)})
    index=0
    try:
        while time.monotonic()-began < duration:
            append(args.output,{"kind":"probe","utc":now(),"index":index,**check(args.port)})
            index+=1
            remaining=duration-(time.monotonic()-began)
            if remaining>0: time.sleep(min(remaining,args.interval))
    except KeyboardInterrupt:
        append(args.output,{"kind":"aborted","utc":now()})
        raise SystemExit(130)
    append(args.output,{"kind":"complete","utc":now(),"success":True})
    summary=summarize(args.output,duration)
    result=args.output.with_suffix(".summary.json")
    result.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
    return 0 if summary["qualified_for_tcp_gate"] else 2

def main(argv=None):
    p=argparse.ArgumentParser(description="Independent local-only liveness monitor; no secrets or commands")
    p.add_argument("--port",type=int,default=8766)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--hours",type=float,default=12)
    p.add_argument("--interval",type=int,default=15)
    args=p.parse_args(argv)
    if not 1<=args.port<=65535:p.error("invalid TCP port")
    if not .01<=args.hours<=168:p.error("hours out of range")
    if not 5<=args.interval<=60:p.error("interval must be 5..60 seconds")
    try:return observe(args)
    except FileExistsError as exc:
        p.error(str(exc))
if __name__=="__main__":
    raise SystemExit(main())
