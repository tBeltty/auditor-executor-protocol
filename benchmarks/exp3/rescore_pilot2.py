#!/usr/bin/env python3
"""Rescore Pilot 2 runs with the 66-test hidden suite that Pilot 2 used (exp2/hidden/test_crm_v66.py,
sha256 e977915d...). Builds a temporary tree so the frozen exp2/score.py is used unchanged."""
import json, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
BM = Path(__file__).resolve().parent.parent
tmp = Path(tempfile.mkdtemp(prefix="p2_"))
shutil.copy(BM / "exp2/score.py", tmp / "score.py")
(tmp / "hidden").mkdir()
shutil.copy(BM / "exp2/hidden/test_crm_v66.py", tmp / "hidden/test_crm.py")
stored = {r["run"]: r for r in map(json.loads, open(BM / "results/pilot2_runs.jsonl")) if r["stage"] == "final"}
def one(run):
    o = subprocess.run([sys.executable, str(tmp / "score.py"), str(BM / "runs/pilot2" / run), "crm"], capture_output=True, text=True).stdout.strip().splitlines()
    return run, json.loads(o[-1])
with ThreadPoolExecutor(6) as ex:
    res = dict(ex.map(one, sorted(stored)))
bad = [r for r in stored if (res[r]["killed_by_agent_tests"], res[r]["behavioural_mutants"]) != (stored[r]["killed_by_agent_tests"], stored[r]["behavioural_mutants"])]
print(f"{len(stored) - len(bad)} of {len(stored)} Pilot 2 runs reproduce exactly; mismatches: {bad}")
shutil.rmtree(tmp, ignore_errors=True)
