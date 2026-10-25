"""Negative control: remove the permission check (rule 3)."""

import pathlib

P = pathlib.Path("/tmp/aep-lab/pilot/AE-neutral-3/refunds.py")

OLD = '''    # 3. Permission.
    _check_permission(order, actor)
'''

NEW = '''    # 3. Permission check REMOVED by negative control.
'''

source = P.read_text()
if OLD not in source:
    raise SystemExit("anchor missing")
P.write_text(source.replace(OLD, NEW, 1))
