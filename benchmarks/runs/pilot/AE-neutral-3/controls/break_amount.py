"""Negative control: remove amount validation (rule 2)."""

import pathlib

P = pathlib.Path("/tmp/aep-lab/pilot/AE-neutral-3/refunds.py")

OLD = '''    # 2. Amount must be a positive int (bool is not an int for our purposes).
    _check_amount_type(amount)
'''

NEW = '''    # 2. Amount validation REMOVED by negative control.
'''

source = P.read_text()
if OLD not in source:
    raise SystemExit("anchor missing")
P.write_text(source.replace(OLD, NEW, 1))
