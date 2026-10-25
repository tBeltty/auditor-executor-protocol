"""Negative control: remove the refundable-cap check (rule 5)."""

import pathlib

P = pathlib.Path("/tmp/aep-lab/pilot/AE-neutral-3/refunds.py")

OLD = '''    # 5. Amount must not exceed what is still refundable.
    _check_cap(order, amount)
'''

NEW = '''    # 5. Refundable-cap check REMOVED by negative control.
'''

source = P.read_text()
if OLD not in source:
    raise SystemExit("anchor missing")
P.write_text(source.replace(OLD, NEW, 1))
