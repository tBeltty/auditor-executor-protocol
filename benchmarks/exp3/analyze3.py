#!/usr/bin/env python3
"""Pilot 3 analysis (descriptive). Reads results/pilot3_runs.jsonl and driver logs for timeouts."""
import json, re, statistics as st, sys, collections
BM = "/Users/jhonatan/Documents/auditor-executor-protocol/benchmarks"
rows = [json.loads(l) for l in open(f"{BM}/results/pilot3_runs.jsonl")]
# cells whose Executor was stopped by the wave time limit
to = set()
for log, pre in [(f"{BM}/results/pilot3_driver_main.log", None), (f"{BM}/results/pilot3_driver_deepseek_rerun.log", None)]:
    try: txt = open(log).read()
    except FileNotFoundError: continue
    for m in re.finditer(r"TIMEOUT stop (\S+) exec (\S+)", txt):
        key = m.group(1)
        if key == "deepseek": continue  # first DeepSeek block is quarantined (contaminated); only the clean rerun counts
        to.add((key.replace("-rerun", ""), m.group(2)))
fin = [r for r in rows if r["stage"] == "final" and r.get("fixed_kill_rate") is not None]
for r in fin: r["timed_out"] = (r["model"], f'{r["arm"]}-{r["pressure"]}-{r["rep"]}') in to
def mean(v): return sum(v) / len(v) if v else float("nan")
def table(sub, label):
    print(f"\n{label}  (n runs = {len(sub)})")
    print(f"{'arm':4}{'neutral':>22}{'pressure':>22}")
    for a in ("U", "U2", "N", "AE"):
        cells = []
        for p in ("neutral", "pressure"):
            v = [r["fixed_kill_rate"] for r in sub if r["arm"] == a and r["pressure"] == p]
            cells.append(f"{mean(v):.3f} [{min(v):.2f}-{max(v):.2f}] n={len(v)}" if v else "-")
        print(f"{a:4}{cells[0]:>22}{cells[1]:>22}")
table(fin, "POOLED fixed-mutant kill rate (all models, all runs)")
table([r for r in fin if not r["timed_out"]], "POOLED excluding Executor runs stopped by the time limit")
for m in ("deepseek", "qwen", "glm"):
    table([r for r in fin if r["model"] == m], f"MODEL {m}")
print("\nCorrectness (share of hidden tests passing), pooled:")
for a in ("U", "U2", "N", "AE"):
    print(f"  {a:3}", " ".join(f"{p[:3]}={mean([r['correctness_pass'] for r in fin if r['arm']==a and r['pressure']==p]):.3f}" for p in ("neutral", "pressure")))
print("\nPaired difference vs U (same model, pressure, mean over models), fixed kill rate:")
for a in ("U2", "N", "AE"):
    d = []
    for m in ("deepseek", "qwen", "glm"):
        for p in ("neutral", "pressure"):
            x = [r["fixed_kill_rate"] for r in fin if r["model"] == m and r["arm"] == a and r["pressure"] == p]
            u = [r["fixed_kill_rate"] for r in fin if r["model"] == m and r["arm"] == "U" and r["pressure"] == p]
            if x and u: d.append(mean(x) - mean(u))
    print(f"  {a:3} mean diff {mean(d):+.3f}  over {len(d)} model x pressure cells; per-cell: {[round(x,3) for x in d]}")
print("\nAE Auditor verdicts (initial):", dict(collections.Counter((r['model'], r['audit_verdict_initial']) for r in fin if r['arm'] == 'AE')))
pre = [r for r in rows if r["stage"] == "pre_second_session"]
for a in ("U2", "AE"):
    x = [(r["fixed_kill_rate"], next((f["fixed_kill_rate"] for f in fin if (f["model"], f["arm"], f["pressure"], f["rep"]) == (r["model"], r["arm"], r["pressure"], r["rep"])), None)) for r in pre if r["arm"] == a and r.get("fixed_kill_rate") is not None]
    x = [(b, c) for b, c in x if c is not None]
    if x: print(f"  {a} second session: before {mean([b for b,_ in x]):.3f} -> after {mean([c for _,c in x]):.3f} (n={len(x)})")
print("\nTimed-out Executor runs:", sorted(to))
print("Within-cell SD (pooled over models) vs arm gaps:")
sds = [st.pstdev([r["fixed_kill_rate"] for r in fin if r["arm"] == a and r["pressure"] == p]) for a in ("U", "U2", "N", "AE") for p in ("neutral", "pressure") if len([r for r in fin if r["arm"] == a and r["pressure"] == p]) > 1]
print(f"  mean within-cell SD = {mean(sds):.3f}")
