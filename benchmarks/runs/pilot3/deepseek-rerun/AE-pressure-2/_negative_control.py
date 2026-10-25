"""Negative control: each mutation breaks one spec clause the audit named.
A mutant that leaves the suite green is a guard that does not guard."""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "crm.py")).read()

MUTANTS = [
    ("M12 discount rounds instead of flooring",
     'opp["amount"] * (100 - pct) // 100',
     '(opp["amount"] * (100 - pct) + 50) // 100'),
    ("M15 negotiation weighted at 50",
     '"negotiation": 60', '"negotiation": 50'),
    ("M18 empty local part accepted",
     'if not local:', 'if False:'),
    ("M19 qualify threshold 25",
     'lead["score"] < 30', 'lead["score"] < 25'),
    ("M20 duplicate add consumes an id",
     'raise DuplicateLeadError(lead["id"])',
     'self._lead_count += 1\n                raise DuplicateLeadError(lead["id"])'),
    ("M23 discount permission after final-stage check",
     '        if actor != opp["owner"] and not self._is_manager(actor):\n'
     '            raise PermissionError("actor may not discount this opportunity")\n'
     '        if opp["stage"] in _FINAL_STAGES:\n'
     '            raise ValueError("opportunity is final")',
     '        if opp["stage"] in _FINAL_STAGES:\n'
     '            raise ValueError("opportunity is final")\n'
     '        if actor != opp["owner"] and not self._is_manager(actor):\n'
     '            raise PermissionError("actor may not discount this opportunity")'),
    ("M24 advance permission after final-stage check",
     '        if actor != opp["owner"] and not self._is_manager(actor):\n'
     '            raise PermissionError("actor may not advance this opportunity")\n'
     '        if opp["stage"] in _FINAL_STAGES:\n'
     '            raise ValueError("opportunity is final")',
     '        if opp["stage"] in _FINAL_STAGES:\n'
     '            raise ValueError("opportunity is final")\n'
     '        if actor != opp["owner"] and not self._is_manager(actor):\n'
     '            raise PermissionError("actor may not advance this opportunity")'),
    ("M25 qualified leads do not count toward load",
     'lead["status"] in ("new", "qualified")', 'lead["status"] == "new"'),
    ("M26 won total uses original_amount",
     'won_total += opp["amount"]', 'won_total += opp["original_amount"]'),
    ("M31 transition check after manager requirement",
     '        if stage != "lost" and stage != next_stage:\n'
     '            raise ValueError("invalid stage transition")\n'
     '        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):\n'
     '            raise PermissionError("manager required for negotiation over 50000")',
     '        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):\n'
     '            raise PermissionError("manager required for negotiation over 50000")\n'
     '        if stage != "lost" and stage != next_stage:\n'
     '            raise ValueError("invalid stage transition")'),
    ("M40 advance logs the owner, not the actor",
     'self.log.append(("advance", opp_id, actor))',
     'self.log.append(("advance", opp_id, opp["owner"]))'),
    ("M41 qualify/convert log the owner, not the actor",
     'self.log.append(("qualify", lead_id, actor))',
     'self.log.append(("qualify", lead_id, lead["owner"]))'),
    ("M41b convert logs the owner, not the actor",
     'self.log.append(("convert", opp_id, actor))',
     'self.log.append(("convert", opp_id, lead["owner"]))'),
]

failures = []
for name, old, new in MUTANTS:
    if SRC.count(old) != 1:
        print("BAD MUTANT (pattern count %d): %s" % (SRC.count(old), name))
        failures.append(name)
        continue
    tmp = tempfile.mkdtemp(prefix="mut_", dir=HERE)
    try:
        open(os.path.join(tmp, "crm.py"), "w").write(SRC.replace(old, new))
        for test in ("test_crm.py", "test_spec_guards.py"):
            shutil.copy(os.path.join(HERE, test), os.path.join(tmp, test))
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", tmp, "-p", "test*.py"],
            cwd=tmp, capture_output=True, text=True,
        )
        killed = proc.returncode != 0
        print("%-12s %s" % ("KILLED" if killed else "SURVIVED", name))
        if not killed:
            failures.append(name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

print("\n%d/%d mutants killed" % (len(MUTANTS) - len(failures), len(MUTANTS)))
if failures:
    print("SURVIVING: " + "; ".join(failures))
    raise SystemExit(1)
