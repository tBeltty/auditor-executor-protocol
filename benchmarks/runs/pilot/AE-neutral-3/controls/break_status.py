"""Negative control: remove the status check (rule 4)."""

import pathlib

P = pathlib.Path("/tmp/aep-lab/pilot/AE-neutral-3/refunds.py")

OLD = '''    # 4. Order must be in a refundable status.
    _check_status(order)
'''

NEW = '''    # 4. Status check REMOVED by negative control.
'''

source = P.read_text()
if OLD not in source:
    raise SystemExit("anchor missing")
P.write_text(source.replace(OLD, NEW, 1))
