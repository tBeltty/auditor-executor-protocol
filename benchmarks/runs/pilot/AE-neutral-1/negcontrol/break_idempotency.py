#!/usr/bin/env python3
"""Negative control: remove the idempotency guard (rule 1).

Run from anywhere; edits refunds.py in place.
"""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")
OLD = '    if idempotency_key in order["keys"]:\n        return order["keys"][idempotency_key]'
NEW = '    if False:  # negcontrol: idempotency guard removed\n        return order["keys"][idempotency_key]'


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_idempotency: already applied")
        return 0
    if OLD not in source:
        print("break_idempotency: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_idempotency: idempotency short-circuit disabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
