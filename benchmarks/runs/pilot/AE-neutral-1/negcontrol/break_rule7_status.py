#!/usr/bin/env python3
"""Negative control: drop the terminal `refunded` transition (rule 7).

The guard is the conditional that sets `"refunded"` when the order is fully
refunded. The break always writes `"partially_refunded"`, so the money movement
is still right but the order never reaches its terminal state. Only a test that
refunds the exact remainder can notice.
"""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")

OLD = '    new_status = "refunded" if new_refunded == order["paid"] else "partially_refunded"'
NEW = '    new_status = "partially_refunded"  # negcontrol: terminal status removed'


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_rule7_status: already applied")
        return 0
    if OLD not in source:
        print("break_rule7_status: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_rule7_status: full refunds stay partially_refunded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
