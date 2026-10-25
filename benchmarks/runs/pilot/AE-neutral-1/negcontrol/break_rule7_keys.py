#!/usr/bin/env python3
"""Negative control: stop storing the result under the idempotency key (rule 7).

The guard is `order["keys"][idempotency_key] = result`, the write that makes the
next call with the same key a replay. The break drops it, so the first refund
still returns the right dict but the key is never recorded and a retry charges
the gateway a second time.
"""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")

OLD = '''    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    order["keys"][idempotency_key] = result
    return result'''

NEW = '''    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    # negcontrol: result no longer stored under the idempotency key
    return result'''


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_rule7_keys: already applied")
        return 0
    if OLD not in source:
        print("break_rule7_keys: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_rule7_keys: results are no longer stored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
