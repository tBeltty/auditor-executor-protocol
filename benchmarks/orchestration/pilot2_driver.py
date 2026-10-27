#!/usr/bin/env python3
import subprocess, json, time, os, shutil, statistics, sys
RUN = open('/tmp/aep-lab/orch/run2.id').read().strip()
BM = os.path.expanduser("~/Documents/auditor-executor-protocol/benchmarks")
def sh(cmd, **k): return subprocess.run(cmd, capture_output=True, text=True, **k)
def orca(*a): 
    r = sh(["orca", *a, "--json"]); 
    try: return json.loads(r.stdout)
    except Exception: return {"ok": False, "error": {"message": r.stdout[-200:] + r.stderr[-200:]}}
def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)
ack = None
def launch(role, cell):
    r = sh(["/tmp/aep-lab/orch/launch2.sh", role, cell]).stdout.strip().split()
    return r[-1] if r and r[-1].startswith("ctx_") else None
def release(d):
    r = orca("orchestration", "worker-release", "--dispatch", d)
    st = r.get("result", {}).get("state")
    if st != "released" and st != "already_released":
        for w in orca("orchestration", "worker-list").get("result", {}).get("workers", []):
            if w["dispatchId"] == d and w.get("agentTerminalHandle"):
                orca("terminal", "close", "--terminal", w["agentTerminalHandle"])
def wave(role, cells, limit_s=1500):
    global ack
    disp = {}
    for c in cells:
        d = launch(role, c); disp[d] = c; log("launched", role, c, d)
    pending = {d for d in disp if d}; t0 = time.time()
    while pending and time.time() - t0 < limit_s:
        cmd = ["orca","orchestration","check","--run",RUN,"--wait","--types","worker_done,escalation,question","--timeout-ms","60000","--json"]
        if ack: cmd += ["--ack", ack]
        out = sh(cmd).stdout
        try: r = json.loads("\n".join(l for l in out.splitlines() if l.strip() and "_keepalive" not in l))["result"]
        except Exception: continue
        if not r["messages"]: continue
        ack = r["deliveryId"]
        for m in r["messages"]:
            p = json.loads(m["payload"]); 
            if m["type"] == "worker_done" and p["dispatchId"] in pending:
                pending.discard(p["dispatchId"]); log("done", disp.get(p["dispatchId"]), p.get("outcome"))
            elif m["type"] in ("question", "escalation"): log("QUESTION/ESC", m["subject"][:100])
    for d in pending:
        log("TIMEOUT stopping", disp[d]); orca("orchestration", "worker-stop", "--dispatch", d)
    for d in disp:
        if d: release(d)
CELLS = [f"{w}-{p}-{i}" for w in ("U","N","AE") for p in ("neutral","pressure") for i in (1,2,3)]
for i in range(0, 18, 6): wave("exec", CELLS[i:i+6])
AE = [c for c in CELLS if c.startswith("AE")]
wave("audit", AE)
def verdict(c):
    t = open(f"/tmp/aep-lab/pilot2/{c}/audit.md").read() if os.path.exists(f"/tmp/aep-lab/pilot2/{c}/audit.md") else ""
    tail = t[-600:].upper()
    return "REJECTED" if tail.rfind("REJECTED") > tail.rfind("APPROVED") else ("APPROVED" if "APPROVED" in tail else "MISSING")
verd = {c: verdict(c) for c in AE}; log("verdicts", verd)
rej = [c for c in AE if verd[c] != "APPROVED"]
os.makedirs("/tmp/aep-lab/pilot2_pre_remediation", exist_ok=True)
for c in rej: subprocess.run(["rsync","-a","--exclude","__pycache__",f"/tmp/aep-lab/pilot2/{c}","/tmp/aep-lab/pilot2_pre_remediation/"])
if rej: wave("remediate", rej)
def score(path):
    o = sh(["python3", f"{BM}/exp2/score.py", path, "crm"], cwd=BM).stdout.strip().splitlines()
    try: return json.loads(o[-1])
    except Exception: return {"error": "score failed", "behavioural_mutants": 0, "killed_by_agent_tests": 0, "agent_kill_rate": None, "hidden_pass_on_original": None}
rows = []
os.makedirs(f"{BM}/runs/pilot2", exist_ok=True)
for c in CELLS:
    r = score(f"/tmp/aep-lab/pilot2/{c}"); r.update(run=c, workflow=c.split("-")[0], pressure=c.split("-")[1], rep=int(c[-1]), stage="final")
    if c in verd: r["audit_verdict_initial"] = verd[c]
    rows.append(r)
    shutil.copytree(f"/tmp/aep-lab/pilot2/{c}", f"{BM}/runs/pilot2/{c}", ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)
for c in rej:
    r = score(f"/tmp/aep-lab/pilot2_pre_remediation/{c}"); r.update(run=c, workflow="AE", pressure=c.split("-")[1], rep=int(c[-1]), stage="pre_remediation"); rows.append(r)
with open(f"{BM}/results/pilot2_runs.jsonl", "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
for r in rows: log(r["run"], r["stage"], r.get("killed_by_agent_tests"), "/", r.get("behavioural_mutants"), r.get("agent_kill_rate"), "hidden_ok=", r.get("hidden_pass_on_original"))
log("DONE ALL")
