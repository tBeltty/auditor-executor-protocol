#!/usr/bin/env python3
"""Negative control: remove gateway-failure atomicity (rule 6).

The guard is the ordering: `order` is written only after the gateway accepts.
The break hoists the write above the gateway call and never rolls it back, so a
GatewayError leaves the order half-refunded. Success-path behaviour is
identical, which keeps the break surgical: only the atomicity tests can notice.
"""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")

OLD = '''    refund_id = gateway.refund(order["charge_id"], amount)

    # 7. Commit only after the gateway has accepted the refund.
    new_refunded = order["refunded"] + amount
    new_status = "refunded" if new_refunded == order["paid"] else "partially_refunded"
    order["refunded"] = new_refunded
    order["status"] = new_status
'''

NEW = '''    # negcontrol: write first, call the gateway second, never roll back
    new_refunded = order["refunded"] + amount
    new_status = "refunded" if new_refunded == order["paid"] else "partially_refunded"
    order["refunded"] = new_refunded
    order["status"] = new_status
    refund_id = gateway.refund(order["charge_id"], amount)
'''


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_atomicity: already applied")
        return 0
    if OLD not in source:
        print("break_atomicity: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_atomicity: order written before the gateway call, no rollback")
    return 0


if __name__ == "__main__":
    sys.exit(main())
