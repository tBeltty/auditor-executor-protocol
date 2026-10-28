#!/usr/bin/env python3
"""Sensitivity check for the Pilot 3 scorer: check_subtest_sensitivity.py [--jobs N]

score3.py reads the verbose output of unittest with a single-line pattern and counts a valid test
that is absent from that output as a kill. Since Python 3.11, `unittest -v` prints a failing
subTest on its own indented line, so a test whose subtest fails can be absent from the parse.

For every final Pilot 3 run in results/pilot3_runs.jsonl this script
  1. counts the behavioural mutants on which a valid test is absent from the single-line parse,
     and checks that each absent test appears on an indented subTest FAIL or ERROR line;
  2. rescores the run with a collector that records each test's outcome through the unittest
     result API (no output parsing) and compares valid tests, kills, and surviving mutants with
     the stored row.
Requires Python >= 3.11. Prints one JSON line per run and a summary, and writes both to
results/pilot3_subtest_check.json.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
BM = HERE.parent
sys.path.insert(0, str(HERE))
from fixed_mutants import M  # noqa: E402

REF = (BM / "exp2/reference/crm.py").read_text()
HIDDEN = BM / "exp2/hidden/test_crm.py"
LINE = re.compile(r"^(test\w*) \(([\w.]+)\)(?:\n.*?)? \.\.\. (ok|FAIL|ERROR|skipped.*)$", re.M)  # as in score3.py
SUB = re.compile(r"^\s+test\w* \(([\w.]+)\).* \.\.\. (FAIL|ERROR)$", re.M)

COLLECT = r"""
import json, os, sys, unittest
sys.path.insert(0, os.getcwd())
class R(unittest.TestResult):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.o = {}
    def addSuccess(self, t): self.o.setdefault(t.id(), 'ok')
    def addFailure(self, t, e): super().addFailure(t, e); self.o[t.id()] = 'fail'
    def addError(self, t, e): super().addError(t, e); self.o[t.id()] = 'error'
    def addSkip(self, t, r): self.o.setdefault(t.id(), 'skip')
    def addSubTest(self, t, st, e):
        if e is not None: self.o[t.id()] = 'fail'
L = unittest.TestLoader()
s = L.discover('.', pattern='test*.py') if sys.argv[1] == 'discover' else L.loadTestsFromName(sys.argv[1])
r = R(); s.run(r)
print(json.dumps({'o': r.o, 'loader_errors': [str(e) for e in L.errors]}))
"""


def workdir(agent, code, hidden):
    d = tempfile.mkdtemp(prefix="s3chk_")
    if hidden:
        shutil.copy(HIDDEN, d)
    else:
        shutil.copytree(agent, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".git"))
    Path(d, "crm.py").write_text(code)
    return d


def collect(d, target, timeout=60):
    try:
        p = subprocess.run([sys.executable, "-c", COLLECT, target], cwd=d, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    return json.loads(p.stdout.strip().splitlines()[-1])


def verbose(d, timeout=60):
    try:
        p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-v", "-s", ".", "-p", "test*.py"],
                           cwd=d, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    return p.stdout + p.stderr


def behavioural(m):
    name, old, new = m
    d = workdir(None, REF.replace(old, new), True)
    r = collect(d, "test_crm")
    shutil.rmtree(d, ignore_errors=True)
    return name, r is None or bool(r["loader_errors"]) or any(v != "ok" for v in r["o"].values())


def check_run(row, beh, jobs):
    model = "deepseek-rerun" if row["model"] == "deepseek" else row["model"]
    agent = BM / "runs/pilot3" / model / f'{row["arm"]}-{row["pressure"]}-{row["rep"]}'
    d = workdir(agent, REF, False)
    base = collect(d, "discover", 120)
    base_txt = verbose(d, 120)
    shutil.rmtree(d, ignore_errors=True)
    valid = {k for k, v in base["o"].items() if v == "ok"}
    valid_regex = {m.group(2) for m in LINE.finditer(base_txt) if m.group(3) == "ok"}

    def one(m):
        name, old, new = m
        d = workdir(agent, REF.replace(old, new), False)
        r = collect(d, "discover")
        txt = verbose(d)
        shutil.rmtree(d, ignore_errors=True)
        killed = r is None or bool(r["loader_errors"]) or any(r["o"].get(t) != "ok" for t in valid)
        absent, explained = False, True
        if txt is not None:
            parsed = {mm.group(2) for mm in LINE.finditer(txt)}
            sub = {mm.group(1) for mm in SUB.finditer(txt)}
            missing = [t for t in valid_regex if t not in parsed]
            absent = bool(missing)
            explained = all(t in sub for t in missing)
        return name, killed, absent, explained

    with ThreadPoolExecutor(jobs) as ex:
        res = list(ex.map(one, [m for m in M if m[0] in beh]))
    survivors = sorted(n for n, k, _, _ in res if not k)
    return {
        "run": f'{row["model"]}/{row["arm"]}-{row["pressure"]}-{row["rep"]}',
        "valid_same": len(valid) == row["tests_valid"] and valid == valid_regex,
        "killed": sum(k for _, k, _, _ in res), "stored_killed": row["killed"],
        "survivors_same": survivors == sorted(row["survivors"]),
        "mutants_with_absent_test": sum(a for _, _, a, _ in res),
        "absences_on_subtest_lines": all(e for _, _, a, e in res if a),
    }


def main():
    if sys.version_info < (3, 11):
        sys.exit("Python >= 3.11 is required (older unittest output omits the test method name)")
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 8
    with ThreadPoolExecutor(jobs) as ex:
        beh = {n for n, b in ex.map(behavioural, M) if b}
    rows = [json.loads(l) for l in open(BM / "results/pilot3_runs.jsonl")]
    rows = [r for r in rows if r["stage"] == "final"]
    out = []
    for row in rows:
        rec = check_run(row, beh, jobs)
        out.append(rec)
        print(json.dumps(rec), flush=True)
    hit = [r["mutants_with_absent_test"] for r in out if r["mutants_with_absent_test"]]
    same = sum(r["valid_same"] and r["killed"] == r["stored_killed"] and r["survivors_same"] for r in out)
    summary = {
        "runs": len(out), "behavioural_mutants": len(beh),
        "runs_identical_to_stored": same,
        "runs_with_absent_tests": len(hit),
        "absent_mutants_per_run": [min(hit), max(hit)] if hit else None,
        "all_absences_on_subtest_lines": all(r["absences_on_subtest_lines"] for r in out),
    }
    with open(BM / "results/pilot3_subtest_check.json", "w") as f:
        json.dump({"summary": summary, "runs": out}, f, indent=1)
        f.write("\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
