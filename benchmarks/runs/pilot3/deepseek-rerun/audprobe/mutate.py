"""Guard-test strength audit: apply one mutant at a time to a COPY of the
delivery and re-run the delivered suite. A mutant that survives is a behavior
the delivered tests do not guard. The delivery itself is never modified.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

SRC = pathlib.Path("/tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-2")
PY = "/tmp/aep-lab/v060/bin/python"

MUTANTS = [
    ("M1 forecast: floor after summing instead of per opportunity (spec: per opp)",
     [('                weighted += opp["amount"] * _STAGE_WEIGHTS[stage] // 100',
       '                weighted += opp["amount"] * _STAGE_WEIGHTS[stage]')],
     [('        return {"open": open_count, "weighted": weighted, "won": won}',
       '        return {"open": open_count, "weighted": weighted // 100, "won": won}')]),
    ("M2 owner tie-break: numeric id order instead of string order",
     [('        candidates.sort(key=lambda item: (item[0], item[1]))',
       '        candidates.sort(key=lambda item: (item[0], int(item[1][1:])))')]),
    ("M3 advance: apply the >50000 manager gate to 'lost' too (spec: negotiation only)",
     [('        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):',
       '        if stage in ("negotiation", "lost") and opp["amount"] > 50000 and not self._is_manager(actor):')]),
    ("M4 forecast: weight original_amount instead of current amount",
     [('                weighted += opp["amount"] * _STAGE_WEIGHTS[stage] // 100',
       '                weighted += opp["original_amount"] * _STAGE_WEIGHTS[stage] // 100')]),
    ("M5 transfer: check manager before opportunity existence",
     [('        opp = self._get_opp(opp_id)\n'
       '        if not self._is_manager(actor):\n'
       '            raise PermissionError("only managers may transfer opportunities")',
       '        if not self._is_manager(actor):\n'
       '            raise PermissionError("only managers may transfer opportunities")\n'
       '        opp = self._get_opp(opp_id)')]),
    ("M6 discount: check final stage before permission",
     [('        if opp["owner"] != actor and not self._is_manager(actor):\n'
       '            raise PermissionError("actor may not discount this opportunity")\n'
       '        if opp["stage"] in _FINAL_STAGES:\n'
       '            raise ValueError("opportunity is already final")',
       '        if opp["stage"] in _FINAL_STAGES:\n'
       '            raise ValueError("opportunity is already final")\n'
       '        if opp["owner"] != actor and not self._is_manager(actor):\n'
       '            raise PermissionError("actor may not discount this opportunity")')]),
    ("M7 add_lead: append a log entry before failing name validation (atomicity)",
     [('        if not isinstance(name, str) or not name.strip():\n'
       '            raise ValueError("name must be a non-empty string")',
       '        if not isinstance(name, str) or not name.strip():\n'
       '            self.log.append(("add_lead", "X", actor))\n'
       '            raise ValueError("name must be a non-empty string")')]),
    ("M8 qualify: append a log entry before rejecting a non-owner (atomicity)",
     [('        if lead["owner"] != actor and not self._is_manager(actor):\n'
       '            raise PermissionError("actor may not qualify this lead")',
       '        if lead["owner"] != actor and not self._is_manager(actor):\n'
       '            self.log.append(("qualify", lead_id, actor))\n'
       '            raise PermissionError("actor may not qualify this lead")')]),
    # --- positive controls: these SHOULD be caught ---
    ("C1 control: transfer stops freeing the previous owner's slot",
     [('        self._assign_waiting(previous_owner)',
       '        pass  # control')]),
    ("C2 control: email rule no longer rejects leading/trailing dots",
     [('        if domain.startswith(".") or domain.endswith(".") or "." not in domain:',
       '        if "." not in domain:')]),
    ("C3 control: waiting queue assigned LIFO instead of FIFO",
     [('            lead_id = self.waiting.popleft()',
       '            lead_id = self.waiting.pop()')]),
    ("C4 control: load ignores open opportunities",
     [('            if opp["owner"] == rep_id and opp["stage"] in _OPEN_STAGES:',
       '            if opp["owner"] == rep_id and opp["stage"] in _OPEN_STAGES and False:')]),
]


def run_suite(work):
    proc = subprocess.run(
        [PY, "-m", "unittest", "discover", "-s", str(work), "-p", "test*.py"],
        cwd=str(work), capture_output=True, text=True,
    )
    tail = proc.stderr.strip().splitlines()
    ran = next((l for l in tail if l.startswith("Ran ")), "?")
    failed = [l for l in tail if l.startswith(("FAIL:", "ERROR:"))]
    return proc.returncode, ran, failed


results = []
for entry in MUTANTS:
    name = entry[0]
    edits = [pair for group in entry[1:] for pair in group]
    work = pathlib.Path(tempfile.mkdtemp(dir="/tmp/aep-lab/pilot3/deepseek-rerun/audprobe", prefix="mut-"))
    for f in ("crm.py", "test_crm_core.py", "test_crm_workflow.py"):
        shutil.copy(SRC / f, work / f)
    text = (work / "crm.py").read_text()
    ok = True
    for old, new in edits:
        if old not in text:
            ok = False
            break
        text = text.replace(old, new, 1)
    if not ok:
        print("!! mutation text not found:", name)
        shutil.rmtree(work)
        continue
    (work / "crm.py").write_text(text)
    rc, ran, failed = run_suite(work)
    survived = rc == 0
    results.append((name, survived, ran, failed))
    shutil.rmtree(work)

print("delivered suite vs mutants (survived == delivered tests do NOT guard it)\n")
for name, survived, ran, failed in results:
    print("%-9s %-12s %s" % ("SURVIVED" if survived else "caught", ran, name))
    for line in failed[:3]:
        print("            ", line)
