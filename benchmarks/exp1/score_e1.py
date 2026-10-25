#!/usr/bin/env python3
"""Scores Part B run directories (S-* spec-first, O-* opportunity-shaped).
usage: score_e1.py <runs_dir>   -> prints a JSON list and a summary.
All numbers are measured from the files the agents produced."""
import ast, json, re, statistics, subprocess, sys
from pathlib import Path

INFRA = re.compile(r"\b(kafka|redis|rabbitmq|celery|sqs|kubernetes|zookeeper|postgres|nats|mongodb)\b", re.I)


def loc(p):
    return sum(1 for l in p.read_text(errors="ignore").splitlines() if l.strip() and not l.strip().startswith("#"))


def words(paths):
    return sum(len(p.read_text(errors="ignore").split()) for p in paths if p.is_file())


def score(d: Path):
    cond = d.name.split("-")[0]
    py = [p for p in d.rglob("*.py") if "__pycache__" not in p.parts]
    tests = [p for p in py if p.name.startswith("test")]
    impl = [p for p in py if p not in tests]
    docs = ([d / "spec.md", d / "plan.md", d / "tasks.md"] if cond == "S"
            else [d / "plan-of-record.md", d / "execution-guide.md"])
    task_file = d / ("tasks.md" if cond == "S" else "execution-guide.md")
    plan_file = d / ("plan.md" if cond == "S" else "plan-of-record.md")
    ttxt = task_file.read_text(errors="ignore") if task_file.is_file() else ""
    ptxt = plan_file.read_text(errors="ignore") if plan_file.is_file() else ""
    m = re.findall(r"NEW_INFRA:\s*(.*)", ptxt)
    std = set(sys.stdlib_module_names)
    third = set()
    for p in impl + tests:
        try:
            for n in ast.walk(ast.parse(p.read_text(errors="ignore"))):
                mods = [a.name for a in n.names] if isinstance(n, ast.Import) else (
                    [n.module] if isinstance(n, ast.ImportFrom) and n.module and n.level == 0 else [])
                for x in mods:
                    top = x.split(".")[0]
                    if top not in std and not (d / f"{top}.py").exists() and not (d / top).is_dir():
                        third.add(top)
        except SyntaxError:
            pass
    sel = re.search(r"selected option[^\n]*?option\s*([ABC])", ptxt, re.I | re.S) if cond == "O" else None
    rc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(d), "-p", "test*.py"],
                        capture_output=True, cwd=d, timeout=120).returncode if tests else None
    return {"run": d.name, "cond": cond, "impl_loc": sum(loc(p) for p in impl), "test_loc": sum(loc(p) for p in tests),
            "tests_pass": rc == 0 if rc is not None else None, "doc_words": words(docs),
            "tasks": len(re.findall(r"TASK\s*\d+", ttxt)), "new_infra": (m[-1].strip() if m else None),
            "third_party_imports": sorted(third), "infra_terms_in_plan": len(INFRA.findall(ptxt)),
            "selected_option": (sel.group(1).upper() if sel else None)}


def main():
    root = Path(sys.argv[1]).resolve()
    rows = [score(d) for d in sorted(root.iterdir()) if d.is_dir()]
    print(json.dumps(rows, indent=1))
    for c in ("S", "O"):
        r = [x for x in rows if x["cond"] == c]
        if not r:
            continue
        f = lambda k: (round(statistics.mean(x[k] for x in r), 1), min(x[k] for x in r), max(x[k] for x in r))
        print(c, "n=", len(r), "impl_loc(mean,min,max)=", f("impl_loc"), "doc_words=", f("doc_words"), "tasks=", f("tasks"))


if __name__ == "__main__":
    main()
