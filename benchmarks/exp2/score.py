#!/usr/bin/env python3
"""Independent mutation oracle for Part C.

usage: score.py <agent_dir> <module_name>

Generates generic AST mutants of <agent_dir>/<module_name>.py, runs a HIDDEN reference
suite (hidden/test_<module>.py) and the AGENT's own tests on every mutant, and reports:
  - hidden_pass_on_original: does the agent's implementation meet the contract at all
  - agent_pass_on_original: do the agent's own tests pass on its code
  - behavioural mutants = mutants the hidden suite kills (verifiably change behaviour)
  - agent_kill_rate = share of behavioural mutants that the agent's tests also kill
The mutation operators are generic (comparison flips, condition forced True/False,
and/or swap, raise removal, not removal, +/-, int+1); they know nothing about aepkit.
"""
import ast, copy, json, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CMP = {ast.Eq: [ast.NotEq], ast.NotEq: [ast.Eq], ast.Lt: [ast.GtE, ast.LtE], ast.LtE: [ast.Gt, ast.Lt],
       ast.Gt: [ast.LtE, ast.GtE], ast.GtE: [ast.Lt, ast.Gt], ast.In: [ast.NotIn], ast.NotIn: [ast.In],
       ast.Is: [ast.IsNot], ast.IsNot: [ast.Is]}


class Mut(ast.NodeTransformer):
    def __init__(self, target=None):
        self.target = target; self.i = 0; self.counts = []

    def _site(self, alts):
        idx = self.i; self.i += 1
        if self.target is None:
            self.counts.append(len(alts)); return None
        return self.target[1] if idx == self.target[0] else None

    def visit_Compare(self, n):
        self.generic_visit(n)
        alts = CMP.get(type(n.ops[0]), [])
        a = self._site(alts)
        if a is not None and alts:
            m = copy.deepcopy(n); m.ops[0] = alts[a](); return m
        return n

    def _test(self, n):
        self.generic_visit(n)
        a = self._site([0, 1])
        if a is not None:
            n.test = ast.Constant(value=bool(a)); 
        return n
    visit_If = visit_While = visit_IfExp = _test

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        a = self._site([0])
        if a is not None:
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        return n

    def visit_Raise(self, n):
        a = self._site([0])
        return ast.Pass() if a is not None else n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, ast.Not):
            a = self._site([0])
            if a is not None: return n.operand
        return n

    def visit_BinOp(self, n):
        self.generic_visit(n)
        if isinstance(n.op, (ast.Add, ast.Sub)):
            a = self._site([0])
            if a is not None: n.op = ast.Sub() if isinstance(n.op, ast.Add) else ast.Add()
        return n

    def visit_Constant(self, n):
        if isinstance(n.value, int) and not isinstance(n.value, bool):
            a = self._site([0])
            if a is not None: return ast.Constant(value=n.value + 1)
        return n


def run(cmd, cwd, timeout=10):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        return 124


def mutants(src):
    tree = ast.parse(src)
    probe = Mut(); probe.visit(copy.deepcopy(tree))
    for site, n in enumerate(probe.counts):
        for alt in range(n):
            t = copy.deepcopy(tree); m = Mut(target=(site, alt)); t = m.visit(t); ast.fix_missing_locations(t)
            out = ast.unparse(t)
            if out != ast.unparse(tree):
                yield (site, alt), out


def agent_tests_cmd():
    return [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test*.py"]


def main():
    agent, mod = Path(sys.argv[1]), sys.argv[2]
    src = (agent / f"{mod}.py").read_text(encoding="utf-8")
    hidden_test = HERE / "hidden" / f"test_{mod}.py"

    def hidden_rc(code):
        with tempfile.TemporaryDirectory() as d:
            Path(d, f"{mod}.py").write_text(code, encoding="utf-8")
            shutil.copy(hidden_test, d)
            return run([sys.executable, "-m", "unittest", "-q", f"test_{mod}"], d)

    def agent_rc(code):
        with tempfile.TemporaryDirectory() as d:
            shutil.copytree(agent, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".git"))
            Path(d, f"{mod}.py").write_text(code, encoding="utf-8")
            return run(agent_tests_cmd(), d)

    res = {"module": mod, "hidden_pass_on_original": hidden_rc(src) == 0,
           "agent_pass_on_original": agent_rc(src) == 0,
           "agent_test_files": sorted(p.name for p in agent.glob("test*.py"))}
    kills_h = kills_a = total = 0
    survivors = []
    for key, code in mutants(src):
        total += 1
        h = hidden_rc(code) != 0
        if not h:
            continue
        kills_h += 1
        a = agent_rc(code) != 0
        kills_a += a
        if not a:
            survivors.append(key)
    res.update({"mutants_total": total, "behavioural_mutants": kills_h,
                "killed_by_agent_tests": kills_a,
                "agent_kill_rate": (kills_a / kills_h if kills_h else None),
                "surviving_behavioural_mutants": len(survivors)})
    print(json.dumps(res))


if __name__ == "__main__":
    main()
