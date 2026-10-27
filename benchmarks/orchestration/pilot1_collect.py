#!/usr/bin/env python3
"""collect.py <n> <first_ack>: wait for n worker_done messages, ack each, print dispatch ids."""
import subprocess, json, sys
n=int(sys.argv[1]); ack=sys.argv[2] if len(sys.argv)>2 else None
done=[]; t=0
while len(done)<n and t<12:
    t+=1
    cmd=["orca","orchestration","check","--run","run_d06f3412f849","--wait","--types","worker_done,escalation,question","--timeout-ms","120000","--json"]
    if ack: cmd+=["--ack",ack]
    out=subprocess.run(cmd,capture_output=True,text=True).stdout
    lines=[l for l in out.splitlines() if l.strip() and '_keepalive' not in l]
    try: r=json.loads("\n".join(lines))['result']
    except Exception as e: continue
    if not r['messages']: continue
    ack=r['deliveryId']
    for m in r['messages']:
        p=json.loads(m['payload']); print(m['type'],p.get('dispatchId'),p.get('outcome'),m['subject'][:80],flush=True)
        if m['type']=='worker_done': done.append(p['dispatchId'])
print("LAST_ACK",ack)
