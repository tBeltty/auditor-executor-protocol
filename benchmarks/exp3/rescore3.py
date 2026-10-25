#!/usr/bin/env python3
"""Rescore every Pilot 3 row with the corrected oracle (see pilot/PILOT3_ORACLE_CORRECTION.md).
Reads results/pilot3_runs_original_oracle.jsonl, writes results/pilot3_runs.jsonl."""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
BM = Path(__file__).resolve().parent.parent
rows = [json.loads(l) for l in open(BM / "results/pilot3_runs_original_oracle.jsonl")]
def d(r):
    model = "deepseek-rerun" if r["model"] == "deepseek" else r["model"]
    base = "runs/pilot3" if r["stage"] == "final" else "runs/pilot3_pre"
    return BM / base / model / f'{r["arm"]}-{r["pressure"]}-{r["rep"]}'
def one(r):
    o = subprocess.run([sys.executable, str(BM / "exp3/score3.py"), str(d(r))], capture_output=True, text=True)
    new = json.loads(o.stdout.strip().splitlines()[-1])
    keep = {k: r[k] for k in ("model", "arm", "pressure", "rep", "stage", "audit_verdict_initial") if k in r}
    return {**new, **keep}
with ThreadPoolExecutor(3) as ex:
    out = list(ex.map(one, rows))
with open(BM / "results/pilot3_runs.jsonl", "w") as f:
    for r in out: f.write(json.dumps(r) + "\n")
print(len(out), "rows rescored")
