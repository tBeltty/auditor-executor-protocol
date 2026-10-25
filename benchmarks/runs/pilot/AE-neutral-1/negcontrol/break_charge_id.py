#!/usr/bin/env python3
"""Negative control: stop forwarding the order's charge id to the gateway.

The guard is `gateway.refund(order["charge_id"], amount)`. The break pins the
first argument to "ch_1", the id used by almost every fixture, so a fixture
that reuses "ch_1" cannot tell the two apart. Only an order with a different
charge id can notice that the wrong charge was refunded.
"""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")

OLD = '    refund_id = gateway.refund(order["charge_id"], amount)'
NEW = '    refund_id = gateway.refund("ch_1", amount)  # negcontrol: charge id hard-coded'


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_charge_id: already applied")
        return 0
    if OLD not in source:
        print("break_charge_id: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_charge_id: gateway always charged ch_1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
