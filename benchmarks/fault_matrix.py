#!/usr/bin/env python3
"""Executed fault-coverage matrix for aepkit (paper replication, Part A).

Every cell of the matrix is the exit status of a command that this script runs.
Nothing is hard-coded. Conditions:

  C1  standard test runner (python -m unittest) on the same artifacts
  C2  a small Spec-First checklist checker defined in this file (a model of
      checklist-style completion checks, NOT AWS Kiro or GitHub Spec Kit)
  C3  auditor-executor-protocol 0.4.0 from PyPI (role separation + lint +
      negcontrol, no --expect, no ODD shaping gate)
  C3b auditor-executor-protocol 0.5.2 from PyPI (adds --expect, still no ODD gate)
  C4  aepkit 0.6.0 from PyPI (ODD shaping gate + --expect + deferred ledger)

The 16 faults were written by the tool author to exercise specific mechanisms.
The matrix therefore measures MECHANISM COVERAGE on constructed faults, not
effectiveness on naturally occurring faults. It also runs clean artifacts
through every condition to measure false positives.

Usage:  python3 benchmarks/fault_matrix.py [--out results/fault_matrix.json]
Needs network access to PyPI the first time (creates throw-away venvs).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
import tempfile
import time
import venv
from pathlib import Path

VERSIONS = {
    "C3": ("auditor-executor-protocol==0.4.0", "auditkit"),
    "C3b": ("auditor-executor-protocol==0.5.2", "auditkit"),
    "C4": ("aepkit==0.6.0", "aepkit"),
}


def sh(args, cwd=None, timeout=60):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def make_venvs(root: Path) -> dict[str, str]:
    bins = {}
    for cond, (spec, exe) in VERSIONS.items():
        d = root / f"venv_{cond}"
        venv.create(d, with_pip=True)
        rc, out = sh([str(d / "bin" / "pip"), "install", "-q", spec], timeout=300)
        if rc != 0:
            sys.exit(f"pip install {spec} failed:\n{out}")
        bins[cond] = str(d / "bin" / exe)
    return bins


# ---------------------------------------------------------------- fixtures

def plan_full() -> str:
    return """# plan — Plan of Record

## 1. Why this exists (opportunity framing)
- **Target outcome:** Reduce webhook delivery retry latency p99 from 14.2s to under 1.5s without dropping events.
- **Problem / friction:** Synchronous HTTP webhook dispatch blocks worker threads during downstream timeouts.
- **Cost of doing nothing:** Worker pool exhaustion during peak traffic causes 8% order-confirmation delay.

## 3. Opportunity shaping & decisions
- **Option A (minimal / existing tooling / config-only):** SQLite WAL outbox table with a stdlib asyncio poller.
- **Option B (balanced / pragmatic implementation):** Redis-backed task queue with a dedicated worker container.
- **Option C (full architectural / custom build):** Distributed event mesh with a dead-letter microservice.
- **Selected option & rationale:** Option A wins because peak throughput is 40 webhooks/sec, well within single-node capacity.
- **Riskiest assumption & first-phase validation:** SQLite WAL write contention under a 100 req/s burst; validated in P0-T1.

## 4. What this deliberately does not do
- **Explicit non-goals:** Multi-region replication and a customer retry UI.

## 6. Deferred items ledger
| ID | What | Deferred to | Closed by |
|---|---|---|---|
| D-1 | Add dead-letter admin CLI | Phase 0 | P0-T1 |
"""


def plan_bypass() -> str:
    na = "N/A (Deterministic Fix/Compliance)"
    return f"""# plan — Plan of Record

## 1. Why this exists (opportunity framing)
- **Target outcome:** Zero unauthorized cross-tenant reads on /api/v1/invoices (HTTP 403 enforced).
- **Problem / friction:** A missing tenant_id predicate lets a Tenant A user read Tenant B records.
- **Cost of doing nothing:** Cross-tenant data exposure violating an isolation commitment.

## 3. Opportunity shaping & decisions
- **Option A (minimal / existing tooling / config-only):** {na}
- **Option B (balanced / pragmatic implementation):** {na}
- **Option C (full architectural / custom build):** {na}
- **Selected option & rationale:** {na} mandatory security boundary patch.
- **Riskiest assumption & first-phase validation:** {na} deterministic predicate fix.

