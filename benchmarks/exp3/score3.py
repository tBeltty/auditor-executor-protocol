#!/usr/bin/env python3
"""Pilot 3 scorer: score3.py <agent_dir>
 correctness_pass: share of hidden-suite tests passing on the agent's crm.py
 tests_total / tests_valid: agent tests, and those passing on the reference crm.py
 fixed_kill_rate: share of behavioural fixed mutants (of the reference) failed by at least one VALID agent test
"""
import sys, re, json, shutil, subprocess, tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
HERE = Path(__file__).resolve().parent
BM = HERE.parent
sys.path.insert(0, str(HERE))
from fixed_mutants import M
REF = (BM / "exp2/reference/crm.py").read_text()
HIDDEN = BM / "exp2/hidden/test_crm.py"
LINE = re.compile(r"^(test\w*) \(([\w.]+)\)(?:\n.*?)? \.\.\. (ok|FAIL|ERROR|skipped.*)$", re.M)

def run_tests(workdir, args, timeout=60):
    try:
        r = subprocess.run([sys.executable, "-m", "unittest", *( [args[0], "-v", *args[1:]] if args[0]=="discover" else ["-v", *args] )], cwd=workdir, capture_output=True, text=True, timeout=timeout)
        out = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return None
    res = {}
    for m in LINE.finditer(out):
        res[m.group(2)] = m.group(3) == "ok"
    return res

def with_code(agent, code, hidden=False):
    d = tempfile.mkdtemp(prefix="s3_")
    if hidden:
        shutil.copy(HIDDEN, d)
    else:
        shutil.copytree(agent, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".git"))
    Path(d, "crm.py").write_text(code)
    return d

def main():
    agent = Path(sys.argv[1])
    src = (agent / "crm.py").read_text()
    d = with_code(agent, src, hidden=True)
    h = run_tests(d, ["test_crm"]) or {}
    shutil.rmtree(d, ignore_errors=True)
    out = {"hidden_total": len(h), "hidden_pass": sum(h.values()), "correctness_pass": (sum(h.values()) / len(h)) if h else 0.0}
    # agent tests on the reference
    d = with_code(agent, REF)
    base = run_tests(d, ["discover", "-s", ".", "-p", "test*.py"]) or {}
    shutil.rmtree(d, ignore_errors=True)
    valid = {k for k, v in base.items() if v}
    out.update(tests_total=len(base), tests_valid=len(valid))
    def one(m):
        name, old, new = m
        code = REF.replace(old, new)
        dh = with_code(agent, code, hidden=True)
        hh = run_tests(dh, ["test_crm"]); shutil.rmtree(dh, ignore_errors=True)
        if hh is not None and all(hh.values()):
            return name, None  # not behavioural w.r.t. hidden suite
        da = with_code(agent, code)
        a = run_tests(da, ["discover", "-s", ".", "-p", "test*.py"], timeout=60); shutil.rmtree(da, ignore_errors=True)
        killed = a is None or any((not a.get(t, False)) for t in valid) or any(t not in a for t in valid)
        return name, killed
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, M))
    beh = [(n, k) for n, k in res if k is not None]
    out.update(mutants_total=len(M), mutants_behavioural=len(beh), killed=sum(1 for _, k in beh if k),
               fixed_kill_rate=(sum(1 for _, k in beh if k) / len(beh)) if beh else None,
               survivors=[n for n, k in beh if not k])
    print(json.dumps(out))

if __name__ == "__main__":
    main()
