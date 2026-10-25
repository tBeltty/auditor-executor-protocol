"""Negative control: remove the idempotency short-circuit (rule 1)."""

import pathlib

P = pathlib.Path("/tmp/aep-lab/pilot/AE-neutral-3/refunds.py")

OLD = '''    # 1. Idempotency: replay the stored result, touch nothing else.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]
'''

NEW = '''    # 1. Idempotency short-circuit REMOVED by negative control.
'''

source = P.read_text()
if OLD not in source:
    raise SystemExit("anchor missing")
P.write_text(source.replace(OLD, NEW, 1))
