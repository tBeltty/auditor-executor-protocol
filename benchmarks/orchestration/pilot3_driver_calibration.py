#!/usr/bin/env python3
import subprocess, json, time, os, shutil, random, sys, re
BM = os.path.expanduser("~/Documents/auditor-executor-protocol/benchmarks")
sys.path.insert(0, BM + "/exp3")
from prompts3 import build
LAB = "/tmp/aep-lab"; MJ = os.path.expanduser("~/.local/state/opencode/model.json")
MODELS = [("deepseek", "opencode-go", "deepseek-v4.1-flash"), ("qwen", "opencode-go", "qwen3.8-flash"), ("glm", "opencode-go", "glm-5.3-flash")]
ARMS = ["U", "U2", "N", "AE"]; PRES = ["neutral", "pressure"]; REPS = [1, 2, 3]
def sh(cmd, **k): return subprocess.run(cmd, capture_output=True, text=True, **k)
def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)
def orca(*a):
    r = sh(["orca", *a, "--json"])
    try: return json.loads(r.stdout)
    except Exception: return {"ok": False, "error": {"message": (r.stdout + r.stderr)[-200:]}}
def set_model(prov, mid):
    m = json.load(open(MJ)); t = {"providerID": prov, "modelID": mid}
    m["recent"] = [t] + [r for r in m["recent"] if r != t]; m.setdefault("variant", {})[f"{prov}/{mid}"] = "high"
    json.dump(m, open(MJ, "w")); time.sleep(2); log("model set", prov, mid)
RUN = None; ack = None
def new_run(obj):
    global RUN, ack
    RUN = orca("orchestration", "run-create", "--objective", obj)["result"]["run"]["id"]; ack = None
def launch(prompt, title):
    r = orca("orchestration", "worker-start", "--run", RUN, "--spec", prompt, "--task-title", title, "--worktree", "current", "--agent", "opencode")
    return r["result"]["dispatchId"] if r.get("ok") else (log("LAUNCH FAIL", title, r["error"]["message"][:120]) or None)
def release(d):
    r = orca("orchestration", "worker-release", "--dispatch", d); st = r.get("result", {}).get("state")
    if st not in ("released", "already_released"):
        for w in orca("orchestration", "worker-list").get("result", {}).get("workers", []):
            if w["dispatchId"] == d and w.get("agentTerminalHandle"): orca("terminal", "close", "--terminal", w["agentTerminalHandle"])
def wave(items, limit_s=1800):
    """items: list of (title, prompt)"""
    global ack
    disp = {}
    for title, prompt in items:
        d = launch(prompt, title)
        if d: disp[d] = title; log("launched", title, d)
        time.sleep(2)
    pending = set(disp); t0 = time.time()
    while pending and time.time() - t0 < limit_s:
        cmd = ["orca", "orchestration", "check", "--run", RUN, "--wait", "--types", "worker_done,escalation,question", "--timeout-ms", "60000", "--json"]
        if ack: cmd += ["--ack", ack]
        out = sh(cmd).stdout
        try: r = json.loads("\n".join(l for l in out.splitlines() if l.strip() and "_keepalive" not in l))["result"]
        except Exception: continue
        if not r["messages"]: continue
        ack = r["deliveryId"]
        for m in r["messages"]:
            p = json.loads(m["payload"])
            if m["type"] == "worker_done" and p["dispatchId"] in pending:
                pending.discard(p["dispatchId"]); log("done", disp[p["dispatchId"]], p.get("outcome"))
            elif m["type"] in ("question", "escalation"): log("QUESTION/ESC", m["subject"][:100])
    for d in pending:
        log("TIMEOUT stop", disp[d]); orca("orchestration", "worker-stop", "--dispatch", d)
    for d in disp: release(d)
    return {disp[d] for d in disp} 
def chunks(l, n): return [l[i:i + n] for i in range(0, len(l), n)]
def verdict(D):
    p = f"{D}/audit.md"
    if not os.path.exists(p): return "MISSING"
    lines = [l.strip() for l in open(p).read().splitlines() if l.strip()]
    last = lines[-1].upper() if lines else ""
    return "APPROVED" if "VERDICT: APPROVED" in last else ("REJECTED" if "VERDICT: REJECTED" in last else "UNPARSED")
def score(D):
    o = sh(["python3", f"{BM}/exp3/score3.py", D], cwd=BM).stdout.strip().splitlines()
    try: return json.loads(o[-1])
    except Exception: return {"error": "score failed"}
def snap(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True); sh(["rsync", "-a", "--exclude", "__pycache__", src + "/", dst + "/"])
def save(path, rows):
    with open(path, "a") as f:
        for r in rows: f.write(json.dumps(r) + "\n")

