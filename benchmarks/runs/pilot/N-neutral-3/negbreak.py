"""Negative-control break helper: removes exactly one guard from refunds.py.

Usage: python3 negbreak.py <guard>
Guards: idempotency | amount | permission | status | cap | atomicity

Every break targets a `# GUARD:<name>` marker and asserts that the marker was
found exactly once, so a silent no-op break can never fake a control.
"""

import sys
from pathlib import Path

PATH = Path(__file__).with_name("refunds.py")

BREAKS = {
    "idempotency": (
        '    if idempotency_key in keys:  # GUARD:idempotency\n',
        '    if False:  # GUARD:idempotency\n',
    ),
    "amount": (
        '    if not _is_positive_int(amount):  # GUARD:amount\n',
        '    if False:  # GUARD:amount\n',
    ),
    "permission": (
        '    if not _is_authorized(actor, order):  # GUARD:permission\n',
        '    if False:  # GUARD:permission\n',
    ),
    "status": (
        '    if order["status"] not in _VALID_REFUND_STATUSES:  # GUARD:status\n',
        '    if False:  # GUARD:status\n',
    ),
    "cap": (
        '    if amount > remaining:  # GUARD:cap\n',
        '    if False:  # GUARD:cap\n',
    ),
    "atomicity": (
        '    except GatewayError:\n'
        '        raise  # GUARD:atomicity\n',
        '    except GatewayError:\n'
        '        order["refunded"] += amount  # GUARD:atomicity removed\n'
        '        raise\n',
    ),
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in BREAKS:
        sys.exit("usage: negbreak.py {%s}" % "|".join(BREAKS))
    old, new = BREAKS[sys.argv[1]]
    source = PATH.read_text()
    count = source.count(old)
    if count != 1:
        sys.exit("marker for %r matched %d times (expected 1)" % (sys.argv[1], count))
    PATH.write_text(source.replace(old, new, 1))
    print("broke guard: %s" % sys.argv[1])


if __name__ == "__main__":
    main()
