"""Negative-control breaker: removes or reorders one guard in refunds.py.

Used by `aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py <guard>"`.
aepkit restores refunds.py from its backup after each control.

Whole-block modes ("idempotency", "amount", "permission", "status", "cap")
delete that guard. "atomicity" moves the order mutation in front of the
gateway call. The "order-*" modes permute two guard blocks to violate the
spec's "Rules, checked in this order" contract.
"""

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().parent / "refunds.py"

AMOUNT_BLOCK = '''    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("amount must be a positive int")

'''

PERMISSION_BLOCK = '''    if not _may_refund(actor, order):
        raise PermissionError("actor may not refund this order")

'''

STATUS_BLOCK = '''    if order["status"] not in _REFUNDABLE_STATUSES:
        raise ValueError("order is not in a refundable state")

'''

CAP_BLOCK = '''    if amount > order["paid"] - order["refunded"]:
        raise ValueError("amount exceeds the refundable balance")

'''

REMOVALS = {
    "idempotency": '''    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

''',
    "amount": AMOUNT_BLOCK,
    "permission": PERMISSION_BLOCK,
    "status": STATUS_BLOCK,
    "cap": CAP_BLOCK,
}

# (source span, replacement) pairs that reorder the guard blocks.
SWAPS = {
    "order-amount-permission": (
        AMOUNT_BLOCK + PERMISSION_BLOCK,
        PERMISSION_BLOCK + AMOUNT_BLOCK,
    ),
    "order-permission-status": (
        PERMISSION_BLOCK + STATUS_BLOCK,
        STATUS_BLOCK + PERMISSION_BLOCK,
    ),
    "order-status-cap": (
        STATUS_BLOCK + CAP_BLOCK,
        CAP_BLOCK + STATUS_BLOCK,
    ),
    "order-cap-permission": (
        PERMISSION_BLOCK + STATUS_BLOCK + CAP_BLOCK,
        CAP_BLOCK + STATUS_BLOCK + PERMISSION_BLOCK,
    ),
}

GATEWAY_CALL = '    refund_id = gateway.refund(order["charge_id"], amount)\n'
ATOMICITY_BREAK = (
    '    order["refunded"] += amount\n'
    '    refund_id = gateway.refund(order["charge_id"], amount)\n'
)


def main(guard):
    source = TARGET.read_text()
    if guard == "atomicity":
        old, new = GATEWAY_CALL, ATOMICITY_BREAK
    elif guard in REMOVALS:
        old, new = REMOVALS[guard], ""
    elif guard in SWAPS:
        old, new = SWAPS[guard]
    else:
        raise SystemExit("unknown guard: %s" % guard)
    if source.count(old) != 1:
        raise SystemExit("guard snippet not found exactly once: %s" % guard)
    TARGET.write_text(source.replace(old, new))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