# ---- calibration (deepseek)
set_model("opencode-go", "deepseek-v4.1-flash"); new_run("Pilot3 auditor calibration")
cal = []
for n in ["gold-1", "gold-2", "gold-3", "bad-1", "bad-2", "bad-3"]:
    D = f"{LAB}/pilot3/calib/{n}"; snap(f"{LAB}/calib/{n}", D); cal.append((n, D))
wave([(f"calib {n}", build("audit", "AE", "neutral", D)) for n, D in cal])
res = {n: verdict(D) for n, D in cal}; log("calibration", res)
json.dump(res, open(f"{BM}/results/pilot3_calibration.json", "w"), indent=1)
shutil.copytree(f"{LAB}/pilot3/calib", f"{BM}/runs/pilot3/calib", ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)

for key, prov, mid in MODELS:
    t_block = time.time() * 1000
    set_model(prov, mid); new_run(f"Pilot3 {key}")
    cells = [(a, p, r) for a in ARMS for p in PRES for r in REPS]; random.Random(key).shuffle(cells)
    Dof = lambda a, p, r: f"{LAB}/pilot3/{key}/{a}-{p}-{r}"
    for a, p, r in cells: os.makedirs(Dof(a, p, r), exist_ok=True)
    for ch in chunks(cells, 6):
        wave([(f"{key} exec {a}-{p}-{r}", build("exec", a, p, Dof(a, p, r))) for a, p, r in ch])
    # U2 review + AE audit
    for a, p, r in cells:
        if a == "U2": snap(Dof(a, p, r), f"{LAB}/pilot3_pre/{key}/{a}-{p}-{r}")
    follow = [(f"{key} review {a}-{p}-{r}", build("review", a, p, Dof(a, p, r))) for a, p, r in cells if a == "U2"] + \
             [(f"{key} audit {a}-{p}-{r}", build("audit", a, p, Dof(a, p, r))) for a, p, r in cells if a == "AE"]
    for ch in chunks(follow, 6): wave(ch)
    verd = {f"AE-{p}-{r}": verdict(Dof("AE", p, r)) for a, p, r in cells if a == "AE"}; log(key, "verdicts", verd)
    rej = [c for c, v in verd.items() if v != "APPROVED"]
    for c in rej: snap(f"{LAB}/pilot3/{key}/{c}", f"{LAB}/pilot3_pre/{key}/{c}")
    for ch in chunks(rej, 6):
        wave([(f"{key} remediate {c}", build("remediate", "AE", c.split("-")[1], f"{LAB}/pilot3/{key}/{c}")) for c in ch])
    rows = []
    for a, p, r in cells:
        D = Dof(a, p, r); row = score(D); row.update(model=key, arm=a, pressure=p, rep=r, stage="final")
        if a == "AE": row["audit_verdict_initial"] = verd[f"{a}-{p}-{r}"]
        rows.append(row)
        if a == "U2" or (a == "AE" and f"AE-{p}-{r}" in rej):
            row2 = score(f"{LAB}/pilot3_pre/{key}/{a}-{p}-{r}"); row2.update(model=key, arm=a, pressure=p, rep=r, stage="pre_second_session"); rows.append(row2)
        log(key, f"{a}-{p}-{r}", row.get("fixed_kill_rate"), row.get("correctness_pass"))
    save(f"{BM}/results/pilot3_runs.jsonl", rows)
    shutil.copytree(f"{LAB}/pilot3/{key}", f"{BM}/runs/pilot3/{key}", ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)
    # model verification from exported sessions created during this block
    ses = json.loads(sh(["opencode", "session", "list", "-n", "400", "--format", "json"], cwd=os.path.expanduser("~")).stdout or "[]")
    cnt = {}
    for s in ses:
        if s["created"] < t_block: continue
        e = sh(["opencode", "session", "export", s["id"]], cwd=os.path.expanduser("~")).stdout
        m = set(re.findall(r'"model": ?\{\s*"id": "([^"]+)",\s*"providerID": "([^"]+)",\s*"variant": "([^"]+)"', e))
        for x in m: cnt["/".join(x)] = cnt.get("/".join(x), 0) + 1
    json.dump(cnt, open(f"{BM}/results/pilot3_model_check_{key}.json", "w"), indent=1); log(key, "model check", cnt)
shutil.copy(f"{LAB}/orch/pilot3.log", f"{BM}/results/pilot3_driver.log")
shutil.copy("/tmp/model.json.bak", MJ); log("model.json restored"); log("DONE ALL")
