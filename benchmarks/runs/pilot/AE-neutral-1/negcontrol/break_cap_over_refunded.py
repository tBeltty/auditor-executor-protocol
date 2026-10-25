#!/usr/bin/env python3
"""Negative control: skip the refundable cap when the remainder is negative.

The guard is `if amount > remaining:` with `remaining = paid - refunded`. For a
degenerate order (refunded > paid) the remainder is negative and every positive
amount is rejected. The break adds the plausible-looking "defensive" condition
`remaining >= 0`, i.e. it stops enforcing the cap exactly when the order data is
already inconsistent, and the over-refund then goes through to the gateway.
"""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")

OLD = '''    remaining = order["paid"] - order["refunded"]
    if amount > remaining:'''

NEW = '''    remaining = order["paid"] - order["refunded"]
    if remaining >= 0 and amount > remaining:  # negcontrol: cap skipped on a negative remainder'''


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_cap_over_refunded: already applied")
        return 0
    if OLD not in source:
        print("break_cap_over_refunded: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_cap_over_refunded: cap no longer applies to an over-refunded order")
    return 0


if __name__ == "__main__":
    sys.exit(main())
