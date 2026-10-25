"""Remove exactly one guard from refunds.py so a negative control can prove a test catches it.

Usage: python3 break_guard.py <guard-name>
Exit status 1 if the guard's source text is not found (never silently no-op).
"""

import pathlib
import sys

# Resolved relative to this script so the control still breaks the right file if the
# tree is re-run from a copy rather than in place.
TARGET = pathlib.Path(__file__).resolve().parent.parent / "refunds.py"

BREAKS = {
    "idempotency": (
        '    if idempotency_key in order["keys"]:\n'
        '        return order["keys"][idempotency_key]\n',
        "    if False:\n"
        '        return order["keys"][idempotency_key]\n',
    ),
    "amount": (
        "    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:\n",
        "    if False:\n",
    ),
    "permission": (
        "    if not _may_refund(order, actor):\n"
        '        raise PermissionError("actor %r may not refund this order" % (actor.get("id"),))\n',
        "    if False:\n"
        '        raise PermissionError("actor %r may not refund this order" % (actor.get("id"),))\n',
    ),
    "status": (
        '    if order["status"] not in ("paid", "partially_refunded"):\n',
        "    if False:\n",
    ),
    "cap": (
        "    if amount > remaining:\n",
        "    if False:\n",
    ),
    "gateway-failure-atomicity": (
        "    # Rule 6: exactly one gateway call; a gateway failure leaves the order intact.\n"
        "    try:\n"
        '        refund_id = gateway.refund(order["charge_id"], amount)\n',
        "    # Rule 6: exactly one gateway call; a gateway failure leaves the order intact.\n"
        '    order["refunded"] += amount\n'
        "    try:\n"
        '        refund_id = gateway.refund(order["charge_id"], amount)\n',
    ),
}


def main(argv):
    if len(argv) != 2 or argv[1] not in BREAKS:
        sys.stderr.write("usage: break_guard.py {%s}\n" % "|".join(BREAKS))
        return 2
    old, new = BREAKS[argv[1]]
    source = TARGET.read_text()
    if source.count(old) != 1:
        sys.stderr.write("guard %r not found exactly once in %s\n" % (argv[1], TARGET))
        return 1
    TARGET.write_text(source.replace(old, new))
    print("guard removed: %s" % argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