## 4. What this deliberately does not do
- **Explicit non-goals:** No billing schema redesign and no OAuth token changes.

## 6. Deferred items ledger
| ID | What | Deferred to | Closed by |
|---|---|---|---|
"""


EXEC_GUIDE = """# plan — Execution Guide

### P0-T1 — Implement tenant isolation check
- **Report:** `P0-T1`
- **Verify:** `pytest -q`

### P0-G1 — Gate: Tenant boundary verified
- **Report:** `P0-G1`
- **Negative control:** Remove `tenant_id` check from `auth.py` and confirm `pytest` fails with `403 Forbidden AssertionError`.
"""

COMPLIANCE = """# plan — Compliance Log

| ID | Kind | Status | Verdict |
|---|---|---|---|
| P0-T1 | Task | DONE | APPROVED |
| P0-G1 | Gate | DONE | APPROVED |

### P0-T1 — DONE
**Verify output:**
```text
2 passed in 0.04s
```

### P0-G1 — DONE
**Verify output:**
```text
[negcontrol] break applied -> test failed as expected (AssertionError: 403 != 200) -> restored byte-identical -> 2 passed.
```
"""

NEG = "Remove `tenant_id` check from `auth.py` and confirm `pytest` fails with `403 Forbidden AssertionError`."


def make_run(root: Path, name: str, plan: str | None = None) -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "annexes").mkdir()
    (d / "plan-of-record.md").write_text(plan or plan_full(), encoding="utf-8")
    (d / "execution-guide.md").write_text(EXEC_GUIDE, encoding="utf-8")
    (d / "compliance-log.md").write_text(COMPLIANCE, encoding="utf-8")
    return d


def edit(d: Path, fname: str, old: str, new: str, append: bool = False):
    p = d / fname
    t = p.read_text(encoding="utf-8")
    if append:
        p.write_text(t + new, encoding="utf-8")
        return
    assert old in t, f"fixture drift: {old!r} not in {fname}"
    p.write_text(t.replace(old, new), encoding="utf-8")


def build_lint_faults(root: Path) -> list[tuple[str, str, str, Path]]:
    out = []

    def add(fid, cat, desc, d):
        out.append((fid, cat, desc, d))

    d = make_run(root, "f01"); edit(d, "compliance-log.md", "```text\n2 passed in 0.04s\n```", "Verified manually, all tests pass.")
    add("F01", "Evidence", "DONE claimed with prose instead of terminal output", d)
    d = make_run(root, "f02"); edit(d, "compliance-log.md", "2 passed in 0.04s", "TBD")
    add("F02", "Evidence", "Deferred placeholder (TBD) inside the evidence block", d)
    d = make_run(root, "f03"); edit(d, "execution-guide.md", f"- **Negative control:** {NEG}\n", "")
    add("F03", "Gate", "Phase gate omits the negative control", d)
    d = make_run(root, "f04"); edit(d, "execution-guide.md", NEG, "N/A — not needed for this gate.")
    add("F04", "Gate", "Phase gate waives the negative control", d)
    d = make_run(root, "f05"); edit(d, "execution-guide.md", NEG, "Removing `tenant_id` check would probably fail in theory.")
    add("F05", "Gate", "Negative control is a hedge (would probably fail)", d)
    d = make_run(root, "f06"); edit(d, "execution-guide.md", NEG, "Comment out the middleware in `auth.py` during testing.")
    add("F06", "Gate", "Negative control states an action without a failure oracle", d)
    d = make_run(root, "f07"); edit(d, "execution-guide.md", "", "\n### P0-T2 — Add rate limiter\n- **Report:** `P0-T2`\n", append=True)
    add("F07", "Scope", "Task in the guide has no report in the log", d)
    d = make_run(root, "f08"); edit(d, "compliance-log.md", "", "\n### P0-T99 — DONE\n**Verify output:**\n```text\n1 passed\n```\n", append=True)
    add("F08", "Scope", "Orphan report in the log (unauthorized scope)", d)
    d = make_run(root, "f09")
    edit(d, "execution-guide.md", "", "\n### P1-T1 — Next phase work\n- **Report:** `P1-T1`\n", append=True)
    edit(d, "compliance-log.md", "| P0-G1 | Gate | DONE | APPROVED |", "| P0-G1 | Gate | DONE | CONDITIONAL |")
    edit(d, "compliance-log.md", "", "\n### P1-T1 — DONE\n**Verify output:**\n```text\n1 passed\n```\n", append=True)
    add("F09", "Order", "Phase 1 work reported while the Phase 0 gate is CONDITIONAL", d)
    d = make_run(root, "f10"); edit(d, "plan-of-record.md", "| D-1 | Add dead-letter admin CLI | Phase 0 | P0-T1 |", "| D-1 | Add dead-letter admin CLI | Phase 0 | TBD |")
    add("F10", "Deferred debt", "Phase closed while a deferred-ledger row is still TBD", d)
    d = make_run(root, "f11", plan="# Plan of Record\n\n## 1. Why this exists\nBuild the Kafka webhook mesh.\n")
    add("F11", "ODD", "No opportunity framing or cost of doing nothing", d)
    d = make_run(root, "f12"); edit(d, "plan-of-record.md", "- **Option B (balanced / pragmatic implementation):** Redis-backed task queue with a dedicated worker container.", "- **Option B (balanced / pragmatic implementation):** TBD")
    add("F12", "ODD", "Single-option bias: Option B left TBD without the bypass token", d)
    return out


# ------------------------------------------------- C2: checklist model

def c2_checklist(d: Path) -> int:
    """Spec-First checklist model: required files exist and every task id in the
    execution guide has a completed report in the log. Returns non-zero if it flags."""
    need = ["plan-of-record.md", "execution-guide.md", "compliance-log.md"]
    if any(not (d / n).is_file() for n in need):
        return 1
    guide = (d / "execution-guide.md").read_text(encoding="utf-8")
    log = (d / "compliance-log.md").read_text(encoding="utf-8")
    tasks = re.findall(r"^###\s+(P\d+-T\d+)\b", guide, re.M)
    done = set(re.findall(r"^###\s+(P\d+-T\d+)\s+—\s+DONE", log, re.M))
    return 1 if set(tasks) - done else 0


# ----------------------------------------------------- code-level faults

GOOD_SERVICE = '''def get_invoice(user_tenant, invoice_tenant, is_authenticated):
    if not is_authenticated:
        raise PermissionError("401 Unauthorized: authentication required")
    if user_tenant != invoice_tenant:
        raise PermissionError("403 Forbidden: cross-tenant access denied")
    return {"status": 200, "data": "invoice_payload"}
'''
TAUTOLOGICAL = '''import unittest
from auth_service import get_invoice
class T(unittest.TestCase):
    def test_happy_path_only(self):
        self.assertEqual(get_invoice("a", "a", True)["status"], 200)
unittest.main()
'''
REAL = '''import unittest
from auth_service import get_invoice
class T(unittest.TestCase):
    def test_cross_tenant_blocked(self):
        with self.assertRaisesRegex(PermissionError, "403 Forbidden"):
            get_invoice("a", "b", True)
unittest.main()
'''
BREAK_GUARD = "python3 -c \"p=open('auth_service.py').read().replace('user_tenant != invoice_tenant','False');open('auth_service.py','w').write(p)\""
BREAK_SYNTAX = "python3 -c \"open('auth_service.py','a').write('\\ndef broken(:\\n')\""
BREAK_HANG = "python3 -c \"p=open('auth_service.py').read().replace('if user_tenant != invoice_tenant:','while True: pass\\n    if False:');open('auth_service.py','w').write(p)\""


def lab(root: Path, name: str, test_src: str) -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "auth_service.py").write_text(GOOD_SERVICE, encoding="utf-8")
    (d / "test_x.py").write_text(test_src, encoding="utf-8")
    return d


def negcontrol(bin_: str, d: Path, break_cmd: str, expect: str | None, supports_expect: bool,
               restore: str | None = None, timeout: int | None = 5, use_file: bool = True):
    args = [bin_, "negcontrol"] + (["--file", "auth_service.py"] if use_file else []) + [
        "--break-cmd", break_cmd, "--test-cmd", "python3 test_x.py"]
    if restore is not None:
        args += ["--restore-cmd", restore]
    if timeout:
        args += ["--timeout", str(timeout)]
    if expect and supports_expect:
        args += ["--expect", expect]
    return sh(args, cwd=d, timeout=60)


def run_matrix(bins: dict[str, str]) -> dict:
    results = []
    clean = {}
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        faults = build_lint_faults(root)
        clean_full = make_run(root, "clean_full")
        clean_bypass = make_run(root, "clean_bypass", plan=plan_bypass())
        conds = ["C1", "C2", "C3", "C3b", "C4"]

        def lint(c, d):
            if c == "C1":  # unittest over the (unchanged) code: nothing in documents can fail it
                code = root / "code_ok"
                if not code.exists():
                    code.mkdir()
                    (code / "auth_service.py").write_text(GOOD_SERVICE)
                    (code / "test_x.py").write_text(REAL)
                return sh([sys.executable, "test_x.py"], cwd=code)[0]
            if c == "C2":
                return c2_checklist(d)
            return sh([bins[c], "lint", str(d)])[0]

        for name, d in (("clean_full", clean_full), ("clean_bypass", clean_bypass)):
            clean[name] = {c: lint(c, d) for c in conds}

        for fid, cat, desc, d in faults:
            row = {"id": fid, "category": cat, "description": desc, "kind": "document"}
            for c in conds:
                row[c] = lint(c, d) != 0
            results.append(row)

        # F13..F16: code-level faults. C1/C2 have no negative-control mechanism: not applicable.
        specs = [
            ("F13", "Hollow test: passes with the tenant guard removed", TAUTOLOGICAL, BREAK_GUARD, "403 Forbidden", None, 5),
            ("F14", "Mutation is a SyntaxError that mimics a caught failure", REAL, BREAK_SYNTAX, "AssertionError|PermissionError not raised", None, 5),
            ("F15", "Buggy restore command leaves the guard disabled", REAL, BREAK_GUARD, "PermissionError not raised", "true", 5),
            ("F16", "Mutation causes a hang (infinite loop)", REAL, BREAK_HANG, "PermissionError", None, 1),
        ]
        for fid, desc, test_src, brk, expect, restore, to in specs:
            row = {"id": fid, "category": "Test oracle", "description": desc, "kind": "code",
                   "C1": None, "C2": None}
            for c in ("C3", "C3b", "C4"):
                d = lab(root, f"{fid}_{c}", test_src)
                # F15 models a buggy restore with no --file backup; with --file the tool restores from backup
                rc, out = negcontrol(bins[c], d, brk, expect, c != "C3", restore, to, use_file=(fid != "F15"))
                row[c] = rc != 0
                row[f"{c}_output"] = out.strip().splitlines()[-1] if out.strip() else ""
            results.append(row)

        # positive control: a correct negative control must exit 0 in every aepkit version
        pos = {}
        for c in ("C3", "C3b", "C4"):
            d = lab(root, f"pos_{c}", REAL)
            rc, _ = negcontrol(bins[c], d, BREAK_GUARD, "PermissionError not raised", c != "C3", None, 5)
            pos[c] = rc

        # latency of the mechanical checks on the clean fixture (RQ3), 10 trials each
        lat = {}
        for label, cmd in (("lint", "lint"), ("status", "status")):
            xs = []
            for _ in range(10):
                t0 = time.perf_counter()
                sh([bins["C4"], cmd, str(clean_full)])
                xs.append((time.perf_counter() - t0) * 1000)
            lat[label] = {"mean_ms": round(statistics.mean(xs), 1), "sd_ms": round(statistics.stdev(xs), 1)}

    doc = [r for r in results if r["kind"] == "document"]
    code = [r for r in results if r["kind"] == "code"]
    summary = {}
    for c in ("C1", "C2", "C3", "C3b", "C4"):
        summary[c] = {
            "document_faults_caught": sum(1 for r in doc if r[c]),
            "document_faults_total": len(doc),
            "code_faults_caught": (None if c in ("C1", "C2") else sum(1 for r in code if r[c])),
            "code_faults_total": len(code),
        }
    return {"summary": summary, "false_positives_on_clean": clean,
            "positive_control_exit_codes": pos, "latency_ms_clean_fixture": lat,
            "faults": results, "versions": {k: v[0] for k, v in VERSIONS.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).parent / "results" / "fault_matrix.json"))
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as t:
        bins = make_venvs(Path(t))
        data = run_matrix(bins)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    for c, s in data["summary"].items():
        print(c, s)
    print("false positives on clean artifacts (exit codes):", data["false_positives_on_clean"])
    print("positive control exit codes:", data["positive_control_exit_codes"])
    print("latency:", data["latency_ms_clean_fixture"])


if __name__ == "__main__":
    main()
